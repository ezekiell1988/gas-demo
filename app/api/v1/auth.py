"""
Endpoints de autenticación con QuickBooks API.
Maneja el flujo OAuth2 para conectar con QuickBooks Online.
"""

from fastapi import APIRouter, HTTPException, Query, Response, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import secrets
import base64
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer

from app.utils.quickbooks_auth import quickbooks_auth
from app.core.settings import settings
from app.core.http_request import HTTPClient

logger = logging.getLogger(__name__)

router = APIRouter()


class OAuthConfig(BaseModel):
    """Configuración de OAuth2 para QuickBooks."""
    client_id: str
    client_secret: str
    redirect_uri: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "ABcsbItNHsBXZBhJUE54khDqCRot2r4aA80p1t6Ky6MMo5q4O8",
                "client_secret": "786UBsaZkU9c31R3yz4WlU0beOqqHxCeqw87IXtk",
                "redirect_uri": "http://localhost:8001/api/v1/auth/callback"
            }
        }


# Configuración OAuth desde variables de entorno
def get_oauth_config() -> Optional[OAuthConfig]:
    """Obtiene la configuración OAuth desde las variables de entorno."""
    if settings.quickbooks_client_id and settings.quickbooks_client_secret:
        return OAuthConfig(
            client_id=settings.quickbooks_client_id,
            client_secret=settings.quickbooks_client_secret,
            redirect_uri=settings.quickbooks_redirect_uri
        )
    return None


# Inicializar configuración OAuth al arrancar
oauth_config: Optional[OAuthConfig] = get_oauth_config()

# Almacenar state para validación CSRF (en producción usar Redis o base de datos)
active_states: dict = {}

# Almacenar tokens por sesión (en producción usar Redis)
# Estructura: {session_id: {access_token, refresh_token, token_expiry, realm_id}}
user_sessions: Dict[str, Dict[str, Any]] = {}

# Serializador para firmar cookies de forma segura
SECRET_KEY = settings.quickbooks_client_secret or secrets.token_urlsafe(32)
serializer = URLSafeTimedSerializer(SECRET_KEY)


@router.get(
    "/auth/login",
    tags=["Authentication"],
    summary="Iniciar sesión con QuickBooks",
    description="Inicia el flujo de autenticación OAuth2 con QuickBooks. Redirige al usuario a la página de autorización de QuickBooks."
)
async def login(response: Response):
    """
    Inicia el flujo de autenticación OAuth2 con QuickBooks.
    
    **Abre este endpoint en tu navegador:** http://localhost:8002/api/v1/auth/login
    
    Redirige a QuickBooks para autorización.
    Genera un state aleatorio para prevenir ataques CSRF.
    Crea una sesión única para el usuario.
    """
    if not oauth_config:
        raise HTTPException(
            status_code=400,
            detail="OAuth2 no configurado. Verifica QUICKBOOKS_CLIENT_ID y QUICKBOOKS_CLIENT_SECRET en .env"
        )
    
    # Generar session_id único para este usuario
    session_id = secrets.token_urlsafe(32)
    
    # Generar state aleatorio seguro para prevenir CSRF
    state = secrets.token_urlsafe(32)
    # Asociar state con session_id
    active_states[state] = session_id
    
    # Crear cookie de sesión temporal (se actualizará en callback)
    response = RedirectResponse(url="")
    response.set_cookie(
        key="qb_session",
        value=serializer.dumps(session_id),
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=3600  # 1 hora
    )
    
    auth_url = await quickbooks_auth.get_authorization_url(
        client_id=oauth_config.client_id,
        redirect_uri=oauth_config.redirect_uri,
        state=state
    )
    
    response.headers["location"] = auth_url
    response.status_code = 302
    
    logger.info(f"🚀 Redirigiendo a QuickBooks: {auth_url}")
    logger.info(f"🔐 State generado: {state}")
    logger.info(f"🆔 Session ID: {session_id}")
    return response


@router.get(
    "/auth/callback",
    tags=["Authentication"],
    summary="Callback de OAuth2",
    description="Endpoint de callback que recibe el código de autorización desde QuickBooks y lo intercambia por tokens de acceso."
)
async def oauth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    realmId: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """
    Callback de OAuth2 desde QuickBooks (automático).
    Valida el state para prevenir ataques CSRF según la documentación oficial.
    Guarda los tokens en la sesión del usuario específico.
    """
    if error:
        logger.error(f"❌ Error OAuth: {error}")
        raise HTTPException(status_code=400, detail=f"Error OAuth: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Código de autorización no recibido")
    
    # Validar state para prevenir CSRF
    if not state or state not in active_states:
        logger.error(f"❌ State inválido o no encontrado: {state}")
        raise HTTPException(
            status_code=400,
            detail="State inválido. Posible ataque CSRF. Inicie el proceso de login nuevamente."
        )
    
    # Obtener session_id asociado al state
    session_id = active_states.pop(state, None)
    
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 no configurado")
    
    try:
        token_data = await quickbooks_auth.exchange_code_for_token(
            code=code,
            client_id=oauth_config.client_id,
            client_secret=oauth_config.client_secret,
            redirect_uri=oauth_config.redirect_uri
        )
        
        # Guardar tokens en la sesión del usuario
        expires_in = token_data.get("expires_in", 3600)
        user_sessions[session_id] = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "token_expiry": datetime.now() + timedelta(seconds=expires_in),
            "realm_id": realmId
        }
        
        logger.info(f"✅ Autenticación exitosa para sesión {session_id}")
        logger.info(f"✅ Company ID (realmId): {realmId}")
        logger.info(f"✅ Tokens guardados en sesión, redirigiendo a /")
        
        # Crear respuesta con redirect y asegurar que la cookie esté presente
        response = RedirectResponse(url="/", status_code=302)
        response.set_cookie(
            key="qb_session",
            value=serializer.dumps(session_id),
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=3600,  # 1 hora
            path="/"
        )
        
        return response
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/auth/status",
    tags=["Authentication"],
    summary="Verificar estado de autenticación",
    description="Obtiene el estado actual de la autenticación con QuickBooks, incluyendo validez del token y fecha de expiración."
)
async def auth_status(request: Request):
    """
    Verifica el estado de autenticación de la sesión actual del usuario.
    Lee la cookie de sesión y verifica si el usuario está autenticado.
    """
    # Obtener cookie de sesión
    session_cookie = request.cookies.get("qb_session")
    
    if not session_cookie:
        return {
            "authenticated": False,
            "token_valid": False,
            "realm_id": None,
            "expires_at": None
        }
    
    try:
        # Deserializar session_id de la cookie firmada
        session_id = serializer.loads(session_cookie, max_age=3600)
        
        # Verificar si existe sesión para este usuario
        if session_id not in user_sessions:
            return {
                "authenticated": False,
                "token_valid": False,
                "realm_id": None,
                "expires_at": None
            }
        
        session_data = user_sessions[session_id]
        token_expiry = session_data.get("token_expiry")
        
        # Verificar si el token sigue siendo válido
        token_valid = token_expiry and datetime.now() < (token_expiry - timedelta(minutes=5))
        
        return {
            "authenticated": True,
            "token_valid": token_valid,
            "realm_id": session_data.get("realm_id"),
            "expires_at": token_expiry.isoformat() if token_expiry else None
        }
        
    except Exception as e:
        logger.error(f"❌ Error verificando sesión: {str(e)}")
        return {
            "authenticated": False,
            "token_valid": False,
            "realm_id": None,
            "expires_at": None
        }


@router.post(
    "/auth/refresh",
    tags=["Authentication"],
    summary="Renovar token de acceso",
    description="Renueva el access_token usando el refresh_token. Devuelve nuevos tokens y actualiza la sesión."
)
async def refresh_token(request: Request):
    """
    Renueva el access_token usando el refresh_token.
    
    QuickBooks tokens expiran después de 1 hora.
    Este endpoint usa el refresh_token para obtener nuevos tokens.
    
    **Importante:**
    - Access token válido: 1 hora (3600 segundos)
    - Refresh token válido: 100 días (8726400 segundos)
    - Cada refresh devuelve NUEVOS access_token Y refresh_token
    """
    # Obtener cookie de sesión
    session_cookie = request.cookies.get("qb_session")
    
    if not session_cookie:
        raise HTTPException(
            status_code=401,
            detail="No autenticado. Debe llamar a /auth/login primero"
        )
    
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 no configurado")
    
    try:
        # Deserializar session_id de la cookie firmada
        session_id = serializer.loads(session_cookie, max_age=3600)
        
        # Verificar si existe sesión para este usuario
        if session_id not in user_sessions:
            raise HTTPException(
                status_code=401,
                detail="Sesión no encontrada. Debe autenticarse nuevamente"
            )
        
        session_data = user_sessions[session_id]
        refresh_token_value = session_data.get("refresh_token")
        
        if not refresh_token_value:
            raise HTTPException(
                status_code=401,
                detail="Refresh token no disponible. Debe autenticarse nuevamente"
            )
        
        # Preparar credenciales en formato Basic Auth
        credentials = f"{oauth_config.client_id}:{oauth_config.client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        # Llamar al endpoint de refresh de QuickBooks
        client = HTTPClient()
        url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        # Body como form-urlencoded
        body = f"grant_type=refresh_token&refresh_token={refresh_token_value}"
        
        logger.info(f"🔄 Renovando token para sesión {session_id}")
        
        response = await client.post(url, headers=headers, data=body)
        
        if response.status == 200:
            token_data = await response.json()
            
            # Actualizar sesión con nuevos tokens
            expires_in = token_data.get("expires_in", 3600)
            user_sessions[session_id].update({
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "token_expiry": datetime.now() + timedelta(seconds=expires_in)
            })
            
            logger.info(f"✅ Token renovado exitosamente para sesión {session_id}")
            
            return {
                "status": "success",
                "message": "Token renovado exitosamente",
                "expires_in": expires_in,
                "token_expiry": user_sessions[session_id]["token_expiry"].isoformat()
            }
        else:
            error_text = await response.text()
            logger.error(f"❌ Error renovando token: {response.status} - {error_text}")
            raise HTTPException(
                status_code=response.status,
                detail=f"Error renovando token: {error_text}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error renovando token: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno renovando token: {str(e)}"
        )


@router.post(
    "/auth/logout",
    tags=["Authentication"],
    summary="Cerrar sesión",
    description="Revoca el refresh_token en QuickBooks y limpia la sesión local."
)
async def logout(request: Request, response: Response):
    """
    Cierra la sesión del usuario.
    
    Realiza dos acciones:
    1. Revoca el refresh_token en QuickBooks (también revoca el access_token)
    2. Elimina la sesión del servidor y limpia la cookie
    
    **Nota:** Revocar el refresh_token automáticamente revoca el access_token asociado.
    """
    # Obtener cookie de sesión
    session_cookie = request.cookies.get("qb_session")
    
    if not session_cookie:
        # No hay sesión, simplemente limpiar cookie
        response.delete_cookie("qb_session")
        return {
            "status": "success",
            "message": "Sesión cerrada (no había sesión activa)"
        }
    
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 no configurado")
    
    try:
        # Deserializar session_id de la cookie firmada
        session_id = serializer.loads(session_cookie, max_age=3600)
        
        # Verificar si existe sesión para este usuario
        if session_id in user_sessions:
            session_data = user_sessions[session_id]
            refresh_token_value = session_data.get("refresh_token")
            
            if refresh_token_value:
                # Preparar credenciales en formato Basic Auth
                credentials = f"{oauth_config.client_id}:{oauth_config.client_secret}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                
                # Llamar al endpoint de revoke de QuickBooks
                client = HTTPClient()
                url = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
                headers = {
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                body = {"token": refresh_token_value}
                
                logger.info(f"🚪 Revocando token para sesión {session_id}")
                
                try:
                    revoke_response = await client.post(url, headers=headers, json_data=body)
                    
                    if revoke_response.status == 200:
                        logger.info(f"✅ Token revocado exitosamente en QuickBooks")
                    else:
                        error_text = await revoke_response.text()
                        logger.warning(f"⚠️ Error revocando token en QuickBooks: {revoke_response.status} - {error_text}")
                except Exception as revoke_error:
                    logger.warning(f"⚠️ Error revocando token en QuickBooks: {str(revoke_error)}")
            
            # Eliminar sesión del servidor
            user_sessions.pop(session_id, None)
            logger.info(f"✅ Sesión {session_id} eliminada del servidor")
        
        # Limpiar cookie
        response.delete_cookie("qb_session")
        
        return {
            "status": "success",
            "message": "Sesión cerrada exitosamente"
        }
        
    except Exception as e:
        logger.error(f"❌ Error cerrando sesión: {str(e)}")
        # Aún así limpiar la cookie
        response.delete_cookie("qb_session")
        return {
            "status": "success",
            "message": "Sesión cerrada (con advertencias)"
        }

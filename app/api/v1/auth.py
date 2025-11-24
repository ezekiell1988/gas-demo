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
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer

from app.utils.quickbooks_auth import quickbooks_auth
from app.core.settings import settings

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
        
        return RedirectResponse(url="/", status_code=302)
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

"""
Endpoints de autenticación con QuickBooks API.
Maneja el flujo OAuth2 para conectar con QuickBooks Online.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import logging
import secrets

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


@router.get(
    "/auth/login",
    tags=["Authentication"],
    summary="Iniciar sesión con QuickBooks",
    description="Inicia el flujo de autenticación OAuth2 con QuickBooks. Redirige al usuario a la página de autorización de QuickBooks."
)
async def login():
    """
    Inicia el flujo de autenticación OAuth2 con QuickBooks.
    
    **Abre este endpoint en tu navegador:** http://localhost:8002/api/v1/auth/login
    
    Redirige a QuickBooks para autorización.
    Genera un state aleatorio para prevenir ataques CSRF.
    """
    if not oauth_config:
        raise HTTPException(
            status_code=400,
            detail="OAuth2 no configurado. Verifica QUICKBOOKS_CLIENT_ID y QUICKBOOKS_CLIENT_SECRET en .env"
        )
    
    # Generar state aleatorio seguro para prevenir CSRF
    state = secrets.token_urlsafe(32)
    active_states[state] = True
    
    auth_url = await quickbooks_auth.get_authorization_url(
        client_id=oauth_config.client_id,
        redirect_uri=oauth_config.redirect_uri,
        state=state
    )
    
    logger.info(f"🚀 Redirigiendo a QuickBooks: {auth_url}")
    logger.info(f"🔐 State generado: {state}")
    return RedirectResponse(url=auth_url)


@router.get(
    "/auth/callback",
    tags=["Authentication"],
    summary="Callback de OAuth2",
    description="Endpoint de callback que recibe el código de autorización desde QuickBooks y lo intercambia por tokens de acceso."
)
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    realmId: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """
    Callback de OAuth2 desde QuickBooks (automático).
    Valida el state para prevenir ataques CSRF según la documentación oficial.
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
    
    # Remover state usado (un solo uso)
    active_states.pop(state, None)
    
    if not oauth_config:
        raise HTTPException(status_code=400, detail="OAuth2 no configurado")
    
    if realmId:
        quickbooks_auth.realm_id = realmId
        logger.info(f"✅ Company ID (realmId): {realmId}")
    
    try:
        token_data = await quickbooks_auth.exchange_code_for_token(
            code=code,
            client_id=oauth_config.client_id,
            client_secret=oauth_config.client_secret,
            redirect_uri=oauth_config.redirect_uri
        )
        
        return {
            "status": "success",
            "message": "Autenticación exitosa",
            "realm_id": realmId,
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_in": token_data.get("expires_in")
        }
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/auth/status",
    tags=["Authentication"],
    summary="Verificar estado de autenticación",
    description="Obtiene el estado actual de la autenticación con QuickBooks, incluyendo validez del token y fecha de expiración."
)
async def auth_status():
    """
    Verifica el estado de autenticación.
    """
    return {
        "authenticated": quickbooks_auth.access_token is not None,
        "token_valid": quickbooks_auth.is_token_valid(),
        "realm_id": quickbooks_auth.realm_id,
        "expires_at": quickbooks_auth.token_expiry.isoformat() if quickbooks_auth.token_expiry else None
    }

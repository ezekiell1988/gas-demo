"""
Utilidad para manejar la autenticación con QuickBooks API.
Gestiona tokens de acceso, refresh tokens y credenciales OAuth2.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import base64
import json
from urllib.parse import urlencode

from app.core.settings import settings
from app.core.http_request import HTTPClient

logger = logging.getLogger(__name__)


class QuickBooksAuth:
    """
    Maneja la autenticación OAuth2 con QuickBooks API.
    
    QuickBooks usa OAuth 2.0 para autenticación. Este módulo gestiona:
    - Obtención de tokens de acceso
    - Refresh de tokens expirados
    - Almacenamiento de tokens en memoria
    - Headers de autenticación para peticiones
    """
    
    def __init__(self):
        """Inicializa el manejador de autenticación de QuickBooks."""
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self.realm_id: str = settings.quickbooks_company_id
        
        # URLs de OAuth2 para QuickBooks
        self.auth_url = "https://appcenter.intuit.com/connect/oauth2"
        self.token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        self.revoke_url = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
        
        # Cliente HTTP para peticiones de autenticación
        self.http_client = HTTPClient()
        
    def _get_basic_auth_header(self, client_id: str, client_secret: str) -> str:
        """
        Genera el header de autenticación básica para OAuth2.
        
        Args:
            client_id: ID del cliente de QuickBooks
            client_secret: Secret del cliente de QuickBooks
            
        Returns:
            Header de autorización Basic codificado en base64
        """
        credentials = f"{client_id}:{client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def get_authorization_url(
        self,
        client_id: str,
        redirect_uri: str,
        state: Optional[str] = None,
        scope: str = "com.intuit.quickbooks.accounting openid profile email phone address"
    ) -> str:
        """
        Genera la URL de autorización para redirigir al usuario.
        
        Según la documentación oficial de QuickBooks OAuth 2.0:
        https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/oauth-2.0
        
        Args:
            client_id: ID del cliente de QuickBooks
            redirect_uri: URI de redirección después de la autorización
            state: Estado para prevenir CSRF (recomendado)
            scope: Alcance de permisos solicitados. Debe incluir:
                   - com.intuit.quickbooks.accounting (acceso a datos contables)
                   - openid (requerido para OpenID Connect)
                   - profile, email, phone, address (información del usuario, opcional)
            
        Returns:
            URL completa de autorización con parámetros correctamente codificados
        """
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state or ""
        }
        
        # Usar urlencode para codificar correctamente los parámetros según RFC 3986
        query_string = urlencode(params)
        return f"{self.auth_url}?{query_string}"
    
    async def exchange_code_for_token(
        self,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Intercambia el código de autorización por tokens de acceso.
        
        Args:
            code: Código de autorización recibido del callback
            client_id: ID del cliente de QuickBooks
            client_secret: Secret del cliente de QuickBooks
            redirect_uri: URI de redirección (debe coincidir con la registrada)
            
        Returns:
            Diccionario con access_token, refresh_token, expires_in, etc.
            
        Raises:
            Exception: Si hay error en la petición de token
        """
        headers = {
            "Authorization": self._get_basic_auth_header(client_id, client_secret),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        logger.info(f"Intercambiando código por token con QuickBooks")
        
        try:
            response = await self.http_client.post(
                self.token_url,
                headers=headers,
                data=data
            )
            
            if response.status == 200:
                token_data = await response.json()
                
                # Guardar tokens en memoria
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                
                # Calcular expiración (generalmente 3600 segundos = 1 hora)
                expires_in = token_data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("✅ Token de acceso obtenido exitosamente")
                return token_data
            else:
                error_text = await response.text()
                logger.error(f"❌ Error obteniendo token: {response.status} - {error_text}")
                raise Exception(f"Error obteniendo token: {error_text}")
                
        except Exception as e:
            logger.error(f"❌ Excepción intercambiando código por token: {str(e)}")
            raise
    
    async def refresh_access_token(
        self,
        client_id: str,
        client_secret: str
    ) -> Dict[str, Any]:
        """
        Refresca el token de acceso usando el refresh token.
        
        Args:
            client_id: ID del cliente de QuickBooks
            client_secret: Secret del cliente de QuickBooks
            
        Returns:
            Diccionario con el nuevo access_token y refresh_token
            
        Raises:
            Exception: Si no hay refresh token o hay error en la petición
        """
        if not self.refresh_token:
            raise Exception("No hay refresh token disponible")
        
        headers = {
            "Authorization": self._get_basic_auth_header(client_id, client_secret),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        logger.info("Refrescando token de acceso de QuickBooks")
        
        try:
            response = await self.http_client.post(
                self.token_url,
                headers=headers,
                data=data
            )
            
            if response.status == 200:
                token_data = await response.json()
                
                # Actualizar tokens
                self.access_token = token_data.get("access_token")
                self.refresh_token = token_data.get("refresh_token")
                
                # Actualizar expiración
                expires_in = token_data.get("expires_in", 3600)
                self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("✅ Token de acceso refrescado exitosamente")
                return token_data
            else:
                error_text = await response.text()
                logger.error(f"❌ Error refrescando token: {response.status} - {error_text}")
                raise Exception(f"Error refrescando token: {error_text}")
                
        except Exception as e:
            logger.error(f"❌ Excepción refrescando token: {str(e)}")
            raise
    
    async def revoke_token(
        self,
        client_id: str,
        client_secret: str,
        token: Optional[str] = None
    ) -> bool:
        """
        Revoca un token de acceso o refresh token.
        
        Args:
            client_id: ID del cliente de QuickBooks
            client_secret: Secret del cliente de QuickBooks
            token: Token a revocar (por defecto usa el refresh_token actual)
            
        Returns:
            True si se revocó exitosamente
        """
        token_to_revoke = token or self.refresh_token
        if not token_to_revoke:
            logger.warning("No hay token para revocar")
            return False
        
        headers = {
            "Authorization": self._get_basic_auth_header(client_id, client_secret),
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "token": token_to_revoke
        }
        
        try:
            response = await self.http_client.post(
                self.revoke_url,
                headers=headers,
                json_data=payload
            )
            
            if response.status == 200:
                logger.info("✅ Token revocado exitosamente")
                # Limpiar tokens locales
                self.access_token = None
                self.refresh_token = None
                self.token_expiry = None
                return True
            else:
                error_text = await response.text()
                logger.error(f"❌ Error revocando token: {response.status} - {error_text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción revocando token: {str(e)}")
            return False
    
    def is_token_valid(self) -> bool:
        """
        Verifica si el token actual es válido y no ha expirado.
        
        Returns:
            True si el token es válido y no ha expirado
        """
        if not self.access_token or not self.token_expiry:
            return False
        
        # Considerar el token inválido 5 minutos antes de que expire
        return datetime.now() < (self.token_expiry - timedelta(minutes=5))
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Obtiene los headers de autenticación para peticiones al API.
        
        Returns:
            Diccionario con los headers de autenticación
            
        Raises:
            Exception: Si no hay token de acceso válido
        """
        if not self.access_token:
            raise Exception("No hay token de acceso disponible. Debe autenticarse primero.")
        
        if not self.is_token_valid():
            logger.warning("⚠️ El token de acceso ha expirado. Debe refrescarse.")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def set_tokens(
        self,
        access_token: str,
        refresh_token: str,
        expires_in: int = 3600
    ):
        """
        Establece manualmente los tokens (útil para restaurar sesión).
        
        Args:
            access_token: Token de acceso
            refresh_token: Token de refresco
            expires_in: Tiempo de expiración en segundos
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
        logger.info("✅ Tokens establecidos manualmente")
    
    def get_company_url(self, endpoint: str) -> str:
        """
        Construye la URL completa para un endpoint de la API de QuickBooks.
        
        Args:
            endpoint: Endpoint relativo (ej: "customer", "employee")
            
        Returns:
            URL completa con company ID
        """
        base_url = settings.quickbooks_base_url
        company_id = self.realm_id
        
        # Remover slash inicial si existe
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        
        return f"{base_url}/company/{company_id}/{endpoint}"


# Instancia global del manejador de autenticación
quickbooks_auth = QuickBooksAuth()

"""
Modelos Pydantic para autenticación.
"""

from pydantic import BaseModel


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

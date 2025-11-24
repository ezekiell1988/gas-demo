from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuraciones de la aplicación cargadas desde variables de entorno."""
    
    # Configuración del servidor
    port: int = 8001
    environment: str = "development"
    allow_origins: str = "http://localhost:8001,http://127.0.0.1:8001"
    
    @property
    def origins_list(self) -> List[str]:
        """Convierte la cadena de orígenes separada por comas en una lista."""
        return [origin.strip() for origin in self.allow_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Permitir campos extra en caso de que se agreguen nuevas variables
        extra = "ignore"

# Instancia global de configuración
settings = Settings()
from fastapi import APIRouter
from .health import router as health_router

# Router principal para todos los endpoints de la API
router = APIRouter()

# Incluir routers de módulos específicos
router.include_router(health_router, prefix="/v1")
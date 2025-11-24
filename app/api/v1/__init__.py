from fastapi import APIRouter
from .health import router as health_router
from .auth import router as auth_router
from .employees import router as employees_router

# Router principal para todos los endpoints de la API
router = APIRouter()

# Incluir routers de módulos específicos
router.include_router(health_router, prefix="/v1")
router.include_router(auth_router, prefix="/v1")
router.include_router(employees_router, prefix="/v1")
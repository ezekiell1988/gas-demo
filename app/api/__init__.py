from fastapi import APIRouter
from .v1 import router as v1_router

# Router principal para todos los endpoints de la API
api_router = APIRouter()

# Incluir routers de módulos específicos
api_router.include_router(v1_router)
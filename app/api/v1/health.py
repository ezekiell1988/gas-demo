from fastapi import APIRouter

# Router principal para todos los endpoints de la API
router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de salud para verificar que la API está funcionando."""
    return {"status": "ok"}
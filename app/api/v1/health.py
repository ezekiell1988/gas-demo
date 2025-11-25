from fastapi import APIRouter
from datetime import datetime

# Router principal para todos los endpoints de la API
router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """Endpoint de salud para verificar que la API está funcionando."""
    now = datetime.now()
    return {
        "status": "ok",
        "server_time": now.strftime("%I:%M:%S %p"),
        "timestamp": now.isoformat()
    }
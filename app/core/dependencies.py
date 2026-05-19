"""
Shared FastAPI dependencies for the application.
"""
from services.shiprocket_service import ShiprocketService
from core.config import settings


async def get_shiprocket_service() -> ShiprocketService:
    """Dependency to get authenticated ShiprocketService instance"""
    service = ShiprocketService(
        email=settings.SHIPROCKET_EMAIL,
        password=settings.SHIPROCKET_PASSWORD
    )
    await service.authenticate()
    return service

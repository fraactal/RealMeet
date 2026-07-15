from fastapi import APIRouter

from app.api.routes import admin, appointments, auth, availability, categories, integrations, metrics, professionals, specialties, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(specialties.router, prefix="/specialties", tags=["specialties"])
api_router.include_router(professionals.router, prefix="/professionals", tags=["professionals"])
api_router.include_router(availability.router, tags=["availability"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(metrics.router, tags=["metrics"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

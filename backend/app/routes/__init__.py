from fastapi import APIRouter

from app.routes.auth import router as auth_routes
from app.routes.photos import router as photo_routes
from app.routes.profile import router as profile_routes

router = APIRouter(prefix="/api")
router.include_router(auth_routes)
router.include_router(profile_routes)
router.include_router(photo_routes)

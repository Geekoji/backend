from fastapi import APIRouter
from shared.api import routers as system

from .routes import auth, oauth2, token

__all__ = [
    "router",
]

router = APIRouter()

router.include_router(auth.router)
router.include_router(oauth2.router)
router.include_router(token.router)
router.include_router(system.router)

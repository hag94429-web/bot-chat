from .user import router as user_router
from .shop import router as shop_router
from .stars import router as stars_router

routers = [
    user_router,
    shop_router,
    stars_router
]


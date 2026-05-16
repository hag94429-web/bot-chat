from .activity import router as activity_router
from .cases import router as cases_router
from .duel import router as duel_router
from .economy import router as economy_router
from .inventory import router as inventory_router
from .shop_weapons import router as shop_weapons_router
from .shop import router as shop_router
from .stars import router as stars_router
from .user import router as user_router

routers = [
    user_router,
    cases_router,
    duel_router,
    economy_router,
    inventory_router,
    shop_weapons_router,
    shop_router,
    stars_router,
    activity_router
]

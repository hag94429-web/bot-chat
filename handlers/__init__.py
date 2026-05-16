from .profile import router as profile_router
from .daily import router as daily_router
from .bonus import router as bonus_router
from .top import router as top_router

from .shop import router as shop_router
from .stars_shop import router as stars_shop_router

from .cases import router as cases_router
from .roulette import router as roulette_router

from .duel import router as duel_router
from .inventory import router as inventory_router
from .shop_weapons import router as shop_weapons_router

from .payments import router as payments_router

from .activity import router as activity_router

routers = [
    profile_router,
    daily_router,
    bonus_router,
    top_router,

    shop_router,
    stars_shop_router,

    cases_router,
    roulette_router,

    duel_router,
    inventory_router,
    shop_weapons_router,

    payments_router,

    activity_router
]
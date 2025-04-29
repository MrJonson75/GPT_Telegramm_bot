from aiogram import Router

from .command import comm_router
from .random_fact import rand_router

all_handlers = Router()
all_handlers.include_routers(
    comm_router,
    rand_router,
)


__all__ = [
    'all_handlers',
           ]
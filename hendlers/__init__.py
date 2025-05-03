from aiogram import Router

from .command import comm_router
from .random_fact import rand_router
from .gpt_interface import gpt_router
from .talk import talk_router
from .trans import trans_router
from .quiz import quiz_router


all_handlers = Router()
all_handlers.include_routers(
    comm_router,
    rand_router,
    gpt_router,
    talk_router,
    trans_router,
    quiz_router,

)


__all__ = [
    'all_handlers',
           ]
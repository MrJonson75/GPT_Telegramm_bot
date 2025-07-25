from aiogram import Router

from .command import comm_router
from .random_fact import rand_router
from .gpt_interface import gpt_router
from .talk import talk_router
from .trans import trans_router
from .quiz import quiz_router
from .voice_gpt import voice_router


all_handlers = Router()
all_handlers.include_routers(
    comm_router,
    trans_router,
    rand_router,
    gpt_router,
    quiz_router,
    talk_router,
    voice_router,

)


__all__ = [
    'all_handlers',
           ]
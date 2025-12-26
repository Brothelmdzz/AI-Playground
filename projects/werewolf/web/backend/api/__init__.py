# ==================== API 路由 ====================
from .games import router as games_router
from .benchmark import router as benchmark_router
from .websocket import router as ws_router
from .config import router as config_router

__all__ = ["games_router", "benchmark_router", "ws_router", "config_router"]

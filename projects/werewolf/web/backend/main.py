# ==================== FastAPI 主入口 ====================
"""AI 狼人杀 Web 后端"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api import games_router, benchmark_router, ws_router, config_router


app = FastAPI(
    title="AI Werewolf",
    description="AI 狼人杀游戏服务器",
    version="0.3.0",
)

# CORS 配置（开发环境）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(games_router)
app.include_router(benchmark_router)
app.include_router(ws_router)
app.include_router(config_router)


@app.get("/")
async def root():
    """健康检查"""
    return {
        "name": "AI Werewolf Server",
        "version": "0.3.0",
        "status": "running",
    }


@app.get("/api/health")
async def health():
    """API 健康检查"""
    return {"status": "healthy"}


# 静态文件（前端打包后）
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

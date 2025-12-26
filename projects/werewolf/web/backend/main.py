# ==================== FastAPI 主入口 ====================
"""AI 狼人杀 Web 后端"""

from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path

from .api import games_router, benchmark_router, ws_router, config_router

# 访问密码
ACCESS_PASSWORD = "caoji123"


class PasswordMiddleware(BaseHTTPMiddleware):
    """简单的密码保护中间件"""

    async def dispatch(self, request: Request, call_next):
        # 检查是否已经通过 cookie 验证
        if request.cookies.get("access_token") == ACCESS_PASSWORD:
            return await call_next(request)

        # 检查 URL 参数中的密码
        password = request.query_params.get("password")
        if password == ACCESS_PASSWORD:
            response = await call_next(request)
            response.set_cookie("access_token", ACCESS_PASSWORD, max_age=86400)  # 24小时
            return response

        # 登录页面和验证接口不需要密码
        if request.url.path in ["/login", "/api/health"]:
            return await call_next(request)

        # 显示登录页面
        return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>AI 狼人杀 - 访问验证</title>
    <meta charset="utf-8">
    <style>
        body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 40px rgba(0,0,0,0.3); text-align: center; }
        h1 { color: #333; margin-bottom: 20px; }
        input { padding: 12px 20px; font-size: 16px; border: 2px solid #ddd; border-radius: 5px; margin-bottom: 15px; width: 200px; }
        button { padding: 12px 30px; font-size: 16px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; }
        button:hover { background: #5a6fd6; }
    </style>
</head>
<body>
    <div class="box">
        <h1>🐺 AI 狼人杀</h1>
        <p>请输入访问密码</p>
        <form method="get">
            <input type="password" name="password" placeholder="密码" autofocus><br>
            <button type="submit">进入游戏</button>
        </form>
    </div>
</body>
</html>
        """, status_code=200)


app = FastAPI(
    title="AI Werewolf",
    description="AI 狼人杀游戏服务器",
    version="0.3.0",
)

# 密码保护中间件
app.add_middleware(PasswordMiddleware)

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

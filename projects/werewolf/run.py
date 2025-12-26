#!/usr/bin/env python3
# ==================== 一键启动脚本 ====================
"""
启动 AI 狼人杀 Web 服务

用法:
    python run.py          # 开发模式（前后端热重载）
    python run.py --prod   # 生产模式（使用打包后的前端）
    python run.py --build  # 先打包前端再启动
"""

import os
import sys
import subprocess
import argparse
import signal
import time
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).parent
BACKEND_DIR = ROOT / "web" / "backend"
FRONTEND_DIR = ROOT / "web" / "frontend"


def check_dependencies():
    """检查依赖"""
    # 检查 Python 包
    try:
        import fastapi
        import uvicorn
    except ImportError:
        print("安装后端依赖...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-q",
            "fastapi", "uvicorn[standard]", "websockets", "pyyaml"
        ], check=True)

    # 检查 Node.js
    if not (FRONTEND_DIR / "node_modules").exists():
        print("安装前端依赖...")
        subprocess.run(["npm", "install"], cwd=FRONTEND_DIR, shell=True, check=True)


def build_frontend():
    """打包前端"""
    print("打包前端...")
    subprocess.run(["npm", "run", "build"], cwd=FRONTEND_DIR, shell=True, check=True)
    print("前端打包完成: web/frontend/dist/")


def run_dev():
    """开发模式：同时启动前后端"""
    check_dependencies()

    processes = []

    try:
        # 启动后端
        print("\n[*] Starting backend (http://localhost:8000)...")
        backend_env = os.environ.copy()
        backend_env["PYTHONPATH"] = str(ROOT)

        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn",
             "web.backend.main:app",
             "--reload",
             "--host", "0.0.0.0",
             "--port", "8000"],
            cwd=ROOT,
            env=backend_env,
        )
        processes.append(backend_proc)

        time.sleep(2)  # 等待后端启动

        # 启动前端
        print("\n[*] Starting frontend (http://localhost:3000)...")
        frontend_proc = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=True,
        )
        processes.append(frontend_proc)

        print("\n" + "=" * 50)
        print("AI Werewolf Started!")
        print("=" * 50)
        print(f"Frontend: http://localhost:3000")
        print(f"Backend:  http://localhost:8000")
        print(f"API Docs: http://localhost:8000/docs")
        print(f"Settings: http://localhost:3000/settings")
        print("=" * 50)
        print("Press Ctrl+C to stop\n")

        # 等待进程
        for proc in processes:
            proc.wait()

    except KeyboardInterrupt:
        print("\n\nStopping services...")
    finally:
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                proc.kill()
        print("Services stopped.")


def run_prod():
    """生产模式：使用打包后的前端"""
    check_dependencies()

    dist_dir = FRONTEND_DIR / "dist"
    if not dist_dir.exists():
        print("未找到前端打包文件，正在打包...")
        build_frontend()

    print("\n[*] Starting production server (http://localhost:8000)...")

    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = str(ROOT)

    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn",
             "web.backend.main:app",
             "--host", "0.0.0.0",
             "--port", "8000"],
            cwd=ROOT,
            env=backend_env,
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")


def main():
    parser = argparse.ArgumentParser(description="AI 狼人杀 Web 服务")
    parser.add_argument("--prod", action="store_true", help="生产模式")
    parser.add_argument("--build", action="store_true", help="打包前端")
    parser.add_argument("--port", type=int, default=8000, help="后端端口")

    args = parser.parse_args()

    os.chdir(ROOT)

    if args.build:
        check_dependencies()
        build_frontend()
    elif args.prod:
        run_prod()
    else:
        run_dev()


if __name__ == "__main__":
    main()

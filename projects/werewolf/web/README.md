# AI 狼人杀 Web 可视化

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TS)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │ GameBoard│ │ ChatPanel│ │ Controls │ │ BenchmarkDashboard││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘│
│       └────────────┴────────────┴────────────────┘          │
│                            │                                 │
│                    WebSocket + REST                          │
└────────────────────────────┼─────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │ REST API │ │WebSocket │ │GameManager│ │  BenchmarkRunner ││
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘│
│       └────────────┴────────────┴────────────────┘          │
│                            │                                 │
│                     Game Engine                              │
└──────────────────────────────────────────────────────────────┘
```

## 目录结构

```
web/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── api/
│   │   ├── games.py         # 游戏管理 API
│   │   ├── benchmark.py     # Benchmark API
│   │   └── websocket.py     # WebSocket 处理
│   ├── services/
│   │   ├── game_service.py  # 游戏服务
│   │   └── benchmark_service.py
│   └── models/
│       └── schemas.py       # Pydantic 模型
│
└── frontend/
    ├── package.json
    ├── src/
    │   ├── App.tsx
    │   ├── components/
    │   │   ├── GameBoard.tsx    # 游戏主界面
    │   │   ├── PlayerCard.tsx   # 玩家卡片
    │   │   ├── ChatPanel.tsx    # 聊天/发言面板
    │   │   ├── ActionPanel.tsx  # 行动面板
    │   │   ├── GameControls.tsx # 控制按钮
    │   │   └── BenchmarkDashboard.tsx
    │   ├── hooks/
    │   │   ├── useWebSocket.ts
    │   │   └── useGame.ts
    │   ├── types/
    │   │   └── game.ts
    │   └── styles/
    └── public/
```

## API 设计

### REST Endpoints

| Method | Path | 说明 |
|--------|------|------|
| POST | /api/games | 创建游戏 |
| GET | /api/games | 列出游戏 |
| GET | /api/games/{id} | 获取游戏状态 |
| POST | /api/games/{id}/join | 加入游戏 |
| POST | /api/games/{id}/start | 开始游戏 |
| POST | /api/benchmark | 启动 Benchmark |
| GET | /api/benchmark/{id} | 获取 Benchmark 结果 |

### WebSocket Events

**Server → Client:**
- `game_state`: 游戏状态更新
- `player_action`: 玩家行动
- `phase_change`: 阶段变更
- `game_over`: 游戏结束

**Client → Server:**
- `submit_action`: 提交行动
- `speak`: 发言
- `vote`: 投票

## 启动方式

```bash
# 后端
cd web/backend
pip install -r requirements.txt
uvicorn main:app --reload

# 前端
cd web/frontend
npm install
npm run dev
```

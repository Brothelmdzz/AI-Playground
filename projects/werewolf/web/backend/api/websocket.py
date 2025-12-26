# ==================== WebSocket 处理 ====================
"""实时游戏通信"""

from __future__ import annotations
import asyncio
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models.schemas import GameState, GameEvent, WSMessage
from ..services.game_service import game_service

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # game_id -> set of websockets
        self.game_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> (game_id, player_id)
        self.connection_info: Dict[WebSocket, tuple] = {}

    async def connect(self, websocket: WebSocket, game_id: str, player_id: int = None):
        """建立连接"""
        await websocket.accept()

        if game_id not in self.game_connections:
            self.game_connections[game_id] = set()

        self.game_connections[game_id].add(websocket)
        self.connection_info[websocket] = (game_id, player_id)

        # 注册状态变更回调
        session = await game_service.get_session(game_id)
        if session:
            session.on_state_change = lambda state: self._broadcast_state(game_id, state)
            session.on_event = lambda event: self._broadcast_event(game_id, event)

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        if websocket in self.connection_info:
            game_id, _ = self.connection_info[websocket]
            if game_id in self.game_connections:
                self.game_connections[game_id].discard(websocket)
            del self.connection_info[websocket]

    async def _broadcast_state(self, game_id: str, state: GameState):
        """广播游戏状态"""
        if game_id not in self.game_connections:
            return

        message = {
            "type": "game_state",
            "data": state.model_dump(),
        }

        await self._broadcast(game_id, message)

    async def _broadcast_event(self, game_id: str, event: GameEvent):
        """广播事件"""
        if game_id not in self.game_connections:
            return

        message = {
            "type": "event",
            "data": event.model_dump(),
        }

        await self._broadcast(game_id, message)

    async def _broadcast(self, game_id: str, message: dict):
        """广播消息到游戏房间"""
        if game_id not in self.game_connections:
            return

        disconnected = set()
        for ws in self.game_connections[game_id]:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)

        # 清理断开的连接
        for ws in disconnected:
            self.disconnect(ws)

    async def send_to_player(self, game_id: str, player_id: int, message: dict):
        """发送消息给特定玩家"""
        if game_id not in self.game_connections:
            return

        for ws in self.game_connections[game_id]:
            info = self.connection_info.get(ws)
            if info and info[1] == player_id:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/game/{game_id}")
async def websocket_game(websocket: WebSocket, game_id: str, player_id: int = None):
    """游戏 WebSocket 端点"""
    await manager.connect(websocket, game_id, player_id)

    try:
        # 发送初始状态
        session = await game_service.get_session(game_id)
        if session:
            state = game_service.get_game_state(session, player_id)
            await websocket.send_json({
                "type": "game_state",
                "data": state.model_dump(),
            })

        # 消息循环
        while True:
            data = await websocket.receive_json()
            await handle_client_message(websocket, game_id, player_id, data)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        print(f"WebSocket error: {e}")


async def handle_client_message(
    websocket: WebSocket,
    game_id: str,
    player_id: int,
    data: dict
):
    """处理客户端消息"""
    msg_type = data.get("type")

    if msg_type == "submit_action":
        # 人类玩家提交行动
        action_type = data.get("action_type")
        target_id = data.get("target_id")

        session = await game_service.get_session(game_id)
        if session and session.game and player_id is not None:
            from werewolf.core.events import Action
            from werewolf.core.enums import ActionType

            try:
                action = Action(
                    action_type=ActionType(action_type),
                    actor_id=player_id,
                    target_id=target_id,
                )
                session.game.submit_action(action)

                await websocket.send_json({
                    "type": "action_submitted",
                    "success": True,
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })

    elif msg_type == "speak":
        # 人类玩家发言
        content = data.get("content", "")

        session = await game_service.get_session(game_id)
        if session:
            event = GameEvent(
                round=session.game.round if session.game else 0,
                phase="day_discussion",
                event_type="speech",
                description=f"Player_{player_id}: {content}",
                details={"player_id": player_id, "content": content},
            )
            session.events.append(event)

            # 广播发言
            await manager._broadcast_event(game_id, event)

    elif msg_type == "ping":
        await websocket.send_json({"type": "pong"})

    else:
        await websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {msg_type}",
        })

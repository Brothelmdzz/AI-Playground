# ==================== 游戏 API ====================
"""游戏管理 REST API"""

from fastapi import APIRouter, HTTPException
from typing import List

from ..models.schemas import (
    CreateGameRequest, CreateGameResponse, JoinGameRequest,
    GameState, GameListItem
)
from ..services.game_service import game_service

router = APIRouter(prefix="/api/games", tags=["games"])


@router.post("", response_model=CreateGameResponse)
async def create_game(request: CreateGameRequest):
    """创建新游戏"""
    session = await game_service.create_game(request)
    return CreateGameResponse(
        game_id=session.game_id,
        join_url=f"/game/{session.game_id}",
    )


@router.get("", response_model=List[GameListItem])
async def list_games():
    """列出所有游戏"""
    return await game_service.list_games()


@router.get("/{game_id}", response_model=GameState)
async def get_game(game_id: str):
    """获取游戏状态"""
    session = await game_service.get_session(game_id)
    if not session:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_service.get_game_state(session)


@router.post("/{game_id}/join")
async def join_game(game_id: str, request: JoinGameRequest):
    """加入游戏"""
    # 注意：实际的 connection_id 应该从 WebSocket 获取
    seat_id = await game_service.join_game(
        game_id,
        request.player_name,
        connection_id="http_client",
        seat_id=request.seat_id,
    )
    if seat_id is None:
        raise HTTPException(status_code=400, detail="Cannot join game")
    return {"seat_id": seat_id, "message": "Joined successfully"}


@router.post("/{game_id}/start")
async def start_game(game_id: str, seed: int = None):
    """开始游戏"""
    print(f"[API] start_game called: game_id={game_id}, seed={seed}", flush=True)
    success = await game_service.start_game(game_id, seed)
    print(f"[API] start_game result: {success}", flush=True)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot start game")
    return {"message": "Game started"}


@router.post("/{game_id}/pause")
async def pause_game(game_id: str):
    """暂停游戏"""
    success = await game_service.pause_game(game_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot pause game")
    return {"message": "Game paused"}


@router.post("/{game_id}/resume")
async def resume_game(game_id: str):
    """恢复游戏"""
    success = await game_service.resume_game(game_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot resume game")
    return {"message": "Game resumed"}


@router.post("/{game_id}/speed")
async def set_speed(game_id: str, speed: float):
    """设置游戏速度"""
    success = await game_service.set_speed(game_id, speed)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot set speed")
    return {"message": f"Speed set to {speed}x"}

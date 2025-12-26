# ==================== Pydantic 模型定义 ====================
"""Web API 数据模型"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 枚举 ====================

class GameMode(str, Enum):
    """游戏模式"""
    AI_VS_AI = "ai_vs_ai"           # 纯 AI 对战
    HUMAN_VS_AI = "human_vs_ai"     # 人类 + AI
    SPECTATE = "spectate"           # 观战模式


class PlayerType(str, Enum):
    """玩家类型"""
    HUMAN = "human"
    AI_RANDOM = "ai_random"
    AI_LLM = "ai_llm"


# ==================== 请求模型 ====================

class CreateGameRequest(BaseModel):
    """创建游戏请求"""
    preset: str = Field(default="6p", description="预设配置: 6p, 9p, 12p")
    mode: GameMode = Field(default=GameMode.AI_VS_AI)
    seed: Optional[int] = Field(default=None, description="随机种子")
    ai_provider: Optional[str] = Field(default=None, description="LLM 提供商: openai, anthropic")
    ai_model: Optional[str] = Field(default=None, description="模型名称")
    speed: float = Field(default=1.0, ge=0.1, le=10.0, description="游戏速度倍率")


class JoinGameRequest(BaseModel):
    """加入游戏请求"""
    player_name: str = Field(..., min_length=1, max_length=20)
    seat_id: Optional[int] = Field(default=None, description="指定座位号")


class SubmitActionRequest(BaseModel):
    """提交行动请求"""
    action_type: str = Field(..., description="行动类型")
    target_id: Optional[int] = Field(default=None, description="目标玩家ID")


class SpeakRequest(BaseModel):
    """发言请求"""
    content: str = Field(..., min_length=1, max_length=500)


class BenchmarkRequest(BaseModel):
    """Benchmark 请求"""
    num_games: int = Field(default=10, ge=1, le=100)
    preset: str = Field(default="6p")
    providers: List[str] = Field(default=["random"])
    models: Optional[Dict[str, str]] = Field(default=None)
    seed: Optional[int] = Field(default=None)


# ==================== 响应模型 ====================

class PlayerInfo(BaseModel):
    """玩家信息"""
    id: int
    name: str
    is_alive: bool
    player_type: PlayerType
    role: Optional[str] = None  # 仅自己或游戏结束后可见
    faction: Optional[str] = None


class GameEvent(BaseModel):
    """游戏事件"""
    round: int
    phase: str
    event_type: str
    description: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class GameState(BaseModel):
    """游戏状态"""
    game_id: str
    status: str  # waiting, running, finished
    phase: str
    round: int
    players: List[PlayerInfo]
    alive_count: int
    events: List[GameEvent] = []
    winner: Optional[str] = None
    current_speaker: Optional[int] = None
    pending_action: Optional[str] = None  # 当前等待的行动类型


class GameListItem(BaseModel):
    """游戏列表项"""
    game_id: str
    status: str
    mode: GameMode
    player_count: int
    created_at: datetime


class CreateGameResponse(BaseModel):
    """创建游戏响应"""
    game_id: str
    join_url: str


class BenchmarkResult(BaseModel):
    """Benchmark 结果"""
    benchmark_id: str
    status: str  # running, completed
    total_games: int
    completed_games: int
    results: Optional[Dict[str, Any]] = None


# ==================== WebSocket 消息 ====================

class WSMessage(BaseModel):
    """WebSocket 消息基类"""
    type: str
    data: Dict[str, Any]


class WSGameStateMessage(BaseModel):
    """游戏状态消息"""
    type: str = "game_state"
    state: GameState


class WSEventMessage(BaseModel):
    """事件消息"""
    type: str = "event"
    event: GameEvent


class WSErrorMessage(BaseModel):
    """错误消息"""
    type: str = "error"
    message: str
    code: Optional[str] = None

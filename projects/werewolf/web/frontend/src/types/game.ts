// ==================== 游戏类型定义 ====================

export type GameMode = 'ai_vs_ai' | 'human_vs_ai' | 'spectate'
export type PlayerType = 'human' | 'ai_random' | 'ai_llm'
export type GameStatus = 'waiting' | 'running' | 'finished' | 'error'

export interface PlayerInfo {
  id: number
  name: string
  is_alive: boolean
  player_type: PlayerType
  role: string | null
  faction: string | null
}

export interface GameEvent {
  round: number
  phase: string
  event_type: string
  description: string
  details?: Record<string, any>
  timestamp: string
}

export interface GameState {
  game_id: string
  status: GameStatus
  phase: string
  round: number
  players: PlayerInfo[]
  alive_count: number
  events: GameEvent[]
  winner: string | null
  current_speaker: number | null
  pending_action: string | null
}

export interface GameListItem {
  game_id: string
  status: GameStatus
  mode: GameMode
  player_count: number
  created_at: string
}

export interface CreateGameRequest {
  preset: string
  mode: GameMode
  seed?: number
  speed?: number
}

export interface BenchmarkResult {
  benchmark_id: string
  status: string
  total_games: number
  completed_games: number
  results?: {
    win_rates: Record<string, number>
    wins: Record<string, number>
    avg_rounds: number
    min_rounds: number
    max_rounds: number
    avg_duration: number
    total_duration: number
  }
}

// WebSocket 消息类型
export interface WSMessage {
  type: string
  data?: any
}

export interface WSGameStateMessage extends WSMessage {
  type: 'game_state'
  data: GameState
}

export interface WSEventMessage extends WSMessage {
  type: 'event'
  data: GameEvent
}

// 角色信息
export const ROLE_COLORS: Record<string, string> = {
  '狼人': '#dc2626',
  '平民': '#16a34a',
  '预言家': '#7c3aed',
  '女巫': '#c026d3',
  '猎人': '#ea580c',
  '守卫': '#0891b2',
}

export const ROLE_ICONS: Record<string, string> = {
  '狼人': '🐺',
  '平民': '👤',
  '预言家': '🔮',
  '女巫': '🧪',
  '猎人': '🏹',
  '守卫': '🛡️',
}

export const PHASE_NAMES: Record<string, string> = {
  'init': '准备中',
  'night': '夜晚',
  'day_discussion': '白天讨论',
  'day_vote': '投票阶段',
  'game_over': '游戏结束',
}

export const FACTION_NAMES: Record<string, string> = {
  'werewolf': '狼人阵营',
  'villager': '村民阵营',
}

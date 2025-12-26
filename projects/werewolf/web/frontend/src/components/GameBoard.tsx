// ==================== 游戏面板 ====================
import type { GameState } from '../types/game'
import { PlayerCard } from './PlayerCard'

interface GameBoardProps {
  gameState: GameState
  selectedPlayer?: number
  onSelectPlayer?: (playerId: number) => void
}

export function GameBoard({ gameState, selectedPlayer, onSelectPlayer }: GameBoardProps) {
  const { players, phase } = gameState
  const isNight = phase === 'night'

  // 计算圆形布局位置
  const getPlayerPosition = (index: number, total: number) => {
    const angle = (index / total) * 2 * Math.PI - Math.PI / 2 // 从顶部开始
    const radius = 42 // 百分比
    const x = 50 + radius * Math.cos(angle)
    const y = 50 + radius * Math.sin(angle)
    return { x, y }
  }

  return (
    <div className={`relative aspect-square rounded-lg shadow-lg overflow-hidden ${
      isNight ? 'bg-gray-900' : 'bg-gradient-to-b from-blue-100 to-blue-200'
    }`}>
      {/* 中央信息 */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className={`text-center ${isNight ? 'text-white' : 'text-gray-800'}`}>
          <div className="text-6xl mb-2">
            {isNight ? '🌙' : phase === 'game_over' ? '🏆' : '☀️'}
          </div>
          <div className="text-xl font-bold">
            {phase === 'night' ? '夜晚' :
             phase === 'day_discussion' ? '讨论中' :
             phase === 'day_vote' ? '投票中' :
             phase === 'game_over' ? '游戏结束' : '进行中'}
          </div>
        </div>
      </div>

      {/* 玩家卡片 */}
      {players.map((player, index) => {
        const pos = getPlayerPosition(index, players.length)
        return (
          <div
            key={player.id}
            className="absolute transform -translate-x-1/2 -translate-y-1/2"
            style={{
              left: `${pos.x}%`,
              top: `${pos.y}%`,
            }}
          >
            <PlayerCard
              player={player}
              isSelected={selectedPlayer === player.id}
              onClick={() => onSelectPlayer?.(player.id)}
              showRole={gameState.status === 'finished'}
            />
          </div>
        )
      })}

      {/* 装饰元素 */}
      {isNight && (
        <div className="absolute top-4 right-4 text-4xl animate-pulse">⭐</div>
      )}
    </div>
  )
}

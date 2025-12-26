// ==================== 玩家卡片 ====================
import type { PlayerInfo } from '../types/game'
import { ROLE_COLORS, ROLE_ICONS } from '../types/game'

interface PlayerCardProps {
  player: PlayerInfo
  isSelected?: boolean
  onClick?: () => void
  showRole?: boolean
}

export function PlayerCard({ player, isSelected, onClick, showRole }: PlayerCardProps) {
  const { name, is_alive, role, faction, player_type } = player

  const roleColor = role ? ROLE_COLORS[role] || '#6b7280' : '#6b7280'
  const roleIcon = role ? ROLE_ICONS[role] || '❓' : '❓'

  return (
    <div
      onClick={onClick}
      className={`
        w-24 p-3 rounded-lg text-center cursor-pointer transition-all duration-200
        ${is_alive
          ? 'bg-white shadow-lg hover:shadow-xl hover:-translate-y-1'
          : 'bg-gray-200 opacity-60'
        }
        ${isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''}
      `}
    >
      {/* 头像 */}
      <div
        className={`
          w-12 h-12 mx-auto rounded-full flex items-center justify-center text-2xl
          ${is_alive ? 'bg-gray-100' : 'bg-gray-300'}
        `}
        style={showRole && role ? { backgroundColor: `${roleColor}20` } : {}}
      >
        {showRole && role ? roleIcon : (is_alive ? '👤' : '💀')}
      </div>

      {/* 名称 */}
      <div className="mt-2 text-sm font-medium truncate" title={name}>
        {name}
      </div>

      {/* 角色标签 */}
      {showRole && role && (
        <div
          className="mt-1 text-xs font-medium px-2 py-0.5 rounded-full"
          style={{
            backgroundColor: `${roleColor}20`,
            color: roleColor,
          }}
        >
          {role}
        </div>
      )}

      {/* AI 标识 */}
      {player_type !== 'human' && (
        <div className="mt-1 text-xs text-gray-400">
          🤖
        </div>
      )}

      {/* 死亡标记 */}
      {!is_alive && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-4xl opacity-50">✖️</div>
        </div>
      )}
    </div>
  )
}

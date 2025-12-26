// ==================== 游戏控制 ====================

interface GameControlsProps {
  isPaused: boolean
  speed: number
  onPauseToggle: () => void
  onSpeedChange: (speed: number) => void
}

export function GameControls({
  isPaused,
  speed,
  onPauseToggle,
  onSpeedChange,
}: GameControlsProps) {
  const speeds = [0.5, 1, 2, 3, 5]

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between">
        {/* 暂停/播放 */}
        <button
          onClick={onPauseToggle}
          className={`btn ${isPaused ? 'btn-success' : 'btn-primary'}`}
        >
          {isPaused ? '▶️ 继续' : '⏸️ 暂停'}
        </button>

        {/* 速度控制 */}
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">速度:</span>
          <div className="flex space-x-1">
            {speeds.map((s) => (
              <button
                key={s}
                onClick={() => onSpeedChange(s)}
                className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                  speed === s
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* 其他控制 */}
        <div className="flex space-x-2">
          <button className="btn bg-gray-200 text-gray-700 hover:bg-gray-300">
            🔄 重播
          </button>
        </div>
      </div>
    </div>
  )
}

// ==================== 游戏页面 ====================
import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { useWebSocket } from '../hooks/useWebSocket'
import { GameBoard } from '../components/GameBoard'
import { ChatPanel } from '../components/ChatPanel'
import { GameControls } from '../components/GameControls'
import type { GameState, GameEvent } from '../types/game'
import { PHASE_NAMES, FACTION_NAMES } from '../types/game'

export function GamePage() {
  const { gameId } = useParams<{ gameId: string }>()
  const { startGame, pauseGame, resumeGame, setSpeed, loading, error } = useApi()

  const [gameState, setGameState] = useState<GameState | null>(null)
  const [events, setEvents] = useState<GameEvent[]>([])
  const [isPaused, setIsPaused] = useState(false)
  const [currentSpeed, setCurrentSpeed] = useState(1)

  const handleStateChange = useCallback((state: GameState) => {
    setGameState(state)
  }, [])

  const handleEvent = useCallback((event: GameEvent) => {
    setEvents((prev) => [...prev, event])
  }, [])

  const { isConnected, submitAction, speak } = useWebSocket({
    gameId: gameId!,
    onStateChange: handleStateChange,
    onEvent: handleEvent,
  })

  // 开始游戏
  const handleStart = async () => {
    await startGame(gameId!)
  }

  // 暂停/恢复
  const handlePauseToggle = async () => {
    if (isPaused) {
      await resumeGame(gameId!)
      setIsPaused(false)
    } else {
      await pauseGame(gameId!)
      setIsPaused(true)
    }
  }

  // 调整速度
  const handleSpeedChange = async (speed: number) => {
    await setSpeed(gameId!, speed)
    setCurrentSpeed(speed)
  }

  if (!gameId) {
    return <div className="text-center py-8">无效的游戏 ID</div>
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* 左侧：游戏面板 */}
      <div className="lg:col-span-2 space-y-4">
        {/* 状态栏 */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {isConnected ? '已连接' : '连接中...'}
              </span>

              {gameState && (
                <>
                  <span className="text-gray-600">
                    第 {gameState.round} 回合
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    gameState.phase === 'night'
                      ? 'bg-gray-800 text-white'
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {PHASE_NAMES[gameState.phase] || gameState.phase}
                  </span>
                  <span className="text-gray-600">
                    存活: {gameState.alive_count} / {gameState.players.length}
                  </span>
                </>
              )}
            </div>

            <div className="text-sm text-gray-500">
              房间: {gameId}
            </div>
          </div>
        </div>

        {/* 游戏主区域 */}
        {gameState && gameState.status !== 'waiting' ? (
          <GameBoard
            gameState={gameState}
            onSelectPlayer={(id) => console.log('Selected:', id)}
          />
        ) : (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <div className="text-6xl mb-4">🐺</div>
            <h2 className="text-xl font-bold mb-4">等待游戏开始</h2>
            <p className="text-gray-500 mb-4">
              {gameState ? `${gameState.players.length} 名玩家已就位` : '加载中...'}
            </p>
            <button
              onClick={handleStart}
              disabled={loading}
              className="btn btn-primary"
            >
              {loading ? '启动中...' : '开始游戏'}
            </button>
          </div>
        )}

        {/* 游戏结束 */}
        {gameState?.winner && (
          <div className={`rounded-lg shadow p-6 text-center ${
            gameState.winner === 'werewolf'
              ? 'bg-red-600 text-white'
              : 'bg-green-600 text-white'
          }`}>
            <div className="text-4xl mb-2">
              {gameState.winner === 'werewolf' ? '🐺' : '🎉'}
            </div>
            <h2 className="text-2xl font-bold">
              {FACTION_NAMES[gameState.winner] || gameState.winner} 获胜！
            </h2>
          </div>
        )}

        {/* 控制栏 */}
        {gameState && gameState.status === 'running' && (
          <GameControls
            isPaused={isPaused}
            speed={currentSpeed}
            onPauseToggle={handlePauseToggle}
            onSpeedChange={handleSpeedChange}
          />
        )}

        {error && (
          <div className="bg-red-50 text-red-600 rounded-lg p-4">
            {error}
          </div>
        )}
      </div>

      {/* 右侧：聊天面板 */}
      <div className="lg:col-span-1">
        <ChatPanel
          events={events}
          onSpeak={speak}
          disabled={!gameState || gameState.phase !== 'day_discussion'}
        />
      </div>
    </div>
  )
}

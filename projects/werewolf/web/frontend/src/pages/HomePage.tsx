// ==================== 首页 ====================
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import type { GameMode } from '../types/game'

export function HomePage() {
  const navigate = useNavigate()
  const { loading, error, createGame } = useApi()

  const [preset, setPreset] = useState('6p')
  const [mode, setMode] = useState<GameMode>('ai_vs_ai')
  const [speed, setSpeed] = useState(1)

  const handleCreate = async () => {
    const result = await createGame({
      preset,
      mode,
      speed,
    })

    if (result) {
      // 创建成功后跳转到游戏页面
      navigate(`/game/${result.game_id}`)
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-3xl font-bold text-center mb-8">
          🐺 AI 狼人杀
        </h1>

        <div className="space-y-6">
          {/* 游戏配置 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              游戏人数
            </label>
            <select
              value={preset}
              onChange={(e) => setPreset(e.target.value)}
              className="w-full p-3 border rounded-lg"
            >
              <option value="6p">6人局（2狼4民）</option>
              <option value="9p">9人局（3狼6民）</option>
              <option value="12p">12人局（4狼8民）</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              游戏模式
            </label>
            <div className="grid grid-cols-3 gap-4">
              <button
                onClick={() => setMode('ai_vs_ai')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  mode === 'ai_vs_ai'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-2">🤖</div>
                <div className="font-medium">AI 对战</div>
                <div className="text-xs text-gray-500">观看 AI 对决</div>
              </button>

              <button
                onClick={() => setMode('human_vs_ai')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  mode === 'human_vs_ai'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-2">👤</div>
                <div className="font-medium">人机对战</div>
                <div className="text-xs text-gray-500">亲自参与</div>
              </button>

              <button
                onClick={() => setMode('spectate')}
                className={`p-4 rounded-lg border-2 transition-colors ${
                  mode === 'spectate'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="text-2xl mb-2">👁️</div>
                <div className="font-medium">观战模式</div>
                <div className="text-xs text-gray-500">上帝视角</div>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              游戏速度: {speed}x
            </label>
            <input
              type="range"
              min="0.5"
              max="5"
              step="0.5"
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>0.5x 慢速</span>
              <span>5x 快速</span>
            </div>
          </div>

          {error && (
            <div className="p-4 bg-red-50 text-red-600 rounded-lg">
              {error}
            </div>
          )}

          <button
            onClick={handleCreate}
            disabled={loading}
            className="w-full btn btn-primary py-4 text-lg font-bold disabled:opacity-50"
          >
            {loading ? '创建中...' : '开始游戏'}
          </button>
        </div>
      </div>

      {/* 游戏规则 */}
      <div className="mt-8 bg-white rounded-lg shadow-lg p-8">
        <h2 className="text-xl font-bold mb-4">游戏规则</h2>
        <div className="grid md:grid-cols-2 gap-6 text-sm">
          <div>
            <h3 className="font-bold text-red-600 mb-2">🐺 狼人阵营</h3>
            <p className="text-gray-600">
              夜晚统一选择一名玩家击杀。白天隐藏身份，投票淘汰好人。
              当狼人数量 ≥ 好人数量时获胜。
            </p>
          </div>
          <div>
            <h3 className="font-bold text-green-600 mb-2">👤 好人阵营</h3>
            <p className="text-gray-600">
              白天讨论，投票淘汰狼人。
              当所有狼人被淘汰时获胜。
            </p>
          </div>
          <div>
            <h3 className="font-bold text-purple-600 mb-2">🔮 预言家</h3>
            <p className="text-gray-600">每晚查验一名玩家的阵营。</p>
          </div>
          <div>
            <h3 className="font-bold text-pink-600 mb-2">🧪 女巫</h3>
            <p className="text-gray-600">一瓶解药救人，一瓶毒药杀人，各限用一次。</p>
          </div>
          <div>
            <h3 className="font-bold text-orange-600 mb-2">🏹 猎人</h3>
            <p className="text-gray-600">被狼杀或投票出局时，可带走一名玩家。</p>
          </div>
          <div>
            <h3 className="font-bold text-cyan-600 mb-2">🛡️ 守卫</h3>
            <p className="text-gray-600">每晚守护一名玩家免受狼刀，不能连续守护同一人。</p>
          </div>
        </div>
      </div>
    </div>
  )
}

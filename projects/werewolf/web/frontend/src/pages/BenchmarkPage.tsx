// ==================== Benchmark 页面 ====================
import { useState, useEffect } from 'react'
import { useApi } from '../hooks/useApi'
import type { BenchmarkResult } from '../types/game'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'

const COLORS = ['#dc2626', '#16a34a']

export function BenchmarkPage() {
  const { startBenchmark, getBenchmark, loading, error } = useApi()

  const [numGames, setNumGames] = useState(10)
  const [preset, setPreset] = useState('6p')
  const [result, setResult] = useState<BenchmarkResult | null>(null)
  const [polling, setPolling] = useState(false)

  // 轮询获取结果
  useEffect(() => {
    if (!polling || !result) return

    const interval = setInterval(async () => {
      const updated = await getBenchmark(result.benchmark_id)
      if (updated) {
        setResult(updated)
        if (updated.status === 'completed' || updated.status === 'error') {
          setPolling(false)
        }
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [polling, result, getBenchmark])

  const handleStart = async () => {
    const res = await startBenchmark(numGames, preset)
    if (res) {
      setResult(res)
      setPolling(true)
    }
  }

  // 准备图表数据
  const winRateData = result?.results ? [
    { name: '狼人', value: result.results.win_rates.werewolf || 0 },
    { name: '村民', value: result.results.win_rates.villager || 0 },
  ] : []

  const roundsData = result?.results ? [
    { name: '平均回合', value: result.results.avg_rounds },
    { name: '最少回合', value: result.results.min_rounds },
    { name: '最多回合', value: result.results.max_rounds },
  ] : []

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-2xl font-bold mb-6">📊 Benchmark</h1>

        <div className="grid md:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              游戏局数
            </label>
            <input
              type="number"
              value={numGames}
              onChange={(e) => setNumGames(Number(e.target.value))}
              min={1}
              max={100}
              className="w-full p-3 border rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              游戏配置
            </label>
            <select
              value={preset}
              onChange={(e) => setPreset(e.target.value)}
              className="w-full p-3 border rounded-lg"
            >
              <option value="6p">6人局</option>
              <option value="9p">9人局</option>
              <option value="12p">12人局</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleStart}
              disabled={loading || polling}
              className="w-full btn btn-primary py-3 disabled:opacity-50"
            >
              {polling ? '运行中...' : '开始测试'}
            </button>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-red-600 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* 进度 */}
        {result && result.status === 'running' && (
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>进度</span>
              <span>{result.completed_games} / {result.total_games}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-600 h-4 rounded-full transition-all"
                style={{
                  width: `${(result.completed_games / result.total_games) * 100}%`
                }}
              />
            </div>
          </div>
        )}

        {/* 结果 */}
        {result?.results && (
          <div className="space-y-8">
            {/* 统计卡片 */}
            <div className="grid md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-gray-800">
                  {result.total_games}
                </div>
                <div className="text-sm text-gray-500">总局数</div>
              </div>
              <div className="bg-red-50 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-red-600">
                  {((result.results.win_rates.werewolf || 0) * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-500">狼人胜率</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-green-600">
                  {((result.results.win_rates.villager || 0) * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-500">村民胜率</div>
              </div>
              <div className="bg-blue-50 rounded-lg p-4 text-center">
                <div className="text-3xl font-bold text-blue-600">
                  {result.results.avg_rounds.toFixed(1)}
                </div>
                <div className="text-sm text-gray-500">平均回合</div>
              </div>
            </div>

            {/* 图表 */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* 胜率饼图 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-bold mb-4 text-center">胜率分布</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={winRateData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${(value * 100).toFixed(1)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {winRateData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* 回合柱状图 */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-bold mb-4 text-center">回合统计</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={roundsData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* 详细信息 */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-bold mb-4">详细统计</h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">狼人获胜场次</span>
                  <span className="font-medium">{result.results.wins.werewolf || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">村民获胜场次</span>
                  <span className="font-medium">{result.results.wins.villager || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">最短游戏</span>
                  <span className="font-medium">{result.results.min_rounds} 回合</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">最长游戏</span>
                  <span className="font-medium">{result.results.max_rounds} 回合</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">平均耗时</span>
                  <span className="font-medium">{result.results.avg_duration.toFixed(2)}s</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">总耗时</span>
                  <span className="font-medium">{result.results.total_duration.toFixed(2)}s</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

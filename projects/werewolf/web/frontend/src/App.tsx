// ==================== 主应用 ====================
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { GamePage } from './pages/GamePage'
import { BenchmarkPage } from './pages/BenchmarkPage'
import { SettingsPage } from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-100">
        {/* 导航栏 */}
        <nav className="bg-gray-800 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex items-center justify-between h-16">
              <Link to="/" className="flex items-center space-x-2">
                <span className="text-2xl">🐺</span>
                <span className="font-bold text-xl">AI 狼人杀</span>
              </Link>

              <div className="flex space-x-4">
                <Link to="/" className="hover:text-gray-300 px-3 py-2">
                  首页
                </Link>
                <Link to="/benchmark" className="hover:text-gray-300 px-3 py-2">
                  Benchmark
                </Link>
                <Link to="/settings" className="hover:text-gray-300 px-3 py-2">
                  ⚙️ 配置
                </Link>
              </div>
            </div>
          </div>
        </nav>

        {/* 主内容 */}
        <main className="max-w-7xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/game/:gameId" element={<GamePage />} />
            <Route path="/benchmark" element={<BenchmarkPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>

        {/* 页脚 */}
        <footer className="bg-gray-800 text-gray-400 py-4 mt-8">
          <div className="max-w-7xl mx-auto px-4 text-center text-sm">
            AI Werewolf v0.3.0 | Built with FastAPI + React
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}

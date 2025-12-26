// ==================== 设置页面 ====================
import { useState, useEffect } from 'react'

interface LLMProviderConfig {
  api_key: string | null
  base_url: string | null
  model: string
}

interface Config {
  llm: {
    default_provider: string
    openai: LLMProviderConfig
    anthropic: LLMProviderConfig
    deepseek?: LLMProviderConfig
    custom: LLMProviderConfig
  }
  game: {
    default_preset: string
    default_speed: number
    max_rounds: number
  }
}

export function SettingsPage() {
  const [config, setConfig] = useState<Config | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // 表单状态
  const [formData, setFormData] = useState({
    default_provider: 'openai',
    openai_api_key: '',
    openai_base_url: '',
    openai_model: 'gpt-4o-mini',
    anthropic_api_key: '',
    anthropic_model: 'claude-3-5-haiku-20241022',
    deepseek_api_key: '',
    deepseek_model: 'deepseek-chat',
    custom_api_key: '',
    custom_base_url: 'http://localhost:11434/v1',
    custom_model: 'llama3.2',
  })

  // 加载配置
  useEffect(() => {
    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        setConfig(data)
        setFormData({
          default_provider: data.llm.default_provider,
          openai_api_key: '',  // 不显示脱敏后的 key
          openai_base_url: data.llm.openai.base_url || '',
          openai_model: data.llm.openai.model,
          anthropic_api_key: '',
          anthropic_model: data.llm.anthropic.model,
          deepseek_api_key: '',
          deepseek_model: data.llm.deepseek?.model || 'deepseek-chat',
          custom_api_key: '',
          custom_base_url: data.llm.custom.base_url || 'http://localhost:11434/v1',
          custom_model: data.llm.custom.model || 'llama3.2',
        })
        setLoading(false)
      })
      .catch(err => {
        setMessage({ type: 'error', text: '加载配置失败: ' + err.message })
        setLoading(false)
      })
  }, [])

  // 保存配置
  const handleSave = async () => {
    setSaving(true)
    setMessage(null)

    try {
      const update: any = {
        default_provider: formData.default_provider,
      }

      // 只发送非空的 API Key
      if (formData.openai_api_key) {
        update.openai = {
          api_key: formData.openai_api_key,
          base_url: formData.openai_base_url || null,
          model: formData.openai_model,
        }
      } else {
        update.openai = {
          base_url: formData.openai_base_url || null,
          model: formData.openai_model,
        }
      }

      if (formData.anthropic_api_key) {
        update.anthropic = {
          api_key: formData.anthropic_api_key,
          model: formData.anthropic_model,
        }
      } else {
        update.anthropic = {
          model: formData.anthropic_model,
        }
      }

      if (formData.deepseek_api_key) {
        update.deepseek = {
          api_key: formData.deepseek_api_key,
          model: formData.deepseek_model,
        }
      } else {
        update.deepseek = {
          model: formData.deepseek_model,
        }
      }

      if (formData.custom_api_key || formData.custom_base_url) {
        update.custom = {
          api_key: formData.custom_api_key || undefined,
          base_url: formData.custom_base_url || null,
          model: formData.custom_model,
        }
      }

      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      })

      if (res.ok) {
        setMessage({ type: 'success', text: '配置已保存' })
        // 清空密码字段
        setFormData(prev => ({
          ...prev,
          openai_api_key: '',
          anthropic_api_key: '',
          deepseek_api_key: '',
          custom_api_key: '',
        }))
      } else {
        const err = await res.json()
        setMessage({ type: 'error', text: err.detail || '保存失败' })
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  // 测试连接
  const handleTest = async (provider: string) => {
    setTesting(provider)
    setTestResult(null)

    try {
      const res = await fetch(`/api/config/test?provider=${provider}`, {
        method: 'POST',
      })
      const data = await res.json()

      if (data.success) {
        setTestResult({ success: true, message: `连接成功! 响应: "${data.response}"` })
      } else {
        setTestResult({ success: false, message: `连接失败: ${data.error}` })
      }
    } catch (err: any) {
      setTestResult({ success: false, message: err.message })
    } finally {
      setTesting(null)
    }
  }

  if (loading) {
    return <div className="text-center py-8">加载中...</div>
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h1 className="text-2xl font-bold mb-6">⚙️ 配置中心</h1>

        {message && (
          <div className={`p-4 rounded-lg mb-6 ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* 默认提供商 */}
        <div className="mb-8">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            默认 LLM 提供商
          </label>
          <select
            value={formData.default_provider}
            onChange={(e) => setFormData({ ...formData, default_provider: e.target.value })}
            className="w-full p-3 border rounded-lg"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="deepseek">DeepSeek</option>
            <option value="custom">自定义 (OpenAI 兼容)</option>
          </select>
        </div>

        {/* OpenAI 配置 */}
        <div className="mb-8 p-6 bg-gray-50 rounded-lg">
          <h3 className="font-bold text-lg mb-4 flex items-center">
            <span className="mr-2">🟢</span> OpenAI
            {config?.llm.openai.api_key && (
              <span className="ml-2 text-xs text-green-600 font-normal">
                (已配置: {config.llm.openai.api_key})
              </span>
            )}
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">API Key</label>
              <input
                type="password"
                value={formData.openai_api_key}
                onChange={(e) => setFormData({ ...formData, openai_api_key: e.target.value })}
                placeholder="sk-..."
                className="w-full p-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">Base URL (可选)</label>
              <input
                type="text"
                value={formData.openai_base_url}
                onChange={(e) => setFormData({ ...formData, openai_base_url: e.target.value })}
                placeholder="https://api.openai.com/v1"
                className="w-full p-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">模型</label>
              <input
                type="text"
                value={formData.openai_model}
                onChange={(e) => setFormData({ ...formData, openai_model: e.target.value })}
                className="w-full p-2 border rounded"
              />
            </div>

            <button
              onClick={() => handleTest('openai')}
              disabled={testing === 'openai'}
              className="btn bg-gray-200 hover:bg-gray-300 text-gray-700"
            >
              {testing === 'openai' ? '测试中...' : '测试连接'}
            </button>
          </div>
        </div>

        {/* DeepSeek 配置 */}
        <div className="mb-8 p-6 bg-gray-50 rounded-lg">
          <h3 className="font-bold text-lg mb-4 flex items-center">
            <span className="mr-2">🔷</span> DeepSeek
            {config?.llm.deepseek?.api_key && (
              <span className="ml-2 text-xs text-green-600 font-normal">
                (已配置: {config.llm.deepseek.api_key})
              </span>
            )}
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">API Key</label>
              <input
                type="password"
                value={formData.deepseek_api_key}
                onChange={(e) => setFormData({ ...formData, deepseek_api_key: e.target.value })}
                placeholder="sk-..."
                className="w-full p-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">模型</label>
              <select
                value={formData.deepseek_model}
                onChange={(e) => setFormData({ ...formData, deepseek_model: e.target.value })}
                className="w-full p-2 border rounded"
              >
                <option value="deepseek-chat">deepseek-chat (推荐)</option>
                <option value="deepseek-reasoner">deepseek-reasoner (R1)</option>
              </select>
            </div>

            <button
              onClick={() => handleTest('deepseek')}
              disabled={testing === 'deepseek'}
              className="btn bg-gray-200 hover:bg-gray-300 text-gray-700"
            >
              {testing === 'deepseek' ? '测试中...' : '测试连接'}
            </button>
          </div>
        </div>

        {/* Anthropic 配置 */}
        <div className="mb-8 p-6 bg-gray-50 rounded-lg">
          <h3 className="font-bold text-lg mb-4 flex items-center">
            <span className="mr-2">🟠</span> Anthropic
            {config?.llm.anthropic.api_key && (
              <span className="ml-2 text-xs text-green-600 font-normal">
                (已配置: {config.llm.anthropic.api_key})
              </span>
            )}
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">API Key</label>
              <input
                type="password"
                value={formData.anthropic_api_key}
                onChange={(e) => setFormData({ ...formData, anthropic_api_key: e.target.value })}
                placeholder="sk-ant-..."
                className="w-full p-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">模型</label>
              <input
                type="text"
                value={formData.anthropic_model}
                onChange={(e) => setFormData({ ...formData, anthropic_model: e.target.value })}
                className="w-full p-2 border rounded"
              />
            </div>

            <button
              onClick={() => handleTest('anthropic')}
              disabled={testing === 'anthropic'}
              className="btn bg-gray-200 hover:bg-gray-300 text-gray-700"
            >
              {testing === 'anthropic' ? '测试中...' : '测试连接'}
            </button>
          </div>
        </div>

        {/* 自定义配置 */}
        <div className="mb-8 p-6 bg-gray-50 rounded-lg">
          <h3 className="font-bold text-lg mb-4 flex items-center">
            <span className="mr-2">🔵</span> 自定义 (OpenAI 兼容)
            <span className="ml-2 text-xs text-gray-500 font-normal">
              支持 Ollama, DeepSeek, Azure 等
            </span>
          </h3>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Base URL</label>
              <input
                type="text"
                value={formData.custom_base_url}
                onChange={(e) => setFormData({ ...formData, custom_base_url: e.target.value })}
                placeholder="http://localhost:11434/v1"
                className="w-full p-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">API Key (可选)</label>
              <input
                type="password"
                value={formData.custom_api_key}
                onChange={(e) => setFormData({ ...formData, custom_api_key: e.target.value })}
                placeholder="如 Ollama 通常不需要"
                className="w-full p-2 border rounded"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">模型</label>
              <input
                type="text"
                value={formData.custom_model}
                onChange={(e) => setFormData({ ...formData, custom_model: e.target.value })}
                className="w-full p-2 border rounded"
              />
            </div>

            <button
              onClick={() => handleTest('custom')}
              disabled={testing === 'custom'}
              className="btn bg-gray-200 hover:bg-gray-300 text-gray-700"
            >
              {testing === 'custom' ? '测试中...' : '测试连接'}
            </button>
          </div>
        </div>

        {/* 测试结果 */}
        {testResult && (
          <div className={`p-4 rounded-lg mb-6 ${
            testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {testResult.message}
          </div>
        )}

        {/* 保存按钮 */}
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full btn btn-primary py-3 text-lg disabled:opacity-50"
        >
          {saving ? '保存中...' : '保存配置'}
        </button>

        {/* 提示 */}
        <div className="mt-6 text-sm text-gray-500">
          <p>💡 提示:</p>
          <ul className="list-disc list-inside mt-2 space-y-1">
            <li>配置仅保存在内存中，重启后需重新配置</li>
            <li>如需持久化，请编辑 <code className="bg-gray-100 px-1 rounded">config.yaml</code> 文件</li>
            <li>也可通过环境变量配置: <code className="bg-gray-100 px-1 rounded">OPENAI_API_KEY</code>, <code className="bg-gray-100 px-1 rounded">ANTHROPIC_API_KEY</code></li>
          </ul>
        </div>
      </div>
    </div>
  )
}

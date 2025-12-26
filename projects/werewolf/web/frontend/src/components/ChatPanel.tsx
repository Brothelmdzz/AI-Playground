// ==================== 聊天面板 ====================
import { useState, useRef, useEffect } from 'react'
import type { GameEvent } from '../types/game'

interface ChatPanelProps {
  events: GameEvent[]
  onSpeak?: (content: string) => void
  disabled?: boolean
}

export function ChatPanel({ events, onSpeak, disabled }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 自动滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && onSpeak) {
      onSpeak(input.trim())
      setInput('')
    }
  }

  // 格式化事件为消息
  const formatEvent = (event: GameEvent) => {
    switch (event.event_type) {
      case 'speech':
        return {
          type: 'player' as const,
          content: event.description,
          details: event.details,
        }
      case 'phase_change':
        return {
          type: 'system' as const,
          content: event.description,
        }
      case 'action':
        return {
          type: 'system' as const,
          content: event.description,
        }
      default:
        return {
          type: 'system' as const,
          content: event.description,
        }
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg flex flex-col h-[600px]">
      {/* 标题 */}
      <div className="p-4 border-b">
        <h3 className="font-bold text-lg">💬 游戏日志</h3>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {events.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            等待游戏开始...
          </div>
        ) : (
          events.map((event, index) => {
            const msg = formatEvent(event)
            return (
              <div
                key={index}
                className={`chat-message ${msg.type}`}
              >
                {msg.type === 'player' && msg.details?.player_id !== undefined && (
                  <div className="text-xs text-gray-500 mb-1">
                    玩家 {msg.details.player_id}
                  </div>
                )}
                <div className="text-sm">{msg.content}</div>
                <div className="text-xs text-gray-400 mt-1">
                  回合 {event.round} · {event.phase}
                </div>
              </div>
            )
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 输入框 */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={disabled ? '等待发言阶段...' : '输入发言内容...'}
            disabled={disabled}
            className="flex-1 p-2 border rounded-lg disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={disabled || !input.trim()}
            className="btn btn-primary disabled:opacity-50"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  )
}

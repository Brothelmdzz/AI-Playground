// ==================== WebSocket Hook ====================
import { useEffect, useRef, useState, useCallback } from 'react'
import type { GameState, GameEvent, WSMessage } from '../types/game'

interface UseWebSocketOptions {
  gameId: string
  playerId?: number
  onStateChange?: (state: GameState) => void
  onEvent?: (event: GameEvent) => void
  onError?: (error: string) => void
}

export function useWebSocket(options: UseWebSocketOptions) {
  const { gameId, playerId, onStateChange, onEvent, onError } = options
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [lastState, setLastState] = useState<GameState | null>(null)

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws/game/${gameId}${playerId !== undefined ? `?player_id=${playerId}` : ''}`

    const ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
      // 尝试重连
      setTimeout(connect, 3000)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      onError?.('WebSocket connection error')
    }

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)

        switch (message.type) {
          case 'game_state':
            const state = message.data as GameState
            setLastState(state)
            onStateChange?.(state)
            break
          case 'event':
            const gameEvent = message.data as GameEvent
            onEvent?.(gameEvent)
            break
          case 'error':
            onError?.(message.data?.message || 'Unknown error')
            break
          case 'pong':
            // Heartbeat response
            break
          default:
            console.log('Unknown message type:', message.type)
        }
      } catch (e) {
        console.error('Failed to parse message:', e)
      }
    }

    wsRef.current = ws
  }, [gameId, playerId, onStateChange, onEvent, onError])

  useEffect(() => {
    connect()

    // Heartbeat
    const heartbeat = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)

    return () => {
      clearInterval(heartbeat)
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((message: WSMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    }
  }, [])

  const submitAction = useCallback((actionType: string, targetId?: number) => {
    send({
      type: 'submit_action',
      action_type: actionType,
      target_id: targetId,
    } as any)
  }, [send])

  const speak = useCallback((content: string) => {
    send({
      type: 'speak',
      content,
    } as any)
  }, [send])

  return {
    isConnected,
    lastState,
    send,
    submitAction,
    speak,
  }
}

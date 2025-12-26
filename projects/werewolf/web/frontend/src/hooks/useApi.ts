// ==================== API Hook ====================
import { useState, useCallback } from 'react'
import type { GameState, GameListItem, CreateGameRequest, BenchmarkResult } from '../types/game'

const API_BASE = '/api'

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || 'Request failed')
  }

  return response.json()
}

export function useApi() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const request = useCallback(async <T>(fn: () => Promise<T>): Promise<T | null> => {
    setLoading(true)
    setError(null)
    try {
      const result = await fn()
      return result
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Unknown error'
      setError(message)
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  // 游戏 API
  const createGame = useCallback((data: CreateGameRequest) => {
    return request(() => fetchApi<{ game_id: string; join_url: string }>('/games', {
      method: 'POST',
      body: JSON.stringify(data),
    }))
  }, [request])

  const listGames = useCallback(() => {
    return request(() => fetchApi<GameListItem[]>('/games'))
  }, [request])

  const getGame = useCallback((gameId: string) => {
    return request(() => fetchApi<GameState>(`/games/${gameId}`))
  }, [request])

  const startGame = useCallback((gameId: string, seed?: number) => {
    return request(() => fetchApi<{ message: string }>(`/games/${gameId}/start?seed=${seed || ''}`, {
      method: 'POST',
    }))
  }, [request])

  const pauseGame = useCallback((gameId: string) => {
    return request(() => fetchApi<{ message: string }>(`/games/${gameId}/pause`, {
      method: 'POST',
    }))
  }, [request])

  const resumeGame = useCallback((gameId: string) => {
    return request(() => fetchApi<{ message: string }>(`/games/${gameId}/resume`, {
      method: 'POST',
    }))
  }, [request])

  const setSpeed = useCallback((gameId: string, speed: number) => {
    return request(() => fetchApi<{ message: string }>(`/games/${gameId}/speed?speed=${speed}`, {
      method: 'POST',
    }))
  }, [request])

  // Benchmark API
  const startBenchmark = useCallback((numGames: number, preset: string = '6p') => {
    return request(() => fetchApi<BenchmarkResult>('/benchmark', {
      method: 'POST',
      body: JSON.stringify({ num_games: numGames, preset }),
    }))
  }, [request])

  const getBenchmark = useCallback((benchmarkId: string) => {
    return request(() => fetchApi<BenchmarkResult>(`/benchmark/${benchmarkId}`))
  }, [request])

  return {
    loading,
    error,
    createGame,
    listGames,
    getGame,
    startGame,
    pauseGame,
    resumeGame,
    setSpeed,
    startBenchmark,
    getBenchmark,
  }
}

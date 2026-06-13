import { useEffect, useRef, useCallback } from 'react'

/**
 * Lightweight WebSocket hook for real-time log streaming.
 *
 * Usage:
 *   const { status } = useWebSocket('ws://localhost:8000/ws/logs', {
 *     onMessage: (msg) => console.log(msg),
 *   })
 *
 * The backend does not yet expose a WS endpoint, so this hook gracefully
 * handles connection failures — it retries up to maxRetries times with
 * exponential backoff, then gives up.  Components can check `status` to
 * show a degraded-mode indicator.
 */
export function useWebSocket(url, { onMessage, onOpen, onClose, maxRetries = 3 } = {}) {
  const wsRef       = useRef(null)
  const retriesRef  = useRef(0)
  const statusRef   = useRef('idle')   // 'idle' | 'connecting' | 'open' | 'closed' | 'error'
  const timerRef    = useRef(null)

  const connect = useCallback(() => {
    if (!url) return
    statusRef.current = 'connecting'

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        statusRef.current = 'open'
        retriesRef.current = 0
        onOpen?.()
      }

      ws.onmessage = (evt) => {
        try {
          onMessage?.(JSON.parse(evt.data))
        } catch {
          onMessage?.(evt.data)
        }
      }

      ws.onclose = () => {
        statusRef.current = 'closed'
        onClose?.()
        if (retriesRef.current < maxRetries) {
          const delay = Math.min(1000 * 2 ** retriesRef.current, 16_000)
          retriesRef.current++
          timerRef.current = setTimeout(connect, delay)
        }
      }

      ws.onerror = () => {
        statusRef.current = 'error'
        ws.close()
      }
    } catch {
      statusRef.current = 'error'
    }
  }, [url, onMessage, onOpen, onClose, maxRetries])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(timerRef.current)
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  return {
    send,
    get status() { return statusRef.current },
    close() { wsRef.current?.close() },
  }
}

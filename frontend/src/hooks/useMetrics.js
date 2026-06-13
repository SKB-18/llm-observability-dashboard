import { useState, useEffect, useCallback, useRef } from 'react'
import {
  fetchMetricsSummary,
  fetchMetricsByModel,
  fetchMetricsByHour,
  fetchLatencyPercentiles,
} from '../services/api'

const REFETCH_INTERVAL_MS = 30_000

export function useMetrics(filters = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const filtersKey = JSON.stringify(filters)
  const abortRef = useRef(null)

  const fetchAll = useCallback(async () => {
    // Cancel any in-flight request
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()

    setLoading(true)
    setError(null)

    try {
      const [summary, byModel, byHour, percentiles] = await Promise.all([
        fetchMetricsSummary(filters),
        fetchMetricsByModel(filters),
        fetchMetricsByHour(filters),
        fetchLatencyPercentiles(filters),
      ])
      setData({ summary, byModel, byHour, percentiles })
    } catch (err) {
      if (err.name === 'CanceledError' || err.name === 'AbortError') return
      if (err.code === 'ECONNABORTED') {
        setError('Request timed out after 5 s. Is the backend running?')
      } else {
        setError(err.message || 'Failed to load metrics')
      }
      setData(null)
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtersKey])

  // Fetch on mount and whenever filters change
  useEffect(() => {
    fetchAll()
  }, [fetchAll])

  // Auto-refresh every 30 s
  useEffect(() => {
    const id = setInterval(fetchAll, REFETCH_INTERVAL_MS)
    return () => clearInterval(id)
  }, [fetchAll])

  return { data, loading, error, refetch: fetchAll }
}

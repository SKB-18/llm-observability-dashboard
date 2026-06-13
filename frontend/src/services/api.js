import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || ''

const client = axios.create({
  baseURL: BASE,
  timeout: 5000,
})

// Log requests in dev mode
if (import.meta.env.DEV) {
  client.interceptors.request.use((config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.params || '')
    return config
  })
}

function buildParams(filters = {}) {
  const p = {}
  if (filters.start_date) p.start_date = filters.start_date
  if (filters.end_date) p.end_date = filters.end_date
  if (filters.model) p.model = filters.model
  return p
}

export async function fetchMetricsSummary(filters = {}) {
  const { data } = await client.get('/api/v1/metrics/summary', { params: buildParams(filters) })
  return data
}

export async function fetchMetricsByModel(filters = {}) {
  const { data } = await client.get('/api/v1/metrics/by-model', { params: buildParams(filters) })
  return data
}

export async function fetchMetricsByHour(filters = {}) {
  const { data } = await client.get('/api/v1/metrics/by-hour', { params: buildParams(filters) })
  return data
}

export async function fetchLatencyPercentiles(filters = {}) {
  const { data } = await client.get('/api/v1/metrics/latency-percentiles', { params: buildParams(filters) })
  return data
}

export async function fetchCostBreakdown(filters = {}) {
  const { data } = await client.get('/api/v1/metrics/cost-breakdown', { params: buildParams(filters) })
  return data
}

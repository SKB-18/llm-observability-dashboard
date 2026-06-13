import React, { useState, useEffect } from 'react'
import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react'

const MODEL_COLOR = {
  'gpt-4':           'bg-emerald-900 text-emerald-300 border-emerald-700',
  'gpt-4-turbo':     'bg-emerald-900 text-emerald-300 border-emerald-700',
  'gpt-3.5-turbo':   'bg-sky-900 text-sky-300 border-sky-700',
  'claude-3-opus':   'bg-violet-900 text-violet-300 border-violet-700',
  'claude-3-5-sonnet':'bg-purple-900 text-purple-300 border-purple-700',
}

function modelBadge(model = '') {
  const cls = MODEL_COLOR[model] ?? 'bg-gray-800 text-gray-400 border-gray-600'
  const label = model.length > 16 ? model.slice(0, 14) + '…' : model
  return (
    <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${cls}`}>
      {label}
    </span>
  )
}

function latencyColor(ms) {
  if (ms < 200) return 'text-emerald-400'
  if (ms < 500) return 'text-amber-400'
  return 'text-red-400'
}

export default function CompletionsTable({ source = null }) {
  const [page, setPage]     = useState(1)
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(false)
  const LIMIT = 10

  function load(p = page) {
    setLoading(true)
    const src = source ? `&source=${encodeURIComponent(source)}` : ''
    fetch(`/api/v1/logs?page=${p}&limit=${LIMIT}${src}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }

  useEffect(() => { load(page) }, [page])

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const pages = data?.pages ?? 1

  return (
    <div data-testid="completions-table" className="rounded-2xl bg-gray-800 border border-gray-700 shadow-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
            Recent Completions
          </h3>
          <p className="text-xs text-gray-600 mt-0.5">{total.toLocaleString()} total</p>
        </div>
        <button
          onClick={() => load(page)}
          disabled={loading}
          className="p-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-400 disabled:opacity-40 transition-colors"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-700">
              {['ID', 'Model', 'Prompt', 'Response', 'Tokens↓↑', 'Latency', 'Cost', 'Time'].map(h => (
                <th key={h} className="px-3 py-2 text-left text-[10px] uppercase tracking-wider text-gray-500 font-medium whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/50">
            {loading && !items.length ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  {Array.from({ length: 8 }).map((_, j) => (
                    <td key={j} className="px-3 py-2.5">
                      <div className="h-3 bg-gray-700 rounded w-16" />
                    </td>
                  ))}
                </tr>
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-gray-600 text-xs">
                  No completions logged yet. Send a request to <code className="bg-gray-700 px-1 rounded">POST /api/v1/logs</code>
                </td>
              </tr>
            ) : (
              items.map(item => (
                <tr key={item.id} className="hover:bg-gray-700/30 transition-colors group">
                  <td className="px-3 py-2.5 text-gray-500 tabular-nums">#{item.id}</td>
                  <td className="px-3 py-2.5">{modelBadge(item.model)}</td>
                  <td className="px-3 py-2.5 max-w-[180px]">
                    <span className="text-gray-300 truncate block" title={item.prompt}>
                      {item.prompt}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 max-w-[180px]">
                    <span className="text-gray-400 truncate block" title={item.response}>
                      {item.response}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 tabular-nums text-gray-400 whitespace-nowrap">
                    <span className="text-sky-400">{item.tokens_in}</span>
                    {' / '}
                    <span className="text-violet-400">{item.tokens_out}</span>
                  </td>
                  <td className={`px-3 py-2.5 tabular-nums font-medium whitespace-nowrap ${latencyColor(item.latency_ms)}`}>
                    {item.latency_ms?.toFixed(0)}ms
                  </td>
                  <td className="px-3 py-2.5 tabular-nums text-gray-400 whitespace-nowrap">
                    ${item.cost_usd?.toFixed(4)}
                  </td>
                  <td className="px-3 py-2.5 text-gray-600 whitespace-nowrap">
                    {item.timestamp
                      ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                      : '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-700">
          <span className="text-xs text-gray-600">
            Page {page} of {pages}
          </span>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="p-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-400 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft size={12} />
            </button>
            <button
              onClick={() => setPage(p => Math.min(pages, p + 1))}
              disabled={page >= pages || loading}
              className="p-1.5 rounded bg-gray-700 hover:bg-gray-600 text-gray-400 disabled:opacity-40 transition-colors"
            >
              <ChevronRight size={12} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

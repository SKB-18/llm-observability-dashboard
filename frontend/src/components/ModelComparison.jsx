import React, { useState } from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from 'recharts'
import { ArrowUpDown, TrendingDown } from 'lucide-react'

const MODEL_COLORS = [
  '#3b82f6',
  '#10b981',
  '#f59e0b',
  '#8b5cf6',
  '#ef4444',
  '#06b6d4',
  '#ec4899',
  '#84cc16',
]

function cls(...args) {
  return args.filter(Boolean).join(' ')
}

function CostBadge({ value, best, worst }) {
  if (value === best) return <span className="ml-1 text-xs text-emerald-400 font-bold">↓ cheapest</span>
  if (value === worst) return <span className="ml-1 text-xs text-red-400">↑ priciest</span>
  return null
}

function LatencyBadge({ value, best, worst }) {
  if (value === best) return <span className="ml-1 text-xs text-emerald-400 font-bold">⚡ fastest</span>
  if (value === worst) return <span className="ml-1 text-xs text-red-400">🐢 slowest</span>
  return null
}

function shortLabel(model = '') {
  return model
    .replace('claude-3-', 'c3-')
    .replace('claude-3.5-', 'c3.5-')
    .replace('gpt-3.5-', 'g3.5-')
    .replace('gpt-4-turbo', 'gpt4t')
    .replace('gpt-4', 'g4')
    .replace('gemini-', 'gem-')
}

export default function ModelComparison({ models = [] }) {
  const [chartMetric, setChartMetric] = useState('latency')

  if (!models.length) {
    return (
      <div data-testid="model-comparison" className="rounded-2xl bg-gray-800 border border-gray-700 p-6 text-center text-gray-500">
        No model data available
      </div>
    )
  }

  const bestCost   = Math.min(...models.map((m) => m.total_cost_usd))
  const worstCost  = Math.max(...models.map((m) => m.total_cost_usd))
  const bestLat    = Math.min(...models.map((m) => m.avg_latency_ms))
  const worstLat   = Math.max(...models.map((m) => m.avg_latency_ms))

  const chartData = models.map((m, i) => ({
    model: shortLabel(m.model),
    fullModel: m.model,
    latency: Math.round(m.avg_latency_ms),
    cost: +(m.total_cost_usd * 1000).toFixed(4),
    requests: m.request_count,
    color: MODEL_COLORS[i % MODEL_COLORS.length],
  }))

  return (
    <div data-testid="model-comparison" className="rounded-2xl bg-gray-800 border border-gray-700 p-4 shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400 flex items-center gap-2">
          <ArrowUpDown size={14} />
          Model Comparison
        </h3>
        <div className="flex rounded-lg bg-gray-700 overflow-hidden text-xs">
          {[
            { key: 'latency', label: 'Latency' },
            { key: 'cost',    label: 'Cost' },
            { key: 'requests', label: 'Requests' },
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setChartMetric(key)}
              className={cls(
                'px-3 py-1.5 transition-colors',
                chartMetric === key
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto mb-4">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="text-xs text-gray-500 border-b border-gray-700">
              <th className="pb-2 pr-4 font-medium">Model</th>
              <th className="pb-2 pr-4 font-medium text-right">Requests</th>
              <th className="pb-2 pr-4 font-medium text-right">Total Cost</th>
              <th className="pb-2 pr-4 font-medium text-right">Avg Latency</th>
              <th className="pb-2 font-medium text-right">Tokens In / Out</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m, i) => (
              <tr
                key={m.model}
                className="border-b border-gray-700/50 hover:bg-gray-750 transition-colors"
              >
                <td className="py-2.5 pr-4 font-medium text-white flex items-center gap-2">
                  <span
                    className="inline-block w-2 h-2 rounded-full flex-shrink-0"
                    style={{ background: MODEL_COLORS[i % MODEL_COLORS.length] }}
                  />
                  <span className="truncate max-w-[160px]" title={m.model}>{m.model}</span>
                </td>
                <td className="py-2.5 pr-4 text-right tabular-nums text-gray-200">
                  {m.request_count.toLocaleString()}
                </td>
                <td className="py-2.5 pr-4 text-right tabular-nums text-gray-200">
                  ${m.total_cost_usd.toFixed(4)}
                  <CostBadge value={m.total_cost_usd} best={bestCost} worst={worstCost} />
                </td>
                <td className="py-2.5 pr-4 text-right tabular-nums text-gray-200">
                  {Math.round(m.avg_latency_ms)} ms
                  <LatencyBadge value={m.avg_latency_ms} best={bestLat} worst={worstLat} />
                </td>
                <td className="py-2.5 text-right tabular-nums text-gray-400">
                  {Math.round(m.avg_tokens_in)} / {Math.round(m.avg_tokens_out)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Bar chart */}
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={chartData} margin={{ top: 4, right: 4, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
          <XAxis
            dataKey="model"
            tick={{ fill: '#6b7280', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={40}
            tickFormatter={(v) =>
              chartMetric === 'latency'
                ? `${v}ms`
                : chartMetric === 'cost'
                ? `${v}m¢`
                : v.toLocaleString()
            }
          />
          <Tooltip
            contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 12 }}
            labelStyle={{ color: '#e5e7eb', fontSize: 12 }}
            formatter={(v) => [
              chartMetric === 'latency'
                ? `${v} ms`
                : chartMetric === 'cost'
                ? `${v} m¢ × 1k`
                : v.toLocaleString() + ' req',
              chartMetric,
            ]}
          />
          <Bar dataKey={chartMetric} radius={[6, 6, 0, 0]}>
            {chartData.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

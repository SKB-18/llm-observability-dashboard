import React from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts'

function formatHour(isoStr) {
  try {
    return new Date(isoStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoStr
  }
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-700 px-3 py-2 shadow-xl text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} className="font-semibold text-emerald-300">
          ${Number(p.value).toFixed(6)} USD
        </p>
      ))}
    </div>
  )
}

export default function CostChart({ data = [] }) {
  const normalised = data.map((d) => ({
    ...d,
    label: formatHour(d.hour),
    cost: typeof d.cost === 'number' ? d.cost : (d.avg_cost_usd ?? 0),
  }))

  const total = normalised.reduce((s, d) => s + d.cost, 0)

  return (
    <div data-testid="cost-chart" className="rounded-2xl bg-gray-800 border border-gray-700 p-4 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
          Cost Over Time
        </h3>
        {total > 0 && (
          <span className="text-xs font-semibold text-emerald-400">
            ${total.toFixed(4)} total
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={normalised}>
          <defs>
            <filter id="costGlow">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: '#6b7280', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#6b7280', fontSize: 10 }}
            tickFormatter={(v) => `$${v.toFixed(3)}`}
            axisLine={false}
            tickLine={false}
            width={50}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="cost"
            stroke="#10b981"
            strokeWidth={2.5}
            dot={false}
            activeDot={{ r: 5, fill: '#10b981', strokeWidth: 0 }}
            filter="url(#costGlow)"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

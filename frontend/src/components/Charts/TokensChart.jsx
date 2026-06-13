import React from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-700 px-3 py-2 shadow-xl text-xs space-y-1">
      <p className="text-gray-400 mb-1">{label?.slice(11, 16) || label}</p>
      {payload.map(p => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-gray-300">{p.name}:</span>
          <span className="font-semibold text-white">{p.value?.toLocaleString()}</span>
        </div>
      ))}
      <div className="pt-1 border-t border-gray-700 flex items-center gap-2">
        <span className="text-gray-500">Total:</span>
        <span className="font-bold text-white">
          {payload.reduce((s, p) => s + (p.value || 0), 0).toLocaleString()}
        </span>
      </div>
    </div>
  )
}

export default function TokensChart({ data = [] }) {
  const enriched = data.map(d => ({
    ...d,
    label: d.hour?.slice(11, 16) || d.hour,
  }))

  if (!enriched.length) {
    return (
      <div className="rounded-2xl bg-gray-800 border border-gray-700 p-4 h-[220px] flex items-center justify-center">
        <p className="text-gray-600 text-xs">No token data yet</p>
      </div>
    )
  }

  return (
    <div data-testid="tokens-chart" className="rounded-2xl bg-gray-800 border border-gray-700 p-4 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">Token Usage</h3>
        <div className="flex gap-3 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-sky-500 inline-block" />Tokens In
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-violet-500 inline-block" />Tokens Out
          </span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={enriched} margin={{ bottom: 4 }}>
          <defs>
            <linearGradient id="tokensInGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#0ea5e9" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="tokensOutGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#8b5cf6" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
            </linearGradient>
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
            axisLine={false}
            tickLine={false}
            width={36}
            tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="avg_tokens_in"
            name="Tokens In"
            stroke="#0ea5e9"
            strokeWidth={2}
            fill="url(#tokensInGrad)"
            dot={false}
            activeDot={{ r: 4, fill: '#0ea5e9' }}
          />
          <Area
            type="monotone"
            dataKey="avg_tokens_out"
            name="Tokens Out"
            stroke="#8b5cf6"
            strokeWidth={2}
            fill="url(#tokensOutGrad)"
            dot={false}
            activeDot={{ r: 4, fill: '#8b5cf6' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

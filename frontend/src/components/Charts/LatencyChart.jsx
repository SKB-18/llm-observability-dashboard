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
    <div className="rounded-xl bg-gray-900 border border-gray-700 px-3 py-2 shadow-xl text-xs space-y-1">
      <p className="text-gray-400 mb-1">{label}</p>
      {[...payload].reverse().map((p) => (
        <p key={p.dataKey} style={{ color: p.stroke }} className="font-semibold">
          {p.name}: {p.value} ms
        </p>
      ))}
    </div>
  )
}

export default function LatencyChart({ data = [] }) {
  const normalised = data.map((d) => ({ ...d, label: formatHour(d.hour) }))

  return (
    <div data-testid="latency-chart" className="rounded-2xl bg-gray-800 border border-gray-700 p-4 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
          Latency Percentiles
        </h3>
        <span className="text-xs text-gray-500">p50 · p95 · p99</span>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <AreaChart data={normalised}>
          <defs>
            <linearGradient id="p99g" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="p95g" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#f97316" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="p50g" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
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
            tickFormatter={(v) => `${v}ms`}
            axisLine={false}
            tickLine={false}
            width={45}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            iconType="circle"
            wrapperStyle={{ fontSize: 11, paddingTop: 4 }}
            formatter={(v) => <span className="text-gray-400">{v}</span>}
          />
          <Area type="monotone" dataKey="p99" stroke="#ef4444" strokeWidth={2} fill="url(#p99g)" name="p99" dot={false} />
          <Area type="monotone" dataKey="p95" stroke="#f97316" strokeWidth={2} fill="url(#p95g)" name="p95" dot={false} />
          <Area type="monotone" dataKey="p50" stroke="#3b82f6" strokeWidth={2} fill="url(#p50g)" name="p50" dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

import React from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  LabelList,
} from 'recharts'

function barColor(score) {
  if (score >= 8) return '#10b981'
  if (score >= 6) return '#f59e0b'
  return '#ef4444'
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const score = payload[0]?.value
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-700 px-3 py-2 shadow-xl text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      <p className="font-semibold" style={{ color: barColor(score) }}>
        Score: {Number(score).toFixed(1)} / 10
      </p>
    </div>
  )
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

export default function QualityChart({ data = [] }) {
  const enriched = data.map((d) => ({ ...d, shortModel: shortLabel(d.model) }))

  return (
    <div data-testid="quality-chart" className="rounded-2xl bg-gray-800 border border-gray-700 p-4 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
          Quality Score by Model
        </h3>
        <div className="flex gap-2 text-xs">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />≥8</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />≥6</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500 inline-block" />&lt;6</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={enriched} margin={{ bottom: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
          <XAxis
            dataKey="shortModel"
            tick={{ fill: '#6b7280', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 10]}
            tick={{ fill: '#6b7280', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={25}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="score" name="Quality Score" radius={[6, 6, 0, 0]}>
            <LabelList
              dataKey="score"
              position="top"
              style={{ fill: '#9ca3af', fontSize: 10 }}
              formatter={(v) => v.toFixed(1)}
            />
            {enriched.map((entry, i) => (
              <Cell key={i} fill={barColor(entry.score)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

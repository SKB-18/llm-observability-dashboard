import React, { useState } from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ReferenceLine,
  Legend,
} from 'recharts'

const TYPE_COLOR = {
  llm_judge:        '#a78bfa',
  bleu:             '#38bdf8',
  rouge:            '#34d399',
  rules:            '#fb923c',
  human_preference: '#f472b6',
  human:            '#fbbf24',
}

const TYPE_LABEL = {
  llm_judge:        'LLM Judge',
  bleu:             'BLEU',
  rouge:            'ROUGE',
  rules:            'Rules',
  human_preference: 'Human Pref',
  human:            'Human',
}
const DEFAULT_COLOR = '#6b7280'

function bucketColor(range) {
  if (range.startsWith('80')) return '#10b981'
  if (range.startsWith('60')) return '#34d399'
  if (range.startsWith('40')) return '#f59e0b'
  if (range.startsWith('20')) return '#f97316'
  return '#ef4444'
}

function ScoreChip({ score }) {
  const pct = Math.round((score ?? 0) * 100)
  const color =
    pct >= 80 ? 'text-emerald-400' :
    pct >= 60 ? 'text-amber-400' :
    'text-red-400'
  return <span className={`font-bold tabular-nums ${color}`}>{pct}%</span>
}

function DistributionTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-700 px-3 py-2 shadow-xl text-xs">
      <p className="text-gray-400 mb-1">{label}</p>
      <p className="text-white font-semibold">{payload[0].value} eval{payload[0].value !== 1 ? 's' : ''}</p>
    </div>
  )
}

function TrendTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const score = payload[0]?.value
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-700 px-3 py-2 shadow-xl text-xs">
      <p className="text-gray-400 mb-1">{label?.slice(11, 16)}</p>
      <p className="text-violet-400 font-semibold">Avg: {(score * 100).toFixed(1)}%</p>
      {payload[1] && <p className="text-gray-400">{payload[1].value} evals</p>}
    </div>
  )
}

export default function EvalAnalytics({ data }) {
  const [tab, setTab] = useState('distribution')

  if (!data || data.total_evals === 0) {
    return (
      <div className="rounded-2xl bg-gray-800 border border-gray-700 p-6 text-center">
        <p className="text-gray-500 text-sm">No eval results yet.</p>
        <p className="text-gray-600 text-xs mt-1">
          Run evaluations via <code className="bg-gray-700 px-1 rounded">POST /api/v1/evals/evaluate</code>
        </p>
      </div>
    )
  }

  const tabs = [
    { id: 'distribution', label: 'Distribution' },
    { id: 'trend',        label: 'Trend' },
    { id: 'bytype',       label: 'By Type' },
    { id: 'bymodel',      label: 'By Model' },
  ]

  return (
    <div className="rounded-2xl bg-gray-800 border border-gray-700 p-4 shadow-xl" data-testid="eval-analytics">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
            Eval Analytics
          </h3>
          <p className="text-xs text-gray-600 mt-0.5">
            {data.total_evals.toLocaleString()} evaluations ·{' '}
            overall avg{' '}
            <span className={`font-bold ${
              (data.overall_avg_score ?? 0) >= 0.8 ? 'text-emerald-400' :
              (data.overall_avg_score ?? 0) >= 0.6 ? 'text-amber-400' :
              'text-red-400'
            }`}>
              {data.overall_avg_score != null
                ? `${(data.overall_avg_score * 100).toFixed(1)}%`
                : '—'}
            </span>
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-gray-900 rounded-lg p-0.5 gap-0.5">
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                tab === t.id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Distribution tab */}
      {tab === 'distribution' && (
        <ResponsiveContainer width="100%" height={180}>
          <BarChart data={data.distribution} margin={{ bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
            <XAxis
              dataKey="range"
              tick={{ fill: '#6b7280', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fill: '#6b7280', fontSize: 10 }}
              axisLine={false}
              tickLine={false}
              width={28}
            />
            <Tooltip content={<DistributionTooltip />} />
            <Bar dataKey="count" radius={[6, 6, 0, 0]}>
              {(data.distribution ?? []).map((entry, i) => (
                <Cell key={i} fill={bucketColor(entry.range)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}

      {/* Trend tab */}
      {tab === 'trend' && (
        data.trend.length === 0 ? (
          <div className="h-[180px] flex items-center justify-center text-gray-600 text-xs">
            Not enough data for trend view
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={data.trend} margin={{ bottom: 4 }}>
              <defs>
                <linearGradient id="evalGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#a78bfa" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#a78bfa" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
              <XAxis
                dataKey="hour"
                tickFormatter={v => v?.slice(11, 16) ?? ''}
                tick={{ fill: '#6b7280', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                domain={[0, 1]}
                tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                tick={{ fill: '#6b7280', fontSize: 10 }}
                axisLine={false}
                tickLine={false}
                width={36}
              />
              <Tooltip content={<TrendTooltip />} />
              <ReferenceLine
                y={data.overall_avg_score ?? 0}
                stroke="#a78bfa"
                strokeDasharray="4 4"
                strokeOpacity={0.5}
              />
              <Area
                type="monotone"
                dataKey="avg_score"
                stroke="#a78bfa"
                strokeWidth={2}
                fill="url(#evalGrad)"
                dot={false}
                activeDot={{ r: 4, fill: '#a78bfa' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )
      )}

      {/* By Type tab */}
      {tab === 'bytype' && (
        <div className="space-y-2 py-1">
          {data.by_type.length === 0 ? (
            <p className="text-gray-600 text-xs text-center py-8">No eval type data</p>
          ) : (
            data.by_type.map(t => {
              const color = TYPE_COLOR[t.eval_type] ?? DEFAULT_COLOR
              const pct = Math.round((t.avg_score ?? 0) * 100)
              return (
                <div key={t.eval_type} className="flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: color }} />
                  <span className="text-xs text-gray-300 w-24 capitalize">
                    {TYPE_LABEL[t.eval_type] ?? t.eval_type.replace('_', ' ')}
                  </span>
                  <div className="flex-1 h-2 rounded-full bg-gray-700 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, background: color }}
                    />
                  </div>
                  <ScoreChip score={t.avg_score} />
                  <span className="text-xs text-gray-600 w-14 text-right">
                    {t.count.toLocaleString()} evals
                  </span>
                </div>
              )
            })
          )}
        </div>
      )}

      {/* Trend — multi-line, one line per eval type */}
      {tab === 'trend' && (
        (() => {
          const trendData = data.trend_by_type ?? data.trend ?? []
          const evalTypes = data.by_type.map(t => t.eval_type)
          if (!trendData.length) {
            return (
              <div className="h-[180px] flex items-center justify-center text-gray-600 text-xs">
                Not enough data for trend view
              </div>
            )
          }
          return (
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={trendData} margin={{ bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                <XAxis
                  dataKey="hour"
                  tickFormatter={v => v?.slice(11, 16) ?? ''}
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 1]}
                  tickFormatter={v => `${(v * 100).toFixed(0)}%`}
                  tick={{ fill: '#6b7280', fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  width={36}
                />
                <Tooltip
                  formatter={(v, name) => [`${(v * 100).toFixed(1)}%`, name.replace('_', ' ')]}
                  labelFormatter={l => l?.slice(11, 16) ?? l}
                  contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 8, fontSize: 11 }}
                />
                <Legend
                  formatter={v => v.replace('_', ' ')}
                  wrapperStyle={{ fontSize: 10, color: '#9ca3af' }}
                />
                <ReferenceLine y={data.overall_avg_score ?? 0} stroke="#6b7280" strokeDasharray="4 4" strokeOpacity={0.4} />
                {evalTypes.map(et => (
                  <Line
                    key={et}
                    type="monotone"
                    dataKey={et}
                    name={et}
                    stroke={TYPE_COLOR[et] ?? DEFAULT_COLOR}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )
        })()
      )}

      {/* By Model tab */}
      {tab === 'bymodel' && (
        <div className="space-y-2 py-1">
          {(data.by_model ?? []).length === 0 ? (
            <p className="text-gray-600 text-xs text-center py-8">No per-model eval data</p>
          ) : (
            (data.by_model ?? []).map((m, i) => {
              const evalTypes = data.by_type.map(t => t.eval_type)
              const modelColor = ['#38bdf8','#a78bfa','#34d399','#fb923c','#f472b6'][i % 5]
              return (
                <div key={m.model} className="rounded-xl bg-gray-900/60 p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full" style={{ background: modelColor }} />
                    <span className="text-xs font-medium text-gray-200">{m.model}</span>
                  </div>
                  {evalTypes.map(et => {
                    const score = m[et]
                    if (score == null) return null
                    const color = TYPE_COLOR[et] ?? DEFAULT_COLOR
                    return (
                      <div key={et} className="flex items-center gap-2 pl-4">
                        <span className="text-[10px] text-gray-500 w-20 capitalize">{TYPE_LABEL[et] ?? et.replace('_',' ')}</span>
                        <div className="flex-1 h-1.5 rounded-full bg-gray-700 overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${(score * 100).toFixed(0)}%`, background: color }}
                          />
                        </div>
                        <span className="text-[10px] font-bold tabular-nums" style={{ color }}>
                          {(score * 100).toFixed(0)}%
                        </span>
                      </div>
                    )
                  })}
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}

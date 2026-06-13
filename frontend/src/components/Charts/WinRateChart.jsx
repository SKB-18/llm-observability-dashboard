import React, { useState } from 'react'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  Legend,
} from 'recharts'

const COLORS = ['#38bdf8', '#a78bfa', '#34d399', '#fb923c', '#f472b6', '#fbbf24', '#60a5fa', '#4ade80', '#f87171', '#c084fc']

function WinTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  return (
    <div className="rounded-xl bg-gray-900 border border-gray-700 px-3 py-2 shadow-xl text-xs space-y-1">
      <p className="text-gray-200 font-semibold">{d?.model}</p>
      <p className="text-emerald-400">Wins: {d?.wins} ({(d?.win_rate * 100).toFixed(1)}%)</p>
      <p className="text-amber-400">Ties: {d?.ties} ({((d?.ties / d?.battles) * 100).toFixed(1)}%)</p>
      <p className="text-red-400">Losses: {d?.losses}</p>
      <p className="text-gray-500">{d?.battles} battles total</p>
    </div>
  )
}

export default function WinRateChart({ data }) {
  const [sortBy, setSortBy] = useState('win_rate')

  if (!data || data.length === 0) {
    return (
      <div className="rounded-2xl bg-gray-800 border border-gray-700 p-6 text-center">
        <p className="text-gray-500 text-sm">No win-rate data available.</p>
      </div>
    )
  }

  const sorted = [...data].sort((a, b) => b[sortBy] - a[sortBy])

  // Stacked bar data: wins / ties / losses (as fractions for display)
  const chartData = sorted.map((r, i) => ({
    ...r,
    shortModel: r.model.length > 14 ? r.model.slice(0, 13) + '…' : r.model,
    winPct:  +(r.win_rate * 100).toFixed(1),
    tiePct:  +((r.ties / r.battles) * 100).toFixed(1),
    lossPct: +(((r.battles - r.wins - r.ties) / r.battles) * 100).toFixed(1),
    color: COLORS[i % COLORS.length],
  }))

  return (
    <div className="rounded-2xl bg-gray-800 border border-gray-700 p-4 shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-gray-400">
            Arena Win Rates
          </h3>
          <p className="text-xs text-gray-600 mt-0.5">
            Human preference from LMSYS chatbot arena · {data.reduce((s, r) => s + r.battles, 0).toLocaleString()} battles
          </p>
        </div>
        <div className="flex bg-gray-900 rounded-lg p-0.5 gap-0.5">
          {[['win_rate', 'Win Rate'], ['win_tie_rate', 'Win+Tie']].map(([k, label]) => (
            <button
              key={k}
              onClick={() => setSortBy(k)}
              className={`px-2 py-1 rounded-md text-xs font-medium transition-colors ${
                sortBy === k ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Horizontal stacked bar chart */}
      <ResponsiveContainer width="100%" height={Math.max(180, chartData.length * 28)}>
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ left: 8, right: 12, top: 4, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 100]}
            tickFormatter={v => `${v}%`}
            tick={{ fill: '#6b7280', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="shortModel"
            tick={{ fill: '#9ca3af', fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={88}
          />
          <Tooltip content={<WinTooltip />} />
          <Legend
            formatter={v => ({ win: 'Win', tie: 'Tie', loss: 'Loss' }[v] ?? v)}
            wrapperStyle={{ fontSize: 10, color: '#9ca3af', paddingTop: 8 }}
          />
          <Bar dataKey="winPct"  name="win"  stackId="a" fill="#10b981" radius={[0,0,0,0]} />
          <Bar dataKey="tiePct"  name="tie"  stackId="a" fill="#f59e0b" radius={[0,0,0,0]} />
          <Bar dataKey="lossPct" name="loss" stackId="a" fill="#ef4444" radius={[0,4,4,0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

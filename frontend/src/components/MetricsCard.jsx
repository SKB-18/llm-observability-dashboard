import React from 'react'
import {
  Activity,
  DollarSign,
  Clock,
  Star,
  CheckCircle,
  Cpu,
  TrendingUp,
  TrendingDown,
  Minus,
} from 'lucide-react'

const VARIANTS = {
  blue: {
    card: 'bg-gradient-to-br from-blue-950 to-blue-900 border-blue-700',
    icon: 'bg-blue-800 text-blue-300',
    label: 'text-blue-300',
    value: 'text-white',
  },
  green: {
    card: 'bg-gradient-to-br from-emerald-950 to-emerald-900 border-emerald-700',
    icon: 'bg-emerald-800 text-emerald-300',
    label: 'text-emerald-300',
    value: 'text-white',
  },
  yellow: {
    card: 'bg-gradient-to-br from-amber-950 to-yellow-900 border-amber-600',
    icon: 'bg-amber-800 text-amber-300',
    label: 'text-amber-300',
    value: 'text-white',
  },
  purple: {
    card: 'bg-gradient-to-br from-purple-950 to-violet-900 border-purple-700',
    icon: 'bg-purple-800 text-purple-300',
    label: 'text-purple-300',
    value: 'text-white',
  },
  red: {
    card: 'bg-gradient-to-br from-red-950 to-red-900 border-red-700',
    icon: 'bg-red-800 text-red-300',
    label: 'text-red-300',
    value: 'text-white',
  },
  gray: {
    card: 'bg-gradient-to-br from-gray-800 to-gray-750 border-gray-600',
    icon: 'bg-gray-700 text-gray-300',
    label: 'text-gray-300',
    value: 'text-white',
  },
}

const ICONS = {
  'Total Requests': Activity,
  'Total Cost': DollarSign,
  'Avg Latency': Clock,
  'Avg Quality': Star,
  'Success Rate': CheckCircle,
  'Active Models': Cpu,
}

function TrendBadge({ trend }) {
  if (!trend) return null
  const up = trend.startsWith('+') || trend.startsWith('↑')
  const down = trend.startsWith('-') || trend.startsWith('↓')
  const Icon = up ? TrendingUp : down ? TrendingDown : Minus
  const color = up ? 'text-emerald-400' : down ? 'text-red-400' : 'text-gray-400'
  return (
    <span className={`flex items-center gap-1 text-xs font-medium ${color}`}>
      <Icon size={12} />
      {trend}
    </span>
  )
}

export default function MetricsCard({
  title,
  value,
  unit = '',
  trend,
  color = 'blue',
  loading = false,
}) {
  const v = VARIANTS[color] ?? VARIANTS.blue
  const Icon = ICONS[title] ?? Activity

  if (loading) {
    return (
      <div
        data-testid="metrics-card"
        className={`rounded-2xl border p-5 shadow-xl ${v.card} animate-pulse`}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="h-4 bg-white/10 rounded w-3/4" />
          <div className="h-9 w-9 rounded-xl bg-white/10" />
        </div>
        <div className="h-9 bg-white/10 rounded w-1/2 mb-2" />
        <div className="h-3 bg-white/10 rounded w-1/3" />
      </div>
    )
  }

  return (
    <div
      data-testid="metrics-card"
      className={`rounded-2xl border p-5 shadow-xl transition-all duration-200 hover:scale-[1.02] hover:shadow-2xl cursor-default ${v.card}`}
    >
      <div className="flex items-start justify-between mb-3">
        <span className={`text-xs font-semibold uppercase tracking-widest ${v.label}`}>
          {title}
        </span>
        <div className={`p-2 rounded-xl ${v.icon}`}>
          <Icon size={16} />
        </div>
      </div>

      <div className="flex items-baseline gap-1.5">
        <span className={`text-3xl font-bold tabular-nums ${v.value}`}>
          {value ?? '—'}
        </span>
        {unit && (
          <span className={`text-sm font-medium ${v.label}`}>{unit}</span>
        )}
      </div>

      <div className="mt-2 min-h-[1.25rem]">
        <TrendBadge trend={trend} />
      </div>
    </div>
  )
}

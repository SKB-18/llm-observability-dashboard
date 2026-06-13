import React, { useState, useEffect } from 'react'
import {
  RefreshCw,
  AlertCircle,
  Activity,
  BarChart2,
  Database,
  FlaskConical,
  Upload,
} from 'lucide-react'
import MetricsCard from './MetricsCard'
import Filters from './Filters'
import ModelComparison from './ModelComparison'
import CostChart from './Charts/CostChart'
import LatencyChart from './Charts/LatencyChart'
import QualityChart from './Charts/QualityChart'
import RequestsChart from './Charts/RequestsChart'
import EvalAnalytics from './Charts/EvalAnalytics'
import WinRateChart from './Charts/WinRateChart'
import TokensChart from './Charts/TokensChart'
import CompletionsTable from './CompletionsTable'
import UploadDataset from './UploadDataset'

function fmt(val, decimals = 0) {
  if (val == null) return '—'
  return typeof val === 'number' ? val.toFixed(decimals) : String(val)
}

function LiveDot({ loading }) {
  return (
    <span className="relative flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full ${loading ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
      <span className="text-xs text-gray-500">{loading ? 'Refreshing…' : 'Live'}</span>
    </span>
  )
}

function SectionHeader({ icon: Icon, title, subtitle, badge }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <div className="p-1.5 rounded-lg bg-gray-700 text-gray-300">
        <Icon size={14} />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400">{title}</h2>
          {badge && (
            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-blue-900/40 text-blue-400 border border-blue-800/50">
              {badge}
            </span>
          )}
        </div>
        {subtitle && <p className="text-xs text-gray-600">{subtitle}</p>}
      </div>
    </div>
  )
}

function SourceBadge({ label, color = 'blue' }) {
  const cls = {
    blue:   'bg-blue-900/30 text-blue-400 border-blue-800/40',
    green:  'bg-emerald-900/30 text-emerald-400 border-emerald-800/40',
    purple: 'bg-purple-900/30 text-purple-400 border-purple-800/40',
  }[color]
  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full border ${cls}`}>
      {label}
    </span>
  )
}

function DividerWithLabel({ label }) {
  return (
    <div className="flex items-center gap-3 py-1">
      <div className="flex-1 h-px bg-gray-800" />
      <span className="text-[10px] uppercase tracking-widest text-gray-600 font-medium">{label}</span>
      <div className="flex-1 h-px bg-gray-800" />
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="rounded-2xl border border-gray-700 bg-gray-800 p-5 animate-pulse">
      <div className="flex items-start justify-between mb-3">
        <div className="h-3 bg-gray-700 rounded w-24" />
        <div className="h-9 w-9 rounded-xl bg-gray-700" />
      </div>
      <div className="h-9 bg-gray-700 rounded w-20 mb-2" />
      <div className="h-3 bg-gray-700 rounded w-14" />
    </div>
  )
}

function SkeletonChart() {
  return (
    <div className="rounded-2xl border border-gray-700 bg-gray-800 p-4 animate-pulse">
      <div className="h-3 bg-gray-700 rounded w-36 mb-4" />
      <div className="h-40 bg-gray-700/50 rounded-xl" />
    </div>
  )
}

// Inline benchmark quality cards (no separate component needed)
function BenchmarkQualityCards({ evalSummary }) {
  const qs = evalSummary?.evals_benchmark?.quality_scores ?? {}
  const cards = [
    { key: 'bleu',   label: 'BLEU Score',    unit: '',    color: 'blue',   desc: 'Text n-gram similarity' },
    { key: 'rouge',  label: 'ROUGE Score',   unit: '',    color: 'green',  desc: 'Content coverage (rougeL)' },
    { key: 'human',  label: 'Human Rating',  unit: '/ 1', color: 'purple', desc: 'Avg human quality rating' },
  ]
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
      {cards.map(({ key, label, unit, color, desc }) => {
        const entry = qs[key]
        return (
          <div key={key} className="rounded-2xl border border-gray-700 bg-gray-800 p-4">
            <p className="text-xs text-gray-500 mb-1">{label}</p>
            <p className="text-2xl font-bold text-white tabular-nums">
              {entry ? entry.avg.toFixed(3) : '—'}
              {entry && <span className="text-xs text-gray-500 ml-1">{unit}</span>}
            </p>
            <p className="text-[10px] text-gray-600 mt-1">
              {entry ? `${entry.count} evals · range ${entry.min.toFixed(2)}–${entry.max.toFixed(2)}` : desc}
            </p>
          </div>
        )
      })}
    </div>
  )
}

export default function Dashboard({ metrics, onFiltersChange }) {
  const { data, loading, error, refetch } = metrics
  const [filters, setFilters] = useState({})
  const [lastUpdated, setLastUpdated] = useState(null)
  const [evalData, setEvalData]           = useState(null)
  const [evalSummary, setEvalSummary]     = useState(null)
  const [modelComparison, setModelComp]   = useState(null)

  useEffect(() => {
    if (data && !loading) setLastUpdated(new Date())
  }, [data, loading])

  // Fetch all analytics endpoints together whenever main data refreshes
  useEffect(() => {
    Promise.all([
      fetch('/api/v1/metrics/evals').then(r => r.ok ? r.json() : null).catch(() => null),
      fetch('/api/v1/metrics/eval-summary').then(r => r.ok ? r.json() : null).catch(() => null),
      fetch('/api/v1/metrics/model-comparison').then(r => r.ok ? r.json() : null).catch(() => null),
    ]).then(([evals, summary, comparison]) => {
      setEvalData(evals)
      setEvalSummary(summary)
      setModelComp(comparison)
    })
  }, [data])

  function handleFilter(f) {
    setFilters(f)
    if (onFiltersChange) onFiltersChange(f)
  }

  const summary = data?.summary ?? {}
  const byModel = data?.byModel ?? []
  const byHour  = data?.byHour  ?? []

  // Per-model quality score: human_preference from win-rate data
  // Convert win_tie_rate_pct (0–100) to a 0–10 quality score for the chart axis
  const byModelWithScore = (modelComparison?.models ?? []).map(m => ({
    model: m.model,
    score: +(m.win_tie_rate_pct / 10).toFixed(1),
  }))

  const isInitialLoad = loading && !data

  // Benchmark data from eval-summary
  const benchCount = evalSummary?.evals_benchmark?.completions ?? 0

  return (
    <div className="min-h-screen bg-[#0f1117] text-white">
      {/* ── Header ──────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-20 bg-[#0f1117]/80 backdrop-blur-md border-b border-gray-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-blue-600/20 border border-blue-500/30">
            <BarChart2 size={18} className="text-blue-400" />
          </div>
          <div>
            <h1 className="text-base font-bold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              LLM Observability
            </h1>
            <p className="text-xs text-gray-500 leading-none">
              Real-time monitoring · {byModel.length} model{byModel.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <LiveDot loading={loading} />
          {lastUpdated && (
            <span className="text-xs text-gray-600 hidden sm:block">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={refetch}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 disabled:opacity-40 transition-colors"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </header>

      <main className="p-4 md:p-6 space-y-6 max-w-[1600px] mx-auto">
        {/* ── Filters ─────────────────────────────────────────────── */}
        <Filters onFilter={handleFilter} initialFilters={filters} />

        {/* ── Error ───────────────────────────────────────────────── */}
        {error && (
          <div className="flex items-center gap-3 rounded-xl bg-red-950/60 border border-red-800 p-4 text-red-300 text-sm">
            <AlertCircle size={16} className="flex-shrink-0" />
            <div>
              <p className="font-semibold">Failed to load metrics</p>
              <p className="text-xs text-red-400 mt-0.5">{error}</p>
            </div>
            <button onClick={refetch} className="ml-auto text-xs border border-red-700 rounded px-2 py-1 hover:bg-red-900 transition-colors">
              Retry
            </button>
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════
            SECTION 1 — PRODUCTION METRICS  (LMSYS Chatbot Arena)
            Real cost, latency, usage, and model win rates from 5 000
            human-judged arena battles.
        ════════════════════════════════════════════════════════════ */}
        <div className="rounded-2xl border border-blue-900/30 bg-blue-950/10 p-4 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database size={14} className="text-blue-400" />
              <span className="text-sm font-semibold text-blue-300">Production Metrics</span>
              <SourceBadge label="LMSYS Chatbot Arena" color="blue" />
            </div>
            <span className="text-[10px] text-gray-600">
              {(summary.total_requests ?? 0).toLocaleString()} real conversations · cost, latency, win rates
            </span>
          </div>

          {/* Overview cards */}
          <div>
            <SectionHeader icon={Activity} title="Overview" subtitle="Last 7 days · LMSYS arena data" />
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3">
              {isInitialLoad ? (
                Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
              ) : (
                <>
                  <MetricsCard
                    title="Total Requests"
                    value={(summary.total_requests ?? 0).toLocaleString()}
                    color="blue"
                    trend={summary.total_requests > 0 ? `${summary.total_requests.toLocaleString()} logged` : undefined}
                  />
                  <MetricsCard
                    title="Total Cost"
                    value={fmt(summary.total_cost_usd, 4)}
                    unit="USD"
                    color="green"
                  />
                  <MetricsCard
                    title="Avg Latency"
                    value={fmt(summary.avg_latency_ms, 0)}
                    unit="ms"
                    color="yellow"
                  />
                  <MetricsCard
                    title="Best Win Rate"
                    value={modelComparison?.models?.[0]
                      ? modelComparison.models[0].win_tie_rate_pct.toFixed(1)
                      : '—'}
                    unit="%"
                    color="purple"
                    trend={modelComparison?.models?.[0]?.model ?? undefined}
                  />
                  <MetricsCard
                    title="Success Rate"
                    value={fmt(summary.success_rate_percent, 1)}
                    unit="%"
                    color={(summary.success_rate_percent ?? 100) >= 99 ? 'green' : (summary.success_rate_percent ?? 100) >= 95 ? 'yellow' : 'red'}
                  />
                  <MetricsCard
                    title="Active Models"
                    value={(summary.models ?? []).length}
                    color="gray"
                    trend={(summary.models ?? []).slice(0, 2).join(', ') || undefined}
                  />
                </>
              )}
            </div>
          </div>

          {/* Time-series charts */}
          <div>
            <SectionHeader icon={BarChart2} title="Time Series" subtitle="Hourly breakdown" />
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-3">
              {isInitialLoad ? (
                Array.from({ length: 4 }).map((_, i) => <SkeletonChart key={i} />)
              ) : (
                <>
                  <RequestsChart data={byHour} />
                  <CostChart     data={byHour} />
                  <LatencyChart  data={byHour} />
                  <TokensChart   data={byHour} />
                </>
              )}
            </div>
          </div>

          {/* Model Comparison + Quality */}
          <div>
            <SectionHeader
              icon={Activity}
              title="Model Comparison"
              subtitle={`${byModel.length} model${byModel.length !== 1 ? 's' : ''} tracked · cost & latency from LMSYS`}
            />
            {isInitialLoad ? (
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
                <div className="xl:col-span-2"><SkeletonChart /></div>
                <SkeletonChart />
              </div>
            ) : (
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-3">
                <div className="xl:col-span-2">
                  <ModelComparison models={byModel} />
                </div>
                <QualityChart data={byModelWithScore} />
              </div>
            )}
          </div>

          {/* Arena Win Rates */}
          {modelComparison?.models?.length > 0 && (
            <div>
              <SectionHeader
                icon={BarChart2}
                title="Arena Win Rates"
                subtitle="Human preference from real chatbot arena battles"
                badge="Human-judged"
              />
              <WinRateChart data={modelComparison.models} />
            </div>
          )}

          {/* Recent Completions */}
          <div>
            <SectionHeader icon={Activity} title="Recent Completions" subtitle="Latest LMSYS logs · paginated" />
            <CompletionsTable source="lmsys" />
          </div>
        </div>

        {/* ════════════════════════════════════════════════════════════
            SECTION 2 — BENCHMARK QUALITY EVALS  (evals_dataset.csv)
            Real prompt/response pairs scored with BLEU, ROUGE, and
            human ratings. Separate from production data.
        ════════════════════════════════════════════════════════════ */}
        <div className="rounded-2xl border border-purple-900/30 bg-purple-950/10 p-4 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FlaskConical size={14} className="text-purple-400" />
              <span className="text-sm font-semibold text-purple-300">Benchmark Quality Evals</span>
              <SourceBadge label="evals_dataset.csv" color="purple" />
            </div>
            <span className="text-[10px] text-gray-600">
              {benchCount} real prompt/response pairs · BLEU, ROUGE, human ratings
            </span>
          </div>

          {/* Quality score cards */}
          <div>
            <SectionHeader
              icon={FlaskConical}
              title="Quality Scores"
              subtitle="Computed on real prompt/response text"
            />
            <BenchmarkQualityCards evalSummary={evalSummary} />
          </div>

          {/* Eval Analytics (distribution, trend, by-type) */}
          <div>
            <SectionHeader
              icon={BarChart2}
              title="Eval Analytics"
              subtitle="Score distribution · trend · by eval type · by model"
            />
            {isInitialLoad ? (
              <SkeletonChart />
            ) : (
              <EvalAnalytics data={evalData} />
            )}
          </div>
        </div>

        {/* ════════════════════════════════════════════════════════════
            SECTION 3 — UPLOAD YOUR OWN DATASET
            Upload any CSV with prompt+response pairs and get real
            BLEU, ROUGE, and human-rating metrics instantly.
        ════════════════════════════════════════════════════════════ */}
        <div className="rounded-2xl border border-indigo-900/30 bg-indigo-950/10 p-4 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Upload size={14} className="text-indigo-400" />
              <span className="text-sm font-semibold text-indigo-300">Upload Your Dataset</span>
              <SourceBadge label="CSV upload" color="blue" />
            </div>
            <span className="text-[10px] text-gray-600">
              prompt + response pairs → BLEU · ROUGE · human rating
            </span>
          </div>
          <UploadDataset />
        </div>

        {/* ── Footer ─────────────────────────────────────────────── */}
        <footer className="text-center text-xs text-gray-700 pb-4">
          LLM Observability Dashboard · Auto-refreshes every 30 s
        </footer>
      </main>
    </div>
  )
}

import React, { useState, useRef, useCallback, useEffect } from 'react'
import { Upload, X, FileText, CheckCircle, AlertCircle, Trash2, ChevronDown, ChevronUp, Info } from 'lucide-react'

const SCORE_COLOR = (v) =>
  v >= 0.7 ? 'text-emerald-400' : v >= 0.4 ? 'text-amber-400' : 'text-red-400'

const EVAL_LABEL = { bleu: 'BLEU', rouge: 'ROUGE', human: 'Human Rating', llm_judge: 'LLM Judge' }

function ScorePill({ label, value }) {
  if (value == null) return null
  const pct = (value * 100).toFixed(1)
  return (
    <div className="flex flex-col items-center bg-gray-900 rounded-xl px-3 py-2 min-w-[72px]">
      <span className="text-[10px] text-gray-500 uppercase tracking-wider mb-0.5">{label}</span>
      <span className={`text-lg font-bold tabular-nums ${SCORE_COLOR(value)}`}>{pct}%</span>
    </div>
  )
}

function UploadCard({ upload, onDelete }) {
  const [expanded, setExpanded] = useState(false)
  const [deleting, setDeleting] = useState(false)

  async function handleDelete() {
    if (!window.confirm(`Delete "${upload.filename}" and all its data?`)) return
    setDeleting(true)
    try {
      await fetch(`/api/v1/upload/${upload.id}`, { method: 'DELETE' })
      onDelete(upload.id)
    } catch {
      setDeleting(false)
    }
  }

  const scores = upload.scores ?? {}
  const scoreEntries = Object.entries(scores)

  return (
    <div className="rounded-2xl border border-gray-700 bg-gray-800/60 overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3">
        <FileText size={14} className="text-indigo-400 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{upload.filename}</p>
          <p className="text-[10px] text-gray-500">
            {upload.row_count.toLocaleString()} rows ·{' '}
            {new Date(upload.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
            {upload.has_quality_rating && <span className="ml-1 text-purple-400">· quality ratings</span>}
            {upload.has_model_column && <span className="ml-1 text-blue-400">· multi-model</span>}
          </p>
        </div>

        {/* Score pills */}
        <div className="hidden sm:flex gap-2">
          {scoreEntries.slice(0, 3).map(([k, v]) => (
            <ScorePill key={k} label={EVAL_LABEL[k] ?? k} value={v} />
          ))}
        </div>

        <div className="flex items-center gap-1 ml-2">
          <button
            onClick={() => setExpanded(e => !e)}
            className="p-1.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-gray-700 transition-colors"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-1.5 rounded-lg text-gray-600 hover:text-red-400 hover:bg-red-950/40 transition-colors disabled:opacity-40"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-700/60 px-4 py-3 space-y-3">
          {/* All score pills on mobile */}
          {scoreEntries.length > 0 && (
            <div className="flex flex-wrap gap-2 sm:hidden">
              {scoreEntries.map(([k, v]) => (
                <ScorePill key={k} label={EVAL_LABEL[k] ?? k} value={v} />
              ))}
            </div>
          )}

          {/* Score bars */}
          <div className="space-y-2">
            {scoreEntries.map(([k, v]) => {
              const pct = Math.round(v * 100)
              return (
                <div key={k} className="flex items-center gap-3">
                  <span className="text-[10px] text-gray-500 w-20">{EVAL_LABEL[k] ?? k}</span>
                  <div className="flex-1 h-2 rounded-full bg-gray-700 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${pct}%`,
                        background: v >= 0.7 ? '#10b981' : v >= 0.4 ? '#f59e0b' : '#ef4444'
                      }}
                    />
                  </div>
                  <span className={`text-xs font-bold tabular-nums w-10 text-right ${SCORE_COLOR(v)}`}>
                    {pct}%
                  </span>
                </div>
              )
            })}
          </div>

          <div className="flex items-center gap-2 pt-1">
            <span className="text-[10px] text-gray-600 font-mono">{upload.source_id}</span>
            <span className="text-gray-700">·</span>
            <a
              href={upload.metrics_url}
              target="_blank"
              rel="noreferrer"
              className="text-[10px] text-blue-500 hover:text-blue-400 underline underline-offset-2"
            >
              Raw metrics JSON
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

function FormatGuide() {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-xl border border-gray-700/60 bg-gray-900/40 overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left"
      >
        <Info size={12} className="text-gray-500" />
        <span className="text-xs text-gray-500 flex-1">CSV format guide</span>
        {open ? <ChevronUp size={12} className="text-gray-600" /> : <ChevronDown size={12} className="text-gray-600" />}
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2">
          <div className="grid grid-cols-2 gap-1 text-[10px]">
            <div>
              <p className="text-emerald-400 font-semibold mb-1">Required columns</p>
              {[['prompt', 'Input text sent to the model'], ['response', 'Model output text']].map(([col, desc]) => (
                <div key={col} className="flex gap-2 py-0.5">
                  <code className="text-indigo-300 w-20 flex-shrink-0">{col}</code>
                  <span className="text-gray-500">{desc}</span>
                </div>
              ))}
            </div>
            <div>
              <p className="text-amber-400 font-semibold mb-1">Optional columns</p>
              {[
                ['model', 'Model name (default: "uploaded")'],
                ['tokens_in', 'Input token count'],
                ['tokens_out', 'Output token count'],
                ['latency_ms', 'Response latency (ms)'],
                ['cost_usd', 'Cost in USD'],
                ['quality_rating', '0–10 human quality score'],
                ['criteria', 'Evaluation criteria text'],
              ].map(([col, desc]) => (
                <div key={col} className="flex gap-2 py-0.5">
                  <code className="text-indigo-300 w-24 flex-shrink-0">{col}</code>
                  <span className="text-gray-500">{desc}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="mt-2">
            <p className="text-[10px] text-gray-600 mb-1">Example:</p>
            <pre className="text-[10px] text-gray-400 bg-gray-900 rounded-lg p-2 overflow-x-auto">
{`prompt,response,model,quality_rating
"What is Python?","Python is a programming language.",gpt-4,8
"Explain async/await","async/await is used for...",claude-3-opus,9`}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}

export default function UploadDataset() {
  const [dragging, setDragging]   = useState(false)
  const [uploading, setUploading] = useState(false)
  const [result, setResult]       = useState(null)   // last upload result
  const [error, setError]         = useState(null)
  const [history, setHistory]     = useState([])
  const inputRef = useRef(null)

  const loadHistory = useCallback(() => {
    fetch('/api/v1/upload/datasets')
      .then(r => r.ok ? r.json() : [])
      .then(setHistory)
      .catch(() => {})
  }, [])

  useEffect(() => { loadHistory() }, [loadHistory])

  async function handleFile(file) {
    if (!file || !file.name.toLowerCase().endsWith('.csv')) {
      setError('Only .csv files are accepted.')
      return
    }
    setError(null)
    setResult(null)
    setUploading(true)

    const form = new FormData()
    form.append('file', file)

    try {
      const res = await fetch('/api/v1/upload/csv', { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail ?? 'Upload failed.')
      } else {
        setResult(data)
        loadHistory()
      }
    } catch (err) {
      setError('Network error: ' + err.message)
    } finally {
      setUploading(false)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function onInputChange(e) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  function handleDelete(id) {
    setHistory(h => h.filter(u => u.id !== id))
  }

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`
          relative flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed
          p-8 text-center cursor-pointer select-none transition-all duration-200
          ${dragging
            ? 'border-indigo-500 bg-indigo-950/30 scale-[1.01]'
            : uploading
            ? 'border-gray-700 bg-gray-800/40 cursor-not-allowed opacity-70'
            : 'border-gray-700 bg-gray-800/30 hover:border-indigo-600/60 hover:bg-indigo-950/10'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={onInputChange}
          disabled={uploading}
        />

        {uploading ? (
          <>
            <div className="w-10 h-10 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
            <p className="text-sm text-gray-400">Uploading and computing metrics…</p>
          </>
        ) : (
          <>
            <div className={`p-3 rounded-2xl ${dragging ? 'bg-indigo-600/20' : 'bg-gray-700/40'} transition-colors`}>
              <Upload size={22} className={dragging ? 'text-indigo-400' : 'text-gray-400'} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-300">
                Drop a CSV file here, or <span className="text-indigo-400 underline underline-offset-2">browse</span>
              </p>
              <p className="text-xs text-gray-600 mt-0.5">Up to 10,000 rows · 50 MB · .csv only</p>
            </div>
          </>
        )}
      </div>

      <FormatGuide />

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 rounded-xl bg-red-950/50 border border-red-800 px-3 py-2.5 text-xs text-red-300">
          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
          <p>{error}</p>
          <button onClick={() => setError(null)} className="ml-auto flex-shrink-0">
            <X size={12} />
          </button>
        </div>
      )}

      {/* Last upload result */}
      {result && (
        <div className="rounded-2xl border border-emerald-800/50 bg-emerald-950/20 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle size={14} className="text-emerald-400" />
            <span className="text-sm font-semibold text-emerald-300">Upload complete</span>
            <button onClick={() => setResult(null)} className="ml-auto text-gray-600 hover:text-gray-400">
              <X size={12} />
            </button>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <FileText size={12} />
            <span className="font-medium text-white">{result.filename}</span>
            <span>·</span>
            <span>{result.row_count.toLocaleString()} rows</span>
            {result.columns_detected && (
              <>
                <span>·</span>
                <span className="text-gray-600">cols: {result.columns_detected.join(', ')}</span>
              </>
            )}
          </div>

          {/* Scores */}
          {Object.keys(result.scores ?? {}).length > 0 && (
            <div className="flex flex-wrap gap-2">
              {Object.entries(result.scores).map(([k, v]) => (
                <ScorePill key={k} label={EVAL_LABEL[k] ?? k} value={v} />
              ))}
            </div>
          )}

          {/* Model breakdown */}
          {result.models?.length > 1 && (
            <div className="space-y-1">
              <p className="text-[10px] text-gray-600 uppercase tracking-wider">Model breakdown</p>
              {result.models.map(m => (
                <div key={m.model} className="flex items-center gap-2 text-xs">
                  <span className="text-gray-300">{m.model}</span>
                  <span className="text-gray-600">{m.count.toLocaleString()} rows</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Upload history */}
      {history.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] uppercase tracking-widest text-gray-600 font-medium px-1">
            Upload history ({history.length})
          </p>
          {history.map(u => (
            <UploadCard key={u.id} upload={u} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  )
}

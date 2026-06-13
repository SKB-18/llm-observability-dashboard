import React, { useState } from 'react'
import { SlidersHorizontal, X, ChevronDown } from 'lucide-react'

const KNOWN_MODELS = [
  'claude-3-5-sonnet',
  'claude-3-opus',
  'gpt-4',
  'gpt-4-turbo',
  'gpt-3.5-turbo',
  'gemini-pro',
  'llama-2-70b',
  'mistral-large',
]

function defaultStart() {
  const d = new Date()
  d.setDate(d.getDate() - 7)
  return d.toISOString().slice(0, 16)
}

function defaultEnd() {
  return new Date().toISOString().slice(0, 16)
}

export default function Filters({ onFilter, initialFilters = {} }) {
  const [startDate, setStartDate] = useState(initialFilters.start_date || defaultStart())
  const [endDate,   setEndDate]   = useState(initialFilters.end_date || defaultEnd())
  const [selectedModels, setSelectedModels] = useState(initialFilters.models || [])
  const [expanded, setExpanded] = useState(false)

  const activeCount =
    selectedModels.length +
    (startDate !== defaultStart() ? 1 : 0) +
    (endDate !== defaultEnd() ? 1 : 0)

  function toggleModel(model) {
    setSelectedModels((prev) =>
      prev.includes(model) ? prev.filter((m) => m !== model) : [...prev, model]
    )
  }

  function handleApply() {
    onFilter({
      start_date: startDate ? new Date(startDate).toISOString() : undefined,
      end_date:   endDate   ? new Date(endDate).toISOString()   : undefined,
      models:     selectedModels,
    })
    setExpanded(false)
  }

  function handleClear() {
    const s = defaultStart()
    const e = defaultEnd()
    setStartDate(s)
    setEndDate(e)
    setSelectedModels([])
    onFilter({ start_date: undefined, end_date: undefined, models: [] })
    setExpanded(false)
  }

  return (
    <div
      data-testid="filters"
      className="rounded-2xl bg-gray-800 border border-gray-700 shadow-xl overflow-hidden"
    >
      {/* Collapsed bar */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-750 transition-colors text-left"
      >
        <SlidersHorizontal size={16} className="text-blue-400 flex-shrink-0" />
        <span className="text-sm font-medium text-gray-300 flex-1">Filters</span>
        {activeCount > 0 && (
          <span className="bg-blue-600 text-white text-xs font-bold rounded-full px-2 py-0.5">
            {activeCount}
          </span>
        )}
        <ChevronDown
          size={14}
          className={`text-gray-500 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
        />
      </button>

      {/* Expanded panel */}
      {expanded && (
        <div className="border-t border-gray-700 px-4 pb-4 pt-3 space-y-4">
          {/* Date range */}
          <div className="flex flex-wrap gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-gray-500">Start date</label>
              <input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="rounded-lg bg-gray-700 border border-gray-600 px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-medium text-gray-500">End date</label>
              <input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="rounded-lg bg-gray-700 border border-gray-600 px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Model chips */}
          <div>
            <label className="text-xs font-medium text-gray-500 block mb-2">Models</label>
            <div className="flex flex-wrap gap-2">
              {KNOWN_MODELS.map((m) => (
                <button
                  key={m}
                  onClick={() => toggleModel(m)}
                  className={`rounded-full px-3 py-1 text-xs font-medium transition-all ${
                    selectedModels.includes(m)
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30 scale-105'
                      : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white border border-gray-600'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-1">
            <button
              onClick={handleClear}
              className="flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-gray-300 border border-gray-600 transition-colors"
            >
              <X size={13} /> Clear all
            </button>
            <button
              onClick={handleApply}
              className="flex-1 rounded-lg px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white font-semibold shadow-md shadow-blue-500/30 transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

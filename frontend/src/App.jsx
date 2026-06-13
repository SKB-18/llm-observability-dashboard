import React, { useState } from 'react'
import Dashboard from './components/Dashboard'
import ErrorBoundary from './components/ErrorBoundary'
import { useMetrics } from './hooks/useMetrics'

export default function App() {
  const [filters, setFilters] = useState({})
  const metrics = useMetrics(filters)

  return (
    <div className="min-h-screen bg-[#0f1117] text-white">
      <ErrorBoundary>
        <Dashboard metrics={metrics} onFiltersChange={setFilters} />
      </ErrorBoundary>
    </div>
  )
}

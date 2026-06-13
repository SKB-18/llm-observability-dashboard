import React from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="rounded-2xl bg-gray-800 border border-red-800 p-6 flex flex-col items-center gap-3 text-center">
        <div className="p-3 rounded-full bg-red-950 border border-red-800">
          <AlertTriangle size={24} className="text-red-400" />
        </div>
        <div>
          <p className="font-semibold text-white">Something went wrong</p>
          <p className="text-xs text-gray-500 mt-1 font-mono">
            {this.state.error?.message ?? 'Unknown error'}
          </p>
        </div>
        <button
          onClick={() => this.setState({ hasError: false, error: null })}
          className="flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 text-gray-300 border border-gray-600 transition-colors"
        >
          <RefreshCw size={12} /> Try again
        </button>
      </div>
    )
  }
}

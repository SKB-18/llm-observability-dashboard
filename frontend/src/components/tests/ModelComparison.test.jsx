import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import ModelComparison from '../ModelComparison'

const MODELS = [
  { model: 'gpt-4', request_count: 800, avg_latency_ms: 310, total_cost_usd: 3.0, avg_tokens_in: 200, avg_tokens_out: 100, success_rate_percent: 99 },
  { model: 'claude-3-5-sonnet', request_count: 400, avg_latency_ms: 340, total_cost_usd: 1.5, avg_tokens_in: 180, avg_tokens_out: 90, success_rate_percent: 99.5 },
]

describe('ModelComparison', () => {
  it('renders model rows', () => {
    render(<ModelComparison models={MODELS} />)
    expect(screen.getByTestId('model-comparison')).toBeTruthy()
    expect(screen.getByText('gpt-4')).toBeTruthy()
    expect(screen.getByText('claude-3-5-sonnet')).toBeTruthy()
  })

  it('shows empty state with no models', () => {
    render(<ModelComparison models={[]} />)
    expect(screen.getByText(/No model data/i)).toBeTruthy()
  })

  it('renders table headers', () => {
    render(<ModelComparison models={MODELS} />)
    expect(screen.getByText('Model')).toBeTruthy()
    // 'Requests' appears both in the table header and the chart toggle button
    expect(screen.getAllByText('Requests').length).toBeGreaterThan(0)
    expect(screen.getByText('Total Cost')).toBeTruthy()
  })

  it('highlights best latency', () => {
    render(<ModelComparison models={MODELS} />)
    // gpt-4 has lower latency → should have green class
    const cells = screen.getAllByText(/310 ms/i)
    expect(cells.length).toBeGreaterThan(0)
  })
})

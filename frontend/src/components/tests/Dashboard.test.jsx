import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Dashboard from '../Dashboard'

const mockMetrics = {
  data: {
    summary: {
      total_requests: 1234,
      total_cost_usd: 5.678,
      avg_latency_ms: 320.5,
      success_rate_percent: 99.1,
      models: ['gpt-4', 'claude-3-5-sonnet'],
    },
    byModel: [
      {
        model: 'gpt-4',
        request_count: 800,
        avg_latency_ms: 310,
        total_cost_usd: 3.0,
        avg_tokens_in: 200,
        avg_tokens_out: 100,
        success_rate_percent: 99,
      },
      {
        model: 'claude-3-5-sonnet',
        request_count: 434,
        avg_latency_ms: 340,
        total_cost_usd: 2.678,
        avg_tokens_in: 180,
        avg_tokens_out: 90,
        success_rate_percent: 99.5,
      },
    ],
    byHour: [
      {
        hour: '2024-06-11T12:00:00',
        requests: 45,
        avg_cost_usd: 0.002,
        avg_latency_ms: 310,
        success_count: 45,
      },
    ],
    percentiles: { p50: 310, p95: 600, p99: 900 },
  },
  loading: false,
  error: null,
  refetch: vi.fn(),
}

describe('Dashboard', () => {
  it('renders the header', () => {
    render(<Dashboard metrics={mockMetrics} />)
    // Header h1 contains 'LLM Observability' — may appear multiple times across DOM
    expect(screen.getAllByText(/LLM Observability/i).length).toBeGreaterThan(0)
  })

  it('shows 6 metrics cards', () => {
    render(<Dashboard metrics={mockMetrics} />)
    const cards = screen.getAllByTestId('metrics-card')
    expect(cards.length).toBe(6)
  })

  it('shows total requests value', () => {
    render(<Dashboard metrics={mockMetrics} />)
    expect(screen.getByText('1,234')).toBeTruthy()
  })

  it('shows skeleton cards when loading and no data', () => {
    render(<Dashboard metrics={{ ...mockMetrics, data: null, loading: true }} />)
    // Skeletons use animate-pulse
    const pulses = document.querySelectorAll('.animate-pulse')
    expect(pulses.length).toBeGreaterThan(0)
  })

  it('shows error message', () => {
    render(<Dashboard metrics={{ ...mockMetrics, error: 'API unreachable' }} />)
    expect(screen.getByText(/API unreachable/i)).toBeTruthy()
  })

  it('renders model comparison table', () => {
    render(<Dashboard metrics={mockMetrics} />)
    expect(screen.getByTestId('model-comparison')).toBeTruthy()
    expect(screen.getAllByText('gpt-4').length).toBeGreaterThan(0)
  })

  it('renders all four charts', () => {
    render(<Dashboard metrics={mockMetrics} />)
    expect(screen.getByTestId('cost-chart')).toBeTruthy()
    expect(screen.getByTestId('latency-chart')).toBeTruthy()
    expect(screen.getByTestId('quality-chart')).toBeTruthy()
    expect(screen.getByTestId('requests-chart')).toBeTruthy()
  })

  it('calls refetch when Refresh button is clicked', () => {
    render(<Dashboard metrics={mockMetrics} />)
    screen.getByText('Refresh').click()
    expect(mockMetrics.refetch).toHaveBeenCalled()
  })
})

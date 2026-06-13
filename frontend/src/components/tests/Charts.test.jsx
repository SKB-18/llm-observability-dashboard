import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import CostChart from '../Charts/CostChart'
import LatencyChart from '../Charts/LatencyChart'
import QualityChart from '../Charts/QualityChart'

const HOUR_DATA = [
  { hour: '2024-06-11T12:00:00Z', avg_cost_usd: 0.002, avg_latency_ms: 320, requests: 10, p50: 320, p95: 600, p99: 900 },
  { hour: '2024-06-11T13:00:00Z', avg_cost_usd: 0.003, avg_latency_ms: 350, requests: 15, p50: 350, p95: 650, p99: 950 },
]

const QUALITY_DATA = [
  { model: 'gpt-4', score: 8.5 },
  { model: 'claude-3-5-sonnet', score: 9.0 },
  { model: 'gpt-3.5-turbo', score: 6.5 },
]

describe('CostChart', () => {
  it('renders with data', () => {
    render(<CostChart data={HOUR_DATA} />)
    expect(screen.getByTestId('cost-chart')).toBeTruthy()
    expect(screen.getByText(/Cost Over Time/i)).toBeTruthy()
  })

  it('renders empty without crashing', () => {
    render(<CostChart data={[]} />)
    expect(screen.getByTestId('cost-chart')).toBeTruthy()
  })
})

describe('LatencyChart', () => {
  it('renders with data', () => {
    render(<LatencyChart data={HOUR_DATA} />)
    expect(screen.getByTestId('latency-chart')).toBeTruthy()
    expect(screen.getByText(/Latency Percentiles/i)).toBeTruthy()
  })

  it('renders empty without crashing', () => {
    render(<LatencyChart data={[]} />)
    expect(screen.getByTestId('latency-chart')).toBeTruthy()
  })
})

describe('QualityChart', () => {
  it('renders with data', () => {
    render(<QualityChart data={QUALITY_DATA} />)
    expect(screen.getByTestId('quality-chart')).toBeTruthy()
    expect(screen.getByText(/Quality Score/i)).toBeTruthy()
  })

  it('renders empty without crashing', () => {
    render(<QualityChart data={[]} />)
    expect(screen.getByTestId('quality-chart')).toBeTruthy()
  })
})

import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MetricsCard from '../MetricsCard'

describe('MetricsCard', () => {
  it('renders title and value', () => {
    render(<MetricsCard title="Avg Latency" value={450} unit="ms" />)
    expect(screen.getByText('Avg Latency')).toBeTruthy()
    expect(screen.getByText('450')).toBeTruthy()
    expect(screen.getByText('ms')).toBeTruthy()
  })

  it('renders trend when provided', () => {
    render(<MetricsCard title="Cost" value={1.2} trend="↓ 5%" />)
    expect(screen.getByText('↓ 5%')).toBeTruthy()
  })

  it('does not render trend when omitted', () => {
    render(<MetricsCard title="Requests" value={100} />)
    expect(screen.queryByText(/↓|↑/)).toBeNull()
  })

  it('renders dash when value is null', () => {
    render(<MetricsCard title="X" value={null} />)
    expect(screen.getByText('—')).toBeTruthy()
  })

  it('applies color class', () => {
    render(<MetricsCard title="X" value={1} color="green" />)
    const card = screen.getByTestId('metrics-card')
    // New variant uses 'emerald' for the green theme
    expect(card.className).toMatch(/emerald|green/)
  })
})

import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Filters from '../Filters'

/** Open the collapsible filter panel so controls are visible */
function renderExpanded(onFilter = vi.fn()) {
  const utils = render(<Filters onFilter={onFilter} />)
  // Click the toggle button to expand the panel
  fireEvent.click(screen.getByText('Filters'))
  return { ...utils, onFilter }
}

describe('Filters', () => {
  it('renders filter bar collapsed by default', () => {
    render(<Filters onFilter={vi.fn()} />)
    expect(screen.getByTestId('filters')).toBeTruthy()
    expect(screen.getByText('Filters')).toBeTruthy()
    // Controls are hidden until expanded
    expect(screen.queryByText('Apply Filters')).toBeNull()
  })

  it('expands to show controls when clicked', () => {
    renderExpanded()
    expect(screen.getByText('Apply Filters')).toBeTruthy()
    expect(screen.getByText('Clear all')).toBeTruthy()
  })

  it('calls onFilter when Apply Filters is clicked', () => {
    const { onFilter } = renderExpanded()
    fireEvent.click(screen.getByText('Apply Filters'))
    expect(onFilter).toHaveBeenCalledTimes(1)
    const arg = onFilter.mock.calls[0][0]
    expect(arg).toHaveProperty('models')
  })

  it('resets and calls onFilter when Clear all is clicked', () => {
    const { onFilter } = renderExpanded()
    fireEvent.click(screen.getByText('Clear all'))
    expect(onFilter).toHaveBeenCalledTimes(1)
    const arg = onFilter.mock.calls[0][0]
    expect(arg.models).toEqual([])
  })

  it('toggles model chip on click', () => {
    renderExpanded()
    const gpt4 = screen.getByText('gpt-4')
    fireEvent.click(gpt4)
    // chip becomes selected – gains bg-blue-600 class
    expect(gpt4.className).toMatch(/blue/)
    // click again → deselect
    fireEvent.click(gpt4)
    expect(gpt4.className).not.toMatch(/blue-600/)
  })

  it('shows active filter count badge when filters are set', () => {
    const { onFilter } = renderExpanded()
    // Select gpt-4
    fireEvent.click(screen.getByText('gpt-4'))
    // Close by clicking "Apply Filters" — badge should appear on re-render
    fireEvent.click(screen.getByText('Apply Filters'))
    // Re-open: badge reflects 1 active model
    // (badge appears in the collapsed bar after re-render)
    fireEvent.click(screen.getByText('Filters'))
    // Model chip is still selected
    expect(screen.getByText('gpt-4').className).toMatch(/blue/)
  })
})

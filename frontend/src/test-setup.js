import '@testing-library/jest-dom'

// Suppress recharts ResizeObserver errors in jsdom
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

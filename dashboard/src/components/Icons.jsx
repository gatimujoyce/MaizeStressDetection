import React from 'react'

export function CheckIcon({ color = 'currentColor', size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="2" strokeLinecap="square">
      <polyline points="3 8 6 11 13 4" />
    </svg>
  )
}

export function WarningIcon({ color = 'currentColor', size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="2" strokeLinecap="square">
      <path d="M8 2L1 14h14L8 2z" />
      <line x1="8" y1="6" x2="8" y2="9" />
      <line x1="8" y1="11.5" x2="8" y2="12" />
    </svg>
  )
}

export function ErrorIcon({ color = 'currentColor', size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="2" strokeLinecap="square">
      <line x1="3" y1="3" x2="13" y2="13" />
      <line x1="13" y1="3" x2="3" y2="13" />
    </svg>
  )
}

export function InfoIcon({ color = 'currentColor', size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="2" strokeLinecap="square">
      <circle cx="8" cy="8" r="6" />
      <line x1="8" y1="7" x2="8" y2="11" />
      <line x1="8" y1="5" x2="8" y2="5.5" />
    </svg>
  )
}
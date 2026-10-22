// Drawn maize plant for the verdict panel and empty state.
// Variants: healthy (golden tassel), droop (dry or hot), wet (standing in water),
// disease (leaf spots), seedling (no checks yet). Decorative: text carries the meaning.
// Needs --illus-gold and --illus-water in global.css.

const SHAPES = {
  healthy: (
    <>
          <ellipse cx="80" cy="148" rx="48" ry="7" fill="var(--color-neutral-text)" opacity="0.15"/>
          <path d="M80 146 C80 120 80 90 80 62" fill="none" stroke="var(--color-healthy-text)" strokeWidth="5" strokeLinecap="round"/>
          <path d="M80 124 C62 108 40 98 14 100 C40 110 62 122 80 132 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 120 C98 104 120 94 146 96 C120 106 98 118 80 128 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 98 C64 80 46 70 26 70 C46 80 64 94 80 106 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 92 C96 74 114 64 134 62 C114 74 96 88 80 100 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 70 C80 56 80 46 80 34" fill="none" stroke="var(--color-healthy-text)" strokeWidth="3" strokeLinecap="round"/>
          <path d="M80 46 C72 42 66 36 62 28" fill="none" stroke="var(--illus-gold)" strokeWidth="2.6" strokeLinecap="round"/>
          <path d="M80 42 C74 34 72 26 72 16" fill="none" stroke="var(--illus-gold)" strokeWidth="2.6" strokeLinecap="round"/>
          <path d="M80 46 C88 42 94 36 98 28" fill="none" stroke="var(--illus-gold)" strokeWidth="2.6" strokeLinecap="round"/>
          <path d="M80 42 C86 34 88 26 88 16" fill="none" stroke="var(--illus-gold)" strokeWidth="2.6" strokeLinecap="round"/>
          <path d="M80 34 C80 26 80 20 80 10" fill="none" stroke="var(--illus-gold)" strokeWidth="2.6" strokeLinecap="round"/>
    </>
  ),
  droop: (
    <>
          <ellipse cx="80" cy="148" rx="48" ry="7" fill="var(--color-neutral-text)" opacity="0.15"/>
          <path d="M80 146 C80 120 80 90 80 62" fill="none" stroke="var(--color-healthy-text)" strokeWidth="5" strokeLinecap="round"/>
          <path d="M80 124 C60 112 38 114 20 138 C40 126 62 128 80 132 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 120 C100 108 122 110 140 134 C120 122 98 124 80 128 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 98 C60 88 40 92 26 120 C44 106 62 104 80 106 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 92 C100 82 120 86 134 114 C116 100 98 98 80 100 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M77 74 C74 56 74 40 64 30 C82 38 86 56 83 74 Z" fill="var(--color-healthy-text)"/>
    </>
  ),
  wet: (
    <>
          <path d="M80 146 C80 120 80 90 80 62" fill="none" stroke="var(--color-healthy-text)" strokeWidth="5" strokeLinecap="round"/>
          <path d="M80 124 C62 108 40 98 14 100 C40 110 62 122 80 132 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 120 C98 104 120 94 146 96 C120 106 98 118 80 128 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 98 C64 80 46 70 26 70 C46 80 64 94 80 106 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 92 C96 74 114 64 134 62 C114 74 96 88 80 100 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M77 74 C74 54 76 30 84 10 C88 32 86 56 83 74 Z" fill="var(--color-healthy-text)"/>
          <path d="M8 128 C20 122 32 122 44 128 C56 134 68 134 80 128 C92 122 104 122 116 128 C128 134 140 134 152 128 L152 152 L8 152 Z" fill="var(--illus-water)" opacity="0.55"/>
    </>
  ),
  disease: (
    <>
          <ellipse cx="80" cy="148" rx="48" ry="7" fill="var(--color-neutral-text)" opacity="0.15"/>
          <path d="M80 146 C80 120 80 90 80 62" fill="none" stroke="var(--color-healthy-text)" strokeWidth="5" strokeLinecap="round"/>
          <path d="M80 124 C62 108 40 98 14 100 C40 110 62 122 80 132 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 120 C98 104 120 94 146 96 C120 106 98 118 80 128 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 98 C64 80 46 70 26 70 C46 80 64 94 80 106 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M80 92 C96 74 114 64 134 62 C114 74 96 88 80 100 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
          <path d="M77 74 C74 54 76 30 84 10 C88 32 86 56 83 74 Z" fill="var(--color-healthy-text)"/>
          <ellipse cx="48" cy="108" rx="4.5" ry="3" transform="rotate(-10 48 108)" fill="var(--color-warning-text)"/>
          <ellipse cx="58" cy="114" rx="4.5" ry="3" transform="rotate(10 58 114)" fill="var(--color-warning-text)"/>
          <ellipse cx="38" cy="104" rx="4.5" ry="3" transform="rotate(0 38 104)" fill="var(--color-warning-text)"/>
          <ellipse cx="108" cy="102" rx="4.5" ry="3" transform="rotate(10 108 102)" fill="var(--color-warning-text)"/>
          <ellipse cx="120" cy="98" rx="4.5" ry="3" transform="rotate(-10 120 98)" fill="var(--color-warning-text)"/>
          <ellipse cx="98" cy="108" rx="4.5" ry="3" transform="rotate(0 98 108)" fill="var(--color-warning-text)"/>
          <ellipse cx="52" cy="80" rx="4.5" ry="3" transform="rotate(-15 52 80)" fill="var(--color-warning-text)"/>
          <ellipse cx="62" cy="86" rx="4.5" ry="3" transform="rotate(0 62 86)" fill="var(--color-warning-text)"/>
          <ellipse cx="104" cy="74" rx="4.5" ry="3" transform="rotate(10 104 74)" fill="var(--color-warning-text)"/>
          <ellipse cx="116" cy="68" rx="4.5" ry="3" transform="rotate(0 116 68)" fill="var(--color-warning-text)"/>
    </>
  ),
  seedling: (
    <>
          <g transform="translate(20 28)">
            <ellipse cx="60" cy="104" rx="35" ry="7" fill="var(--color-neutral-text)" opacity="0.15"/>
            <path d="M58 100 C55 74 40 54 14 50 C38 64 52 82 63 100 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
            <path d="M62 100 C65 72 80 52 106 46 C82 62 68 82 57 100 Z" fill="var(--color-healthy-text)" opacity="0.85"/>
            <path d="M59 100 C56 76 57 52 62 22 C67 52 66 78 63 100 Z" fill="var(--color-healthy-text)"/>
          </g>
    </>
  ),
}

export default function MaizePlant({ variant = 'healthy', className = '' }) {
  return (
    <svg viewBox="0 0 160 160" aria-hidden="true" focusable="false" className={className}>
      {SHAPES[variant] ?? SHAPES.healthy}
    </svg>
  )
}

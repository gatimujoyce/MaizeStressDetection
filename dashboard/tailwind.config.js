/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx}'],
    theme: {
        extend: {
            colors: {
                brand: {
                    DEFAULT: 'var(--color-brand)',
                    hover: 'var(--color-brand-hover)',
                },
                surface: 'var(--color-surface)',
                'app-bg': 'var(--color-bg)',
                border: 'var(--color-border)',
                healthy: {
                    bg: 'var(--color-healthy-bg)',
                    text: 'var(--color-healthy-text)',
                },
                warning: {
                    bg: 'var(--color-warning-bg)',
                    text: 'var(--color-warning-text)',
                },
                critical: {
                    bg: 'var(--color-critical-bg)',
                    text: 'var(--color-critical-text)',
                },
                neutral: {
                    bg: 'var(--color-neutral-bg)',
                    text: 'var(--color-neutral-text)',
                },
                positive: {
                    bg: 'var(--color-positive-bg)',
                    text: 'var(--color-positive-text)',
                },
                ink: {
                    DEFAULT: 'var(--color-text-primary)',
                    secondary: 'var(--color-text-secondary)',
                    muted: 'var(--color-text-muted)',
                },
                'brand-tint': 'var(--color-primary-tint)',
                control: 'var(--color-control-border)',
                focus: 'var(--color-focus)',
            },
            fontFamily: {
                sans: [
                    '"Atkinson Hyperlegible"',
                    'system-ui',
                    '-apple-system',
                    '"Segoe UI"',
                    'Roboto',
                    'Helvetica',
                    'Arial',
                    'sans-serif',
                ],
            },
            // Two shapes only: containers (cards, dialogs, menus) and controls (buttons, fields, segments). Badges are pills.
            borderRadius: {
                control: 'var(--radius-control)',
                card: 'var(--radius-card)',
            },
            // One type scale for both audiences, and two weights (400 and 700).
            //   page     the page title (h1)
            //   section  a section title (h2)
            //   body     reading text, labels, and titles inside a section (with font-bold)
            //   small    secondary lines, table cells, helper text. Farmer screens never go below this.
            //   caption  table headers, axis labels, dense admin metadata
            //   figure   a headline number (a reading, a count)
            fontSize: {
                page: ['26px', { lineHeight: '1.25', fontWeight: '700' }],
                section: ['19px', { lineHeight: '1.35', fontWeight: '700' }],
                body: ['17px', { lineHeight: '1.5' }],
                small: ['15px', { lineHeight: '1.45' }],
                caption: ['13px', { lineHeight: '1.4' }],
                figure: ['28px', { lineHeight: '1.1', fontWeight: '700' }],
            },
            // Spacing steps used on every screen: 1 (4px), 2 (8px), 3 (12px), 4 (16px), 6 (24px), 8 (32px), 12 (48px).
            // The named steps below are the page rhythm; use them instead of picking numbers per screen.
            spacing: {
                gutter: '16px', // page side padding on phones
                stack: '32px', // between sections on a page
            },
            minWidth: {
                table: '45rem', // wide admin tables scroll inside their box below this width
            },
            maxWidth: {
                farmer: '48rem', // 768px: one readable column on every farmer screen
                admin: '80rem', // 1280px
            },
            boxShadow: {
                raised: 'var(--shadow-raised)',
            },
            transitionDuration: {
                fast: 'var(--duration-fast)',
                base: 'var(--duration-base)',
            },
            transitionTimingFunction: {
                out: 'var(--ease-out)',
            },
        },
    },
    plugins: [],
}

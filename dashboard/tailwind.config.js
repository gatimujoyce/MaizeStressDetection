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
            borderRadius: {
                DEFAULT: '2px',
                sm: '2px',
                md: '4px',
                control: 'var(--radius-control)',
                card: 'var(--radius-card)',
            },
            // One type scale for both audiences. Farmer screens use body (17px) and never go below small (15px).
            fontSize: {
                display: ['28px', { lineHeight: '1.2', fontWeight: '700' }],
                title: ['21px', { lineHeight: '1.3', fontWeight: '700' }],
                heading: ['17px', { lineHeight: '1.4', fontWeight: '700' }],
                body: ['17px', { lineHeight: '1.5' }],
                small: ['15px', { lineHeight: '1.45' }],
                caption: ['13px', { lineHeight: '1.4' }],
                stat: ['32px', { lineHeight: '1.1', fontWeight: '700' }],
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

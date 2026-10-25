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
            },
        },
    },
    plugins: [],
}

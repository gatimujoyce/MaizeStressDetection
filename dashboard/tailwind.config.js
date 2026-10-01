/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx}'],
    theme: {
        extend: {
            colors: {
                brand: {
                    DEFAULT: '#A84323',
                    hover: '#8A351B',
                },
                surface: '#FFFFFF',
                'app-bg': '#FAF8F5',
                border: '#DCD8D0',
                healthy: {
                    bg: '#E8F3E8',
                    text: '#1E5B1E',
                },
                warning: {
                    bg: '#FAF0D9',
                    text: '#7A4D00',
                },
                critical: {
                    bg: '#FBE8E6',
                    text: '#96281B',
                },
                neutral: {
                    bg: '#F2F0EB',
                    text: '#4A4844',
                },
            },
            fontFamily: {
                sans: [
                    '-apple-system',
                    'BlinkMacSystemFont',
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

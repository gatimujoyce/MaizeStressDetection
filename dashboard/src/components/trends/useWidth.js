import { useEffect, useRef, useState } from 'react'

// The pixel width of an element, kept up to date, so charts can draw at their real size.
export default function useWidth() {
    const ref = useRef(null)
    const [width, setWidth] = useState(0)
    useEffect(() => {
        const el = ref.current
        if (!el || typeof ResizeObserver === 'undefined') return undefined
        const observer = new ResizeObserver(() => setWidth(el.clientWidth))
        observer.observe(el)
        return () => observer.disconnect()
    }, [])
    return [ref, width]
}
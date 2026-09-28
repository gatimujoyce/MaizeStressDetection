// Fetch wrapper — reads VITE_API_BASE_URL from env, attaches JWT Bearer header.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function getToken() {
    return localStorage.getItem('msm_token')
}

async function request(path, options = {}) {
    const token = getToken()
    const headers = {
        ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
    }

    const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

    if (!res.ok) {
        let message = `HTTP ${res.status}`
        try {
            const data = await res.json()
            message = data.detail || data.message || message
        } catch {
            // response body not JSON — keep the status code message
        }
        throw new Error(message)
    }

    // 204 No Content — nothing to parse
    if (res.status === 204) return null
    return res.json()
}

export const httpClient = {
    get: (path) => request(path),
    post: (path, body) =>
        request(path, {
            method: 'POST',
            body: body instanceof FormData ? body : JSON.stringify(body),
        }),
    patch: (path, body) =>
        request(path, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (path) => request(path, { method: 'DELETE' }),
}

// Fetch wrapper — reads VITE_API_BASE_URL from env, attaches JWT Bearer header.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

function getToken() {
    return localStorage.getItem('msm_token')
}

async function request(path, options = {}) {
    const token = getToken()
    const isFormData = options.body instanceof FormData
    const isUrlEncoded = options.body instanceof URLSearchParams
    const headers = {
        ...(!isFormData && !isUrlEncoded ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
    }

    const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

    if (!res.ok) {
        let data
        try {
            data = await res.json()
        } catch {
            // Use the status code below when the response body is not JSON.
        }

        const detail = data?.detail ?? data?.message
        const message = typeof detail === 'string'
            ? detail
            : Array.isArray(detail)
                ? detail.map((item) => item?.msg || item?.message || item).join('; ')
                : detail
                    ? JSON.stringify(detail)
                    : `Request failed (HTTP ${res.status})`
        const error = new Error(message)
        error.status = res.status
        throw error
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
            body: body instanceof FormData || body instanceof URLSearchParams
                ? body
                : JSON.stringify(body),
        }),
    patch: (path, body) =>
        request(path, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: (path) => request(path, { method: 'DELETE' }),
}

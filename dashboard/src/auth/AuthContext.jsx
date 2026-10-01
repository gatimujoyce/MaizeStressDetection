import { createContext, useContext, useState, useEffect } from 'react'
import { jwtDecode } from 'jwt-decode'

const AuthContext = createContext(null)

function decodeToken(token) {
  try {
    return jwtDecode(token)
  } catch {
    return null
  }
}

function isExpired(decoded) {
  if (!decoded?.exp) return true
  return decoded.exp < Date.now() / 1000
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('msm_token'))
  const [claims, setClaims] = useState(() => {
    const t = localStorage.getItem('msm_token')
    if (!t) return null
    const decoded = decodeToken(t)
    if (!decoded || isExpired(decoded)) {
      localStorage.removeItem('msm_token')
      return null
    }
    return decoded
  })

  const login = (newToken) => {
    const decoded = decodeToken(newToken)
    if (!decoded || isExpired(decoded)) return
    localStorage.setItem('msm_token', newToken)
    setToken(newToken)
    setClaims(decoded)
  }

  const logout = () => {
    localStorage.removeItem('msm_token')
    setToken(null)
    setClaims(null)
  }

  // Handle token expiry while tab is open
  useEffect(() => {
    if (!claims?.exp) return
    const msUntilExpiry = claims.exp * 1000 - Date.now()
    if (msUntilExpiry <= 0) { logout(); return }
    const timer = setTimeout(logout, msUntilExpiry)
    return () => clearTimeout(timer)
  }, [claims])

  return (
    <AuthContext.Provider
      value={{
        token,
        role: claims?.role ?? null,
        userId: claims?.sub ?? null,
        farmId: claims?.farm_id ?? null,
        isAuthenticated: !!claims && !isExpired(claims),
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
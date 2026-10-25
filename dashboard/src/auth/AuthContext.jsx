import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'
import { jwtDecode } from 'jwt-decode'
import * as client from '../api/client'

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
  const [profile, setProfile] = useState(null)
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
  const profileRequests = useRef(new Map())

  const logout = useCallback(() => {
    localStorage.removeItem('msm_token')
    setToken(null)
    setClaims(null)
    setProfile(null)
  }, [])

  const loadProfile = useCallback((accessToken) => {
    const pendingRequest = profileRequests.current.get(accessToken)
    if (pendingRequest) return pendingRequest

    const request = client.getCurrentUser()
      .then((userProfile) => {
        if (localStorage.getItem('msm_token') === accessToken) {
          setProfile(userProfile)
        }
        return userProfile
      })
      .catch((error) => {
        if (error.status === 401 && localStorage.getItem('msm_token') === accessToken) {
          logout()
        }
        throw error
      })
      .finally(() => profileRequests.current.delete(accessToken))

    profileRequests.current.set(accessToken, request)
    return request
  }, [logout])

  const login = useCallback((newToken) => {
    const decoded = decodeToken(newToken)
    if (!decoded || isExpired(decoded)) return Promise.resolve(null)
    localStorage.setItem('msm_token', newToken)
    setToken(newToken)
    setClaims(decoded)
    setProfile(null)
    return loadProfile(newToken)
  }, [loadProfile])

  useEffect(() => {
    if (!token || !claims || isExpired(claims)) return
    loadProfile(token).catch((error) => {
      if (error.status !== 401) {
        console.error('Unable to load the current user profile', error)
      }
    })
  }, [token, claims, loadProfile])

  // Handle token expiry while tab is open
  useEffect(() => {
    if (!claims?.exp) return
    const msUntilExpiry = claims.exp * 1000 - Date.now()
    if (msUntilExpiry <= 0) { logout(); return }
    const timer = setTimeout(logout, msUntilExpiry)
    return () => clearTimeout(timer)
  }, [claims, logout])

  return (
    <AuthContext.Provider
      value={{
        token,
        profile,
        role: profile?.role ?? null,
        userId: profile?.id ?? claims?.sub ?? null,
        name: profile?.name ?? null,
        phone: profile?.phone ?? null,
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
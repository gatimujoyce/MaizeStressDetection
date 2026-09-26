import React from 'react'
import ReactDOM from 'react-dom/client'
import AppRouter from './router'
import { AuthProvider } from './auth/AuthContext'
import './styles/global.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AuthProvider>
      <AppRouter />
    </AuthProvider>
  </React.StrictMode>
)
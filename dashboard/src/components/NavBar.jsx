import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function NavBar() {
  const { role, setRole } = useAuth()

  const toggleRole = () => {
    setRole(prev => (prev === 'farmer' ? 'admin' : 'farmer'))
  }

  return (
    <nav style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center', 
      padding: '1rem 2rem', 
      backgroundColor: '#2e7d32', 
      color: '#fff' 
    }}>
      <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
        <strong style={{ fontSize: '1.2rem' }}>MaizeMonitor</strong>
        {role === 'farmer' && <Link to="/" style={{ color: '#fff' }}>Farmer Dashboard</Link>}
        {role === 'admin' && <Link to="/admin" style={{ color: '#fff' }}>Admin Dashboard</Link>}
      </div>
      <div>
        <button 
          onClick={toggleRole} 
          style={{ 
            padding: '0.5rem 1rem', 
            cursor: 'pointer', 
            backgroundColor: '#fff', 
            color: '#2e7d32', 
            border: 'none', 
            borderRadius: '4px',
            fontWeight: 'bold'
          }}
        >
          Dev Switch: Logged in as [{role.toUpperCase()}]
        </button>
      </div>
    </nav>
  )
}
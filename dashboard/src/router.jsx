import { BrowserRouter, Routes, Route } from 'react-router-dom'
import FarmerDashboard from './views/farmer/FarmerDashboard'
import AdminDashboard from './views/admin/AdminDashboard'
import RoleGuard from './components/RoleGuard'
import Layout from './components/Layout'

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route 
            path="/" 
            element={
              <RoleGuard allowedRole="farmer">
                <FarmerDashboard />
              </RoleGuard>
            } 
          />
          <Route 
            path="/admin" 
            element={
              <RoleGuard allowedRole="admin">
                <AdminDashboard />
              </RoleGuard>
            } 
          />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
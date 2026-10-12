import { BrowserRouter, Routes, Route } from 'react-router-dom'
import FarmerDashboard from './views/farmer/FarmerDashboard'
import AdminDashboard from './views/admin/AdminDashboard'
import AlertsPage from './views/farmer/AlertsPage'
import AddPlot from './views/farmer/AddPlot'
import NewCheckin from './views/farmer/NewCheckin'
import Onboarding from './views/farmer/Onboarding'
import Result from './views/farmer/Result'
import TrendsPage from './views/farmer/TrendsPage'
import Login from './views/auth/Login'
import Register from './views/auth/Register'
import RoleGuard from './components/RoleGuard'
import Layout from './components/Layout'

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <RoleGuard allowedRole="farmer">
                <FarmerDashboard />
              </RoleGuard>
            }
          />
          <Route
            path="/onboarding"
            element={
              <RoleGuard allowedRole="farmer">
                <Onboarding />
              </RoleGuard>
            }
          />
          <Route
            path="/plots/new"
            element={
              <RoleGuard allowedRole="farmer">
                <AddPlot />
              </RoleGuard>
            }
          />
          <Route
            path="/check-in"
            element={
              <RoleGuard allowedRole="farmer">
                <NewCheckin />
              </RoleGuard>
            }
          />
          <Route
            path="/trends"
            element={
              <RoleGuard allowedRole="farmer">
                <TrendsPage />
              </RoleGuard>
            }
          />
          <Route
            path="/alerts"
            element={
              <RoleGuard allowedRole="farmer">
                <AlertsPage />
              </RoleGuard>
            }
          />
          <Route
            path="/result/:predictionId"
            element={
              <RoleGuard allowedRole="farmer">
                <Result />
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
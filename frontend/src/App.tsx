import { Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './hooks/useTheme'
import { AuthProvider } from './hooks/useAuth'
import { WebSocketProvider } from './hooks/useWebSocketContext'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import Agents from './pages/Agents'
import Approvals from './pages/Approvals'
import Events from './pages/Events'
import Hierarchy from './pages/Hierarchy'
import Login from './pages/Login'
import ProviderConfig from './pages/ProviderConfig'
import Onboarding from './pages/Onboarding'
import Settings from './pages/Settings'
import AuditLog from './pages/AuditLog'
import DashboardBuilder from './pages/DashboardBuilder'

import CustomerService from './pages/CustomerService'

import Webhooks from './pages/Webhooks'

import Billing from './pages/Billing'

import Admin from './pages/Admin'

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <WebSocketProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route element={<Layout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/tasks" element={<Tasks />} />
              <Route path="/agents" element={<Agents />} />
              <Route path="/approvals" element={<Approvals />} />
              <Route path="/events" element={<Events />} />
              <Route path="/customer-service" element={<CustomerService />} />
              <Route path="/hierarchy" element={<Hierarchy />} />
              <Route path="/providers" element={<ProviderConfig />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/audit" element={<AuditLog />} />
              <Route path="/dashboard-builder" element={<DashboardBuilder />} />
              <Route path="/webhooks" element={<Webhooks />} />
              <Route path="/billing" element={<Billing />} />
              <Route path="/admin" element={<Admin />} />
            </Route>
          </Routes>
        </WebSocketProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App

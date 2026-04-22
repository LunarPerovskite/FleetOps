import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Tasks from './pages/Tasks'
import Agents from './pages/Agents'
import Approvals from './pages/Approvals'
import Events from './pages/Events'
import Hierarchy from './pages/Hierarchy'
import Login from './pages/Login'
import ProviderConfig from './pages/ProviderConfig'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/agents" element={<Agents />} />
        <Route path="/approvals" element={<Approvals />} />
        <Route path="/events" element={<Events />} />
        <Route path="/hierarchy" element={<Hierarchy />} />
        <Route path="/providers" element={<ProviderConfig />} />
      </Route>
    </Routes>
  )
}

export default App

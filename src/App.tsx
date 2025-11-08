import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import PatientManager from './pages/PatientManager'
import CallQueue from './pages/CallQueue'
import Analytics from './pages/Analytics'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/patients" element={<PatientManager />} />
          <Route path="/calls" element={<CallQueue />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App


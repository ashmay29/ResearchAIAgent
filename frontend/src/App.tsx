import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import AnalysisResult from './pages/AnalysisResult'
import History from './pages/History'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Signup from './pages/Signup'

function App() {
  return (
    <div className="min-h-screen text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-900">
      <Navbar />
      <main className="max-w-5xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analysis/:jobId" element={<AnalysisResult />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default App

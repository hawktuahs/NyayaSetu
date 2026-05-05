import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Navbar from './components/Navbar'
import Upload from './pages/Upload'
import CasesList from './pages/CasesList'
import CaseDetail from './pages/CaseDetail'
import VerifyQueue from './pages/VerifyQueue'
import Verify from './pages/Verify'
import Dashboard from './pages/Dashboard'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Navbar />
        <main className="page-content">
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/cases" element={<CasesList />} />
            <Route path="/cases/:id" element={<CaseDetail />} />
            <Route path="/verify" element={<VerifyQueue />} />
            <Route path="/verify/:id" element={<Verify />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#0F1F38',
            color: '#F0F4F8',
            border: '1px solid rgba(255,255,255,0.08)',
            fontFamily: 'Inter, sans-serif',
            fontSize: '14px',
          },
          success: {
            iconTheme: { primary: '#4CAF50', secondary: '#0F1F38' },
          },
          error: {
            iconTheme: { primary: '#EF5350', secondary: '#0F1F38' },
          },
        }}
      />
    </BrowserRouter>
  )
}

import { Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import AlertesPage from './pages/AlertesPage'
import DashboardPage from './pages/DashboardPage'
import FineTuningPage from './pages/FineTuningPage'
import LoginPage from './pages/LoginPage'
import ComposantsPage from './pages/ComposantsPage'
import SurveillancePage from './pages/SurveillancePage'
import UtilisateursPage from './pages/UtilisateursPage'

function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/surveillance" element={<SurveillancePage />} />
          <Route
            path="/alertes"
            element={
              <RequireAuth roles={['admin', 'superviseur', 'technicien']}>
                <AlertesPage />
              </RequireAuth>
            }
          />
          <Route
            path="/fine-tuning"
            element={
              <RequireAuth roles={['admin']}>
                <FineTuningPage />
              </RequireAuth>
            }
          />
          <Route
            path="/composants"
            element={
              <RequireAuth roles={['admin']}>
                <ComposantsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/utilisateurs"
            element={
              <RequireAuth roles={['admin']}>
                <UtilisateursPage />
              </RequireAuth>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <Toaster position="top-right" />
    </>
  )
}

export default App

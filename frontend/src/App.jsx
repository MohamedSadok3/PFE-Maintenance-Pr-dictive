import { Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import RequireAuth from './components/RequireAuth'
import AlertesPage from './pages/AlertesPage'
import AlertDetailPage from './pages/AlertDetailPage'
import DashboardPage from './pages/DashboardPage'
import FineTuningPage from './pages/FineTuningPage'
import LoginPage from './pages/LoginPage'
import PlantRegistrationPage from './pages/PlantRegistrationPage'
import PlantProfilePage from './pages/PlantProfilePage'
import ComposantsPage from './pages/ComposantsPage'
import SurveillancePage from './pages/SurveillancePage'
import SuperAdminPlantsPage from './pages/SuperAdminPlantsPage'
import SuperAdminRegistrationsPage from './pages/SuperAdminRegistrationsPage'
import UtilisateursPage from './pages/UtilisateursPage'

function App() {
  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/inscription-usine" element={<PlantRegistrationPage />} />
        <Route path="/alerte/*" element={<Navigate to="/alertes" replace />} />

        <Route
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
          }
        >
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route
            path="/usine/profil"
            element={
              <RequireAuth roles={['admin']}>
                <PlantProfilePage />
              </RequireAuth>
            }
          />
          <Route
            path="/superadmin/usines"
            element={
              <RequireAuth roles={['superadmin']}>
                <SuperAdminPlantsPage />
              </RequireAuth>
            }
          />
          <Route
            path="/superadmin/inscriptions"
            element={
              <RequireAuth roles={['superadmin']}>
                <SuperAdminRegistrationsPage />
              </RequireAuth>
            }
          />
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
            path="/alertes/:alertId"
            element={
              <RequireAuth roles={['admin', 'superviseur', 'technicien']}>
                <AlertDetailPage />
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

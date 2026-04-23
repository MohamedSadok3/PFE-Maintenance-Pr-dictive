import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import { logout } from '../services/authService'
import { getAlertes } from '../services/alerteService'
import { getStoredUser } from '../utils/storage'

const navItems = [
  { label: 'Dashboard', path: '/dashboard', roles: ['admin', 'superviseur', 'technicien'] },
  { label: 'Live Monitoring', path: '/surveillance', roles: ['admin', 'superviseur', 'technicien'] },
  { label: 'Alerts', path: '/alertes', roles: ['admin', 'superviseur', 'technicien'] },
  { label: 'Fine-Tuning', path: '/fine-tuning', roles: ['admin'] },
  { label: 'Composants', path: '/composants', roles: ['admin'] },
  { label: 'User Management', path: '/utilisateurs', roles: ['admin'] },
  { label: 'Profil Usine', path: '/usine/profil', roles: ['admin'] },
  { label: 'Profils Usines', path: '/superadmin/usines', roles: ['superadmin'] },
  { label: 'Validation Usines', path: '/superadmin/inscriptions', roles: ['superadmin'] },
]

const titles = {
  '/dashboard': 'Dashboard',
  '/surveillance': 'Surveillance',
  '/alertes': 'Alertes',
  '/fine-tuning': 'Fine-Tuning',
  '/composants': 'Composants',
  '/utilisateurs': 'Utilisateurs',
  '/usine/profil': 'Profil Usine',
  '/superadmin/usines': 'Profils Usines',
  '/superadmin/inscriptions': 'Validation Usines',
}

function Layout() {
  const location = useLocation()
  const navigate = useNavigate()

  const pageTitle = useMemo(() => {
    if (titles[location.pathname]) return titles[location.pathname]
    if (location.pathname.startsWith('/alertes/')) return 'Detail alerte'
    return 'SmartMaintain'
  }, [location.pathname])

  const user = useMemo(() => getStoredUser() || { name: 'Utilisateur', role: 'technicien' }, [])
  const userMachineKey = useMemo(
    () => (Array.isArray(user?.machines) ? user.machines.join('|') : ''),
    [user?.machines],
  )
  const [hasNewAlerts, setHasNewAlerts] = useState(localStorage.getItem('hasNewAlerts') === 'true')
  const [notifications, setNotifications] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)
  const bellRef = useRef(null)

  const canOpenAlerts = useMemo(
    () => ['admin', 'superviseur', 'technicien'].includes(user.role),
    [user.role],
  )

  const buildNotification = (alert) => {
    if (!alert) return null
    const isManager = user.role === 'admin' || user.role === 'superviseur'
    const isTechnicien = user.role === 'technicien'

    if (isManager) {
      if (!alert.assigned_to && (alert.status === 'open' || alert.status === 'reopened')) {
        return {
          key: `${alert.id}-unassigned`,
          alertId: alert.id,
          title: 'Nouvelle alerte non assignee',
          subtitle: `${alert.machine || 'Machine'} - ${alert.defect || 'Defaut detecte'}`,
        }
      }

      if (alert.acknowledged && alert.status === 'acknowledged') {
        return {
          key: `${alert.id}-validation`,
          alertId: alert.id,
          title: 'Alerte acquittee a valider',
          subtitle: `${alert.machine || 'Machine'} - ${alert.defect || 'Validation requise'}`,
        }
      }
    }

    if (isTechnicien && alert.assigned_to === user.id && !alert.acknowledged) {
      return {
        key: `${alert.id}-assigned`,
        alertId: alert.id,
        title: 'Nouvelle alerte assignee',
        subtitle: `${alert.machine || 'Machine'} - ${alert.defect || 'Intervention demandee'}`,
      }
    }

    return null
  }

  const syncHasAlerts = (items) => {
    const hasItems = items.length > 0
    localStorage.setItem('hasNewAlerts', hasItems ? 'true' : 'false')
    setHasNewAlerts(hasItems)
  }

  const upsertNotification = (alert) => {
    const candidate = buildNotification(alert)
    setNotifications((prev) => {
      const withoutAlert = prev.filter((item) => item.alertId !== alert.id)
      if (!candidate) {
        syncHasAlerts(withoutAlert)
        return withoutAlert
      }
      const updated = [candidate, ...withoutAlert].slice(0, 8)
      syncHasAlerts(updated)
      return updated
    })
  }

  useEffect(() => {
    let cancelled = false
    const loadNotifications = async () => {
      try {
        const response = await getAlertes({ page: 1, limit: 50 })
        const alerts = response.data?.alerts || []
        const items = alerts.map(buildNotification).filter(Boolean).slice(0, 8)
        if (!cancelled) {
          setNotifications(items)
          syncHasAlerts(items)
        }
      } catch {
        // Silent fallback: realtime socket updates keep notifications fresh.
      }
    }

    loadNotifications()
    const timer = window.setInterval(loadNotifications, 30000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [user.id, user.role])

  useEffect(() => {
    const hasMachineAccess = (machine) => (user.machines || []).includes(machine)
    const isRelevantAlert = (alert) => {
      if (!alert) return false
      if (user.role === 'admin' || user.role === 'superviseur') {
        return (
          (!alert.assigned_to && (alert.status === 'open' || alert.status === 'reopened')) ||
          (alert.acknowledged && alert.status === 'acknowledged')
        )
      }
      if (user.role === 'technicien') {
        return alert.assigned_to === user.id || hasMachineAccess(alert.machine)
      }
      return false
    }

    const socket = io('http://localhost:5000', { transports: ['websocket', 'polling'] })
    socket.on('alert:new', (alert) => {
      if (isRelevantAlert(alert)) {
        upsertNotification(alert)
      }
    })

    socket.on('alert:updated', (alert) => {
      upsertNotification(alert)
    })

    return () => socket.disconnect()
  }, [user.id, user.role, userMachineKey])

  useEffect(() => {
    const onDocumentClick = (event) => {
      if (!bellRef.current?.contains(event.target)) {
        setShowNotifications(false)
      }
    }
    document.addEventListener('click', onDocumentClick)
    return () => document.removeEventListener('click', onDocumentClick)
  }, [])

  const onBellClick = (event) => {
    event.preventDefault()
    event.stopPropagation()
    setShowNotifications((prev) => !prev)
  }

  const openAlertDetails = (alertId) => {
    setShowNotifications(false)
    if (canOpenAlerts) {
      navigate(`/alertes/${alertId}`)
    }
  }

  const clearNotifications = () => {
    setNotifications([])
    syncHasAlerts([])
    setShowNotifications(false)
  }

  return (
    <div className="h-screen flex">
      <aside className="w-[240px] bg-[#0f172a] text-slate-100 flex flex-col">
        <div className="px-5 py-6 border-b border-slate-700 space-y-1">
          <h1 className="text-xl font-semibold text-[#16a34a]">SmartMaintain</h1>
          <p className="text-xs text-slate-400">Industrial AI Suite</p>
        </div>

        <nav className="p-4 flex-1 space-y-2">
          {navItems.map((item) => {
            const canAccess = item.roles.includes(user.role)
            if (!canAccess) return null

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `block rounded-lg px-4 py-2.5 transition ${
                    isActive
                      ? 'bg-[#16a34a] text-white shadow'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800'
                  }`
                }
              >
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        <div className="p-4 border-t border-slate-700">
          <p className="text-sm font-medium">{user.name}</p>
          <span className="mt-2 inline-block text-xs bg-slate-800 text-slate-200 rounded-full px-2 py-1">
            {user.role}
          </span>
          <button
            type="button"
            onClick={logout}
            className="mt-3 w-full rounded-md bg-slate-800 px-3 py-2 text-xs text-slate-200 hover:bg-slate-700"
          >
            Deconnexion
          </button>
        </div>
      </aside>

      <div className="flex-1 min-h-screen bg-[#e2e8f0]">
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-800">{pageTitle}</h2>
          <div className="relative" ref={bellRef}>
            <button
              type="button"
              onClick={onBellClick}
              className="relative rounded-full p-2 text-slate-600 hover:bg-slate-100"
              aria-label="Notifications"
            >
              <span className="text-lg">🔔</span>
              {hasNewAlerts && <span className="absolute right-1 top-1 h-2.5 w-2.5 rounded-full bg-red-500" />}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 rounded-xl border border-slate-200 bg-white shadow-xl z-50">
                <div className="flex items-center justify-between px-3 py-2 border-b border-slate-100">
                  <p className="text-sm font-semibold text-slate-700">Notifications</p>
                  <button
                    type="button"
                    onClick={clearNotifications}
                    className="text-xs text-slate-500 hover:text-slate-700"
                  >
                    Marquer lu
                  </button>
                </div>

                <div className="max-h-72 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="px-3 py-4 text-sm text-slate-500">Aucune nouvelle notification.</p>
                  ) : (
                    notifications.map((item) => (
                      <button
                        type="button"
                        key={item.key}
                        onClick={() => openAlertDetails(item.alertId)}
                        className="w-full text-left px-3 py-2 border-b border-slate-100 hover:bg-slate-50"
                      >
                        <p className="text-sm font-medium text-slate-800">{item.title}</p>
                        <p className="text-xs text-slate-500">{item.subtitle}</p>
                      </button>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </header>

        <main className="h-[calc(100vh-64px)] overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout

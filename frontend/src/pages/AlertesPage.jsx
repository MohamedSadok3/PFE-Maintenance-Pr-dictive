import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { io } from 'socket.io-client'
import toast from 'react-hot-toast'
import api from '../services/api'
import { getUser } from '../services/authService'
import {
  acknowledgeAlert,
  assignAlert,
  getAlertes,
  reopenAlert,
  resolveAlert,
} from '../services/alerteService'

const LIMIT = 20

function severityBadgeClass(severity) {
  if (severity === 'Critique') return 'bg-red-100 text-red-700'
  if (severity === 'Majeure') return 'bg-amber-100 text-amber-700'
  return 'bg-green-100 text-green-700'
}

function timeAgo(inputDate) {
  if (!inputDate) return '-'
  const diffMs = Date.now() - new Date(inputDate).getTime()
  const mins = Math.max(1, Math.floor(diffMs / 60000))
  if (mins < 60) return `${mins} min ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} h ago`
  const days = Math.floor(hours / 24)
  return `${days} d ago`
}

function AlertesPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const currentUser = getUser()
  const isManager = currentUser?.role === 'admin' || currentUser?.role === 'superviseur'
  const isTechnicien = currentUser?.role === 'technicien'

  const [rows, setRows] = useState([])
  const [techniciens, setTechniciens] = useState([])
  const [loading, setLoading] = useState(true)
  const [flashIds, setFlashIds] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [hasNextPage, setHasNextPage] = useState(false)
  const [focusAlertId, setFocusAlertId] = useState(null)
  const [filters, setFilters] = useState({
    machine: '',
    severity: '',
    status: '',
    acknowledged: '',
    technician: '',
    from: '',
    to: '',
  })
  const isValidatedView = filters.status === 'resolved' && filters.acknowledged === 'true'
  const alertIdFromQuery = useMemo(
    () => Number(new URLSearchParams(location.search).get('alertId')) || null,
    [location.search],
  )

  const visibleRows = useMemo(() => {
    let filtered = rows
    if (isTechnicien) {
      filtered = filtered.filter((item) => item.assigned_to === currentUser?.id)
    }
    if (filters.technician) {
      filtered = filtered.filter((item) => String(item.assigned_to || '') === String(filters.technician))
    }
    return filtered
  }, [rows, isTechnicien, currentUser?.id, filters.technician])

  const pageButtons = useMemo(() => {
    const maxPage = hasNextPage ? currentPage + 1 : currentPage
    return Array.from({ length: maxPage }, (_, idx) => idx + 1)
  }, [currentPage, hasNextPage])

  const fetchAlertes = async (page = currentPage) => {
    setLoading(true)
    try {
      const params = {
        page,
        limit: LIMIT,
        machine: filters.machine || undefined,
        severity: filters.severity || undefined,
        status: filters.status || undefined,
        acknowledged: filters.acknowledged || undefined,
        from: filters.from || undefined,
        to: filters.to || undefined,
      }
      const response = await getAlertes(params)
      const alerts = response.data.alerts || []
      setRows(alerts)
      setHasNextPage(alerts.length === LIMIT)
      setCurrentPage(page)
    } catch (error) {
      toast.error(error.response?.data?.error || 'Erreur chargement alertes')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAlertes(1)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.machine,
    filters.severity,
    filters.status,
    filters.acknowledged,
    filters.from,
    filters.to,
    filters.technician,
  ])

  useEffect(() => {
    if (!alertIdFromQuery) return
    setFocusAlertId(alertIdFromQuery)
  }, [alertIdFromQuery])

  useEffect(() => {
    if (!focusAlertId) return
    const target = document.getElementById(`alert-row-${focusAlertId}`)
    if (!target) return
    target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    window.setTimeout(() => setFocusAlertId(null), 3500)
  }, [focusAlertId, visibleRows])

  useEffect(() => {
    if (!isManager) return
    const loadTechniciens = async () => {
      try {
        const response = await api.get('/api/users', { params: { role: 'technicien' } })
        const users = response.data.users || []
        setTechniciens(users.filter((item) => item.role === 'technicien'))
      } catch {
        toast.error('Impossible de charger les techniciens')
      }
    }
    loadTechniciens()
  }, [isManager])

  useEffect(() => {
    const socket = io('http://localhost:5000', { transports: ['websocket', 'polling'] })
    socket.on('alert:new', (incoming) => {
      setRows((prev) => [incoming, ...prev].slice(0, LIMIT))
      setFlashIds((prev) => [...prev, incoming.id])
      window.setTimeout(() => {
        setFlashIds((prev) => prev.filter((id) => id !== incoming.id))
      }, 2000)
    })
    socket.on('alert:updated', (updated) => {
      setRows((prev) => prev.map((item) => (item.id === updated.id ? updated : item)))
    })
    return () => socket.disconnect()
  }, [])

  const onAssign = async (alertId, value) => {
    const parsedValue = value === '' ? null : Number(value)
    try {
      await assignAlert(alertId, parsedValue)
      setRows((prev) =>
        prev.map((item) =>
          item.id === alertId
            ? {
                ...item,
                assigned_to: parsedValue,
                status: parsedValue ? 'assigned' : 'open',
                acknowledged: false,
              }
            : item,
        ),
      )
      toast.success('Alerte assignee')
    } catch (error) {
      toast.error(error.response?.data?.error || "Echec d'assignation")
    }
  }

  const onResolve = async (alertId) => {
    try {
      await resolveAlert(alertId)
      setRows((prev) =>
        prev.map((item) =>
          item.id === alertId ? { ...item, status: 'resolved', acknowledged: true } : item,
        ),
      )
      toast.success('Tache validee et deplacee vers alertes acquittees')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Echec validation')
    }
  }

  const onAcknowledge = async (alertId) => {
    try {
      await acknowledgeAlert(alertId)
      setRows((prev) =>
        prev.map((item) =>
          item.id === alertId ? { ...item, acknowledged: true, status: 'acknowledged' } : item,
        ),
      )
      toast.success('Tache acquittee')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Echec acquittement')
    }
  }

  const onReopen = async (alertId) => {
    try {
      await reopenAlert(alertId)
      setRows((prev) =>
        prev.map((item) =>
          item.id === alertId
            ? {
                ...item,
                status: item.assigned_to ? 'assigned' : 'open',
                acknowledged: false,
                validation_at: null,
                resolved_at: null,
              }
            : item,
        ),
      )
      toast.success('Tache re-ouverte')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Echec re-ouverture')
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setFilters((prev) => ({ ...prev, status: '', acknowledged: 'false' }))}
          className={`rounded px-3 py-1.5 text-xs ${
            !filters.status && filters.acknowledged === 'false'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
          }`}
        >
          Nouvelles alertes
        </button>
        <button
          type="button"
          onClick={() => setFilters((prev) => ({ ...prev, status: 'acknowledged', acknowledged: 'true' }))}
          className={`rounded px-3 py-1.5 text-xs ${
            filters.status === 'acknowledged' && filters.acknowledged === 'true'
              ? 'bg-amber-500 text-white'
              : 'bg-amber-50 text-amber-700 hover:bg-amber-100'
          }`}
        >
          Taches acquittees a valider
        </button>
        <button
          type="button"
          onClick={() => setFilters((prev) => ({ ...prev, status: 'resolved', acknowledged: 'true' }))}
          className={`rounded px-3 py-1.5 text-xs ${
            filters.status === 'resolved' && filters.acknowledged === 'true'
              ? 'bg-[#16a34a] text-white'
              : 'bg-green-50 text-green-700 hover:bg-green-100'
          }`}
        >
          Taches validees
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-7 gap-3">
        <select
          value={filters.machine}
          onChange={(event) => setFilters((prev) => ({ ...prev, machine: event.target.value }))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Toutes machines</option>
          <option value="moteur">Moteur</option>
          <option value="pompe">Pompe</option>
          <option value="compresseur">Compresseur</option>
          <option value="echangeur">Echangeur</option>
        </select>

        <select
          value={filters.severity}
          onChange={(event) => setFilters((prev) => ({ ...prev, severity: event.target.value }))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Toutes severites</option>
          <option value="Critique">Critique</option>
          <option value="Majeure">Majeure</option>
          <option value="Mineure">Mineure</option>
        </select>

        <select
          value={filters.status}
          onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Tous statuts</option>
          <option value="open">Open</option>
          <option value="assigned">Assigned</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>

        <select
          value={filters.acknowledged}
          onChange={(event) => setFilters((prev) => ({ ...prev, acknowledged: event.target.value }))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Acquittement: tous</option>
          <option value="true">Acquittee</option>
          <option value="false">Non acquittee</option>
        </select>

        <select
          value={filters.technician}
          onChange={(event) => setFilters((prev) => ({ ...prev, technician: event.target.value }))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        >
          <option value="">Tous techniciens</option>
          {techniciens.map((user) => (
            <option key={user.id} value={user.id}>
              {user.name}
            </option>
          ))}
        </select>

        <input
          type="date"
          value={filters.from}
          onChange={(event) => setFilters((prev) => ({ ...prev, from: event.target.value }))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <input
          type="date"
          value={filters.to}
          onChange={(event) => setFilters((prev) => ({ ...prev, to: event.target.value }))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      <div className="overflow-auto">
        <table className="w-full min-w-[980px] text-sm">
          <thead>
            <tr className="text-left text-slate-500 border-b border-slate-200">
              <th className="py-2">ID</th>
              <th className="py-2">Machine</th>
              <th className="py-2">Defect</th>
              <th className="py-2">Severity</th>
              <th className="py-2">Time</th>
              <th className="py-2">Status</th>
              {isValidatedView && <th className="py-2">Assignee par</th>}
              <th className="py-2">Assignee au</th>
              {isValidatedView && <th className="py-2">Date validation</th>}
              <th className="py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={isValidatedView ? 10 : 8} className="py-4 text-slate-500">
                  Chargement...
                </td>
              </tr>
            )}
            {!loading && visibleRows.length === 0 && (
              <tr>
                <td colSpan={isValidatedView ? 10 : 8} className="py-4 text-slate-500">
                  Aucune alerte trouvee.
                </td>
              </tr>
            )}
            {!loading &&
              visibleRows.map((row) => (
                <tr
                  key={row.id}
                  id={`alert-row-${row.id}`}
                  onClick={() => navigate(`/alertes/${row.id}`)}
                  className={`border-b border-slate-100 transition-colors duration-[2000ms] ${
                    flashIds.includes(row.id) || focusAlertId === row.id ? 'bg-green-100' : 'bg-white'
                  } cursor-pointer hover:bg-slate-50`}
                >
                  <td className="py-2">{row.id}</td>
                  <td className="py-2 capitalize">{row.machine}</td>
                  <td className="py-2">{row.defect}</td>
                  <td className="py-2">
                    <span className={`rounded-full px-2 py-1 text-xs ${severityBadgeClass(row.severity)}`}>
                      {row.severity}
                    </span>
                  </td>
                  <td className="py-2 text-slate-600">{timeAgo(row.created_at)}</td>
                  <td className="py-2">{row.status}</td>
                  {isValidatedView && <td className="py-2">{row.assigned_by_name || '-'}</td>}
                  <td className="py-2" onClick={(event) => event.stopPropagation()}>
                    {isManager ? (
                      <select
                        value={row.assigned_to || ''}
                        onChange={(event) => onAssign(row.id, event.target.value)}
                        className="rounded border border-slate-300 px-2 py-1"
                        onClick={(event) => event.stopPropagation()}
                      >
                        <option value="">Non assigne</option>
                        {techniciens.map((user) => (
                          <option key={user.id} value={user.id}>
                            {user.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <span>{row.assigned_to_name || row.assigned_to || '-'}</span>
                    )}
                  </td>
                  {isValidatedView && (
                    <td className="py-2 text-slate-600">
                      {row.validation_at ? new Date(row.validation_at).toLocaleString() : '-'}
                    </td>
                  )}
                  <td className="py-2 space-x-2" onClick={(event) => event.stopPropagation()}>
                    {isManager && !isValidatedView && (
                      <button
                        type="button"
                        onClick={() => onResolve(row.id)}
                        disabled={!row.acknowledged}
                        className="rounded bg-slate-800 px-3 py-1 text-xs text-white hover:bg-slate-700"
                      >
                        Valider acquittement
                      </button>
                    )}
                    {isManager && isValidatedView && (
                      <button
                        type="button"
                        onClick={() => onReopen(row.id)}
                        className="rounded bg-amber-600 px-3 py-1 text-xs text-white hover:bg-amber-500"
                      >
                        Re-open
                      </button>
                    )}
                    {isTechnicien && (
                      <button
                        type="button"
                        onClick={() => onAcknowledge(row.id)}
                        className="rounded bg-[#16a34a] px-3 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-60"
                        disabled={row.acknowledged || row.assigned_to !== currentUser?.id}
                      >
                        {row.acknowledged ? 'Acquittee' : 'Acquitter'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-2">
        {pageButtons.map((pageNumber) => (
          <button
            type="button"
            key={pageNumber}
            onClick={() => fetchAlertes(pageNumber)}
            className={`h-8 min-w-8 rounded px-2 text-sm ${
              currentPage === pageNumber
                ? 'bg-[#16a34a] text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
            }`}
          >
            {pageNumber}
          </button>
        ))}
      </div>
    </section>
  )
}

export default AlertesPage

import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { getAlerteById } from '../services/alerteService'

function severityStyles(severity) {
  if (severity === 'Critique') return 'bg-red-100 text-red-700 border-red-200'
  if (severity === 'Majeure') return 'bg-amber-100 text-amber-700 border-amber-200'
  return 'bg-green-100 text-green-700 border-green-200'
}

function statusStyles(status) {
  if (status === 'resolved') return 'bg-emerald-100 text-emerald-700 border-emerald-200'
  if (status === 'acknowledged') return 'bg-blue-100 text-blue-700 border-blue-200'
  if (status === 'assigned') return 'bg-indigo-100 text-indigo-700 border-indigo-200'
  return 'bg-slate-100 text-slate-700 border-slate-200'
}

function formatDate(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function InfoRow({ label, value, emphasis = false }) {
  return (
    <div className={`rounded-xl border px-4 py-3 ${emphasis ? 'bg-white border-slate-300' : 'bg-slate-50 border-slate-200'}`}>
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-slate-800">{value || '-'}</p>
    </div>
  )
}

function AlertDetailPage() {
  const { alertId } = useParams()
  const [loading, setLoading] = useState(true)
  const [alert, setAlert] = useState(null)

  useEffect(() => {
    const loadAlert = async () => {
      setLoading(true)
      try {
        const response = await getAlerteById(alertId)
        setAlert(response.data?.alert || null)
      } catch (error) {
        toast.error(error.response?.data?.error || "Impossible de charger le detail de l'alerte")
      } finally {
        setLoading(false)
      }
    }
    loadAlert()
  }, [alertId])

  if (loading) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <p className="text-slate-600">Chargement du detail...</p>
      </section>
    )
  }

  if (!alert) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
        <p className="text-slate-700">Alerte introuvable.</p>
        <Link to="/alertes" className="inline-block rounded bg-slate-800 px-3 py-2 text-sm text-white">
          Retour aux alertes
        </Link>
      </section>
    )
  }

  return (
    <section className="space-y-4">
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-700 p-5 text-white shadow-lg">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wider text-slate-300">Alert detail</p>
            <h3 className="mt-1 text-2xl font-bold">Alerte #{alert.id}</h3>
            <p className="mt-1 text-sm text-slate-300">{alert.machine || 'Machine'} - {alert.defect || 'Defaut detecte'}</p>
          </div>
          <Link to="/alertes" className="rounded-lg bg-white/10 px-3 py-2 text-sm text-white hover:bg-white/20">
            Retour aux alertes
          </Link>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${severityStyles(alert.severity)}`}>
            Severite: {alert.severity || '-'}
          </span>
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusStyles(alert.status)}`}>
            Statut: {alert.status || '-'}
          </span>
          <span className="rounded-full border border-slate-300 bg-white/10 px-3 py-1 text-xs font-semibold text-white">
            {alert.acknowledged ? 'Acquittee' : 'Non acquittee'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
          <h4 className="text-sm font-semibold text-slate-700">Informations principales</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <InfoRow label="Machine" value={alert.machine} emphasis />
            <InfoRow label="Defaut detecte" value={alert.defect} emphasis />
            <InfoRow label="Score anomalie" value={String(alert.anomaly_score ?? alert.defect_score ?? '-')} />
            <InfoRow label="Confidence" value={String(alert.confidence ?? '-')} />
            <InfoRow label="Assignee a" value={alert.assigned_to_name || alert.assigned_to} />
            <InfoRow label="Assignee par" value={alert.assigned_by_name || alert.assigned_by} />
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 space-y-3 shadow-sm">
          <h4 className="text-sm font-semibold text-slate-700">Chronologie</h4>
          <InfoRow label="Date creation" value={formatDate(alert.created_at)} />
          <InfoRow label="Date resolution" value={formatDate(alert.resolved_at)} />
          <InfoRow label="Date validation" value={formatDate(alert.validation_at)} />
        </div>
      </div>
    </section>
  )
}

export default AlertDetailPage

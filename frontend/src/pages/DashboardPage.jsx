import {
  Line,
  LineChart,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
} from 'recharts'
import useDashboard from '../hooks/useDashboard'

function getScoreStyle(score) {
  if (score > 70) return { color: '#dc2626', status: 'Critique', badge: 'bg-red-100 text-red-700' }
  if (score >= 40) {
    return { color: '#d97706', status: 'Attention', badge: 'bg-amber-100 text-amber-700' }
  }
  return { color: '#16a34a', status: 'Nominal', badge: 'bg-green-100 text-green-700' }
}

function severityBadge(severity) {
  if (severity === 'Critique') return 'bg-red-100 text-red-700'
  if (severity === 'Majeure') return 'bg-amber-100 text-amber-700'
  return 'bg-green-100 text-green-700'
}

function timeAgo(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  const diff = Math.max(0, Math.floor((Date.now() - date.getTime()) / 60000))
  return `${diff} min ago`
}

function DashboardPage() {
  const { summary, machineCards } = useDashboard()
  const pendingInterventions = summary.pending_interventions_list || summary.pending_list || []

  const kpis = [
    { label: 'Machines actives', value: summary.active_machines ?? 4 },
    { label: 'Alertes en cours', value: summary.open_alerts ?? 0 },
    { label: 'Interventions en attente', value: summary.pending_interventions ?? 0 },
    { label: 'Disponibilite globale', value: `${Math.max(65, 100 - (summary.open_alerts || 0)).toFixed(1)}%` },
  ]

  return (
    <section className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map((metric) => (
          <article key={metric.label} className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="text-sm text-slate-500">{metric.label}</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{metric.value}</p>
          </article>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        {machineCards.map((machine) => {
          const style = getScoreStyle(machine.anomalyScore)
          return (
            <article
              key={machine.key}
              className="rounded-xl border border-slate-200 bg-white p-5 space-y-4"
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-slate-900">{machine.label}</h3>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${style.badge}`}>
                  {style.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 items-center">
                <div className="h-32">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart
                      cx="50%"
                      cy="50%"
                      innerRadius="65%"
                      outerRadius="100%"
                      barSize={14}
                      data={[{ value: machine.anomalyScore }]}
                      startAngle={90}
                      endAngle={-270}
                    >
                      <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                      <RadialBar dataKey="value" fill={style.color} cornerRadius={8} />
                    </RadialBarChart>
                  </ResponsiveContainer>
                </div>

                <div>
                  <p className="text-sm text-slate-500">Defect score</p>
                  <p className="text-3xl font-bold" style={{ color: style.color }}>
                    {machine.anomalyScore.toFixed(1)}%
                  </p>
                </div>
              </div>

              <div className="h-16">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={machine.sparkline}>
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={style.color}
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </article>
          )
        })}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <article className="rounded-xl border border-slate-200 bg-white p-5">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Dernieres alertes</h3>
          <div className="space-y-3">
            {(summary.recent_alerts || []).slice(0, 5).map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between rounded-lg border border-slate-100 p-3"
              >
                <div>
                  <p className="font-medium text-slate-900">{alert.machine}</p>
                  <p className="text-sm text-slate-500">{alert.defect}</p>
                </div>
                <div className="text-right space-y-1">
                  <span
                    className={`inline-block rounded-full px-2 py-1 text-xs font-semibold ${severityBadge(alert.severity)}`}
                  >
                    {alert.severity}
                  </span>
                  <p className="text-xs text-slate-400">{timeAgo(alert.created_at)}</p>
                </div>
              </div>
            ))}
            {(!summary.recent_alerts || summary.recent_alerts.length === 0) && (
              <p className="text-sm text-slate-500">Aucune alerte recente.</p>
            )}
          </div>
        </article>

        <article className="rounded-xl border border-slate-200 bg-white p-5">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Interventions en attente</h3>
          <div className="space-y-3">
            {pendingInterventions.slice(0, 5).map((item) => (
              <div key={item.id} className="rounded-lg border border-slate-100 p-3">
                <p className="font-medium text-slate-900">{item.machine}</p>
                <p className="text-sm text-slate-500">
                  Technicien: {item.assigned_to ? `#${item.assigned_to}` : 'Non assigne'}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Deadline:{' '}
                  {item.deadline
                    ? new Date(item.deadline).toLocaleString()
                    : item.resolved_at
                      ? new Date(item.resolved_at).toLocaleString()
                      : '-'}
                </p>
              </div>
            ))}
            {pendingInterventions.length === 0 && (
              <p className="text-sm text-slate-500">Aucune intervention en attente.</p>
            )}
          </div>
        </article>
      </div>
    </section>
  )
}

export default DashboardPage

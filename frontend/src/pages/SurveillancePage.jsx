import {
  Line,
  LineChart,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import useSurveillance from '../hooks/useSurveillance'

const SENSOR_COLORS = ['#2563eb', '#16a34a', '#f59e0b', '#dc2626', '#7c3aed', '#0891b2']

const SENSOR_UNITS = {
  vibration: 'g',
  current: 'A',
  temperature: '°C',
  pressure_in: 'bar',
  pressure_out: 'bar',
  flow_rate: 'm3/h',
  pressure: 'bar',
  temperature_oil: '°C',
  temperature_air: '°C',
  temp_in_hot: '°C',
  temp_out_hot: '°C',
  temp_in_cold: '°C',
  temp_out_cold: '°C',
}

function getScoreColor(score) {
  if (score > 70) return '#dc2626'
  if (score >= 40) return '#f59e0b'
  return '#16a34a'
}

function sensorDotColor(value) {
  if (value > 80) return 'bg-red-500'
  if (value > 50) return 'bg-amber-500'
  return 'bg-green-500'
}

function formatTime(iso) {
  return new Date(iso).toLocaleString('fr-FR', { hour12: false })
}

function humanize(value) {
  return (value || '').replaceAll('_', ' ')
}

function SurveillancePage() {
  const {
    tabs,
    activeMachine,
    setActiveMachine,
    chartData,
    anomalyScore,
    defectScores,
    modelName,
    requiredSensors,
    sensorList,
    defectHistory,
    lastDefect,
    simulationMode,
  } = useSurveillance()

  const scoreColor = getScoreColor(anomalyScore)
  const gaugeData = [{ name: 'score', value: anomalyScore, fill: scoreColor }]
  const hasTabs = tabs.length > 0
  const defectScoreEntries = Object.entries(defectScores || {})

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveMachine(tab.key)}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
              activeMachine === tab.key
                ? 'bg-[#16a34a] text-white'
                : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-50'
            }`}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>
      {!hasTabs && (
        <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600">
          Aucun composant actif disponible pour ce profil.
        </div>
      )}
      {simulationMode && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
          Aucun flux live detecte: mesures simulees actives pour {tabs.find((t) => t.key === activeMachine)?.label}.
        </div>
      )}

      {hasTabs && <div className="grid grid-cols-1 xl:grid-cols-10 gap-4">
        <div className="xl:col-span-7 space-y-4">
          <article className="rounded-xl border border-slate-200 bg-white p-4 h-[360px]">
            <h3 className="text-base font-semibold text-slate-800 mb-3">Capteurs en direct</h3>
            <ResponsiveContainer width="100%" height="90%">
              <LineChart data={chartData}>
                <XAxis dataKey="timestamp" tick={{ fontSize: 11 }} />
                <YAxis />
                <Tooltip />
                {sensorList.map((sensor, index) => (
                  <Line
                    key={sensor.name}
                    dataKey={sensor.name}
                    type="monotone"
                    dot={false}
                    strokeWidth={2}
                    stroke={SENSOR_COLORS[index % SENSOR_COLORS.length]}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </article>

          <article className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="text-base font-semibold text-slate-800 mb-3">Historique des defauts</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-200">
                    <th className="py-2">Timestamp</th>
                    <th className="py-2">Defaut</th>
                    <th className="py-2">Confiance</th>
                    <th className="py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {defectHistory.slice(0, 10).map((item, idx) => (
                    <tr key={`${item.timestamp}-${idx}`} className="border-b border-slate-100">
                      <td className="py-2">{formatTime(item.timestamp)}</td>
                      <td className="py-2">{humanize(item.defect)}</td>
                      <td className="py-2">{item.confidence}%</td>
                      <td className="py-2">
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs">{item.status}</span>
                      </td>
                    </tr>
                  ))}
                  {defectHistory.length === 0 && (
                    <tr>
                      <td className="py-4 text-slate-500" colSpan={4}>
                        Aucun defaut detecte pour le moment.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </article>
        </div>

        <div className="xl:col-span-3 space-y-4">
          <article className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="text-base font-semibold text-slate-800 mb-2">Score defaut</h3>
            <p className="text-xs text-slate-500 mb-2">
              Modele IA actif: <span className="font-medium text-slate-700">{modelName || 'N/A'}</span>
            </p>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  innerRadius="65%"
                  outerRadius="100%"
                  data={gaugeData}
                  startAngle={180}
                  endAngle={0}
                >
                  <RadialBar background dataKey="value" cornerRadius={8} />
                  <text x="50%" y="58%" textAnchor="middle" className="fill-slate-700 text-xl font-semibold">
                    {anomalyScore}%
                  </text>
                </RadialBarChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="text-base font-semibold text-slate-800 mb-3">Valeurs actuelles</h3>
            <ul className="space-y-2">
              {sensorList.map((sensor) => (
                <li key={sensor.name} className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${sensorDotColor(sensor.value)}`} />
                    <span className="text-slate-700">{sensor.label}</span>
                  </div>
                  <span className="font-medium text-slate-900">
                    {Number(sensor.value).toFixed(2)} {SENSOR_UNITS[sensor.name] || ''}
                  </span>
                </li>
              ))}
            </ul>
          </article>

          <article className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="text-base font-semibold text-slate-800 mb-3">Scores des deux defauts</h3>
            <div className="space-y-2 text-sm">
              {defectScoreEntries.length === 0 && (
                <p className="text-slate-500">Aucun score de defaut disponible.</p>
              )}
              {defectScoreEntries.map(([defect, score]) => (
                <div key={defect} className="rounded-lg border border-slate-100 bg-slate-50 p-2">
                  <p className="font-medium text-slate-800">{humanize(defect)}</p>
                  <p className="text-slate-600">{(Number(score) * 100).toFixed(1)}%</p>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-xl border border-slate-200 bg-white p-4">
            <h3 className="text-base font-semibold text-slate-800 mb-2">Dernier defaut detecte</h3>
            {lastDefect ? (
              <div className="space-y-1 text-sm">
                <p className="font-medium text-slate-900">{humanize(lastDefect.defect)}</p>
                <p className="text-slate-600">Confiance: {lastDefect.confidence}%</p>
                <p className="text-slate-600">Modele: {lastDefect.modelName || modelName || 'N/A'}</p>
                <p className="text-slate-600">
                  Capteurs requis:{' '}
                  {(lastDefect.requiredSensors || requiredSensors).length > 0
                    ? (lastDefect.requiredSensors || requiredSensors).map(humanize).join(', ')
                    : 'N/A'}
                </p>
                <p className="text-slate-500">{formatTime(lastDefect.timestamp)}</p>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Aucun defaut recent.</p>
            )}
          </article>
        </div>
      </div>}
    </section>
  )
}

export default SurveillancePage

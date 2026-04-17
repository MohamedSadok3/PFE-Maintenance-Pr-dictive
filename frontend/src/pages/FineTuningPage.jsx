import { useEffect, useMemo, useState } from 'react'
import { getComponents } from '../services/componentService'

const COMPONENT_MODELS = {
  moteur: ['LSTM-moteur-v2', 'BiLSTM-moteur-v1'],
  pompe: ['LSTM-pompe-v2', 'XGBoost-pompe-v1'],
  compresseur: ['Transformer-compresseur-v1', 'LSTM-compresseur-v2'],
  echangeur: ['LSTM-echangeur-v2', 'RandomForest-echangeur-v1'],
}

const COMPONENT_LABELS = {
  moteur: 'Moteur',
  pompe: 'Pompe',
  compresseur: 'Compresseur',
  echangeur: 'Echangeur Thermique',
}

const BEST_MODEL_BY_TYPE = {
  moteur: 'LSTM-moteur-v2',
  pompe: 'LSTM-pompe-v2',
  compresseur: 'Transformer-compresseur-v1',
  echangeur: 'LSTM-echangeur-v2',
}

function FineTuningPage() {
  const [fileName, setFileName] = useState('')
  const [components, setComponents] = useState([])
  const [component, setComponent] = useState('')
  const [baseModel, setBaseModel] = useState(COMPONENT_MODELS.moteur[0])
  const [progress, setProgress] = useState(0)
  const [isTraining, setIsTraining] = useState(false)
  const [measurements, setMeasurements] = useState({})

  useEffect(() => {
    let mounted = true
    const loadComponents = async () => {
      try {
        const response = await getComponents()
        const enabled = (response.data.components || []).filter((item) => item.enabled)
        if (mounted) {
          setComponents(enabled)
          if (enabled.length > 0) {
            setComponent(enabled[0].key)
          }
        }
      } catch {
        if (mounted) {
          const fallback = Object.keys(COMPONENT_LABELS).map((key) => ({
            key,
            name: COMPONENT_LABELS[key],
            type: key,
            enabled: true,
          }))
          setComponents(fallback)
          setComponent(fallback[0]?.key || '')
        }
      }
    }
    loadComponents()
    return () => {
      mounted = false
    }
  }, [])

  const selectedComponent = useMemo(
    () => components.find((item) => item.key === component) || null,
    [component, components],
  )
  const componentType = selectedComponent?.type || 'moteur'
  const modelOptions = COMPONENT_MODELS[componentType] || COMPONENT_MODELS.moteur
  const bestModel = BEST_MODEL_BY_TYPE[componentType] || modelOptions[0]

  useEffect(() => {
    setBaseModel(bestModel)
  }, [bestModel])

  useEffect(() => {
    const makeMeasurement = () => ({
      moteur: {
        vibration: Number((0.2 + Math.random() * 1.5).toFixed(3)),
        current: Number((8 + Math.random() * 7).toFixed(2)),
        temperature: Number((55 + Math.random() * 35).toFixed(1)),
      },
      pompe: {
        pressure_in: Number((3 + Math.random() * 2).toFixed(2)),
        pressure_out: Number((6 + Math.random() * 4).toFixed(2)),
        flow_rate: Number((90 + Math.random() * 60).toFixed(1)),
      },
      compresseur: {
        pressure: Number((8 + Math.random() * 4).toFixed(2)),
        temperature_oil: Number((70 + Math.random() * 25).toFixed(1)),
        current: Number((12 + Math.random() * 10).toFixed(1)),
      },
      echangeur: {
        temp_in_hot: Number((85 + Math.random() * 20).toFixed(1)),
        temp_out_hot: Number((55 + Math.random() * 18).toFixed(1)),
        flow_rate: Number((120 + Math.random() * 45).toFixed(1)),
      },
    })

    setMeasurements(makeMeasurement())
    const timer = setInterval(() => {
      setMeasurements(makeMeasurement())
    }, 2000)

    return () => clearInterval(timer)
  }, [])

  const metrics = useMemo(
    () => [
      { metric: 'F1-Score', before: '0.81', after: progress >= 100 ? '0.89' : '---' },
      { metric: 'Precision', before: '0.84', after: progress >= 100 ? '0.92' : '---' },
    ],
    [progress],
  )

  const onTrain = () => {
    setIsTraining(true)
    setProgress(0)
    let current = 0
    const timer = setInterval(() => {
      current += 10
      setProgress(current)
      if (current >= 100) {
        clearInterval(timer)
        setIsTraining(false)
      }
    }, 350)
  }

  return (
    <section className="space-y-4">
      <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
        Simulation mode: training jobs are mocked for demo purposes.
      </div>

      <article className="rounded-xl border border-slate-200 bg-white p-6 space-y-5">
        <div>
          <p className="text-sm font-medium text-slate-700 mb-2">Upload CSV</p>
          <label className="block rounded-xl border-2 border-dashed border-slate-300 p-6 text-center cursor-pointer hover:border-[#16a34a]">
            <input
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(event) => setFileName(event.target.files?.[0]?.name || '')}
            />
            <p className="text-slate-600">{fileName || 'Drop CSV file or click to upload'}</p>
          </label>
        </div>

        <div className="grid md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm text-slate-700 mb-1">Composant (instance)</label>
            <select
              value={component}
              onChange={(event) => setComponent(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              {components.map((item) => (
                <option key={item.key} value={item.key}>
                  {item.name} ({COMPONENT_LABELS[item.type] || item.type})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm text-slate-700 mb-1">Base model (selon type)</label>
            <select
              value={baseModel}
              onChange={(event) => setBaseModel(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              {modelOptions.map((modelName) => (
                <option key={modelName} value={modelName}>
                  {modelName}
                  {modelName === bestModel ? ' (best)' : ''}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-slate-500">Meilleur modele recommande: {bestModel}</p>
          </div>
          <button
            type="button"
            onClick={onTrain}
            disabled={!fileName || isTraining}
            className="rounded-lg bg-[#16a34a] px-4 py-2 text-white disabled:opacity-60"
          >
            {isTraining ? 'Training...' : 'Start fine-tuning'}
          </button>
        </div>

        <div>
          <p className="mb-2 text-sm text-slate-700">Training progress</p>
          <div className="h-3 rounded-full bg-slate-200 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[#16a34a] to-[#2563eb] transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </article>

      <article className="rounded-xl border border-slate-200 bg-white p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-3">
          Mesures simulees (aleatoires) - {selectedComponent?.name || 'Composant'}
        </h3>
        <div className="grid sm:grid-cols-3 gap-3">
          {Object.entries(measurements[componentType] || {}).map(([key, value]) => (
            <div key={key} className="rounded-lg bg-slate-50 border border-slate-200 p-3">
              <p className="text-xs uppercase text-slate-500">{key}</p>
              <p className="text-xl font-semibold text-[#2563eb]">{value}</p>
            </div>
          ))}
        </div>
      </article>

      <article className="rounded-xl border border-slate-200 bg-white p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Model quality comparison</h3>
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500">
              <th className="py-2">Metric</th>
              <th className="py-2">Before</th>
              <th className="py-2">After</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((item) => (
              <tr key={item.metric} className="border-b border-slate-100">
                <td className="py-2 font-medium text-slate-800">{item.metric}</td>
                <td className="py-2">{item.before}</td>
                <td className="py-2 text-[#16a34a] font-semibold">{item.after}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  )
}

export default FineTuningPage

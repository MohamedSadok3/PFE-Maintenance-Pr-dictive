import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { getIoTConfig, saveIoTConfig, testMqttConnection } from '../services/iotService'
import { connectSocket } from '../services/socketService'
import { MACHINE_LABELS } from '../constants/machines'

const ONLINE_THRESHOLD_MS = 5000

function emptyMqtt() {
  return { host: 'localhost', port: 1883, username: '', password: '' }
}

function IoTConfigPage() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [mqtt, setMqtt] = useState(emptyMqtt())
  const [sensors, setSensors] = useState([])
  const [machineStatus, setMachineStatus] = useState({})

  const groupedSensors = useMemo(() => {
    const groups = {}
    for (const sensor of sensors) {
      if (!groups[sensor.machine]) {
        groups[sensor.machine] = []
      }
      groups[sensor.machine].push(sensor)
    }
    return groups
  }, [sensors])

  const loadConfig = async () => {
    setLoading(true)
    try {
      const response = await getIoTConfig()
      const mqttData = response.data?.mqtt || {}
      setMqtt({
        host: mqttData.host || 'localhost',
        port: mqttData.port || 1883,
        username: mqttData.username || '',
        password: mqttData.password || '',
      })
      setSensors(response.data?.sensors || [])
    } catch (error) {
      toast.error(error.response?.data?.error || 'Impossible de charger la configuration IoT')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadConfig()
  }, [])

  useEffect(() => {
    const socket = connectSocket()

    const onSensorData = (payload) => {
      if (!payload?.machine) return
      setMachineStatus((prev) => ({
        ...prev,
        [payload.machine]: {
          online: true,
          lastSeen: Date.now(),
          anomalyScore: Math.round(Number(payload.defect_score ?? payload.anomaly_score ?? 0) * 100),
          defect: payload.defect || null,
        },
      }))
    }

    socket.on('sensor:data', onSensorData)

    const intervalId = window.setInterval(() => {
      const now = Date.now()
      setMachineStatus((prev) => {
        const next = { ...prev }
        for (const [machine, status] of Object.entries(next)) {
          if (now - (status.lastSeen || 0) > ONLINE_THRESHOLD_MS) {
            next[machine] = { ...status, online: false }
          }
        }
        return next
      })
    }, 1000)

    return () => {
      window.clearInterval(intervalId)
      socket.off('sensor:data', onSensorData)
    }
  }, [])

  const onTestMqtt = async () => {
    setTesting(true)
    try {
      const response = await testMqttConnection(mqtt)
      toast.success(response.data?.message || 'Connexion MQTT réussie')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Échec du test MQTT')
    } finally {
      setTesting(false)
    }
  }

  const onSave = async () => {
    setSaving(true)
    try {
      const response = await saveIoTConfig({ mqtt, sensors })
      const mqttData = response.data?.mqtt || {}
      setMqtt({
        host: mqttData.host || mqtt.host,
        port: mqttData.port || mqtt.port,
        username: mqttData.username || '',
        password: mqttData.password || '',
      })
      setSensors(response.data?.sensors || sensors)
      toast.success('Configuration IoT enregistrée')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Échec de la sauvegarde')
    } finally {
      setSaving(false)
    }
  }

  const updateSensor = (index, field, value) => {
    setSensors((prev) =>
      prev.map((item, itemIndex) => {
        if (itemIndex !== index) return item
        if (field === 'min_value' || field === 'max_value') {
          return { ...item, [field]: Number(value) }
        }
        if (field === 'enabled') {
          return { ...item, enabled: Boolean(value) }
        }
        return { ...item, [field]: value }
      }),
    )
  }

  if (loading) {
    return (
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <p className="text-slate-500">Chargement...</p>
      </section>
    )
  }

  return (
    <div className="space-y-5">
      <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
        <header className="space-y-1">
          <h3 className="text-lg font-semibold text-slate-800">Configuration MQTT</h3>
          <p className="text-sm text-slate-500">Paramètres de connexion au broker Mosquitto.</p>
        </header>

        <div className="grid md:grid-cols-2 gap-3">
          <label className="space-y-1">
            <span className="text-sm text-slate-700">Adresse IP / Hôte</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={mqtt.host}
              onChange={(e) => setMqtt((prev) => ({ ...prev, host: e.target.value }))}
              placeholder="192.168.1.10"
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-700">Port</span>
            <input
              type="number"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={mqtt.port}
              onChange={(e) => setMqtt((prev) => ({ ...prev, port: Number(e.target.value) }))}
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-700">Nom d'utilisateur</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={mqtt.username}
              onChange={(e) => setMqtt((prev) => ({ ...prev, username: e.target.value }))}
            />
          </label>
          <label className="space-y-1">
            <span className="text-sm text-slate-700">Mot de passe</span>
            <input
              type="password"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={mqtt.password}
              onChange={(e) => setMqtt((prev) => ({ ...prev, password: e.target.value }))}
            />
          </label>
        </div>

        <button
          type="button"
          onClick={onTestMqtt}
          disabled={testing}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm hover:bg-slate-50 disabled:opacity-60"
        >
          {testing ? 'Test en cours...' : 'Tester la connexion'}
        </button>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
        <header className="space-y-1">
          <h3 className="text-lg font-semibold text-slate-800">Capteurs par machine</h3>
          <p className="text-sm text-slate-500">Unités, seuils min/max et activation des capteurs.</p>
        </header>

        {Object.entries(groupedSensors).map(([machine, items]) => (
          <div key={machine} className="space-y-2">
            <h4 className="text-sm font-semibold text-slate-700">
              {MACHINE_LABELS[machine] || machine}
            </h4>
            <div className="overflow-auto">
              <table className="w-full min-w-[720px] text-sm">
                <thead>
                  <tr className="text-left text-slate-500 border-b border-slate-200">
                    <th className="py-2">Capteur</th>
                    <th className="py-2">Unité</th>
                    <th className="py-2">Min</th>
                    <th className="py-2">Max</th>
                    <th className="py-2">État</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((sensor) => {
                    const globalIndex = sensors.findIndex(
                      (item) => item.machine === sensor.machine && item.sensor_name === sensor.sensor_name,
                    )
                    return (
                      <tr key={`${sensor.machine}-${sensor.sensor_name}`} className="border-b border-slate-100">
                        <td className="py-2 capitalize">{sensor.sensor_name.replaceAll('_', ' ')}</td>
                        <td className="py-2">
                          <input
                            className="w-24 rounded border border-slate-300 px-2 py-1"
                            value={sensor.unit}
                            onChange={(e) => updateSensor(globalIndex, 'unit', e.target.value)}
                          />
                        </td>
                        <td className="py-2">
                          <input
                            type="number"
                            step="0.01"
                            className="w-24 rounded border border-slate-300 px-2 py-1"
                            value={sensor.min_value}
                            onChange={(e) => updateSensor(globalIndex, 'min_value', e.target.value)}
                          />
                        </td>
                        <td className="py-2">
                          <input
                            type="number"
                            step="0.01"
                            className="w-24 rounded border border-slate-300 px-2 py-1"
                            value={sensor.max_value}
                            onChange={(e) => updateSensor(globalIndex, 'max_value', e.target.value)}
                          />
                        </td>
                        <td className="py-2">
                          <label className="inline-flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={sensor.enabled}
                              onChange={(e) => updateSensor(globalIndex, 'enabled', e.target.checked)}
                            />
                            <span
                              className={`rounded-full px-2 py-1 text-xs ${
                                sensor.enabled
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-slate-100 text-slate-600'
                              }`}
                            >
                              {sensor.enabled ? 'Actif' : 'Inactif'}
                            </span>
                          </label>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 space-y-4 sm:p-5">
        <header className="space-y-1">
          <h3 className="text-lg font-semibold text-slate-800">Monitoring temps réel</h3>
          <p className="text-sm text-slate-500">Statut des machines basé sur le flux capteurs en direct.</p>
        </header>

        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3">
          {Object.entries(MACHINE_LABELS).map(([machine, label]) => {
            const status = machineStatus[machine] || { online: false, anomalyScore: 0 }
            return (
              <div key={machine} className="rounded-lg border border-slate-200 p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="font-medium text-slate-800">{label}</p>
                  <span
                    className={`rounded-full px-2 py-1 text-xs ${
                      status.online ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {status.online ? 'En ligne' : 'Hors ligne'}
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Score anomalie : <span className="font-medium text-slate-700">{status.anomalyScore || 0}%</span>
                </p>
                {status.defect && status.defect !== 'normal_operation' && (
                  <p className="text-xs text-amber-700">Défaut : {status.defect.replaceAll('_', ' ')}</p>
                )}
              </div>
            )
          })}
        </div>
      </section>

      <div>
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="rounded-lg bg-[#16a34a] px-4 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-60"
        >
          {saving ? 'Enregistrement...' : 'Enregistrer la configuration'}
        </button>
      </div>
    </div>
  )
}

export default IoTConfigPage

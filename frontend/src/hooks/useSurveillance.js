import { useEffect, useMemo, useRef, useState } from 'react'
import { io } from 'socket.io-client'
import api from '../services/api'

const MACHINES = {
  moteur: 'Moteur',
  pompe: 'Pompe',
  compresseur: 'Compresseur',
  echangeur: 'Échangeur',
}

const MACHINE_SENSORS = {
  moteur: ['vibration', 'current', 'temperature'],
  pompe: ['pressure_in', 'pressure_out', 'flow_rate', 'vibration'],
  compresseur: ['pressure', 'temperature_oil', 'temperature_air', 'current'],
  echangeur: ['temp_in_hot', 'temp_out_hot', 'temp_in_cold', 'temp_out_cold', 'flow_rate'],
}

const DEFECT_OPTIONS_BY_TYPE = {
  moteur: ['degradation_roulement', 'desequilibre_desalignement'],
  pompe: ['cavitation', 'usure_garniture_mecanique'],
  compresseur: ['usure_soupapes', 'refroidissement_huile'],
  echangeur: ['encrassement_progressif', 'fuite_interne'],
}

function toLabel(name) {
  return name.replaceAll('_', ' ').replace(/\b\w/g, (char) => char.toUpperCase())
}

export default function useSurveillance() {
  const user = useMemo(() => JSON.parse(localStorage.getItem('user') || 'null'), [])
  const userMachineKey = useMemo(
    () => (Array.isArray(user?.machines) ? user.machines.join('|') : ''),
    [user?.machines],
  )
  const [components, setComponents] = useState([])
  const [activeMachine, setActiveMachine] = useState('moteur')
  const [chartData, setChartData] = useState([])
  const [anomalyScore, setAnomalyScore] = useState(0)
  const [defectScores, setDefectScores] = useState({})
  const [modelName, setModelName] = useState('')
  const [requiredSensors, setRequiredSensors] = useState([])
  const [sensorList, setSensorList] = useState([])
  const [lastDefect, setLastDefect] = useState(null)
  const [defectHistory, setDefectHistory] = useState([])
  const [simulationMode, setSimulationMode] = useState(false)

  const chartBufferRef = useRef([])
  const lastLiveMessageAtRef = useRef(0)

  const tabs = useMemo(() => {
    if (components.length > 0) {
      return components.map((component) => ({
        key: component.key,
        label: component.name,
        type: component.type,
      }))
    }
    return Object.entries(MACHINES).map(([key, label]) => ({ key, label, type: key }))
  }, [components])

  const activeTab = useMemo(
    () => tabs.find((tab) => tab.key === activeMachine) || tabs[0] || null,
    [activeMachine, tabs],
  )

  const activeType = activeTab?.type || activeMachine

  useEffect(() => {
    if (tabs.length > 0 && !tabs.some((tab) => tab.key === activeMachine)) {
      setActiveMachine(tabs[0].key)
    }
  }, [activeMachine, tabs])

  useEffect(() => {
    let mounted = true

    const loadComponents = async () => {
      try {
        const response = await api.get('/api/components')
        const allComponents = (response.data.components || []).filter((item) => item.enabled)
        const visibleComponents =
          user?.role === 'technicien' && Array.isArray(user?.machines) && user.machines.length > 0
            ? allComponents.filter((component) => user.machines.includes(component.type))
            : allComponents
        if (mounted) {
          setComponents(visibleComponents)
          if (visibleComponents.length > 0) {
            setActiveMachine((prev) =>
              visibleComponents.some((component) => component.key === prev)
                ? prev
                : visibleComponents[0].key,
            )
          }
        }
      } catch {
        if (mounted) {
          const fallback = Object.entries(MACHINES).map(([key, label]) => ({ key, name: label, type: key }))
          setComponents(fallback)
          setActiveMachine((prev) => (fallback.some((item) => item.key === prev) ? prev : fallback[0].key))
        }
      }
    }

    loadComponents()
    return () => {
      mounted = false
    }
  }, [user?.role, userMachineKey])

  useEffect(() => {
    const socket = io('http://localhost:5000', { transports: ['websocket', 'polling'] })

    const applyPayload = (payload) => {
      if (!payload || payload.machine !== activeType) {
        return
      }

      lastLiveMessageAtRef.current = Date.now()
      setSimulationMode(false)

      const sensors = payload.sensors || {}
      const timestampRaw = payload.timestamp || new Date().toISOString()
      const chartPoint = {
        timestamp: new Date(timestampRaw).toLocaleTimeString('fr-FR', { hour12: false }),
        ...sensors,
      }

      chartBufferRef.current = [...chartBufferRef.current, chartPoint].slice(-60)
      const score = Number(payload.defect_score ?? payload.anomaly_score ?? 0)
      const liveDefectScores = payload.defect_scores && typeof payload.defect_scores === 'object'
        ? payload.defect_scores
        : {}
      setAnomalyScore(Math.round(score * 100))
      setDefectScores(liveDefectScores)
      setModelName(payload.model_name || '')
      setRequiredSensors(Array.isArray(payload.required_sensors) ? payload.required_sensors : [])

      const sensorItems = Object.entries(sensors).map(([name, value]) => ({
        name,
        label: toLabel(name),
        value: typeof value === 'number' ? value : Number(value || 0),
      }))
      setSensorList(sensorItems)

      if (payload.defect && payload.defect !== 'normal_operation') {
        const defectItem = {
          timestamp: timestampRaw,
          defect: payload.defect,
          defectScores: liveDefectScores,
          confidence: Math.round((payload.confidence || 0) * 100),
          modelName: payload.model_name || '',
          requiredSensors: Array.isArray(payload.required_sensors) ? payload.required_sensors : [],
          status: (Number(payload.defect_score ?? payload.anomaly_score ?? 0) || 0) >= 0.85 ? 'Critique' : 'Surveillance',
        }
        setLastDefect(defectItem)
        setDefectHistory((prev) => [defectItem, ...prev].slice(0, 30))
      }
    }

    socket.on('sensor:data', applyPayload)

    const intervalId = setInterval(() => {
      setChartData([...chartBufferRef.current])
    }, 1000)

    const simulationInterval = setInterval(() => {
      const lastLiveAge = Date.now() - lastLiveMessageAtRef.current
      if (lastLiveAge < 3500) {
        return
      }

      setSimulationMode(true)
      const sensors = {}

      for (const sensor of MACHINE_SENSORS[activeType] || []) {
        if (sensor.includes('temp')) {
          sensors[sensor] = Number((40 + Math.random() * 45).toFixed(2))
        } else if (sensor.includes('pressure')) {
          sensors[sensor] = Number((3 + Math.random() * 8).toFixed(2))
        } else if (sensor.includes('flow')) {
          sensors[sensor] = Number((80 + Math.random() * 80).toFixed(2))
        } else if (sensor.includes('current')) {
          sensors[sensor] = Number((8 + Math.random() * 14).toFixed(2))
        } else {
          sensors[sensor] = Number((0.15 + Math.random() * 1.6).toFixed(3))
        }
      }

      const anomaly = Math.min(
        0.98,
        Math.max(
          0.05,
          Object.values(sensors).reduce((sum, value) => sum + Number(value), 0) /
            (Object.keys(sensors).length * 100),
        ),
      )
      const defects = DEFECT_OPTIONS_BY_TYPE[activeType] || ['defaut_1', 'defaut_2']
      const firstScore = Number(Math.max(0, anomaly - 0.12).toFixed(4))
      const secondScore = Number(Math.min(0.99, anomaly + 0.09).toFixed(4))
      const simulatedDefectScores = {
        [defects[0]]: firstScore,
        [defects[1]]: secondScore,
      }
      const topDefect = firstScore >= secondScore ? defects[0] : defects[1]

      applyPayload({
        machine: activeType,
        sensors,
        defect_score: anomaly,
        anomaly_score: anomaly,
        defect_scores: simulatedDefectScores,
        confidence: 0.65 + Math.random() * 0.3,
        defect: anomaly > 0.45 ? topDefect : 'normal_operation',
        timestamp: new Date().toISOString(),
      })
    }, 2000)

    return () => {
      clearInterval(intervalId)
      clearInterval(simulationInterval)
      socket.disconnect()
    }
  }, [activeType])

  useEffect(() => {
    chartBufferRef.current = []
    setChartData([])
    setAnomalyScore(0)
    setSensorList(
      (MACHINE_SENSORS[activeType] || []).map((sensor) => ({
        name: sensor,
        label: toLabel(sensor),
        value: 0,
      })),
    )
    setLastDefect(null)
    setDefectHistory([])
    setDefectScores({})
    setModelName('')
    setRequiredSensors([])
    setSimulationMode(false)
    lastLiveMessageAtRef.current = 0
  }, [activeType])

  return {
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
  }
}

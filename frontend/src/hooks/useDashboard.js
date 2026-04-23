import { useEffect, useMemo, useState } from 'react'
import { io } from 'socket.io-client'
import api from '../services/api'
import { getStoredUser } from '../utils/storage'

const MACHINE_KEYS = ['moteur', 'pompe', 'compresseur', 'echangeur']

const machineLabel = {
  moteur: 'Moteur',
  pompe: 'Pompe',
  compresseur: 'Compresseur',
  echangeur: 'Echangeur',
}

function createSeedSparkline() {
  const now = Date.now()
  return Array.from({ length: 20 }, (_, idx) => ({
    idx,
    value: Number((20 + Math.sin(idx / 3) * 4 + (idx % 3)).toFixed(2)),
    timestamp: new Date(now - (20 - idx) * 2000).toISOString(),
  }))
}

export default function useDashboard() {
  const user = useMemo(() => getStoredUser(), [])
  const userMachineKey = useMemo(
    () => (Array.isArray(user?.machines) ? user.machines.join('|') : ''),
    [user?.machines],
  )
  const [components, setComponents] = useState([])

  const [summary, setSummary] = useState({
    active_machines: 4,
    open_alerts: 0,
    pending_interventions: 0,
    recent_alerts: [],
    pending_list: [],
  })
  const [machines, setMachines] = useState({})

  const visibleComponents = useMemo(() => {
    const list = components.length
      ? components
      : MACHINE_KEYS.map((machine) => ({ key: machine, name: machineLabel[machine], type: machine, enabled: true }))
    if (user?.role === 'technicien' && Array.isArray(user?.machines) && user.machines.length > 0) {
      return list.filter((component) => user.machines.includes(component.type))
    }
    return list
  }, [components, user?.role, userMachineKey])

  useEffect(() => {
    let mounted = true
    const loadComponents = async () => {
      try {
        const response = await api.get('/api/components')
        if (mounted) {
          const enabled = (response.data.components || []).filter((item) => item.enabled)
          setComponents(enabled)
        }
      } catch {
        if (mounted) {
          setComponents(MACHINE_KEYS.map((machine) => ({ key: machine, name: machineLabel[machine], type: machine })))
        }
      }
    }
    loadComponents()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const seed = createSeedSparkline()
    setMachines((prev) => {
      const next = { ...prev }
      visibleComponents.forEach((component) => {
        if (!next[component.key]) {
          next[component.key] = {
            key: component.key,
            type: component.type,
            label: component.name,
            anomalyScore: 20,
            sparkline: [...seed],
          }
        } else {
          next[component.key] = { ...next[component.key], label: component.name, type: component.type }
        }
      })
      return next
    })
  }, [visibleComponents])

  useEffect(() => {
    let isMounted = true

    const fetchSummary = async () => {
      try {
        const { data } = await api.get('/api/dashboard/summary')
        if (isMounted) {
          setSummary((prev) => ({
            ...prev,
            ...data,
            recent_alerts: (data.recent_alerts || []).slice(0, 5),
            pending_list: (data.pending_list || []).slice(0, 5),
          }))
        }
      } catch {
        // Silent fail: dashboard keeps last known values.
      }
    }

    fetchSummary()
    const intervalId = setInterval(fetchSummary, 30000)

    const socket = io('http://localhost:5000', { transports: ['websocket', 'polling'] })

    socket.on('alert:new', (alert) => {
      localStorage.setItem('hasNewAlerts', 'true')
      setSummary((prev) => ({
        ...prev,
        open_alerts: (prev.open_alerts || 0) + 1,
        recent_alerts: [alert, ...(prev.recent_alerts || [])].slice(0, 5),
      }))
    })

    socket.on('sensor:data', (prediction) => {
      const machine = prediction?.machine
      const score = Number(prediction?.defect_score ?? prediction?.anomaly_score ?? 0)
      if (!MACHINE_KEYS.includes(machine)) return
      setMachines((prev) => {
        const next = { ...prev }
        let changed = false
        visibleComponents.forEach((component) => {
          if (component.type !== machine) return
          const current = next[component.key]
          if (!current) return
          const nextPoint = {
            idx: Date.now(),
            value: Number((score * 100).toFixed(2)),
            timestamp: prediction?.timestamp || new Date().toISOString(),
          }
          next[component.key] = {
            ...current,
            anomalyScore: Number((score * 100).toFixed(2)),
            sparkline: [...current.sparkline.slice(-19), nextPoint],
          }
          changed = true
        })
        return changed ? next : prev
      })
    })

    return () => {
      isMounted = false
      clearInterval(intervalId)
      socket.disconnect()
    }
  }, [visibleComponents])

  const machineCards = useMemo(
    () => visibleComponents.map((component) => machines[component.key]).filter(Boolean),
    [machines, visibleComponents],
  )

  return {
    summary: {
      ...summary,
      active_machines: visibleComponents.length || summary.active_machines,
    },
    machineCards,
  }
}

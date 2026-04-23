import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { getPlants, updatePlant } from '../services/authService'

function SuperAdminPlantsPage() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState(null)

  const fetchPlants = async () => {
    setLoading(true)
    try {
      const response = await getPlants()
      setRows(response.data?.plants || [])
    } catch (error) {
      toast.error(error.response?.data?.error || 'Impossible de charger les usines')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPlants()
  }, [])

  const onInlineChange = (id, field, value) => {
    setRows((prev) => prev.map((item) => (item.id === id ? { ...item, [field]: value } : item)))
  }

  const onSave = async (row) => {
    setSavingId(row.id)
    try {
      const payload = {
        name: row.name,
        status: row.status,
        industry: row.industry,
        location: row.location,
        contact_name: row.contact_name,
        contact_email: row.contact_email,
        contact_phone: row.contact_phone,
        description: row.description,
      }
      const response = await updatePlant(row.id, payload)
      const updated = response.data?.plant
      setRows((prev) => prev.map((item) => (item.id === row.id ? { ...item, ...updated } : item)))
      toast.success('Profil usine mis a jour')
    } catch (error) {
      toast.error(error.response?.data?.error || 'Echec mise a jour usine')
    } finally {
      setSavingId(null)
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
      <h3 className="text-lg font-semibold text-slate-800">Profils des usines</h3>
      {loading && <p className="text-slate-500">Chargement...</p>}

      {!loading && (
        <div className="space-y-4">
          {rows.map((row) => (
            <div key={row.id} className="rounded-xl border border-slate-200 p-4 space-y-3">
              <div className="grid md:grid-cols-4 gap-3">
                <input className="rounded-lg border border-slate-300 px-3 py-2" value={row.name || ''} onChange={(e) => onInlineChange(row.id, 'name', e.target.value)} placeholder="Nom usine" />
                <input className="rounded-lg border border-slate-300 px-3 py-2 bg-slate-50" value={row.code || ''} disabled />
                <select className="rounded-lg border border-slate-300 px-3 py-2" value={row.status || 'active'} onChange={(e) => onInlineChange(row.id, 'status', e.target.value)}>
                  <option value="active">active</option>
                  <option value="inactive">inactive</option>
                </select>
                <input className="rounded-lg border border-slate-300 px-3 py-2" value={row.industry || ''} onChange={(e) => onInlineChange(row.id, 'industry', e.target.value)} placeholder="Secteur" />
                <input className="rounded-lg border border-slate-300 px-3 py-2" value={row.location || ''} onChange={(e) => onInlineChange(row.id, 'location', e.target.value)} placeholder="Localisation" />
                <input className="rounded-lg border border-slate-300 px-3 py-2" value={row.contact_name || ''} onChange={(e) => onInlineChange(row.id, 'contact_name', e.target.value)} placeholder="Nom contact" />
                <input className="rounded-lg border border-slate-300 px-3 py-2" value={row.contact_email || ''} onChange={(e) => onInlineChange(row.id, 'contact_email', e.target.value)} placeholder="Email contact" />
                <input className="rounded-lg border border-slate-300 px-3 py-2" value={row.contact_phone || ''} onChange={(e) => onInlineChange(row.id, 'contact_phone', e.target.value)} placeholder="Telephone contact" />
              </div>
              <textarea className="w-full rounded-lg border border-slate-300 px-3 py-2 min-h-20" value={row.description || ''} onChange={(e) => onInlineChange(row.id, 'description', e.target.value)} placeholder="Description usine" />
              <button
                type="button"
                onClick={() => onSave(row)}
                disabled={savingId === row.id}
                className="rounded bg-[#16a34a] px-3 py-2 text-sm text-white hover:bg-green-700 disabled:opacity-60"
              >
                {savingId === row.id ? 'Enregistrement...' : 'Enregistrer'}
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}

export default SuperAdminPlantsPage

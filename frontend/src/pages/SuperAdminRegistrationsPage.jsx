import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { getRegistrations, reviewRegistration } from '../services/authService'

function SuperAdminRegistrationsPage() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [reviewingId, setReviewingId] = useState(null)

  const fetchRows = async () => {
    setLoading(true)
    try {
      const response = await getRegistrations({ status: 'pending' })
      setRows(response.data?.registrations || [])
    } catch (error) {
      toast.error(error.response?.data?.error || 'Impossible de charger les inscriptions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRows()
  }, [])

  const onReview = async (id, action) => {
    setReviewingId(id)
    try {
      await reviewRegistration(id, { action })
      toast.success(action === 'approve' ? 'Inscription approuvee' : 'Inscription rejetee')
      setRows((prev) => prev.filter((item) => item.id !== id))
    } catch (error) {
      toast.error(error.response?.data?.error || 'Echec traitement inscription')
    } finally {
      setReviewingId(null)
    }
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 space-y-4">
      <h3 className="text-lg font-semibold text-slate-800">Validation inscriptions usines</h3>

      {loading && <p className="text-slate-500">Chargement...</p>}
      {!loading && rows.length === 0 && <p className="text-slate-500">Aucune inscription en attente.</p>}

      {!loading && rows.length > 0 && (
        <div className="overflow-auto">
          <table className="w-full min-w-[980px] text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-200">
                <th className="py-2">Usine</th>
                <th className="py-2">Code</th>
                <th className="py-2">Contact</th>
                <th className="py-2">Admin</th>
                <th className="py-2">Superviseur</th>
                <th className="py-2">Technicien</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-b border-slate-100">
                  <td className="py-2 font-medium text-slate-800">{row.plant_name}</td>
                  <td className="py-2 text-slate-700">{row.plant_code}</td>
                  <td className="py-2 text-slate-700">
                    {row.contact_name}
                    <br />
                    <span className="text-xs text-slate-500">{row.contact_email}</span>
                  </td>
                  <td className="py-2 text-slate-700">{row.payload?.users?.admin?.email || '-'}</td>
                  <td className="py-2 text-slate-700">{row.payload?.users?.superviseur?.email || '-'}</td>
                  <td className="py-2 text-slate-700">{row.payload?.users?.technicien?.email || '-'}</td>
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => onReview(row.id, 'approve')}
                        disabled={reviewingId === row.id}
                        className="rounded bg-[#16a34a] px-3 py-1 text-xs text-white hover:bg-green-700 disabled:opacity-60"
                      >
                        Approuver
                      </button>
                      <button
                        type="button"
                        onClick={() => onReview(row.id, 'reject')}
                        disabled={reviewingId === row.id}
                        className="rounded bg-red-600 px-3 py-1 text-xs text-white hover:bg-red-700 disabled:opacity-60"
                      >
                        Rejeter
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default SuperAdminRegistrationsPage

import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { Link } from 'react-router-dom'
import { registerPlant } from '../services/authService'

function PlantRegistrationPage() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm()

  const onSubmit = async (values) => {
    const optionalAccounts = [
      {
        label: 'superviseur',
        name: values.supervisor_name,
        email: values.supervisor_email,
        password: values.supervisor_password,
      },
      {
        label: 'technicien',
        name: values.technician_name,
        email: values.technician_email,
        password: values.technician_password,
      },
    ]

    for (const account of optionalAccounts) {
      const filled = [account.name, account.email, account.password].filter((v) => (v || '').trim() !== '').length
      if (filled > 0 && filled < 3) {
        toast.error(`Compte ${account.label}: renseigner nom + email + mot de passe, ou laisser vide.`)
        return
      }
    }

    const payload = {
      plant: {
        name: values.plant_name,
        code: values.plant_code.toLowerCase(),
        contact_name: values.contact_name,
        contact_email: values.contact_email.toLowerCase(),
      },
      users: {
        admin: {
          name: values.admin_name,
          email: values.admin_email.toLowerCase(),
          password: values.admin_password,
        },
      },
    }

    if (values.supervisor_name || values.supervisor_email || values.supervisor_password) {
      payload.users.superviseur = {
        name: values.supervisor_name || '',
        email: (values.supervisor_email || '').toLowerCase(),
        password: values.supervisor_password || '',
      }
    }
    if (values.technician_name || values.technician_email || values.technician_password) {
      payload.users.technicien = {
        name: values.technician_name || '',
        email: (values.technician_email || '').toLowerCase(),
        password: values.technician_password || '',
        machines: ['moteur', 'pompe', 'compresseur', 'echangeur'],
      }
    }

    try {
      await registerPlant(payload)
      toast.success("Inscription envoyee. En attente de validation du superadmin.")
      reset()
    } catch (error) {
      toast.error(error.response?.data?.error || "Impossible d'envoyer l'inscription")
    }
  }

  return (
    <div className="min-h-screen bg-slate-100 py-10 px-4">
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-slate-800">Inscription d'une usine</h1>
          <Link to="/login" className="rounded-lg bg-white px-3 py-2 text-sm text-slate-700 border border-slate-200">
            Retour connexion
          </Link>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="rounded-2xl bg-white p-6 shadow-sm border border-slate-200 space-y-6">
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-700 uppercase">Informations usine</h2>
            <div className="grid md:grid-cols-2 gap-3">
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Nom usine" {...register('plant_name', { required: true })} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Code usine (ex: usine-tunis)" {...register('plant_code', { required: true })} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Nom contact" {...register('contact_name', { required: true })} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Email contact" type="email" {...register('contact_email', { required: true })} />
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-700 uppercase">Compte administrateur</h2>
            <div className="grid md:grid-cols-3 gap-3">
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Nom admin" {...register('admin_name', { required: true })} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Email admin" type="email" {...register('admin_email', { required: true })} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Mot de passe admin" type="password" {...register('admin_password', { required: true, minLength: 8 })} />
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-700 uppercase">Compte superviseur</h2>
            <p className="text-xs text-slate-500">Optionnel</p>
            <div className="grid md:grid-cols-3 gap-3">
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Nom superviseur" {...register('supervisor_name')} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Email superviseur" type="email" {...register('supervisor_email')} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Mot de passe superviseur" type="password" {...register('supervisor_password')} />
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-700 uppercase">Compte technicien</h2>
            <p className="text-xs text-slate-500">Optionnel</p>
            <div className="grid md:grid-cols-3 gap-3">
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Nom technicien" {...register('technician_name')} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Email technicien" type="email" {...register('technician_email')} />
              <input className="rounded-lg border border-slate-300 px-3 py-2" placeholder="Mot de passe technicien" type="password" {...register('technician_password')} />
            </div>
          </section>

          {Object.keys(errors).length > 0 && (
            <p className="text-sm text-red-600">
              Champs obligatoires: usine + contact + compte admin (mot de passe min 8).
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg bg-[#16a34a] px-4 py-2 text-white font-medium hover:bg-green-700 disabled:opacity-70"
          >
            {isSubmitting ? "Envoi..." : "Envoyer l'inscription"}
          </button>
        </form>
      </div>
    </div>
  )
}

export default PlantRegistrationPage

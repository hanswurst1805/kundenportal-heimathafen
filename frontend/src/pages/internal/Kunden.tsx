import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, getRole } from '../../api/client'
import { Plus } from 'lucide-react'

export default function Kunden() {
  const queryClient = useQueryClient()
  const isAdmin = getRole() === 'admin'
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [kundennummer, setKundennummer] = useState('')
  const [name, setName] = useState('')
  const [contactEmail, setContactEmail] = useState('')

  const { data: kunden, isLoading } = useQuery({ queryKey: ['intern', 'kunden'], queryFn: api.intern.kunden.list })
  // /intern/users ist admin-only -> Zuordnungs-Anzeige nur fuer Admins laden
  const { data: users } = useQuery({ queryKey: ['intern', 'users'], queryFn: api.intern.users.list, enabled: isAdmin })

  const create = useMutation({
    mutationFn: () => api.intern.kunden.create({ kundennummer, name, contact_email: contactEmail || undefined }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intern', 'kunden'] })
      setKundennummer('')
      setName('')
      setContactEmail('')
      setShowForm(false)
    },
    onError: (e: Error) => setError(e.message),
  })

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => api.intern.kunden.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'kunden'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">Kunden</h1>
        <button
          onClick={() => setShowForm(s => !s)}
          className="flex items-center gap-1 bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium px-3 py-1.5 rounded-lg"
        >
          <Plus size={14} /> Neuer Kunde
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {showForm && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 grid grid-cols-3 gap-3">
          <input
            value={kundennummer}
            onChange={e => setKundennummer(e.target.value)}
            placeholder="Kundennummer"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Name"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <input
            value={contactEmail}
            onChange={e => setContactEmail(e.target.value)}
            placeholder="Kontakt-E-Mail"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <div className="col-span-3">
            <button
              onClick={() => { setError(''); create.mutate() }}
              disabled={!kundennummer || !name || create.isPending}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Anlegen
            </button>
          </div>
        </div>
      )}

      {isLoading || !kunden ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : kunden.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Kunden vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {kunden.map(k => (
            <div key={k.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm text-white">{k.kundennummer} – {k.name}</p>
                {k.contact_email && <p className="text-xs text-slate-500 mt-0.5">{k.contact_email}</p>}
                {isAdmin && (() => {
                  const zugeordnet = users?.filter(u => u.customer_id === k.id) ?? []
                  return (
                    <p className="text-xs text-slate-500 mt-0.5">
                      Benutzer:{' '}
                      {zugeordnet.length === 0 ? (
                        <span className="text-slate-600">keine zugeordnet</span>
                      ) : (
                        <span className="text-slate-400">{zugeordnet.map(u => u.username).join(', ')}</span>
                      )}
                    </p>
                  )
                })()}
              </div>
              <button
                onClick={() => toggleActive.mutate({ id: k.id, is_active: !k.is_active })}
                className={`text-xs font-medium px-3 py-1.5 rounded-lg ${k.is_active ? 'bg-emerald-900 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}
              >
                {k.is_active ? 'Aktiv' : 'Inaktiv'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

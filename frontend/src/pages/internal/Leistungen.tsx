import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import { Plus } from 'lucide-react'

export default function Leistungen() {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [leistungsId, setLeistungsId] = useState('')
  const [name, setName] = useState('')
  const [preis, setPreis] = useState('')
  const [avvErforderlich, setAvvErforderlich] = useState(false)

  const { data: leistungen, isLoading } = useQuery({ queryKey: ['intern', 'leistungen'], queryFn: api.intern.leistungen.list })

  const create = useMutation({
    mutationFn: () => api.intern.leistungen.create({ leistungs_id: leistungsId, name, preis, avv_erforderlich: avvErforderlich }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intern', 'leistungen'] })
      setLeistungsId('')
      setName('')
      setPreis('')
      setAvvErforderlich(false)
      setShowForm(false)
    },
    onError: (e: Error) => setError(e.message),
  })

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => api.intern.leistungen.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'leistungen'] }),
    onError: (e: Error) => setError(e.message),
  })

  const toggleAvv = useMutation({
    mutationFn: ({ id, avv_erforderlich }: { id: string; avv_erforderlich: boolean }) => api.intern.leistungen.update(id, { avv_erforderlich }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'leistungen'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">Katalogpflege</h1>
        <button
          onClick={() => setShowForm(s => !s)}
          className="flex items-center gap-1 bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium px-3 py-1.5 rounded-lg"
        >
          <Plus size={14} /> Neue Leistung
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {showForm && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 grid grid-cols-2 gap-3">
          <input
            value={leistungsId}
            onChange={e => setLeistungsId(e.target.value)}
            placeholder="Leistungs-ID"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <input
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Name"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <input
            value={preis}
            onChange={e => setPreis(e.target.value)}
            placeholder="Preis"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input type="checkbox" checked={avvErforderlich} onChange={e => setAvvErforderlich(e.target.checked)} />
            AVV erforderlich
          </label>
          <div className="col-span-2">
            <button
              onClick={() => { setError(''); create.mutate() }}
              disabled={!leistungsId || !name || !preis || create.isPending}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Anlegen
            </button>
          </div>
        </div>
      )}

      {isLoading || !leistungen ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : leistungen.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Leistungen vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {leistungen.map(l => (
            <div key={l.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm text-white">{l.leistungs_id} – {l.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{l.preis} € {l.preiseinheit}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => toggleAvv.mutate({ id: l.id, avv_erforderlich: !l.avv_erforderlich })}
                  className={`text-xs font-medium px-3 py-1.5 rounded-lg ${l.avv_erforderlich ? 'bg-amber-900 text-amber-300' : 'bg-slate-800 text-slate-400'}`}
                >
                  AVV {l.avv_erforderlich ? 'erforderlich' : 'nicht erforderlich'}
                </button>
                <button
                  onClick={() => toggleActive.mutate({ id: l.id, is_active: !l.is_active })}
                  className={`text-xs font-medium px-3 py-1.5 rounded-lg ${l.is_active ? 'bg-emerald-900 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}
                >
                  {l.is_active ? 'Aktiv' : 'Inaktiv'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

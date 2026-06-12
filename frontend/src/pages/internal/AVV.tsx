import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, getRole } from '../../api/client'
import { formatDate } from '../../lib/format'
import { AVV_STATUS_LABELS } from '../../lib/statuscodes'
import { Plus } from 'lucide-react'

export default function AVV() {
  const queryClient = useQueryClient()
  const isAdmin = getRole() === 'admin'
  const [error, setError] = useState('')

  const { data: avvs, isLoading } = useQuery({ queryKey: ['intern', 'avv'], queryFn: api.intern.avv.list })
  const { data: vorlagen } = useQuery({
    queryKey: ['intern', 'avv-vorlagen'],
    queryFn: api.intern.avv.vorlagen.list,
    enabled: isAdmin,
  })

  const [name, setName] = useState('')
  const [version, setVersion] = useState('1.0')

  const createVorlage = useMutation({
    mutationFn: () => api.intern.avv.vorlagen.create({ name, version }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intern', 'avv-vorlagen'] })
      setName('')
    },
    onError: (e: Error) => setError(e.message),
  })

  const toggleVorlage = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      api.intern.avv.vorlagen.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'avv-vorlagen'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">Auftragsverarbeitungsverträge (AVV)</h1>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Vorgänge</h2>
        {isLoading || !avvs ? (
          <p className="text-sm text-slate-500">Lade…</p>
        ) : avvs.length === 0 ? (
          <p className="text-sm text-slate-500">Keine AVV-Vorgänge vorhanden.</p>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
            {avvs.map(avv => (
              <div key={avv.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="text-sm text-white">AVV {avv.version ?? ''} – {avv.bezugstyp} #{avv.bezugs_id.slice(0, 8)}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Kunde #{avv.customer_id.slice(0, 8)}
                    {avv.abschlussdatum && ` · abgeschlossen am ${formatDate(avv.abschlussdatum)}`}
                  </p>
                </div>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-200">
                  {AVV_STATUS_LABELS[avv.status] ?? avv.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {isAdmin && (
        <section className="space-y-3">
          <h2 className="text-sm font-medium text-slate-300">AVV-Vorlagen</h2>
          {vorlagen && vorlagen.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
              {vorlagen.map(v => (
                <div key={v.id} className="flex items-center justify-between px-5 py-3">
                  <div>
                    <p className="text-sm text-white">{v.name}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Version {v.version}</p>
                  </div>
                  <button
                    onClick={() => toggleVorlage.mutate({ id: v.id, is_active: !v.is_active })}
                    className={`text-xs font-medium px-3 py-1.5 rounded-lg ${v.is_active ? 'bg-emerald-900 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}
                  >
                    {v.is_active ? 'Aktiv' : 'Inaktiv'}
                  </button>
                </div>
              ))}
            </div>
          )}
          <div className="flex items-center gap-2">
            <input
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Name der Vorlage"
              className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            />
            <input
              value={version}
              onChange={e => setVersion(e.target.value)}
              placeholder="Version"
              className="w-24 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            />
            <button
              onClick={() => { setError(''); createVorlage.mutate() }}
              disabled={!name || createVorlage.isPending}
              className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-sm font-medium px-3 py-1.5 rounded-lg"
            >
              <Plus size={14} /> Anlegen
            </button>
          </div>
        </section>
      )}
    </div>
  )
}

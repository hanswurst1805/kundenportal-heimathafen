import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import { formatDateTime } from '../../lib/format'

const PRIORITAETEN = ['niedrig', 'mittel', 'hoch']

export default function Anfragen() {
  const queryClient = useQueryClient()
  const { data: anfragen, isLoading } = useQuery({
    queryKey: ['portal', 'anfragen'],
    queryFn: api.portal.anfragen.list,
  })

  const [thema, setThema] = useState('')
  const [beschreibung, setBeschreibung] = useState('')
  const [fachbereich, setFachbereich] = useState('')
  const [prioritaet, setPrioritaet] = useState('mittel')
  const [error, setError] = useState('')

  const create = useMutation({
    mutationFn: () =>
      api.portal.anfragen.create({
        thema,
        beschreibung: beschreibung || undefined,
        fachbereich: fachbereich || undefined,
        prioritaet,
      }),
    onSuccess: async () => {
      setThema('')
      setBeschreibung('')
      setFachbereich('')
      setPrioritaet('mittel')
      await queryClient.invalidateQueries({ queryKey: ['portal', 'anfragen'] })
    },
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">Anfragen</h1>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Neue Anfrage</h2>
        <form
          onSubmit={e => { e.preventDefault(); setError(''); create.mutate() }}
          className="space-y-3 max-w-lg"
        >
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Thema</label>
            <input
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
              value={thema}
              onChange={e => setThema(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Beschreibung</label>
            <textarea
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
              rows={3}
              value={beschreibung}
              onChange={e => setBeschreibung(e.target.value)}
            />
          </div>
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="block text-xs text-slate-400 mb-1.5">Fachbereich</label>
              <input
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
                value={fachbereich}
                onChange={e => setFachbereich(e.target.value)}
              />
            </div>
            <div className="flex-1">
              <label className="block text-xs text-slate-400 mb-1.5">Priorität</label>
              <select
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
                value={prioritaet}
                onChange={e => setPrioritaet(e.target.value)}
              >
                {PRIORITAETEN.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit"
            disabled={!thema || create.isPending}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
          >
            Anfrage senden
          </button>
        </form>
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Meine Anfragen</h2>
        {isLoading || !anfragen ? (
          <p className="text-sm text-slate-500">Lade…</p>
        ) : anfragen.length === 0 ? (
          <p className="text-sm text-slate-500">Noch keine Anfragen.</p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {anfragen.map(a => (
              <li key={a.id} className="py-3 flex items-start justify-between gap-4 text-sm">
                <div>
                  <p className="text-slate-200 font-medium">{a.anfrage_nr} – {a.thema}</p>
                  {a.beschreibung && <p className="text-slate-500 mt-0.5">{a.beschreibung}</p>}
                  <p className="text-xs text-slate-600 mt-1">{formatDateTime(a.created_at)}</p>
                </div>
                <StatusBadge status={a.status_kunde} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

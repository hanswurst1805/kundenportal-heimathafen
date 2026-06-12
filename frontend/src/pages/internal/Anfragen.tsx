import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, type AnfrageIntern } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import { formatDateTime } from '../../lib/format'
import { KUNDENSTATUS, KUNDENSTATUS_LABELS, INTERNE_ZWISCHENSCHRITTE, PRIORITAET_OPTIONS } from '../../lib/statuscodes'

function AnfrageRow({ anfrage }: { anfrage: AnfrageIntern }) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [fachbereich, setFachbereich] = useState(anfrage.fachbereich ?? '')
  const [prioritaet, setPrioritaet] = useState(anfrage.prioritaet)
  const [statusIntern, setStatusIntern] = useState(anfrage.status_intern ?? '')
  const [statusKunde, setStatusKunde] = useState(anfrage.status_kunde)
  const [error, setError] = useState('')

  const update = useMutation({
    mutationFn: () =>
      api.intern.anfragen.update(anfrage.id, {
        fachbereich: fachbereich || undefined,
        prioritaet,
        status_intern: statusIntern || undefined,
        status_kunde: statusKunde,
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'anfragen'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
      <div className="flex items-center justify-between cursor-pointer" onClick={() => setOpen(o => !o)}>
        <div>
          <p className="text-sm font-medium text-white">{anfrage.anfrage_nr} – {anfrage.thema}</p>
          <p className="text-xs text-slate-500 mt-0.5">{formatDateTime(anfrage.created_at)}</p>
        </div>
        <StatusBadge status={anfrage.status_kunde} />
      </div>

      {open && (
        <div className="space-y-3 pt-3 border-t border-slate-800">
          {anfrage.beschreibung && <p className="text-sm text-slate-300">{anfrage.beschreibung}</p>}

          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <label className="block text-xs text-slate-500 mb-1">Fachbereich</label>
              <input
                value={fachbereich}
                onChange={e => setFachbereich(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Priorität</label>
              <select
                value={prioritaet}
                onChange={e => setPrioritaet(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              >
                {PRIORITAET_OPTIONS.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Interner Status</label>
              <select
                value={statusIntern}
                onChange={e => setStatusIntern(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              >
                <option value="">–</option>
                {INTERNE_ZWISCHENSCHRITTE.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-500 mb-1">Kundenstatus</label>
              <select
                value={statusKunde}
                onChange={e => setStatusKunde(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              >
                {KUNDENSTATUS.map(s => <option key={s} value={s}>{KUNDENSTATUS_LABELS[s]}</option>)}
              </select>
            </div>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <div className="flex items-center gap-2">
            <button
              onClick={() => { setError(''); update.mutate() }}
              disabled={update.isPending}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Speichern
            </button>
            {anfrage.angebot_id ? (
              <Link
                to="/intern/angebote"
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2 rounded-lg"
              >
                Angebot ansehen
              </Link>
            ) : (
              <Link
                to={`/intern/anfragen/${anfrage.id}/angebot`}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2 rounded-lg"
              >
                Angebot erstellen
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function Anfragen() {
  const { data: anfragen, isLoading } = useQuery({
    queryKey: ['intern', 'anfragen'],
    queryFn: api.intern.anfragen.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Anfragen</h1>

      {isLoading || !anfragen ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : anfragen.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Anfragen vorhanden.</p>
      ) : (
        <div className="space-y-3">
          {anfragen.map(a => <AnfrageRow key={a.id} anfrage={a} />)}
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import { KUNDENSTATUS, KUNDENSTATUS_LABELS } from '../../lib/statuscodes'

export default function Statusregeln() {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')

  const { data: regeln, isLoading } = useQuery({ queryKey: ['intern', 'statusregeln'], queryFn: api.intern.statusregeln.list })

  const update = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof api.intern.statusregeln.update>[1] }) =>
      api.intern.statusregeln.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'statusregeln'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Statusregeln</h1>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {isLoading || !regeln ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : regeln.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Statusregeln vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {regeln.map(r => (
            <div key={r.id} className="flex items-center justify-between px-5 py-3 gap-4">
              <div className="flex-1">
                <p className="text-sm text-white">{r.ereignis_typ}</p>
                {r.beschreibung && <p className="text-xs text-slate-500 mt-0.5">{r.beschreibung}</p>}
              </div>
              <select
                defaultValue={r.ziel_status_kunde}
                onBlur={e => update.mutate({ id: r.id, data: { ziel_status_kunde: e.target.value } })}
                className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              >
                {KUNDENSTATUS.map(s => (
                  <option key={s} value={s}>{KUNDENSTATUS_LABELS[s]}</option>
                ))}
              </select>
              <select
                defaultValue={r.benachrichtigung}
                onBlur={e => update.mutate({ id: r.id, data: { benachrichtigung: e.target.value } })}
                className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              >
                <option value="ja">Benachrichtigung: ja</option>
                <option value="optional">Benachrichtigung: optional</option>
                <option value="nein">Benachrichtigung: nein</option>
              </select>
              <label className="flex items-center gap-2 text-xs text-slate-400">
                <input
                  type="checkbox"
                  checked={r.aktiv}
                  onChange={e => update.mutate({ id: r.id, data: { aktiv: e.target.checked } })}
                />
                Aktiv
              </label>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

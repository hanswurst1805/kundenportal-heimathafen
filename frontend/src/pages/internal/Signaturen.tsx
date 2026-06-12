import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { SIGNATUR_STATUS_LABELS } from '../../lib/statuscodes'

export default function Signaturen() {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')

  const { data: vorgaenge, isLoading } = useQuery({
    queryKey: ['intern', 'signaturen'],
    queryFn: api.intern.signaturen.list,
  })

  const erinnerung = useMutation({
    mutationFn: (id: string) => api.intern.signaturen.erinnerung(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'signaturen'] }),
    onError: (e: Error) => setError(e.message),
  })

  const retry = useMutation({
    mutationFn: (id: string) => api.intern.signaturen.retry(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'signaturen'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Signaturen</h1>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {isLoading || !vorgaenge ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : vorgaenge.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Signaturvorgänge vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {vorgaenge.map(v => (
            <div key={v.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm text-white">{v.bezugstyp} #{v.bezugs_id.slice(0, 8)}</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {v.versandzeit && `Versendet ${formatDateTime(v.versandzeit)}`}
                  {v.erinnerung_gesendet_am && ` · Erinnert ${formatDateTime(v.erinnerung_gesendet_am)}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-200">
                  {SIGNATUR_STATUS_LABELS[v.status] ?? v.status}
                </span>
                {v.status === 'versendet' && (
                  <button
                    onClick={() => { setError(''); erinnerung.mutate(v.id) }}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    Erinnerung
                  </button>
                )}
                {(v.status === 'fehler' || v.status === 'abgelaufen') && (
                  <button
                    onClick={() => { setError(''); retry.mutate(v.id) }}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    Erneut versenden
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

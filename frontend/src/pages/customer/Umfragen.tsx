import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Umfrage } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { Star } from 'lucide-react'

function UmfrageCard({ umfrage }: { umfrage: Umfrage }) {
  const queryClient = useQueryClient()
  const [bewertung, setBewertung] = useState(0)
  const [kommentar, setKommentar] = useState('')
  const [error, setError] = useState('')

  const beantworten = useMutation({
    mutationFn: () => api.portal.umfragen.beantworten(umfrage.id, { bewertung, kommentar: kommentar || undefined }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portal', 'umfragen'] }),
    onError: (e: Error) => setError(e.message),
  })

  const beantwortet = umfrage.status === 'beantwortet'

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-white">Kundenzufriedenheitsabfrage</p>
        {umfrage.versandzeit && <span className="text-xs text-slate-500">Versendet {formatDateTime(umfrage.versandzeit)}</span>}
      </div>

      {beantwortet ? (
        <div className="space-y-1">
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map(n => (
              <Star key={n} size={16} className={n <= (umfrage.bewertung ?? 0) ? 'text-amber-400 fill-amber-400' : 'text-slate-600'} />
            ))}
          </div>
          {umfrage.kommentar && <p className="text-sm text-slate-300">{umfrage.kommentar}</p>}
          {umfrage.beantwortet_am && (
            <p className="text-xs text-slate-500">Beantwortet am {formatDateTime(umfrage.beantwortet_am)}</p>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map(n => (
              <button key={n} onClick={() => setBewertung(n)} type="button">
                <Star size={22} className={n <= bewertung ? 'text-amber-400 fill-amber-400' : 'text-slate-600'} />
              </button>
            ))}
          </div>
          <textarea
            value={kommentar}
            onChange={e => setKommentar(e.target.value)}
            placeholder="Kommentar (optional)"
            rows={3}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            onClick={() => { setError(''); beantworten.mutate() }}
            disabled={bewertung === 0 || beantworten.isPending}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
          >
            Absenden
          </button>
        </div>
      )}
    </div>
  )
}

export default function Umfragen() {
  const { data: umfragen, isLoading } = useQuery({
    queryKey: ['portal', 'umfragen'],
    queryFn: api.portal.umfragen.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Umfragen</h1>

      {isLoading || !umfragen ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : umfragen.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Umfragen vorhanden.</p>
      ) : (
        <div className="space-y-3">
          {umfragen.map(u => <UmfrageCard key={u.id} umfrage={u} />)}
        </div>
      )}
    </div>
  )
}

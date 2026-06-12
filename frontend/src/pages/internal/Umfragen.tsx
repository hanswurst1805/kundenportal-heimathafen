import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { Star } from 'lucide-react'

const STATUS_LABELS: Record<string, string> = {
  ausstehend: 'Ausstehend',
  versendet: 'Versendet',
  erinnert: 'Erinnert',
  beantwortet: 'Beantwortet',
}

export default function Umfragen() {
  const { data: umfragen, isLoading } = useQuery({
    queryKey: ['intern', 'umfragen'],
    queryFn: api.intern.umfragen.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Umfragen</h1>

      {isLoading || !umfragen ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : umfragen.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Umfragen vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {umfragen.map(u => (
            <div key={u.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm text-white">Kunde #{u.customer_id.slice(0, 8)} – Leistungsschein #{u.leistungsschein_id.slice(0, 8)}</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {u.versandzeit && `Versendet ${formatDateTime(u.versandzeit)}`}
                  {u.beantwortet_am && ` · Beantwortet ${formatDateTime(u.beantwortet_am)}`}
                </p>
                {u.kommentar && <p className="text-xs text-slate-400 mt-1">{u.kommentar}</p>}
              </div>
              <div className="flex items-center gap-2">
                {u.bewertung != null && (
                  <span className="flex items-center gap-1 text-amber-400 text-sm">
                    <Star size={14} className="fill-amber-400" /> {u.bewertung}
                  </span>
                )}
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-200">
                  {STATUS_LABELS[u.status] ?? u.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

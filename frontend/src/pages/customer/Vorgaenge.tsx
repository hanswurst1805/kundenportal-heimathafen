import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ChevronRight, PenLine } from 'lucide-react'
import { api } from '../../api/client'
import AblaufGrafik from '../../components/AblaufGrafik'
import { formatDate } from '../../lib/format'

const TYP_LABEL: Record<string, string> = { anfrage: 'Anfrage', bestellung: 'Bestellung' }

export default function Vorgaenge() {
  const { data: vorgaenge, isLoading } = useQuery({
    queryKey: ['portal', 'vorgaenge'],
    queryFn: api.portal.vorgaenge.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Meine Vorgänge</h1>
      <p className="text-sm text-slate-400">
        Jeder Vorgang von der Anfrage bzw. Bestellung bis zum Abschluss – mit aktuellem Stand.
      </p>

      {isLoading || !vorgaenge ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : vorgaenge.length === 0 ? (
        <p className="text-sm text-slate-500">Noch keine Vorgänge.</p>
      ) : (
        <div className="space-y-3">
          {vorgaenge.map(v => (
            <div key={`${v.typ}-${v.root_id}`} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
                      {TYP_LABEL[v.typ] ?? v.typ}
                    </span>
                    <span className="text-sm font-medium text-white">{v.referenz}</span>
                  </div>
                  <p className="text-sm text-slate-300 mt-0.5">{v.titel}</p>
                  <p className="text-xs text-slate-600 mt-0.5">{formatDate(v.created_at)}</p>
                </div>
                {v.offene_signatur_token && (
                  <Link
                    to={`/portal/signatur/${v.offene_signatur_token}`}
                    className="flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium px-3 py-1.5 rounded-lg shrink-0"
                  >
                    <PenLine size={13} /> Signieren
                  </Link>
                )}
              </div>

              <AblaufGrafik statusKunde={v.status_kunde} />

              <Link
                to={`/portal/vorgaenge/${v.typ}/${v.root_id}`}
                className="inline-flex items-center gap-1 text-sm text-sky-400 hover:text-sky-300"
              >
                Details ansehen <ChevronRight size={14} />
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

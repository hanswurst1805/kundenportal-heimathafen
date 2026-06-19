import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { PenLine, ChevronRight } from 'lucide-react'
import { api } from '../../api/client'
import AblaufGrafik from '../../components/AblaufGrafik'

const TYP_LABEL: Record<string, string> = { anfrage: 'Anfrage', bestellung: 'Bestellung' }
const ABGESCHLOSSEN = new Set(['abgeschlossen', 'storniert'])

export default function Dashboard() {
  const { data: vorgaenge, isLoading } = useQuery({
    queryKey: ['portal', 'vorgaenge'],
    queryFn: api.portal.vorgaenge.list,
  })
  const { data: offeneSignaturen } = useQuery({
    queryKey: ['portal', 'signaturen', 'offen'],
    queryFn: api.portal.signatur.listOffen,
  })

  if (isLoading || !vorgaenge) return <p className="text-slate-500 text-sm">Lade…</p>

  const laufend = vorgaenge.filter(v => !ABGESCHLOSSEN.has(v.status_kunde))

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">Übersicht</h1>

      {offeneSignaturen && offeneSignaturen.length > 0 && (
        <section className="bg-sky-950/40 border border-sky-800 rounded-xl p-6">
          <h2 className="text-sm font-medium text-sky-200 mb-3">Zu signieren</h2>
          <ul className="divide-y divide-sky-900/60">
            {offeneSignaturen.map(v => (
              <li key={v.id} className="py-2 flex items-center justify-between text-sm">
                <span className="text-slate-100">{v.titel}</span>
                {v.token && (
                  <Link
                    to={`/portal/signatur/${v.token}`}
                    className="flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    <PenLine size={13} /> Signieren
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Laufende Vorgänge</h2>
        {laufend.length === 0 ? (
          <p className="text-sm text-slate-500">Keine laufenden Vorgänge.</p>
        ) : (
          laufend.map(v => (
            <div key={`${v.typ}-${v.root_id}`} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <span className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
                    {TYP_LABEL[v.typ] ?? v.typ}
                  </span>
                  <span className="text-sm font-medium text-white ml-2">{v.referenz}</span>
                  <span className="text-slate-500 text-sm ml-2">{v.titel}</span>
                </div>
                <Link
                  to={`/portal/vorgaenge/${v.typ}/${v.root_id}`}
                  className="inline-flex items-center gap-1 text-sm text-sky-400 hover:text-sky-300 shrink-0"
                >
                  Details <ChevronRight size={14} />
                </Link>
              </div>
              <AblaufGrafik statusKunde={v.status_kunde} />
            </div>
          ))
        )}
      </section>
    </div>
  )
}

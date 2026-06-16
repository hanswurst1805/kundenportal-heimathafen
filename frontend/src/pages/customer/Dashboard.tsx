import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { PenLine } from 'lucide-react'
import { api } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import AblaufGrafik from '../../components/AblaufGrafik'
import { formatDate } from '../../lib/format'

export default function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ['portal', 'dashboard'], queryFn: api.portal.dashboard })
  const { data: offeneSignaturen } = useQuery({
    queryKey: ['portal', 'signaturen', 'offen'],
    queryFn: api.portal.signatur.listOffen,
  })

  if (isLoading || !data) return <p className="text-slate-500 text-sm">Lade…</p>

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

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Offene Bestellungen</h2>
        {data.offene_bestellungen.length === 0 ? (
          <p className="text-sm text-slate-500">Keine offenen Bestellungen.</p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {data.offene_bestellungen.map(b => (
              <li key={b.id} className="py-2 flex items-center justify-between text-sm">
                <span className="text-slate-200">{b.bestell_nr}</span>
                <StatusBadge status={b.status} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Offene Anfragen</h2>
        {data.offene_anfragen.length === 0 ? (
          <p className="text-sm text-slate-500">Keine offenen Anfragen.</p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {data.offene_anfragen.map(a => (
              <li key={a.id} className="py-3 space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-slate-200">{a.anfrage_nr}</span>
                    <span className="text-slate-500 ml-2">{a.thema}</span>
                  </div>
                  <StatusBadge status={a.status_kunde} />
                </div>
                <AblaufGrafik statusKunde={a.status_kunde} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Laufende Leistungsscheine</h2>
        {data.laufende_leistungsscheine.length === 0 ? (
          <p className="text-sm text-slate-500">Keine laufenden Leistungsscheine.</p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {data.laufende_leistungsscheine.map(ls => (
              <li key={ls.id} className="py-2 flex items-center justify-between text-sm">
                <Link to={`/portal/leistungsscheine/${ls.id}`} className="text-sky-400 hover:underline">
                  {ls.ls_nummer}
                </Link>
                <div className="flex items-center gap-3">
                  <span className="text-slate-500">{formatDate(ls.solltermin)}</span>
                  <StatusBadge status={ls.status_kunde} />
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

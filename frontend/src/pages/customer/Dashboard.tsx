import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import { formatDate } from '../../lib/format'

export default function Dashboard() {
  const { data, isLoading } = useQuery({ queryKey: ['portal', 'dashboard'], queryFn: api.portal.dashboard })

  if (isLoading || !data) return <p className="text-slate-500 text-sm">Lade…</p>

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">Übersicht</h1>

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
              <li key={a.id} className="py-2 flex items-center justify-between text-sm">
                <div>
                  <span className="text-slate-200">{a.anfrage_nr}</span>
                  <span className="text-slate-500 ml-2">{a.thema}</span>
                </div>
                <StatusBadge status={a.status_kunde} />
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

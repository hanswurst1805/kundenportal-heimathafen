import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import { formatDate } from '../../lib/format'

export default function Leistungsscheine() {
  const { data: scheine, isLoading } = useQuery({
    queryKey: ['portal', 'leistungsscheine'],
    queryFn: api.portal.leistungsscheine.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Leistungsscheine</h1>

      {isLoading || !scheine ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : scheine.length === 0 ? (
        <p className="text-sm text-slate-500">Noch keine Leistungsscheine.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {scheine.map(ls => (
            <Link
              key={ls.id}
              to={`/portal/leistungsscheine/${ls.id}`}
              className="flex items-center justify-between px-5 py-3 hover:bg-slate-800/50 transition-colors"
            >
              <div>
                <p className="text-sm text-white">{ls.ls_nummer}</p>
                {ls.scope_beschreibung && <p className="text-xs text-slate-500 mt-0.5">{ls.scope_beschreibung}</p>}
              </div>
              <div className="flex items-center gap-3">
                {ls.solltermin && <span className="text-xs text-slate-500">Solltermin {formatDate(ls.solltermin)}</span>}
                <StatusBadge status={ls.status_kunde} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

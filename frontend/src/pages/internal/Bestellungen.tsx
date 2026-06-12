import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import { formatDateTime } from '../../lib/format'

export default function Bestellungen() {
  const { data: bestellungen, isLoading } = useQuery({
    queryKey: ['intern', 'bestellungen'],
    queryFn: api.intern.bestellungen.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Bestellungen</h1>

      {isLoading || !bestellungen ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : bestellungen.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Bestellungen vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {bestellungen.map(b => (
            <div key={b.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm text-white">{b.bestell_nr}</p>
                <p className="text-xs text-slate-500 mt-0.5">Bestellt am {formatDateTime(b.bestelldatum)}</p>
              </div>
              <StatusBadge status={b.status} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

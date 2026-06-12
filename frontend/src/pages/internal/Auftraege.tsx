import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, type Auftrag } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import { formatDateTime } from '../../lib/format'
import { FileCheck2 } from 'lucide-react'

function AuftragRow({ auftrag }: { auftrag: Auftrag }) {
  const { data: bestaetigung } = useQuery({
    queryKey: ['intern', 'auftraege', auftrag.id, 'bestaetigung'],
    queryFn: () => api.intern.auftraege.getAuftragsbestaetigung(auftrag.id),
    retry: false,
    throwOnError: false,
  })

  return (
    <div className="flex items-center justify-between px-5 py-3">
      <div>
        <p className="text-sm text-white">{auftrag.auftragsnummer}</p>
        {auftrag.freigabedatum && (
          <p className="text-xs text-slate-500 mt-0.5">Freigegeben am {formatDateTime(auftrag.freigabedatum)}</p>
        )}
        {bestaetigung && (
          <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
            <FileCheck2 size={12} />
            {bestaetigung.kenntnisnahme_am
              ? `Zur Kenntnis genommen am ${formatDateTime(bestaetigung.kenntnisnahme_am)}`
              : 'Auftragsbestätigung liegt vor, noch nicht zur Kenntnis genommen'}
          </p>
        )}
      </div>
      <div className="flex items-center gap-3">
        <Link to={`/intern/leistungsscheine`} className="text-xs text-sky-500 hover:text-sky-400">
          Leistungsschein
        </Link>
        <StatusBadge status={auftrag.status} />
      </div>
    </div>
  )
}

export default function Auftraege() {
  const { data: auftraege, isLoading } = useQuery({
    queryKey: ['intern', 'auftraege'],
    queryFn: api.intern.auftraege.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Aufträge</h1>

      {isLoading || !auftraege ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : auftraege.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Aufträge vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {auftraege.map(a => <AuftragRow key={a.id} auftrag={a} />)}
        </div>
      )}
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { FileText } from 'lucide-react'

const TYP_LABELS: Record<string, string> = {
  angebot: 'Angebot',
  avv: 'AVV',
  auftragsbestaetigung: 'Auftragsbestätigung',
  leistungsschein: 'Leistungsschein',
  workshop_protokoll: 'Workshop-Protokoll',
  sonstiges: 'Sonstiges',
}

export default function Dokumente() {
  const { data: dokumente, isLoading } = useQuery({
    queryKey: ['portal', 'dokumente'],
    queryFn: api.portal.dokumente.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Dokumente</h1>

      {isLoading || !dokumente ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : dokumente.length === 0 ? (
        <p className="text-sm text-slate-500">Noch keine Dokumente.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {dokumente.map(d => (
            <div key={d.id} className="flex items-center justify-between px-5 py-3">
              <div className="flex items-center gap-3">
                <FileText size={16} className="text-slate-500" />
                <div>
                  <p className="text-sm text-white">{d.dateiname}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{TYP_LABELS[d.typ] ?? d.typ}{d.version > 1 ? ` · v${d.version}` : ''}</p>
                </div>
              </div>
              <span className="text-xs text-slate-500">{formatDateTime(d.created_at)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

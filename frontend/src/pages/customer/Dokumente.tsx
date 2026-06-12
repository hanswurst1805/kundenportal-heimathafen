import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { FileText, Download } from 'lucide-react'

const TYP_LABELS: Record<string, string> = {
  angebot: 'Angebot',
  avv: 'AVV',
  auftragsbestaetigung: 'Auftragsbestätigung',
  leistungsschein: 'Leistungsschein',
  workshop_protokoll: 'Workshop-Protokoll',
  signatur_dokument: 'Signiertes Dokument',
  sonstiges: 'Sonstiges',
}

export default function Dokumente() {
  const [error, setError] = useState('')
  const { data: dokumente, isLoading } = useQuery({
    queryKey: ['portal', 'dokumente'],
    queryFn: api.portal.dokumente.list,
  })

  async function download(id: string, dateiname: string) {
    setError('')
    try {
      await api.portal.dokumente.download(id, dateiname)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Download fehlgeschlagen')
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Dokumente</h1>

      {error && <p className="text-sm text-red-400">{error}</p>}

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
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-500">{formatDateTime(d.created_at)}</span>
                <button
                  onClick={() => download(d.id, d.dateiname)}
                  title="Herunterladen"
                  className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                >
                  <Download size={12} /> PDF
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

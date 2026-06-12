import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Auftrag } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import { formatDateTime } from '../../lib/format'
import { FileCheck2 } from 'lucide-react'

function AuftragCard({ auftrag }: { auftrag: Auftrag }) {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')

  const { data: bestaetigung } = useQuery({
    queryKey: ['portal', 'auftraege', auftrag.id, 'bestaetigung'],
    queryFn: () => api.portal.auftraege.getAuftragsbestaetigung(auftrag.id),
    retry: false,
    throwOnError: false,
  })

  const kenntnisnahme = useMutation({
    mutationFn: () => api.portal.auftraege.kenntnisnahme(auftrag.id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['portal', 'auftraege', auftrag.id, 'bestaetigung'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-medium text-white">{auftrag.auftragsnummer}</h2>
          {auftrag.freigabedatum && (
            <p className="text-xs text-slate-500 mt-0.5">Freigegeben am {formatDateTime(auftrag.freigabedatum)}</p>
          )}
        </div>
        <StatusBadge status={auftrag.status} />
      </div>

      {bestaetigung && (
        <div className="flex items-center justify-between pt-2 border-t border-slate-800">
          <div className="flex items-center gap-2 text-sm text-slate-300">
            <FileCheck2 size={14} />
            {bestaetigung.kenntnisnahme_am ? (
              <span>Auftragsbestätigung zur Kenntnis genommen am {formatDateTime(bestaetigung.kenntnisnahme_am)}</span>
            ) : (
              <span>Auftragsbestätigung liegt vor</span>
            )}
          </div>
          {!bestaetigung.kenntnisnahme_am && (
            <button
              onClick={() => { setError(''); kenntnisnahme.mutate() }}
              disabled={kenntnisnahme.isPending}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Zur Kenntnis nehmen
            </button>
          )}
        </div>
      )}

      {error && (
        <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">{error}</p>
      )}
    </div>
  )
}

export default function Auftraege() {
  const { data: auftraege, isLoading } = useQuery({
    queryKey: ['portal', 'auftraege'],
    queryFn: api.portal.auftraege.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Aufträge</h1>

      {isLoading || !auftraege ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : auftraege.length === 0 ? (
        <p className="text-sm text-slate-500">Noch keine Aufträge.</p>
      ) : (
        <div className="space-y-3">
          {auftraege.map(a => <AuftragCard key={a.id} auftrag={a} />)}
        </div>
      )}
    </div>
  )
}

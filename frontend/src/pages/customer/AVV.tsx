import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import { formatDate } from '../../lib/format'
import { ShieldCheck, ShieldAlert } from 'lucide-react'
import { AVV_STATUS_LABELS } from '../../lib/statuscodes'

export default function AVV() {
  const queryClient = useQueryClient()
  const { data: avvs, isLoading } = useQuery({ queryKey: ['portal', 'avv'], queryFn: api.portal.avv.list })
  const [error, setError] = useState('')

  const annehmen = useMutation({
    mutationFn: (id: string) => api.portal.avv.annehmen(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portal', 'avv'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Auftragsverarbeitungsverträge (AVV)</h1>

      {error && (
        <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">{error}</p>
      )}

      {isLoading || !avvs ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : avvs.length === 0 ? (
        <p className="text-sm text-slate-500">Keine AVV vorhanden.</p>
      ) : (
        <div className="space-y-3">
          {avvs.map(avv => (
            <div key={avv.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                {avv.status === 'abgeschlossen' ? (
                  <ShieldCheck size={18} className="text-emerald-400" />
                ) : (
                  <ShieldAlert size={18} className="text-amber-400" />
                )}
                <div>
                  <p className="text-sm text-white">
                    AVV {avv.version ?? ''} – {avv.bezugstyp} #{avv.bezugs_id.slice(0, 8)}
                  </p>
                  <p className="text-xs text-slate-500">
                    {AVV_STATUS_LABELS[avv.status] ?? avv.status}
                    {avv.abschlussdatum && ` · abgeschlossen am ${formatDate(avv.abschlussdatum)}`}
                  </p>
                </div>
              </div>
              {avv.status === 'ausstehend' && (
                <button
                  onClick={() => { setError(''); annehmen.mutate(avv.id) }}
                  disabled={annehmen.isPending}
                  className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
                >
                  AVV annehmen
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

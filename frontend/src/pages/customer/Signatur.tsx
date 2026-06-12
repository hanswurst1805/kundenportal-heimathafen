import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { FileSignature, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'

const BEZUG_LABELS: Record<string, string> = {
  angebot: 'Angebot',
  bestellung: 'Bestellung',
}

export default function Signatur() {
  const { token } = useParams<{ token: string }>()
  const queryClient = useQueryClient()
  const [error, setError] = useState('')

  const { data: vorgang, isLoading } = useQuery({
    queryKey: ['portal', 'signatur', token],
    queryFn: () => api.portal.signatur.get(token!),
    enabled: !!token,
  })

  const signieren = useMutation({
    mutationFn: () => api.portal.signatur.signieren(token!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portal', 'signatur', token] }),
    onError: (e: Error) => setError(e.message),
  })

  if (isLoading || !vorgang) return <p className="text-slate-500 text-sm">Lade…</p>

  const bezugLabel = BEZUG_LABELS[vorgang.bezugstyp] ?? vorgang.bezugstyp

  return (
    <div className="max-w-lg mx-auto mt-12 bg-slate-900 border border-slate-800 rounded-xl p-8 space-y-6 text-center">
      <div className="flex justify-center">
        <div className="w-12 h-12 rounded-full bg-sky-600/10 flex items-center justify-center">
          <FileSignature className="text-sky-500" size={24} />
        </div>
      </div>

      <div>
        <h1 className="text-lg font-semibold text-white">Digitale Signatur</h1>
        <p className="text-sm text-slate-400 mt-1">{bezugLabel}</p>
      </div>

      {vorgang.status === 'signiert' && (
        <div className="space-y-2">
          <CheckCircle2 className="text-emerald-500 mx-auto" size={32} />
          <p className="text-sm text-slate-300">Dokument wurde erfolgreich signiert.</p>
          {vorgang.signierzeit && <p className="text-xs text-slate-500">am {formatDateTime(vorgang.signierzeit)}</p>}
        </div>
      )}

      {vorgang.status === 'abgelehnt' && (
        <div className="space-y-2">
          <XCircle className="text-red-500 mx-auto" size={32} />
          <p className="text-sm text-slate-300">Diese Signatur wurde abgelehnt.</p>
        </div>
      )}

      {(vorgang.status === 'fehler' || vorgang.status === 'abgelaufen') && (
        <div className="space-y-2">
          <AlertTriangle className="text-amber-500 mx-auto" size={32} />
          <p className="text-sm text-slate-300">
            {vorgang.status === 'abgelaufen' ? 'Dieser Signaturlink ist abgelaufen.' : 'Bei der Signatur ist ein Fehler aufgetreten.'}
          </p>
        </div>
      )}

      {(vorgang.status === 'versendet' || vorgang.status === 'erstellt') && (
        <div className="space-y-4">
          <p className="text-sm text-slate-300">
            Bitte prüfen Sie das Dokument und bestätigen Sie die Signatur, um den Vorgang abzuschließen.
          </p>
          {error && (
            <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">{error}</p>
          )}
          <button
            onClick={() => { setError(''); signieren.mutate() }}
            disabled={signieren.isPending}
            className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2.5 rounded-lg"
          >
            Jetzt signieren
          </button>
        </div>
      )}
    </div>
  )
}

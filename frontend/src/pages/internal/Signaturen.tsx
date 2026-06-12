import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { SIGNATUR_STATUS_LABELS } from '../../lib/statuscodes'
import { Link2, Check, Download } from 'lucide-react'

export default function Signaturen() {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const { data: vorgaenge, isLoading } = useQuery({
    queryKey: ['intern', 'signaturen'],
    queryFn: api.intern.signaturen.list,
  })

  const erinnerung = useMutation({
    mutationFn: (id: string) => api.intern.signaturen.erinnerung(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'signaturen'] }),
    onError: (e: Error) => setError(e.message),
  })

  const retry = useMutation({
    mutationFn: (id: string) => api.intern.signaturen.retry(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'signaturen'] }),
    onError: (e: Error) => setError(e.message),
  })

  async function copyLink(id: string, token: string | null) {
    if (!token) return
    const url = `${window.location.origin}/portal/signatur/${token}`
    try {
      await navigator.clipboard.writeText(url)
      setCopiedId(id)
      setTimeout(() => setCopiedId(c => (c === id ? null : c)), 2000)
    } catch {
      setError('Link konnte nicht kopiert werden.')
    }
  }

  async function downloadBeleg(bezugstyp: string, bezugsId: string) {
    setError('')
    try {
      const docs = await api.intern.dokumente.list({ bezugstyp, bezugs_id: bezugsId })
      const beleg = docs.find(d => d.typ === 'signatur_dokument') ?? docs[0]
      if (!beleg) {
        setError('Kein signierter Beleg vorhanden.')
        return
      }
      await api.intern.dokumente.download(beleg.id, beleg.dateiname)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Download fehlgeschlagen')
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Signaturen</h1>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {isLoading || !vorgaenge ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : vorgaenge.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Signaturvorgänge vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {vorgaenge.map(v => (
            <div key={v.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm text-white">{v.bezugstyp} #{v.bezugs_id.slice(0, 8)}</p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {v.versandzeit && `Versendet ${formatDateTime(v.versandzeit)}`}
                  {v.signierzeit && ` · Signiert ${formatDateTime(v.signierzeit)}`}
                  {v.erinnerung_gesendet_am && ` · Erinnert ${formatDateTime(v.erinnerung_gesendet_am)}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-200">
                  {SIGNATUR_STATUS_LABELS[v.status] ?? v.status}
                </span>

                {(v.status === 'versendet' || v.status === 'erstellt') && v.token && (
                  <button
                    onClick={() => copyLink(v.id, v.token)}
                    title="Signatur-Link für den Kunden kopieren"
                    className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    {copiedId === v.id ? <Check size={12} /> : <Link2 size={12} />}
                    {copiedId === v.id ? 'Kopiert' : 'Link'}
                  </button>
                )}

                {v.status === 'versendet' && (
                  <button
                    onClick={() => { setError(''); erinnerung.mutate(v.id) }}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    Erinnerung
                  </button>
                )}

                {v.status === 'signiert' && v.anbieter === 'inhouse' && (
                  <button
                    onClick={() => downloadBeleg(v.bezugstyp, v.bezugs_id)}
                    title="Signierten Beleg herunterladen"
                    className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    <Download size={12} /> Beleg
                  </button>
                )}

                {(v.status === 'fehler' || v.status === 'abgelaufen') && (
                  <button
                    onClick={() => { setError(''); retry.mutate(v.id) }}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    Erneut versenden
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

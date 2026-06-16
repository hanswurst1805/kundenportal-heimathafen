import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import SignaturePad from 'signature_pad'
import { api } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { FileSignature, CheckCircle2, XCircle, AlertTriangle, Eraser } from 'lucide-react'

const BEZUG_LABELS: Record<string, string> = {
  angebot: 'Angebot',
  bestellung: 'Bestellung',
  avv: 'Auftragsverarbeitungsvertrag',
  auftragsbestaetigung: 'Auftragsbestätigung',
}

export default function Signatur() {
  const { token } = useParams<{ token: string }>()
  const queryClient = useQueryClient()
  const [error, setError] = useState('')
  const [name, setName] = useState('')

  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const padRef = useRef<SignaturePad | null>(null)

  const { data: vorgang, isLoading, isError } = useQuery({
    queryKey: ['portal', 'signatur', token],
    queryFn: () => api.portal.signatur.get(token!),
    enabled: !!token,
    retry: false,
  })

  const signieren = useMutation({
    mutationFn: (payload?: { signatur_bild?: string; unterzeichner_name?: string }) =>
      api.portal.signatur.signieren(token!, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portal', 'signatur', token] }),
    onError: (e: Error) => setError(e.message),
  })

  const signierbar = vorgang?.status === 'versendet' || vorgang?.status === 'erstellt'

  const { data: vorschauUrl } = useQuery({
    queryKey: ['portal', 'signatur', token, 'vorschau'],
    queryFn: () => api.portal.signatur.vorschauUrl(token!),
    enabled: !!token && signierbar,
    staleTime: Infinity,
  })

  // Object-URL freigeben, wenn die Vorschau wechselt / die Seite verlassen wird.
  useEffect(() => {
    return () => {
      if (vorschauUrl) URL.revokeObjectURL(vorschauUrl)
    }
  }, [vorschauUrl])

  useEffect(() => {
    if (!signierbar || !canvasRef.current) return
    const canvas = canvasRef.current
    const ratio = Math.max(window.devicePixelRatio || 1, 1)
    canvas.width = canvas.offsetWidth * ratio
    canvas.height = canvas.offsetHeight * ratio
    canvas.getContext('2d')?.scale(ratio, ratio)
    const pad = new SignaturePad(canvas, { penColor: '#0f172a' })
    padRef.current = pad
    return () => {
      pad.off()
      padRef.current = null
    }
  }, [signierbar])

  if (isError) {
    return (
      <div className="max-w-lg mx-auto mt-12 bg-slate-900 border border-slate-800 rounded-xl p-8 space-y-3 text-center">
        <AlertTriangle className="text-amber-500 mx-auto" size={32} />
        <p className="text-sm text-slate-300">
          Dieser Signaturvorgang ist nicht verfügbar.
        </p>
        <p className="text-xs text-slate-500">
          Der Link ist ungültig oder gehört zu einem anderen Konto. Bitte melden Sie sich mit dem
          richtigen Zugang an oder fordern Sie einen neuen Link an.
        </p>
      </div>
    )
  }

  if (isLoading || !vorgang) return <p className="text-slate-500 text-sm">Lade…</p>

  const bezugLabel = BEZUG_LABELS[vorgang.bezugstyp] ?? vorgang.bezugstyp

  function submit() {
    setError('')
    if (!padRef.current || padRef.current.isEmpty()) {
      setError('Bitte unterschreiben Sie im Feld.')
      return
    }
    if (!name.trim()) {
      setError('Bitte geben Sie Ihren Namen ein.')
      return
    }
    signieren.mutate({
      signatur_bild: padRef.current.toDataURL('image/png'),
      unterzeichner_name: name.trim(),
    })
  }

  return (
    <div className="max-w-2xl mx-auto mt-12 bg-slate-900 border border-slate-800 rounded-xl p-8 space-y-6 text-center">
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
          <p className="text-xs text-slate-500">
            Das signierte, versiegelte PDF finden Sie unter „Dokumente“.
          </p>
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

      {signierbar && (
        <div className="space-y-4">
          {vorschauUrl ? (
            <object data={vorschauUrl} type="application/pdf" className="w-full h-96 rounded-lg border border-slate-700 bg-white">
              <p className="text-xs text-slate-400 p-3">
                Vorschau kann nicht angezeigt werden.{' '}
                <a href={vorschauUrl} target="_blank" rel="noreferrer" className="text-sky-400 underline">
                  Dokument öffnen
                </a>
              </p>
            </object>
          ) : (
            <p className="text-xs text-slate-500">Dokumentvorschau wird geladen…</p>
          )}

          <p className="text-sm text-slate-300">
            Bitte prüfen Sie das Dokument und bestätigen Sie die Signatur, um den Vorgang abzuschließen.
          </p>

          <div className="space-y-3 text-left">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Name (Unterzeichner)</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Vor- und Nachname"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
              />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs text-slate-400">Unterschrift</label>
                <button
                  type="button"
                  onClick={() => padRef.current?.clear()}
                  className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200"
                >
                  <Eraser size={12} /> löschen
                </button>
              </div>
              <canvas
                ref={canvasRef}
                className="w-full h-40 rounded-lg bg-white touch-none cursor-crosshair"
              />
            </div>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">{error}</p>
          )}
          <button
            onClick={submit}
            disabled={signieren.isPending}
            className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2.5 rounded-lg"
          >
            Rechtsverbindlich signieren
          </button>
        </div>
      )}
    </div>
  )
}

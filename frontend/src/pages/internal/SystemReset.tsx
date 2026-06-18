import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Trash2 } from 'lucide-react'
import { api } from '../../api/client'

const BESTAETIGUNG = 'RESET'

export default function SystemReset() {
  const navigate = useNavigate()
  const [wort, setWort] = useState('')
  const [error, setError] = useState('')

  const reset = useMutation({
    mutationFn: () => api.intern.admin.reset(wort),
    onError: (e: Error) => setError(e.message),
    onSuccess: () => {
      // Alle Benutzer wurden gelöscht und der Admin neu angelegt – neu anmelden.
      setTimeout(() => {
        api.auth.logout()
        navigate('/login')
      }, 4000)
    },
  })

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold text-white">System zurücksetzen</h1>

      <div className="bg-red-950/40 border border-red-800 rounded-xl p-6 space-y-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={22} />
          <div className="space-y-2 text-sm">
            <p className="text-red-200 font-medium">
              Achtung: Diese Aktion löscht unwiderruflich alle Geschäftsdaten und Dateien.
            </p>
            <ul className="list-disc list-inside text-slate-300 space-y-1">
              <li>Alle Kunden, Benutzer, Anfragen, Angebote, Bestellungen, Aufträge, Leistungsscheine</li>
              <li>AVV, Signaturvorgänge, Umfragen, Ereignisse, Katalog</li>
              <li>Alle abgelegten Dateien (signierte PDFs und das Siegel-Zertifikat)</li>
            </ul>
            <p className="text-slate-400">
              Erhalten bleiben nur die Statusregeln (Automatisierung). Der Administrator wird neu
              angelegt – du wirst danach abgemeldet und musst dich neu anmelden (inkl. 2FA-Einrichtung).
            </p>
          </div>
        </div>

        {reset.isSuccess ? (
          <div className="text-sm text-emerald-300 bg-emerald-950/40 border border-emerald-800 rounded-lg px-3 py-2">
            System zurückgesetzt: {reset.data.geleerte_tabellen.length} Tabellen geleert,{' '}
            {reset.data.geloeschte_dateien} Dateien gelöscht. Du wirst abgemeldet…
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">
                Zum Bestätigen <span className="font-mono text-red-300">{BESTAETIGUNG}</span> eingeben
              </label>
              <input
                value={wort}
                onChange={e => setWort(e.target.value)}
                placeholder={BESTAETIGUNG}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono focus:outline-none focus:ring-2 focus:ring-red-600"
              />
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}

            <button
              onClick={() => { setError(''); reset.mutate() }}
              disabled={wort !== BESTAETIGUNG || reset.isPending}
              className="flex items-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-40 disabled:hover:bg-red-600 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              <Trash2 size={16} /> {reset.isPending ? 'Wird zurückgesetzt…' : 'Alles unwiderruflich löschen'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

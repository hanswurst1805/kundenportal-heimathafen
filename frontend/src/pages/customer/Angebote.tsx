import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api, type Angebot } from '../../api/client'
import { formatCurrency, formatDate } from '../../lib/format'

const STATUS_LABELS: Record<string, string> = {
  entwurf: 'Entwurf',
  bereitgestellt: 'Bereitgestellt',
  angenommen: 'Angenommen',
  abgelehnt: 'Abgelehnt',
}

function AngebotCard({ angebot }: { angebot: Angebot }) {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')

  const { data: vorgaenge } = useQuery({
    queryKey: ['portal', 'signatur', 'angebot', angebot.id],
    queryFn: () => api.portal.signatur.listByBezug('angebot', angebot.id),
    enabled: angebot.status === 'bereitgestellt',
  })

  const offenerVorgang = vorgaenge?.find(v => v.status === 'versendet')

  const ablehnen = useMutation({
    mutationFn: () => api.portal.angebote.ablehnen(angebot.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['portal', 'angebote'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-medium text-white">{angebot.angebotsnummer} – {angebot.titel}</h2>
          {angebot.gueltig_bis && (
            <p className="text-xs text-slate-500 mt-0.5">Gültig bis {formatDate(angebot.gueltig_bis)}</p>
          )}
        </div>
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-200">
          {STATUS_LABELS[angebot.status] ?? angebot.status}
        </span>
      </div>

      {angebot.positionen.length > 0 && (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-slate-500">
              <th className="pb-1">Position</th>
              <th className="pb-1 text-right">Menge</th>
              <th className="pb-1 text-right">Einzelpreis</th>
              <th className="pb-1 text-right">Gesamt</th>
            </tr>
          </thead>
          <tbody className="text-slate-300">
            {angebot.positionen.map(p => (
              <tr key={p.id} className="border-t border-slate-800">
                <td className="py-1">{p.bezeichnung}</td>
                <td className="py-1 text-right">{p.menge}</td>
                <td className="py-1 text-right">{formatCurrency(p.einzelpreis)}</td>
                <td className="py-1 text-right">{formatCurrency(p.gesamtpreis)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="flex items-center justify-between pt-2 border-t border-slate-800">
        <span className="text-sm font-medium text-white">Gesamt: {formatCurrency(angebot.gesamtpreis)}</span>
        {angebot.status === 'bereitgestellt' && (
          <div className="flex items-center gap-2">
            {offenerVorgang?.token && (
              <Link
                to={`/portal/signatur/${offenerVorgang.token}`}
                className="bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium px-4 py-2 rounded-lg"
              >
                Zur Signatur
              </Link>
            )}
            <button
              onClick={() => { setError(''); ablehnen.mutate() }}
              disabled={ablehnen.isPending}
              className="bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-sm font-medium px-4 py-2 rounded-lg"
            >
              Ablehnen
            </button>
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">{error}</p>
      )}
    </div>
  )
}

export default function Angebote() {
  const { data: angebote, isLoading } = useQuery({
    queryKey: ['portal', 'angebote'],
    queryFn: api.portal.angebote.list,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Angebote</h1>

      {isLoading || !angebote ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : angebote.length === 0 ? (
        <p className="text-sm text-slate-500">Noch keine Angebote.</p>
      ) : (
        <div className="space-y-4">
          {angebote.map(a => <AngebotCard key={a.id} angebot={a} />)}
        </div>
      )}
    </div>
  )
}

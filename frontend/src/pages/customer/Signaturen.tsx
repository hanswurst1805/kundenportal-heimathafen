import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileSignature, PenLine } from 'lucide-react'
import { api } from '../../api/client'

export default function Signaturen() {
  const { data: vorgaenge, isLoading } = useQuery({
    queryKey: ['portal', 'signaturen', 'offen'],
    queryFn: api.portal.signatur.listOffen,
  })

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Zu signieren</h1>

      {isLoading || !vorgaenge ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : vorgaenge.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center space-y-2">
          <FileSignature className="text-slate-600 mx-auto" size={28} />
          <p className="text-sm text-slate-500">Aktuell liegt nichts zur Signatur vor.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {vorgaenge.map(v => (
            <div
              key={v.id}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-sky-600/10 flex items-center justify-center shrink-0">
                  <FileSignature className="text-sky-500" size={18} />
                </div>
                <span className="text-sm font-medium text-white">{v.titel}</span>
              </div>
              {v.token ? (
                <Link
                  to={`/portal/signatur/${v.token}`}
                  className="flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium px-4 py-2 rounded-lg"
                >
                  <PenLine size={14} /> Signieren
                </Link>
              ) : (
                <span className="text-xs text-slate-500">Noch nicht bereit</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

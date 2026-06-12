import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { Inbox, ShoppingCart, ClipboardList, AlertTriangle } from 'lucide-react'

export default function Dashboard() {
  const { data: uebersicht, isLoading } = useQuery({
    queryKey: ['intern', 'monitoring', 'uebersicht'],
    queryFn: api.intern.monitoring.uebersicht,
  })

  const cards = [
    { label: 'Offene Anfragen', value: uebersicht?.offene_anfragen, icon: Inbox, to: '/intern/anfragen' },
    { label: 'Offene Bestellungen', value: uebersicht?.offene_bestellungen, icon: ShoppingCart, to: '/intern/bestellungen' },
    { label: 'Laufende Leistungsscheine', value: uebersicht?.laufende_leistungsscheine, icon: ClipboardList, to: '/intern/leistungsscheine' },
    { label: 'Unverarbeitete Ereignisse', value: uebersicht?.unverarbeitete_ereignisse, icon: AlertTriangle, to: '/intern/monitoring' },
  ]

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Übersicht</h1>

      {isLoading ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {cards.map(c => (
            <Link
              key={c.label}
              to={c.to}
              className="bg-slate-900 border border-slate-800 rounded-xl p-5 hover:border-sky-600/60 hover:bg-slate-800/40 transition-colors"
            >
              <c.icon size={18} className="text-sky-500 mb-2" />
              <p className="text-2xl font-semibold text-white">{c.value ?? '–'}</p>
              <p className="text-xs text-slate-500 mt-1">{c.label}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'
import { formatDateTime } from '../../lib/format'
import { Inbox, ShoppingCart, ClipboardList, AlertTriangle } from 'lucide-react'

export default function Monitoring() {
  const [nurUnverarbeitet, setNurUnverarbeitet] = useState(false)

  const { data: uebersicht } = useQuery({
    queryKey: ['intern', 'monitoring', 'uebersicht'],
    queryFn: api.intern.monitoring.uebersicht,
  })

  const { data: ereignisse, isLoading } = useQuery({
    queryKey: ['intern', 'monitoring', 'ereignisse', nurUnverarbeitet],
    queryFn: () => api.intern.monitoring.ereignisse(nurUnverarbeitet ? { verarbeitet: false } : undefined),
  })

  const cards = [
    { label: 'Offene Anfragen', value: uebersicht?.offene_anfragen, icon: Inbox },
    { label: 'Offene Bestellungen', value: uebersicht?.offene_bestellungen, icon: ShoppingCart },
    { label: 'Laufende Leistungsscheine', value: uebersicht?.laufende_leistungsscheine, icon: ClipboardList },
    { label: 'Unverarbeitete Ereignisse', value: uebersicht?.unverarbeitete_ereignisse, icon: AlertTriangle },
  ]

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-white">Monitoring</h1>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {cards.map(c => (
          <div key={c.label} className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <c.icon size={18} className="text-sky-500 mb-2" />
            <p className="text-2xl font-semibold text-white">{c.value ?? '–'}</p>
            <p className="text-xs text-slate-500 mt-1">{c.label}</p>
          </div>
        ))}
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-medium text-slate-300">Ereignisse</h2>
          <label className="flex items-center gap-2 text-xs text-slate-400">
            <input type="checkbox" checked={nurUnverarbeitet} onChange={e => setNurUnverarbeitet(e.target.checked)} />
            Nur unverarbeitete
          </label>
        </div>

        {isLoading || !ereignisse ? (
          <p className="text-sm text-slate-500">Lade…</p>
        ) : ereignisse.length === 0 ? (
          <p className="text-sm text-slate-500">Keine Ereignisse.</p>
        ) : (
          <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
            {ereignisse.map(e => (
              <div key={e.id} className="flex items-center justify-between px-5 py-3 text-sm">
                <div>
                  <p className="text-white">{e.ereignis_typ}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {formatDateTime(e.zeit)}
                    {e.bezugstyp && ` · ${e.bezugstyp} #${e.bezugs_id?.slice(0, 8)}`}
                    {e.vorher_status && e.nachher_status && ` · ${e.vorher_status} → ${e.nachher_status}`}
                  </p>
                </div>
                {!e.verarbeitet && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-900 text-amber-300">
                    Unverarbeitet
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

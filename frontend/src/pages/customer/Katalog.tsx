import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { formatCurrency } from '../../lib/format'
import { ShieldCheck } from 'lucide-react'

export default function Katalog() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { data: leistungen, isLoading } = useQuery({
    queryKey: ['portal', 'leistungen'],
    queryFn: api.portal.catalog.list,
  })
  const [error, setError] = useState('')

  const bestellen = useMutation({
    mutationFn: (leistungId: string) => api.portal.bestellungen.create(leistungId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['portal', 'bestellungen'] })
      navigate('/portal/auftraege')
    },
    onError: (e: Error) => setError(e.message),
  })

  if (isLoading || !leistungen) return <p className="text-slate-500 text-sm">Lade…</p>

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-white">Katalog</h1>

      {error && (
        <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">{error}</p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {leistungen.map(l => (
          <div key={l.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-3">
            <div>
              <h2 className="text-sm font-medium text-white">{l.name}</h2>
              {l.kategorie && <p className="text-xs text-slate-500 mt-0.5">{l.kategorie}</p>}
            </div>
            {l.beschreibung && <p className="text-sm text-slate-400 flex-1">{l.beschreibung}</p>}
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-200 font-medium">
                {formatCurrency(l.preis)} <span className="text-slate-500 text-xs">/ {l.preiseinheit}</span>
              </span>
              {l.avv_erforderlich && (
                <span className="flex items-center gap-1 text-xs text-amber-400">
                  <ShieldCheck size={12} /> AVV erforderlich
                </span>
              )}
            </div>
            <button
              onClick={() => { setError(''); bestellen.mutate(l.id) }}
              disabled={bestellen.isPending}
              className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium py-2 rounded-lg transition-colors"
            >
              Bestellen
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

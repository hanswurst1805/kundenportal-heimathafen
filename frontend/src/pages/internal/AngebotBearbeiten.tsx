import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { Trash2, Plus } from 'lucide-react'

interface PositionRow {
  bezeichnung: string
  menge: string
  einzelpreis: string
}

export default function AngebotBearbeiten() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [error, setError] = useState('')

  const { data: angebot, isLoading } = useQuery({
    queryKey: ['intern', 'angebote', id],
    queryFn: () => api.intern.angebote.get(id!),
    enabled: !!id,
  })

  const [titel, setTitel] = useState('')
  const [gueltigBis, setGueltigBis] = useState('')
  const [positionen, setPositionen] = useState<PositionRow[]>([])

  useEffect(() => {
    if (!angebot) return
    setTitel(angebot.titel)
    setGueltigBis(angebot.gueltig_bis ?? '')
    setPositionen(
      angebot.positionen.length > 0
        ? angebot.positionen.map(p => ({
            bezeichnung: p.bezeichnung,
            menge: String(p.menge),
            einzelpreis: String(p.einzelpreis),
          }))
        : [{ bezeichnung: '', menge: '1', einzelpreis: '0' }],
    )
  }, [angebot])

  const save = useMutation({
    mutationFn: () =>
      api.intern.angebote.update(id!, {
        titel,
        gueltig_bis: gueltigBis || undefined,
        positionen: positionen
          .filter(p => p.bezeichnung)
          .map((p, i) => ({ bezeichnung: p.bezeichnung, menge: p.menge, einzelpreis: p.einzelpreis, sort_order: i })),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intern', 'angebote'] })
      navigate('/intern/angebote')
    },
    onError: (e: Error) => setError(e.message),
  })

  if (isLoading || !angebot) return <p className="text-sm text-slate-500">Lade…</p>

  if (angebot.status !== 'entwurf') {
    return (
      <div className="max-w-2xl space-y-4">
        <h1 className="text-xl font-semibold text-white">Angebot bearbeiten</h1>
        <p className="text-sm text-amber-400">
          Nur Entwürfe können bearbeitet werden. Dieses Angebot ist bereits bereitgestellt.
        </p>
        <button
          onClick={() => navigate('/intern/angebote')}
          className="bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          Zurück
        </button>
      </div>
    )
  }

  function updatePosition(i: number, field: keyof PositionRow, value: string) {
    setPositionen(prev => prev.map((p, idx) => (idx === i ? { ...p, [field]: value } : p)))
  }

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold text-white">Angebot bearbeiten</h1>
      <p className="text-sm text-slate-400">{angebot.angebotsnummer} (v{angebot.version})</p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div>
          <label className="block text-xs text-slate-500 mb-1">Titel</label>
          <input
            value={titel}
            onChange={e => setTitel(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Gültig bis</label>
          <input
            type="date"
            value={gueltigBis}
            onChange={e => setGueltigBis(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-xs text-slate-500">Positionen</label>
          {positionen.map((p, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                placeholder="Bezeichnung"
                value={p.bezeichnung}
                onChange={e => updatePosition(i, 'bezeichnung', e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              />
              <input
                placeholder="Menge"
                value={p.menge}
                onChange={e => updatePosition(i, 'menge', e.target.value)}
                className="w-20 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              />
              <input
                placeholder="Einzelpreis"
                value={p.einzelpreis}
                onChange={e => updatePosition(i, 'einzelpreis', e.target.value)}
                className="w-28 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              />
              <button
                onClick={() => setPositionen(prev => prev.filter((_, idx) => idx !== i))}
                className="text-slate-500 hover:text-red-400"
                type="button"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          <button
            onClick={() => setPositionen(prev => [...prev, { bezeichnung: '', menge: '1', einzelpreis: '0' }])}
            className="flex items-center gap-1 text-sky-500 hover:text-sky-400 text-sm"
            type="button"
          >
            <Plus size={14} /> Position hinzufügen
          </button>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <div className="flex items-center gap-2">
          <button
            onClick={() => { setError(''); save.mutate() }}
            disabled={!titel || save.isPending}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
          >
            Speichern
          </button>
          <button
            onClick={() => navigate('/intern/angebote')}
            className="bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
            type="button"
          >
            Abbrechen
          </button>
        </div>
      </div>
    </div>
  )
}

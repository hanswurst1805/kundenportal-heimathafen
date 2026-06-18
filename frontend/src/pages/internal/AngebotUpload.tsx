import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Trash2, Plus, Upload } from 'lucide-react'
import { api } from '../../api/client'

interface PositionRow {
  leistung_id: string
  bezeichnung: string
  menge: string
  einzelpreis: string
}

const LEER: PositionRow = { leistung_id: '', bezeichnung: '', menge: '1', einzelpreis: '0' }

export default function AngebotUpload() {
  const navigate = useNavigate()
  const [error, setError] = useState('')

  const { data: kunden } = useQuery({ queryKey: ['intern', 'kunden'], queryFn: api.intern.kunden.list })
  const { data: katalog } = useQuery({ queryKey: ['intern', 'leistungen'], queryFn: api.intern.leistungen.list })

  const [customerId, setCustomerId] = useState('')
  const [titel, setTitel] = useState('')
  const [gueltigBis, setGueltigBis] = useState('')
  const [datei, setDatei] = useState<File | null>(null)
  const [positionen, setPositionen] = useState<PositionRow[]>([{ ...LEER }])

  const upload = useMutation({
    mutationFn: () =>
      api.intern.angebote.uploadExternes({
        customer_id: customerId,
        titel,
        gueltig_bis: gueltigBis || undefined,
        datei: datei!,
        positionen: positionen
          .filter(p => p.bezeichnung)
          .map((p, i) => ({
            bezeichnung: p.bezeichnung,
            menge: p.menge,
            einzelpreis: p.einzelpreis,
            sort_order: i,
            leistung_id: p.leistung_id || undefined,
          })),
      }),
    onSuccess: () => navigate('/intern/angebote'),
    onError: (e: Error) => setError(e.message),
  })

  function updatePosition(i: number, patch: Partial<PositionRow>) {
    setPositionen(prev => prev.map((p, idx) => (idx === i ? { ...p, ...patch } : p)))
  }

  function waehleLeistung(i: number, leistungId: string) {
    const l = katalog?.find(k => k.id === leistungId)
    if (!l) {
      updatePosition(i, { leistung_id: '' })
      return
    }
    updatePosition(i, { leistung_id: l.id, bezeichnung: l.name, einzelpreis: String(l.preis) })
  }

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold text-white">Externes Angebot hochladen</h1>
      <p className="text-sm text-slate-400">
        PDF eines extern erstellten Angebots hochladen und Positionen mit dem Katalog verknüpfen.
      </p>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Kunde</label>
            <select
              value={customerId}
              onChange={e => setCustomerId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            >
              <option value="">– wählen –</option>
              {kunden?.map(k => <option key={k.id} value={k.id}>{k.name}</option>)}
            </select>
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
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">Titel</label>
          <input
            value={titel}
            onChange={e => setTitel(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">Angebots-PDF</label>
          <input
            type="file"
            accept="application/pdf"
            onChange={e => setDatei(e.target.files?.[0] ?? null)}
            className="w-full text-sm text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-1.5 file:text-sm file:text-slate-200 hover:file:bg-slate-700"
          />
          {datei && <p className="text-xs text-slate-500 mt-1">{datei.name}</p>}
        </div>

        <div className="space-y-2">
          <label className="block text-xs text-slate-500">Positionen (aus Katalog oder frei)</label>
          {positionen.map((p, i) => (
            <div key={i} className="flex items-center gap-2">
              <select
                value={p.leistung_id}
                onChange={e => waehleLeistung(i, e.target.value)}
                className="w-40 bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              >
                <option value="">frei…</option>
                {katalog?.filter(k => k.is_active).map(k => (
                  <option key={k.id} value={k.id}>{k.name}</option>
                ))}
              </select>
              <input
                placeholder="Bezeichnung"
                value={p.bezeichnung}
                onChange={e => updatePosition(i, { bezeichnung: e.target.value })}
                className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              />
              <input
                placeholder="Menge"
                value={p.menge}
                onChange={e => updatePosition(i, { menge: e.target.value })}
                className="w-16 bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              />
              <input
                placeholder="Einzelpreis"
                value={p.einzelpreis}
                onChange={e => updatePosition(i, { einzelpreis: e.target.value })}
                className="w-24 bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
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
            onClick={() => setPositionen(prev => [...prev, { ...LEER }])}
            className="flex items-center gap-1 text-sky-500 hover:text-sky-400 text-sm"
            type="button"
          >
            <Plus size={14} /> Position hinzufügen
          </button>
        </div>

        {error && <p className="text-sm text-red-400">{error}</p>}

        <button
          onClick={() => { setError(''); upload.mutate() }}
          disabled={!customerId || !titel || !datei || upload.isPending}
          className="flex items-center gap-2 bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Upload size={16} /> {upload.isPending ? 'Lädt hoch…' : 'Angebot hochladen'}
        </button>
      </div>
    </div>
  )
}

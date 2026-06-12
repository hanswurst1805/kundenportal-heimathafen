import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Leistung, type LeistungCreate, type LeistungUpdate } from '../../api/client'
import { Plus, ChevronDown, ChevronRight } from 'lucide-react'

const PREISEINHEITEN = ['einmalig', 'pro Monat', 'pro Jahr', 'pro Stück', 'pro Stunde']

const inputCls =
  'w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600'
const labelCls = 'block text-xs text-slate-400 mb-1'

function useFeldEditor({
  initial,
  withLeistungsId,
}: {
  initial?: Leistung
  withLeistungsId?: boolean
}) {
  // gemeinsame Feldzustände für Anlegen/Bearbeiten
  const [leistungsId, setLeistungsId] = useState(initial?.leistungs_id ?? '')
  const [name, setName] = useState(initial?.name ?? '')
  const [beschreibung, setBeschreibung] = useState(initial?.beschreibung ?? '')
  const [kategorie, setKategorie] = useState(initial?.kategorie ?? '')
  const [preis, setPreis] = useState(initial?.preis ?? '')
  const [preiseinheit, setPreiseinheit] = useState(initial?.preiseinheit ?? 'einmalig')
  const [avv, setAvv] = useState(initial?.avv_erforderlich ?? false)
  const [bestellbar, setBestellbar] = useState(initial?.ist_bestellbar ?? true)
  const [aktiv, setAktiv] = useState(initial?.is_active ?? true)

  return {
    state: { leistungsId, name, beschreibung, kategorie, preis, preiseinheit, avv, bestellbar, aktiv },
    node: (
      <div className="grid grid-cols-2 gap-3">
        {withLeistungsId && (
          <div>
            <label className={labelCls}>Leistungs-ID</label>
            <input className={inputCls} value={leistungsId} onChange={e => setLeistungsId(e.target.value)} placeholder="z.B. MS-100" />
          </div>
        )}
        <div className={withLeistungsId ? '' : 'col-span-2'}>
          <label className={labelCls}>Name</label>
          <input className={inputCls} value={name} onChange={e => setName(e.target.value)} />
        </div>
        <div className="col-span-2">
          <label className={labelCls}>Beschreibung</label>
          <textarea className={inputCls} rows={2} value={beschreibung} onChange={e => setBeschreibung(e.target.value)} />
        </div>
        <div>
          <label className={labelCls}>Kategorie</label>
          <input className={inputCls} value={kategorie} onChange={e => setKategorie(e.target.value)} placeholder="z.B. Managed Services" />
        </div>
        <div>
          <label className={labelCls}>Preis (EUR)</label>
          <input className={inputCls} value={preis} onChange={e => setPreis(e.target.value)} placeholder="49.90" inputMode="decimal" />
        </div>
        <div>
          <label className={labelCls}>Preiseinheit</label>
          <select className={inputCls} value={preiseinheit} onChange={e => setPreiseinheit(e.target.value)}>
            {[...new Set([preiseinheit, ...PREISEINHEITEN])].map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        <div className="flex items-end gap-4">
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input type="checkbox" checked={avv} onChange={e => setAvv(e.target.checked)} /> AVV erforderlich
          </label>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={bestellbar} onChange={e => setBestellbar(e.target.checked)} /> Bestellbar
        </label>
        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input type="checkbox" checked={aktiv} onChange={e => setAktiv(e.target.checked)} /> Aktiv
        </label>
      </div>
    ),
  }
}

function LeistungRow({ leistung }: { leistung: Leistung }) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [error, setError] = useState('')
  const editor = useFeldEditor({ initial: leistung })

  const update = useMutation({
    mutationFn: (data: LeistungUpdate) => api.intern.leistungen.update(leistung.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intern', 'leistungen'] })
      setOpen(false)
    },
    onError: (e: Error) => setError(e.message),
  })

  function speichern() {
    setError('')
    const s = editor.state
    update.mutate({
      name: s.name,
      beschreibung: s.beschreibung || undefined,
      kategorie: s.kategorie || undefined,
      preis: s.preis,
      preiseinheit: s.preiseinheit,
      avv_erforderlich: s.avv,
      ist_bestellbar: s.bestellbar,
      is_active: s.aktiv,
    })
  }

  return (
    <div>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-slate-800/40"
      >
        <div className="flex items-center gap-2">
          {open ? <ChevronDown size={15} className="text-slate-500" /> : <ChevronRight size={15} className="text-slate-500" />}
          <div>
            <p className="text-sm text-white">{leistung.leistungs_id} – {leistung.name}</p>
            <p className="text-xs text-slate-500 mt-0.5">
              {leistung.preis} € {leistung.preiseinheit}
              {leistung.kategorie ? ` · ${leistung.kategorie}` : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {leistung.avv_erforderlich && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-900 text-amber-300">AVV</span>
          )}
          {!leistung.ist_bestellbar && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">nicht bestellbar</span>
          )}
          <span className={`text-xs px-2 py-0.5 rounded-full ${leistung.is_active ? 'bg-emerald-900 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}>
            {leistung.is_active ? 'Aktiv' : 'Inaktiv'}
          </span>
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 pt-1 space-y-3 bg-slate-950/40">
          {editor.node}
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={speichern}
              disabled={update.isPending}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Speichern
            </button>
            <button
              onClick={() => setOpen(false)}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2 rounded-lg"
            >
              Abbrechen
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function NeuFormular({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')
  const editor = useFeldEditor({ withLeistungsId: true })

  const create = useMutation({
    mutationFn: (data: LeistungCreate) => api.intern.leistungen.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intern', 'leistungen'] })
      onClose()
    },
    onError: (e: Error) => setError(e.message),
  })

  function anlegen() {
    setError('')
    const s = editor.state
    if (!s.leistungsId || !s.name || !s.preis) {
      setError('Leistungs-ID, Name und Preis sind erforderlich.')
      return
    }
    create.mutate({
      leistungs_id: s.leistungsId,
      name: s.name,
      beschreibung: s.beschreibung || undefined,
      kategorie: s.kategorie || undefined,
      preis: s.preis,
      preiseinheit: s.preiseinheit,
      avv_erforderlich: s.avv,
      ist_bestellbar: s.bestellbar,
      is_active: s.aktiv,
    })
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
      <h2 className="text-sm font-medium text-slate-300">Neue Leistung</h2>
      {editor.node}
      {error && <p className="text-sm text-red-400">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={anlegen}
          disabled={create.isPending}
          className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          Anlegen
        </button>
        <button onClick={onClose} className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2 rounded-lg">
          Abbrechen
        </button>
      </div>
    </div>
  )
}

export default function Leistungen() {
  const [showNeu, setShowNeu] = useState(false)
  const { data: leistungen, isLoading } = useQuery({ queryKey: ['intern', 'leistungen'], queryFn: api.intern.leistungen.list })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">Katalog-Editor</h1>
        <button
          onClick={() => setShowNeu(s => !s)}
          className="flex items-center gap-1 bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium px-3 py-1.5 rounded-lg"
        >
          <Plus size={14} /> Neue Leistung
        </button>
      </div>

      {showNeu && <NeuFormular onClose={() => setShowNeu(false)} />}

      {isLoading || !leistungen ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : leistungen.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Leistungen vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {leistungen.map(l => (
            <LeistungRow key={l.id} leistung={l} />
          ))}
        </div>
      )}
    </div>
  )
}

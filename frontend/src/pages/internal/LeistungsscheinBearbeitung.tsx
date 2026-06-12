import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api, type LeistungsscheinInternUpdate } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import {
  KUNDENSTATUS,
  KUNDENSTATUS_LABELS,
  INTERNE_ZWISCHENSCHRITTE,
  AUFGABE_STATUS_LABELS,
  WORKSHOP_STATUS_LABELS,
  WORKSHOP_TYP_LABELS,
} from '../../lib/statuscodes'
import { Trash2, Plus } from 'lucide-react'

function toDateInput(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : ''
}

function toDateTimeInput(value: string | null | undefined): string {
  return value ? value.slice(0, 16) : ''
}

export default function LeistungsscheinBearbeitung() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [error, setError] = useState('')

  const { data: ls, isLoading } = useQuery({
    queryKey: ['intern', 'leistungsscheine', id],
    queryFn: () => api.intern.leistungsscheine.get(id!),
    enabled: !!id,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['intern', 'leistungsscheine', id] })

  const update = useMutation({
    mutationFn: (data: LeistungsscheinInternUpdate) => api.intern.leistungsscheine.update(id!, data),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  const kundenrueckfrage = useMutation({
    mutationFn: () => api.intern.leistungsscheine.kundenrueckfrage(id!),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  const abschliessen = useMutation({
    mutationFn: () => api.intern.leistungsscheine.abschliessen(id!),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  const createAufgabe = useMutation({
    mutationFn: (titel: string) => api.intern.leistungsscheine.aufgaben.create(id!, { titel }),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  const updateAufgabe = useMutation({
    mutationFn: ({ aufgabeId, status }: { aufgabeId: string; status: string }) =>
      api.intern.leistungsscheine.aufgaben.update(id!, aufgabeId, { status }),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  const deleteAufgabe = useMutation({
    mutationFn: (aufgabeId: string) => api.intern.leistungsscheine.aufgaben.delete(id!, aufgabeId),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  const createWorkshop = useMutation({
    mutationFn: (typ: string) => api.intern.leistungsscheine.workshops.create(id!, { typ }),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  const updateWorkshop = useMutation({
    mutationFn: ({ workshopId, data }: { workshopId: string; data: { status?: string; termin?: string; protokoll?: string } }) =>
      api.intern.leistungsscheine.workshops.update(id!, workshopId, data),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  const [neueAufgabe, setNeueAufgabe] = useState('')
  const [neuerWorkshopTyp, setNeuerWorkshopTyp] = useState('kickoff')

  if (isLoading || !ls) return <p className="text-sm text-slate-500">Lade…</p>

  function field<K extends keyof LeistungsscheinInternUpdate>(key: K, value: LeistungsscheinInternUpdate[K]) {
    update.mutate({ [key]: value } as LeistungsscheinInternUpdate)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">{ls.ls_nummer}</h1>
        <StatusBadge status={ls.status_kunde} />
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <h2 className="text-sm font-medium text-slate-300">Allgemein</h2>

        <div>
          <label className="block text-xs text-slate-500 mb-1">Scope-Beschreibung</label>
          <textarea
            defaultValue={ls.scope_beschreibung ?? ''}
            onBlur={e => field('scope_beschreibung', e.target.value)}
            rows={2}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Startdatum</label>
            <input
              type="date"
              defaultValue={toDateInput(ls.startdatum)}
              onBlur={e => field('startdatum', e.target.value || undefined)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Solltermin</label>
            <input
              type="date"
              defaultValue={toDateInput(ls.solltermin)}
              onBlur={e => field('solltermin', e.target.value || undefined)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Kick-Off-Datum</label>
            <input
              type="datetime-local"
              defaultValue={toDateTimeInput(ls.kickoff_datum)}
              onBlur={e => field('kickoff_datum', e.target.value || undefined)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Workshop-Datum</label>
            <input
              type="datetime-local"
              defaultValue={toDateTimeInput(ls.workshop_datum)}
              onBlur={e => field('workshop_datum', e.target.value || undefined)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-slate-500 mb-1">Kundenstatus</label>
            <select
              value={ls.status_kunde}
              onChange={e => field('status_kunde', e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            >
              {KUNDENSTATUS.map(s => <option key={s} value={s}>{KUNDENSTATUS_LABELS[s]}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">Interner Status</label>
            <select
              value={ls.status_intern ?? ''}
              onChange={e => field('status_intern', e.target.value || undefined)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            >
              <option value="">–</option>
              {INTERNE_ZWISCHENSCHRITTE.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs text-slate-500 mb-1">Nächster Schritt</label>
          <input
            defaultValue={ls.naechster_schritt ?? ''}
            onBlur={e => field('naechster_schritt', e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Voraussetzungen</label>
          <textarea
            defaultValue={ls.voraussetzungen ?? ''}
            onBlur={e => field('voraussetzungen', e.target.value)}
            rows={2}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Onboarding-Ziele</label>
          <textarea
            defaultValue={ls.onboarding_ziele ?? ''}
            onBlur={e => field('onboarding_ziele', e.target.value)}
            rows={2}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Offene Punkte (Onboarding)</label>
          <textarea
            defaultValue={ls.onboarding_offene_punkte ?? ''}
            onBlur={e => field('onboarding_offene_punkte', e.target.value)}
            rows={2}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>
        <div>
          <label className="block text-xs text-slate-500 mb-1">Lessons Learned</label>
          <textarea
            defaultValue={ls.lessons_learned ?? ''}
            onBlur={e => field('lessons_learned', e.target.value)}
            rows={2}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
        </div>

        <div className="flex items-center gap-2 pt-2 border-t border-slate-800">
          <button
            onClick={() => { setError(''); kundenrueckfrage.mutate() }}
            disabled={kundenrueckfrage.isPending}
            className="bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-sm font-medium px-4 py-2 rounded-lg"
          >
            Kundenrückfrage senden
          </button>
          <button
            onClick={() => { setError(''); abschliessen.mutate() }}
            disabled={abschliessen.isPending}
            className="bg-emerald-700 hover:bg-emerald-600 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
          >
            Abschließen
          </button>
        </div>
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Aufgaben</h2>
        <ul className="divide-y divide-slate-800">
          {ls.aufgaben.map(a => (
            <li key={a.id} className="py-2 flex items-center justify-between text-sm gap-3">
              <div className="flex-1">
                <p className="text-slate-200">{a.titel}</p>
                {a.beschreibung && <p className="text-xs text-slate-500">{a.beschreibung}</p>}
              </div>
              <select
                value={a.status}
                onChange={e => updateAufgabe.mutate({ aufgabeId: a.id, status: e.target.value })}
                className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              >
                {Object.entries(AUFGABE_STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <button onClick={() => deleteAufgabe.mutate(a.id)} className="text-slate-500 hover:text-red-400">
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>
        <div className="flex items-center gap-2">
          <input
            value={neueAufgabe}
            onChange={e => setNeueAufgabe(e.target.value)}
            placeholder="Neue Aufgabe"
            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <button
            onClick={() => { if (neueAufgabe) { createAufgabe.mutate(neueAufgabe); setNeueAufgabe('') } }}
            className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-3 py-1.5 rounded-lg"
          >
            <Plus size={14} /> Hinzufügen
          </button>
        </div>
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
        <h2 className="text-sm font-medium text-slate-300">Workshops</h2>
        <ul className="divide-y divide-slate-800">
          {ls.workshops.map(w => (
            <li key={w.id} className="py-2 space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <p className="text-slate-200">{WORKSHOP_TYP_LABELS[w.typ] ?? w.typ}</p>
                <select
                  value={w.status}
                  onChange={e => updateWorkshop.mutate({ workshopId: w.id, data: { status: e.target.value } })}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
                >
                  {Object.entries(WORKSHOP_STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="datetime-local"
                  defaultValue={toDateTimeInput(w.termin)}
                  onBlur={e => updateWorkshop.mutate({ workshopId: w.id, data: { termin: e.target.value || undefined } })}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
                />
                <input
                  placeholder="Protokoll"
                  defaultValue={w.protokoll ?? ''}
                  onBlur={e => updateWorkshop.mutate({ workshopId: w.id, data: { protokoll: e.target.value } })}
                  className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
                />
              </div>
            </li>
          ))}
        </ul>
        <div className="flex items-center gap-2">
          <select
            value={neuerWorkshopTyp}
            onChange={e => setNeuerWorkshopTyp(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-2 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          >
            {Object.entries(WORKSHOP_TYP_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <button
            onClick={() => createWorkshop.mutate(neuerWorkshopTyp)}
            className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-3 py-1.5 rounded-lg"
          >
            <Plus size={14} /> Workshop hinzufügen
          </button>
        </div>
      </section>
    </div>
  )
}

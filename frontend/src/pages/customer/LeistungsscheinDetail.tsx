import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { api } from '../../api/client'
import StatusBadge from '../../components/StatusBadge'
import { formatDate, formatDateTime } from '../../lib/format'

const AUFGABE_LABELS: Record<string, string> = {
  offen: 'Offen',
  in_bearbeitung: 'In Bearbeitung',
  erledigt: 'Erledigt',
  blockiert: 'Blockiert',
}

const WORKSHOP_LABELS: Record<string, string> = {
  geplant: 'Geplant',
  durchgefuehrt: 'Durchgeführt',
  protokoll_freigegeben: 'Protokoll freigegeben',
  verschoben: 'Verschoben',
}

const WORKSHOP_TYP_LABELS: Record<string, string> = {
  kickoff: 'Kick-Off',
  onboarding: 'Onboarding',
}

export default function LeistungsscheinDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: ls, isLoading } = useQuery({
    queryKey: ['portal', 'leistungsscheine', id],
    queryFn: () => api.portal.leistungsscheine.get(id!),
    enabled: !!id,
  })

  if (isLoading || !ls) return <p className="text-slate-500 text-sm">Lade…</p>

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-white">{ls.ls_nummer}</h1>
          {ls.scope_beschreibung && <p className="text-sm text-slate-400 mt-1">{ls.scope_beschreibung}</p>}
        </div>
        <StatusBadge status={ls.status_kunde} />
      </div>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-xs text-slate-500">Startdatum</p>
          <p className="text-slate-200">{formatDate(ls.startdatum)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Solltermin</p>
          <p className="text-slate-200">{formatDate(ls.solltermin)}</p>
        </div>
        {ls.naechster_schritt && (
          <div className="col-span-2">
            <p className="text-xs text-slate-500">Nächster Schritt</p>
            <p className="text-slate-200">{ls.naechster_schritt}</p>
          </div>
        )}
        {ls.voraussetzungen && (
          <div className="col-span-2">
            <p className="text-xs text-slate-500">Voraussetzungen</p>
            <p className="text-slate-200">{ls.voraussetzungen}</p>
          </div>
        )}
        {ls.onboarding_ziele && (
          <div className="col-span-2">
            <p className="text-xs text-slate-500">Onboarding-Ziele</p>
            <p className="text-slate-200">{ls.onboarding_ziele}</p>
          </div>
        )}
        {ls.onboarding_offene_punkte && (
          <div className="col-span-2">
            <p className="text-xs text-slate-500">Offene Punkte (Onboarding)</p>
            <p className="text-slate-200">{ls.onboarding_offene_punkte}</p>
          </div>
        )}
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Aufgaben</h2>
        {ls.aufgaben.length === 0 ? (
          <p className="text-sm text-slate-500">Keine Aufgaben.</p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {ls.aufgaben.map(a => (
              <li key={a.id} className="py-2 flex items-center justify-between text-sm">
                <div>
                  <p className="text-slate-200">{a.titel}</p>
                  {a.beschreibung && <p className="text-xs text-slate-500">{a.beschreibung}</p>}
                </div>
                <div className="flex items-center gap-3">
                  {a.faelligkeit && <span className="text-xs text-slate-500">{formatDate(a.faelligkeit)}</span>}
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-200">
                    {AUFGABE_LABELS[a.status] ?? a.status}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h2 className="text-sm font-medium text-slate-300 mb-3">Workshops</h2>
        {ls.workshops.length === 0 ? (
          <p className="text-sm text-slate-500">Keine Workshops geplant.</p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {ls.workshops.map(w => (
              <li key={w.id} className="py-2 flex items-center justify-between text-sm">
                <div>
                  <p className="text-slate-200">{WORKSHOP_TYP_LABELS[w.typ] ?? w.typ}</p>
                  {w.termin && <p className="text-xs text-slate-500">{formatDateTime(w.termin)}</p>}
                </div>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-700 text-slate-200">
                  {WORKSHOP_LABELS[w.status] ?? w.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

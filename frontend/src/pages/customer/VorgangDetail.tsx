import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { PenLine, FileText, ShieldCheck, ClipboardList, FileCheck2, ArrowLeft } from 'lucide-react'
import { api } from '../../api/client'
import AblaufGrafik from '../../components/AblaufGrafik'
import { formatCurrency, formatDate, formatDateTime } from '../../lib/format'
import { ANGEBOT_STATUS_LABELS, AVV_STATUS_LABELS, KUNDENSTATUS_LABELS } from '../../lib/statuscodes'

const TYP_LABEL: Record<string, string> = { anfrage: 'Anfrage', bestellung: 'Bestellung' }

function Abschnitt({ icon, titel, children }: { icon: React.ReactNode; titel: string; children: React.ReactNode }) {
  return (
    <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3">
      <h2 className="flex items-center gap-2 text-sm font-medium text-slate-200">
        <span className="text-sky-500">{icon}</span> {titel}
      </h2>
      {children}
    </section>
  )
}

export default function VorgangDetail() {
  const { typ, id } = useParams<{ typ: string; id: string }>()
  const { data: v, isLoading } = useQuery({
    queryKey: ['portal', 'vorgaenge', typ, id],
    queryFn: () => api.portal.vorgaenge.get(typ!, id!),
    enabled: !!typ && !!id,
  })

  if (isLoading || !v) return <p className="text-sm text-slate-500">Lade…</p>

  return (
    <div className="max-w-3xl space-y-4">
      <Link to="/portal/vorgaenge" className="inline-flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200">
        <ArrowLeft size={14} /> Zurück
      </Link>

      <div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium uppercase tracking-wide text-slate-500">
            {TYP_LABEL[v.typ] ?? v.typ}
          </span>
          <h1 className="text-xl font-semibold text-white">{v.referenz}</h1>
        </div>
        <p className="text-sm text-slate-400 mt-0.5">{v.titel}</p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <AblaufGrafik statusKunde={v.status_kunde} />
      </div>

      {v.offene_signaturen.length > 0 && (
        <Abschnitt icon={<PenLine size={16} />} titel="Zu signieren">
          <ul className="divide-y divide-slate-800">
            {v.offene_signaturen.map(s => (
              <li key={s.id} className="py-2 flex items-center justify-between text-sm">
                <span className="text-slate-200">{s.titel}</span>
                {s.token && (
                  <Link
                    to={`/portal/signatur/${s.token}`}
                    className="flex items-center gap-1.5 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    <PenLine size={13} /> Signieren
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </Abschnitt>
      )}

      {v.angebot && (
        <Abschnitt icon={<FileText size={16} />} titel="Angebot">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-300">{v.angebot.angebotsnummer} – {v.angebot.titel}</span>
            <span className="text-slate-400">{ANGEBOT_STATUS_LABELS[v.angebot.status] ?? v.angebot.status}</span>
          </div>
          {v.angebot.positionen.length > 0 && (
            <table className="w-full text-sm">
              <tbody className="text-slate-300">
                {v.angebot.positionen.map(p => (
                  <tr key={p.id} className="border-t border-slate-800">
                    <td className="py-1">{p.bezeichnung}</td>
                    <td className="py-1 text-right text-slate-500">{p.menge} ×</td>
                    <td className="py-1 text-right">{formatCurrency(p.gesamtpreis)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-sm">
            <span className="font-medium text-white">Gesamt: {formatCurrency(v.angebot.gesamtpreis)}</span>
            <Link to="/portal/angebote" className="text-sky-400 hover:text-sky-300">In Angeboten öffnen</Link>
          </div>
        </Abschnitt>
      )}

      {v.avv && (
        <Abschnitt icon={<ShieldCheck size={16} />} titel="Auftragsverarbeitungsvertrag (AVV)">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">{AVV_STATUS_LABELS[v.avv.status] ?? v.avv.status}</span>
            <Link to="/portal/avv" className="text-sky-400 hover:text-sky-300">AVV öffnen</Link>
          </div>
        </Abschnitt>
      )}

      {v.auftrag && (
        <Abschnitt icon={<FileCheck2 size={16} />} titel="Auftrag & Auftragsbestätigung">
          <div className="flex items-center justify-between text-sm">
            <div className="text-slate-300">
              {v.auftrag.auftragsnummer}
              {v.auftrag.freigabedatum && (
                <span className="text-slate-500"> · freigegeben am {formatDate(v.auftrag.freigabedatum)}</span>
              )}
            </div>
            <span className="text-slate-400">{v.auftrag.status}</span>
          </div>
          {v.auftragsbestaetigung && (
            <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-sm">
              <span className="text-slate-300">
                {v.auftragsbestaetigung.kenntnisnahme_am
                  ? `Zur Kenntnis genommen am ${formatDateTime(v.auftragsbestaetigung.kenntnisnahme_am)}`
                  : 'Auftragsbestätigung liegt vor'}
              </span>
              <Link to="/portal/auftraege" className="text-sky-400 hover:text-sky-300">Aufträge öffnen</Link>
            </div>
          )}
        </Abschnitt>
      )}

      {v.leistungsschein_id && (
        <Abschnitt icon={<ClipboardList size={16} />} titel="Leistungsschein">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400">
              {v.leistungsschein_status ? (KUNDENSTATUS_LABELS[v.leistungsschein_status] ?? v.leistungsschein_status) : '—'}
            </span>
            <Link to={`/portal/leistungsscheine/${v.leistungsschein_id}`} className="text-sky-400 hover:text-sky-300">
              Leistungsschein öffnen
            </Link>
          </div>
        </Abschnitt>
      )}
    </div>
  )
}

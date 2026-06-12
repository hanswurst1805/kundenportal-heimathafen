import { KUNDENSTATUS_LABELS } from '../lib/statuscodes'

const STATUS_COLORS: Record<string, string> = {
  anfrage_eingegangen: 'bg-slate-700 text-slate-200',
  in_pruefung: 'bg-slate-700 text-slate-200',
  angebot_erstellt: 'bg-indigo-900 text-indigo-300',
  warten_auf_signatur: 'bg-amber-900 text-amber-300',
  avv_ausstehend: 'bg-amber-900 text-amber-300',
  beauftragt: 'bg-sky-900 text-sky-300',
  kickoff_gestartet: 'bg-sky-900 text-sky-300',
  in_vorbereitung: 'bg-sky-900 text-sky-300',
  onboarding_workshop: 'bg-sky-900 text-sky-300',
  in_bearbeitung: 'bg-sky-900 text-sky-300',
  warten_auf_kunde: 'bg-amber-900 text-amber-300',
  fertiggestellt: 'bg-emerald-900 text-emerald-300',
  kundenzufriedenheitsabfrage: 'bg-emerald-900 text-emerald-300',
  abgeschlossen: 'bg-emerald-900 text-emerald-300',
  storniert: 'bg-red-900 text-red-300',
}

export default function StatusBadge({ status }: { status: string }) {
  const label = KUNDENSTATUS_LABELS[status] ?? status
  const color = STATUS_COLORS[status] ?? 'bg-slate-700 text-slate-200'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>
      {label}
    </span>
  )
}

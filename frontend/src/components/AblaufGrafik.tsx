import { Fragment } from 'react'
import {
  Check,
  MessageSquareText,
  FileText,
  FileSignature,
  ShieldCheck,
  ClipboardCheck,
  Wrench,
  Flag,
  type LucideIcon,
} from 'lucide-react'
import { KUNDENSTATUS, KUNDENSTATUS_LABELS } from '../lib/statuscodes'

// Verdichtete, kundenfreundliche Phasen. statusIndex = Position im
// KUNDENSTATUS-Modell, ab der die Phase als erreicht gilt.
interface Phase {
  label: string
  statusIndex: number
  Icon: LucideIcon
}

const PHASEN: Phase[] = [
  { label: 'Anfrage', statusIndex: 0, Icon: MessageSquareText },
  { label: 'Angebot', statusIndex: 2, Icon: FileText },
  { label: 'Signatur', statusIndex: 3, Icon: FileSignature },
  { label: 'AVV', statusIndex: 4, Icon: ShieldCheck },
  { label: 'Beauftragt', statusIndex: 5, Icon: ClipboardCheck },
  { label: 'Umsetzung', statusIndex: 6, Icon: Wrench },
  { label: 'Abschluss', statusIndex: 11, Icon: Flag },
]

export default function AblaufGrafik({ statusKunde }: { statusKunde: string }) {
  const aktuell = (KUNDENSTATUS as readonly string[]).indexOf(statusKunde)
  const storniert = statusKunde === 'storniert'

  return (
    <div className="space-y-2">
      <div className="flex items-center overflow-x-auto pb-1">
        {PHASEN.map((phase, i) => {
          const naechster = PHASEN[i + 1]?.statusIndex ?? Infinity
          const erledigt = !storniert && aktuell >= naechster
          const aktiv = !storniert && aktuell >= phase.statusIndex && aktuell < naechster
          const Icon = phase.Icon

          const kreis = erledigt
            ? 'bg-sky-600 text-white border-sky-600'
            : aktiv
              ? 'bg-sky-600/20 text-sky-300 border-sky-500 ring-2 ring-sky-500/40'
              : 'bg-slate-800 text-slate-500 border-slate-700'

          const labelFarbe = erledigt
            ? 'text-slate-300'
            : aktiv
              ? 'text-sky-300 font-medium'
              : 'text-slate-600'

          return (
            <Fragment key={phase.label}>
              <div className="flex flex-col items-center gap-1.5 w-16 shrink-0">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border ${kreis}`}>
                  {erledigt ? <Check size={18} /> : <Icon size={17} />}
                </div>
                <span className={`text-[11px] text-center leading-tight ${labelFarbe}`}>{phase.label}</span>
              </div>
              {i < PHASEN.length - 1 && (
                <div className={`h-0.5 flex-1 min-w-[1.5rem] -mt-5 ${erledigt ? 'bg-sky-600' : 'bg-slate-700'}`} />
              )}
            </Fragment>
          )
        })}
      </div>

      {storniert ? (
        <p className="text-xs text-red-400">Dieser Vorgang wurde storniert.</p>
      ) : (
        <p className="text-xs text-slate-500">
          Aktueller Status: <span className="text-slate-300">{KUNDENSTATUS_LABELS[statusKunde] ?? statusKunde}</span>
        </p>
      )}
    </div>
  )
}

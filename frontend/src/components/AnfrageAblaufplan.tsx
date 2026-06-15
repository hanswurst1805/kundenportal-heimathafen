import { useNavigate } from 'react-router-dom'
import { ChevronRight, Check } from 'lucide-react'
import { KUNDENSTATUS } from '../lib/statuscodes'
import type { AnfrageIntern } from '../api/client'

// Verdichtete Workflow-Phasen (Kacheln). statusIndex = Position im KUNDENSTATUS-
// Modell, ab der die Phase als erreicht gilt.
interface Phase {
  key: string
  label: string
  statusIndex: number
}

const PHASEN: Phase[] = [
  { key: 'anfrage', label: 'Anfrage', statusIndex: 0 },
  { key: 'angebot', label: 'Angebot', statusIndex: 2 },
  { key: 'signatur', label: 'Signatur', statusIndex: 3 },
  { key: 'avv', label: 'AVV', statusIndex: 4 },
  { key: 'auftrag', label: 'Beauftragt', statusIndex: 5 },
  { key: 'leistungsschein', label: 'Leistungsschein', statusIndex: 6 },
  { key: 'umfrage', label: 'Umfrage', statusIndex: 12 },
  { key: 'abschluss', label: 'Abgeschlossen', statusIndex: 13 },
]

function zielFuer(key: string, anfrage: AnfrageIntern): string | null {
  switch (key) {
    case 'angebot':
      return anfrage.angebot_id ? '/intern/angebote' : `/intern/anfragen/${anfrage.id}/angebot`
    case 'signatur':
      return '/intern/signaturen'
    case 'avv':
      return '/intern/avv'
    case 'auftrag':
      return '/intern/auftraege'
    case 'leistungsschein':
    case 'abschluss':
      return '/intern/leistungsscheine'
    case 'umfrage':
      return '/intern/umfragen'
    default:
      return null // Anfrage-Kachel: Detail aufklappen
  }
}

export default function AnfrageAblaufplan({
  anfrage,
  onAnfrageClick,
}: {
  anfrage: AnfrageIntern
  onAnfrageClick?: () => void
}) {
  const navigate = useNavigate()
  const aktuellerIndex = KUNDENSTATUS.indexOf(anfrage.status_kunde)
  const storniert = anfrage.status_kunde === 'storniert'

  function handleClick(phase: Phase) {
    const ziel = zielFuer(phase.key, anfrage)
    if (ziel) navigate(ziel)
    else onAnfrageClick?.()
  }

  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1">
      {PHASEN.map((phase, i) => {
        const naechsterIndex = PHASEN[i + 1]?.statusIndex ?? Infinity
        const erledigt = !storniert && aktuellerIndex >= naechsterIndex
        const aktiv = !storniert && aktuellerIndex >= phase.statusIndex && aktuellerIndex < naechsterIndex

        const farbe = erledigt
          ? 'bg-sky-600 text-white hover:bg-sky-500'
          : aktiv
            ? 'bg-slate-800 text-white ring-2 ring-sky-500 hover:bg-slate-700'
            : 'bg-slate-800/50 text-slate-500 hover:bg-slate-800 hover:text-slate-300'

        return (
          <div key={phase.key} className="flex items-center gap-1 shrink-0">
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); handleClick(phase) }}
              title={phase.label}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${farbe}`}
            >
              {erledigt && <Check size={13} />}
              {phase.label}
            </button>
            {i < PHASEN.length - 1 && <ChevronRight size={14} className="text-slate-600 shrink-0" />}
          </div>
        )
      })}
    </div>
  )
}

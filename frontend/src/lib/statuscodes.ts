export const KUNDENSTATUS = [
  'anfrage_eingegangen',
  'in_pruefung',
  'angebot_erstellt',
  'warten_auf_signatur',
  'avv_ausstehend',
  'beauftragt',
  'kickoff_gestartet',
  'in_vorbereitung',
  'onboarding_workshop',
  'in_bearbeitung',
  'warten_auf_kunde',
  'fertiggestellt',
  'kundenzufriedenheitsabfrage',
  'abgeschlossen',
  'storniert',
] as const

export const KUNDENSTATUS_LABELS: Record<string, string> = {
  anfrage_eingegangen: 'Anfrage eingegangen',
  in_pruefung: 'In Prüfung',
  angebot_erstellt: 'Angebot erstellt',
  warten_auf_signatur: 'Warten auf Signatur',
  avv_ausstehend: 'AVV ausstehend',
  beauftragt: 'Beauftragt',
  kickoff_gestartet: 'Projekt Kick-Off gestartet',
  in_vorbereitung: 'In Vorbereitung',
  onboarding_workshop: 'Onboarding-Workshop',
  in_bearbeitung: 'In Bearbeitung',
  warten_auf_kunde: 'Warten auf Kunde',
  fertiggestellt: 'Fertiggestellt',
  kundenzufriedenheitsabfrage: 'Kundenzufriedenheitsabfrage',
  abgeschlossen: 'Abgeschlossen',
  storniert: 'Storniert',
}

export const INTERNE_ZWISCHENSCHRITTE = [
  'anfrage_klassifiziert',
  'fachbereich_zugeordnet',
  'kalkulation_in_erstellung',
  'angebot_intern_freigegeben',
  'avv_nicht_erforderlich',
  'avv_geprueft',
  'kickoff_termin_geplant',
  'kickoff_durchgefuehrt',
  'vorbereitung_abgeschlossen',
  'workshop_geplant',
  'workshop_durchgefuehrt',
  'workshop_protokoll_freigegeben',
  'aufgabenpakete_angelegt',
  'abschlussdokumente_erstellt',
  'umfrage_versendet',
  'umfrage_erinnert',
  'feedback_ausgewertet',
] as const

export const PRIORITAET_OPTIONS = ['niedrig', 'mittel', 'hoch'] as const

export const AUFGABE_STATUS_LABELS: Record<string, string> = {
  offen: 'Offen',
  in_bearbeitung: 'In Bearbeitung',
  erledigt: 'Erledigt',
  blockiert: 'Blockiert',
}

export const WORKSHOP_STATUS_LABELS: Record<string, string> = {
  geplant: 'Geplant',
  durchgefuehrt: 'Durchgeführt',
  protokoll_freigegeben: 'Protokoll freigegeben',
  verschoben: 'Verschoben',
}

export const WORKSHOP_TYP_LABELS: Record<string, string> = {
  kickoff: 'Kick-Off',
  onboarding: 'Onboarding',
}

export const ANGEBOT_STATUS_LABELS: Record<string, string> = {
  entwurf: 'Entwurf',
  bereitgestellt: 'Bereitgestellt',
  angenommen: 'Angenommen',
  abgelehnt: 'Abgelehnt',
}

export const AVV_STATUS_LABELS: Record<string, string> = {
  nicht_erforderlich: 'Nicht erforderlich',
  ausstehend: 'Ausstehend',
  versendet: 'Versendet',
  abgeschlossen: 'Abgeschlossen',
}

export const SIGNATUR_STATUS_LABELS: Record<string, string> = {
  erstellt: 'Erstellt',
  versendet: 'Versendet',
  signiert: 'Signiert',
  abgelehnt: 'Abgelehnt',
  fehler: 'Fehler',
  abgelaufen: 'Abgelaufen',
}

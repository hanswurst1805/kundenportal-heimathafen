"""Zentrale Status- und Ereignis-Konstanten aus dem Fachkonzept."""

from __future__ import annotations

# Kundensichtbares Hauptstatusmodell (Reihenfolge 1-15)
KUNDENSTATUS = [
    "anfrage_eingegangen",          # 1
    "in_pruefung",                  # 2
    "angebot_erstellt",             # 3
    "warten_auf_signatur",          # 4
    "avv_ausstehend",                # 5
    "beauftragt",                    # 6
    "kickoff_gestartet",             # 7
    "in_vorbereitung",                # 8
    "onboarding_workshop",            # 9
    "in_bearbeitung",                  # 10
    "warten_auf_kunde",                # 11
    "fertiggestellt",                   # 12
    "kundenzufriedenheitsabfrage",      # 13
    "abgeschlossen",                     # 14
    "storniert",                          # 15
]

KUNDENSTATUS_LABELS = {
    "anfrage_eingegangen": "Anfrage eingegangen",
    "in_pruefung": "In Prüfung",
    "angebot_erstellt": "Angebot erstellt",
    "warten_auf_signatur": "Warten auf Signatur",
    "avv_ausstehend": "AVV ausstehend",
    "beauftragt": "Beauftragt",
    "kickoff_gestartet": "Projekt Kick-Off gestartet",
    "in_vorbereitung": "In Vorbereitung",
    "onboarding_workshop": "Onboarding-Workshop",
    "in_bearbeitung": "In Bearbeitung",
    "warten_auf_kunde": "Warten auf Kunde",
    "fertiggestellt": "Fertiggestellt",
    "kundenzufriedenheitsabfrage": "Kundenzufriedenheitsabfrage",
    "abgeschlossen": "Abgeschlossen",
    "storniert": "Storniert",
}

# Interne Zwischenschritte (Beispiele aus dem Fachkonzept)
INTERNE_ZWISCHENSCHRITTE = [
    "anfrage_klassifiziert",
    "fachbereich_zugeordnet",
    "kalkulation_in_erstellung",
    "angebot_intern_freigegeben",
    "avv_nicht_erforderlich",
    "avv_geprueft",
    "kickoff_termin_geplant",
    "kickoff_durchgefuehrt",
    "vorbereitung_abgeschlossen",
    "workshop_geplant",
    "workshop_durchgefuehrt",
    "workshop_protokoll_freigegeben",
    "aufgabenpakete_angelegt",
    "abschlussdokumente_erstellt",
    "umfrage_versendet",
    "umfrage_erinnert",
    "feedback_ausgewertet",
]

# Ereignistypen fuer die Statusautomatisierung (Trigger-Tabelle)
EVENT_SIGNATURE_COMPLETED = "signature_completed"
EVENT_AVV_REQUIRED = "avv_required"
EVENT_AVV_COMPLETED = "avv_completed"
EVENT_KICKOFF_SCHEDULED = "kickoff_scheduled"
EVENT_ONBOARDING_WORKSHOP_SCHEDULED = "onboarding_workshop_scheduled"
EVENT_ONBOARDING_WORKSHOP_FINISHED = "onboarding_workshop_finished"
EVENT_CUSTOMER_INPUT_REQUIRED = "customer_input_required"
EVENT_DELIVERY_COMPLETED = "delivery_completed"
EVENT_SURVEY_SENT = "survey_sent"

ALL_EVENT_TYPES = [
    EVENT_SIGNATURE_COMPLETED,
    EVENT_AVV_REQUIRED,
    EVENT_AVV_COMPLETED,
    EVENT_KICKOFF_SCHEDULED,
    EVENT_ONBOARDING_WORKSHOP_SCHEDULED,
    EVENT_ONBOARDING_WORKSHOP_FINISHED,
    EVENT_CUSTOMER_INPUT_REQUIRED,
    EVENT_DELIVERY_COMPLETED,
    EVENT_SURVEY_SENT,
]

# Benachrichtigungs-Stufen fuer StatusRegel
NOTIFY_JA = "ja"
NOTIFY_OPTIONAL = "optional"
NOTIFY_NEIN = "nein"

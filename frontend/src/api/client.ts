const BASE = '/api/v1'
const AUTH = '/auth'

// ---------------------------------------------------------------------------
// HTTP-Helper
// ---------------------------------------------------------------------------

function getToken() {
  return localStorage.getItem('token')
}

export function getRole(): string | null {
  return localStorage.getItem('role')
}

export function getCustomerId(): string | null {
  return localStorage.getItem('customer_id')
}

function storeSession(data: LoginResult) {
  if (!data.access_token) return
  localStorage.setItem('token', data.access_token)
}

async function req<T>(path: string, opts?: RequestInit & { auth?: boolean }): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts?.headers as Record<string, string>),
  }
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  const res = await fetch((opts?.auth ? AUTH : BASE) + path, { ...opts, headers })
  if (res.status === 401) {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    localStorage.removeItem('customer_id')
    window.location.href = '/login'
    throw new Error('Nicht authentifiziert')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? `${res.status} ${res.statusText}`)
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

// ---------------------------------------------------------------------------
// Auth-Typen
// ---------------------------------------------------------------------------

export type Role = 'admin' | 'user' | 'kunde'

export interface LoginResult {
  mfa_required: boolean
  mfa_token?: string
  access_token?: string
  token_type?: string
  needs_2fa_setup: boolean
}

export interface UserMe {
  id: string
  username: string
  role: Role
  customer_id: string | null
  display_name: string | null
  totp_enabled: boolean
  totp_required: boolean
}

export interface TOTPSetup {
  secret: string
  provisioning_uri: string
}

export interface TOTPEnableResult {
  backup_codes: string[]
}

// ---------------------------------------------------------------------------
// Fachobjekt-Typen (Kundensicht)
// ---------------------------------------------------------------------------

export interface Leistung {
  id: string
  leistungs_id: string
  name: string
  beschreibung: string | null
  kategorie: string | null
  preis: string
  preiseinheit: string
  avv_erforderlich: boolean
  ist_bestellbar: boolean
  is_active: boolean
}

export interface Anfrage {
  id: string
  anfrage_nr: string
  customer_id: string
  thema: string
  beschreibung: string | null
  fachbereich: string | null
  prioritaet: string
  status_kunde: string
  created_at: string
}

export interface AnfrageCreate {
  thema: string
  beschreibung?: string
  fachbereich?: string
  prioritaet?: string
}

export interface AngebotPosition {
  id: string
  bezeichnung: string
  menge: string
  einzelpreis: string
  gesamtpreis: string
  sort_order: number
}

export interface Angebot {
  id: string
  angebotsnummer: string
  version: number
  customer_id: string
  anfrage_id: string | null
  leistung_id: string | null
  titel: string
  gueltig_bis: string | null
  gesamtpreis: string
  status: string
  positionen: AngebotPosition[]
}

export interface Bestellung {
  id: string
  bestell_nr: string
  customer_id: string
  leistung_id: string
  besteller_id: string | null
  bestelldatum: string
  status: string
  angebot_id: string | null
}

export interface Signaturvorgang {
  id: string
  bezugstyp: string
  bezugs_id: string
  anbieter: string
  token: string | null
  signatur_link: string | null
  status: string
  versandzeit: string | null
  signierzeit: string | null
  erinnerung_gesendet_am: string | null
}

export interface AVV {
  id: string
  customer_id: string
  bezugstyp: string
  bezugs_id: string
  pflicht: boolean
  vorlage_id: string | null
  version: string | null
  status: string
  signaturvorgang_id: string | null
  abschlussdatum: string | null
}

export interface Auftrag {
  id: string
  auftragsnummer: string
  customer_id: string
  ursprung_typ: string
  ursprung_id: string
  status: string
  freigabedatum: string | null
}

export interface Auftragsbestaetigung {
  id: string
  auftrag_id: string
  dokument_id: string | null
  bereitgestellt_am: string | null
  kenntnisnahme_am: string | null
}

export interface Aufgabe {
  id: string
  titel: string
  beschreibung: string | null
  zustaendigkeit_id: string | null
  faelligkeit: string | null
  status: string
  sort_order: number
}

export interface Workshop {
  id: string
  typ: string
  termin: string | null
  teilnehmer: unknown[] | null
  protokoll: string | null
  status: string
}

export interface Leistungsschein {
  id: string
  ls_nummer: string
  auftrag_id: string
  leistung_id: string | null
  scope_beschreibung: string | null
  startdatum: string | null
  kickoff_datum: string | null
  workshop_datum: string | null
  solltermin: string | null
  status_kunde: string
  naechster_schritt: string | null
  voraussetzungen: string | null
  onboarding_ziele: string | null
  onboarding_offene_punkte: string | null
  aufgaben: Aufgabe[]
  workshops: Workshop[]
}

export interface Dokument {
  id: string
  customer_id: string
  typ: string
  version: number
  sichtbarkeit: string
  dateiname: string
  bezugstyp: string | null
  bezugs_id: string | null
  leistungsschein_id: string | null
  created_at: string
}

export interface Umfrage {
  id: string
  leistungsschein_id: string
  customer_id: string
  versandzeit: string | null
  erinnert_am: string | null
  status: string
  bewertung: number | null
  kommentar: string | null
  beantwortet_am: string | null
}

export interface UmfrageAntwort {
  bewertung: number
  kommentar?: string
}

export interface DashboardData {
  offene_bestellungen: Bestellung[]
  offene_anfragen: Anfrage[]
  laufende_leistungsscheine: Leistungsschein[]
}

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

export const api = {
  auth: {
    async login(username: string, password: string): Promise<LoginResult> {
      const body = new URLSearchParams({ username, password })
      const result = await req<LoginResult>('/login', {
        method: 'POST',
        auth: true,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      })
      if (!result.mfa_required) storeSession(result)
      return result
    },

    async verify2FA(mfa_token: string, code: string): Promise<LoginResult> {
      const result = await req<LoginResult>('/2fa/verify', {
        method: 'POST',
        auth: true,
        body: JSON.stringify({ mfa_token, code }),
      })
      storeSession(result)
      return result
    },

    async me(): Promise<UserMe> {
      const user = await req<UserMe>('/me', { auth: true })
      localStorage.setItem('role', user.role)
      localStorage.setItem('customer_id', user.customer_id ?? '')
      return user
    },

    setup2FA(): Promise<TOTPSetup> {
      return req<TOTPSetup>('/2fa/setup', { method: 'POST', auth: true })
    },

    enable2FA(code: string): Promise<TOTPEnableResult> {
      return req<TOTPEnableResult>('/2fa/enable', {
        method: 'POST',
        auth: true,
        body: JSON.stringify({ code }),
      })
    },

    disable2FA(code: string): Promise<void> {
      return req<void>('/2fa/disable', {
        method: 'POST',
        auth: true,
        body: JSON.stringify({ code }),
      })
    },

    changePassword(current_password: string, new_password: string): Promise<void> {
      return req<void>('/change-password', {
        method: 'POST',
        auth: true,
        body: JSON.stringify({ current_password, new_password }),
      })
    },

    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('customer_id')
    },

    getToken,
    getRole,
  },

  portal: {
    dashboard(): Promise<DashboardData> {
      return req<DashboardData>('/portal/dashboard')
    },

    catalog: {
      list(): Promise<Leistung[]> {
        return req<Leistung[]>('/portal/leistungen')
      },
    },

    bestellungen: {
      list(): Promise<Bestellung[]> {
        return req<Bestellung[]>('/portal/bestellungen')
      },
      get(id: string): Promise<Bestellung> {
        return req<Bestellung>(`/portal/bestellungen/${id}`)
      },
      create(leistung_id: string): Promise<Bestellung> {
        return req<Bestellung>('/portal/bestellungen', {
          method: 'POST',
          body: JSON.stringify({ leistung_id }),
        })
      },
    },

    anfragen: {
      list(): Promise<Anfrage[]> {
        return req<Anfrage[]>('/portal/anfragen')
      },
      create(data: AnfrageCreate): Promise<Anfrage> {
        return req<Anfrage>('/portal/anfragen', {
          method: 'POST',
          body: JSON.stringify(data),
        })
      },
    },

    angebote: {
      list(): Promise<Angebot[]> {
        return req<Angebot[]>('/portal/angebote')
      },
      get(id: string): Promise<Angebot> {
        return req<Angebot>(`/portal/angebote/${id}`)
      },
      ablehnen(id: string, begruendung?: string): Promise<Angebot> {
        return req<Angebot>(`/portal/angebote/${id}/ablehnen`, {
          method: 'POST',
          body: JSON.stringify({ begruendung }),
        })
      },
    },

    signatur: {
      listByBezug(bezugstyp: string, bezugsId: string): Promise<Signaturvorgang[]> {
        return req<Signaturvorgang[]>(`/portal/signatur/by-bezug/${bezugstyp}/${bezugsId}`)
      },
      get(token: string): Promise<Signaturvorgang> {
        return req<Signaturvorgang>(`/portal/signatur/${token}`)
      },
      signieren(token: string): Promise<Signaturvorgang> {
        return req<Signaturvorgang>(`/portal/signatur/${token}/signieren`, { method: 'POST' })
      },
    },

    avv: {
      list(): Promise<AVV[]> {
        return req<AVV[]>('/portal/avv')
      },
      annehmen(id: string): Promise<AVV> {
        return req<AVV>(`/portal/avv/${id}/annehmen`, { method: 'POST' })
      },
    },

    auftraege: {
      list(): Promise<Auftrag[]> {
        return req<Auftrag[]>('/portal/auftraege')
      },
      get(id: string): Promise<Auftrag> {
        return req<Auftrag>(`/portal/auftraege/${id}`)
      },
      getAuftragsbestaetigung(auftragId: string): Promise<Auftragsbestaetigung> {
        return req<Auftragsbestaetigung>(`/portal/auftraege/${auftragId}/auftragsbestaetigung`)
      },
      kenntnisnahme(auftragId: string): Promise<Auftragsbestaetigung> {
        return req<Auftragsbestaetigung>(`/portal/auftraege/${auftragId}/auftragsbestaetigung/kenntnisnahme`, {
          method: 'POST',
        })
      },
    },

    leistungsscheine: {
      list(): Promise<Leistungsschein[]> {
        return req<Leistungsschein[]>('/portal/leistungsscheine')
      },
      get(id: string): Promise<Leistungsschein> {
        return req<Leistungsschein>(`/portal/leistungsscheine/${id}`)
      },
    },

    dokumente: {
      list(): Promise<Dokument[]> {
        return req<Dokument[]>('/portal/dokumente')
      },
    },

    umfragen: {
      list(): Promise<Umfrage[]> {
        return req<Umfrage[]>('/portal/umfragen')
      },
      beantworten(id: string, data: UmfrageAntwort): Promise<Umfrage> {
        return req<Umfrage>(`/portal/umfragen/${id}/beantworten`, {
          method: 'POST',
          body: JSON.stringify(data),
        })
      },
    },
  },
}

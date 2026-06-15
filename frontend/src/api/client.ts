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
    if (window.location.pathname !== '/login') {
      const ziel = window.location.pathname + window.location.search
      window.location.href = `/login?redirect=${encodeURIComponent(ziel)}`
    }
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
  qr_code: string
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
// Fachobjekt-Typen (Interne Sicht)
// ---------------------------------------------------------------------------

export interface AnfrageIntern extends Anfrage {
  ersteller_id: string | null
  status_intern: string | null
  angebot_id: string | null
}

export interface AnfrageInternUpdate {
  fachbereich?: string
  prioritaet?: string
  status_intern?: string
  status_kunde?: string
}

export interface AngebotCreate {
  customer_id: string
  anfrage_id?: string
  leistung_id?: string
  titel: string
  gueltig_bis?: string
  positionen: { bezeichnung: string; menge: string; einzelpreis: string; sort_order?: number }[]
}

export interface AngebotUpdate {
  titel?: string
  gueltig_bis?: string
  positionen?: { bezeichnung: string; menge: string; einzelpreis: string; sort_order?: number }[]
}

export interface LeistungsscheinIntern extends Leistungsschein {
  customer_id: string
  verantwortlicher_id: string | null
  status_intern: string | null
  onboarding_teilnehmer: unknown[] | null
  lessons_learned: string | null
  abschlussstatus: string | null
}

export interface LeistungsscheinInternUpdate {
  scope_beschreibung?: string
  verantwortlicher_id?: string
  startdatum?: string
  kickoff_datum?: string
  workshop_datum?: string
  solltermin?: string
  status_kunde?: string
  status_intern?: string
  naechster_schritt?: string
  voraussetzungen?: string
  onboarding_ziele?: string
  onboarding_offene_punkte?: string
  lessons_learned?: string
  abschlussstatus?: string
}

export interface AufgabeCreate {
  titel: string
  beschreibung?: string
  zustaendigkeit_id?: string
  faelligkeit?: string
  sort_order?: number
}

export interface AufgabeUpdate {
  titel?: string
  beschreibung?: string
  zustaendigkeit_id?: string
  faelligkeit?: string
  status?: string
  sort_order?: number
}

export interface WorkshopCreate {
  typ: string
  termin?: string
  teilnehmer?: unknown[]
}

export interface WorkshopUpdate {
  termin?: string
  teilnehmer?: unknown[]
  protokoll?: string
  status?: string
}

export interface AVVVorlage {
  id: string
  name: string
  version: string
  inhalt: string | null
  is_active: boolean
}

export interface AVVVorlageCreate {
  name: string
  version?: string
  inhalt?: string
  is_active?: boolean
}

export interface AVVVorlageUpdate {
  name?: string
  version?: string
  inhalt?: string
  is_active?: boolean
}

export interface Customer {
  id: string
  kundennummer: string
  name: string
  short_name: string | null
  contact_name: string | null
  contact_email: string | null
  contact_phone: string | null
  address: string | null
  is_active: boolean
}

export interface CustomerCreate {
  kundennummer: string
  name: string
  short_name?: string
  contact_name?: string
  contact_email?: string
  contact_phone?: string
  address?: string
}

export interface CustomerUpdate {
  name?: string
  short_name?: string
  contact_name?: string
  contact_email?: string
  contact_phone?: string
  address?: string
  is_active?: boolean
}

export interface InternUser {
  id: string
  username: string
  role: string
  customer_id: string | null
  display_name: string | null
  is_active: boolean
  totp_enabled: boolean
  totp_required: boolean
}

export interface InternUserCreate {
  username: string
  password: string
  role: string
  customer_id?: string
  display_name?: string
}

export interface InternUserUpdate {
  display_name?: string
  is_active?: boolean
  role?: string
  customer_id?: string | null
}

export interface LeistungCreate {
  leistungs_id: string
  name: string
  beschreibung?: string
  kategorie?: string
  preis: string
  preiseinheit?: string
  avv_erforderlich?: boolean
  ist_bestellbar?: boolean
  is_active?: boolean
}

export interface LeistungUpdate {
  name?: string
  beschreibung?: string
  kategorie?: string
  preis?: string
  preiseinheit?: string
  avv_erforderlich?: boolean
  ist_bestellbar?: boolean
  is_active?: boolean
}

export interface StatusRegel {
  id: string
  ereignis_typ: string
  ziel_status_kunde: string
  benachrichtigung: string
  aktiv: boolean
  beschreibung: string | null
}

export interface StatusRegelUpdate {
  ziel_status_kunde?: string
  benachrichtigung?: string
  aktiv?: boolean
  beschreibung?: string
}

export interface Ereignis {
  id: string
  zeit: string
  customer_id: string | null
  akteur_id: string | null
  akteur_typ: string
  ereignis_typ: string
  bezugstyp: string | null
  bezugs_id: string | null
  vorher_status: string | null
  nachher_status: string | null
  payload: Record<string, unknown> | null
  verarbeitet: boolean
}

export interface MonitoringUebersicht {
  offene_anfragen: number
  offene_bestellungen: number
  laufende_leistungsscheine: number
  unverarbeitete_ereignisse: number
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
      signieren(
        token: string,
        payload?: { signatur_bild?: string; unterzeichner_name?: string },
      ): Promise<Signaturvorgang> {
        return req<Signaturvorgang>(`/portal/signatur/${token}/signieren`, {
          method: 'POST',
          body: JSON.stringify(payload ?? {}),
        })
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
      async download(id: string, dateiname: string): Promise<void> {
        const res = await fetch(`${BASE}/portal/dokumente/${id}/download`, {
          headers: { Authorization: `Bearer ${getToken()}` },
        })
        if (!res.ok) throw new Error('Download fehlgeschlagen')
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = dateiname
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
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

  intern: {
    anfragen: {
      list(): Promise<AnfrageIntern[]> {
        return req<AnfrageIntern[]>('/intern/anfragen')
      },
      get(id: string): Promise<AnfrageIntern> {
        return req<AnfrageIntern>(`/intern/anfragen/${id}`)
      },
      update(id: string, data: AnfrageInternUpdate): Promise<AnfrageIntern> {
        return req<AnfrageIntern>(`/intern/anfragen/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
      },
      createAngebot(id: string, data: AngebotCreate): Promise<Angebot> {
        return req<Angebot>(`/intern/anfragen/${id}/angebot`, { method: 'POST', body: JSON.stringify(data) })
      },
    },

    angebote: {
      list(): Promise<Angebot[]> {
        return req<Angebot[]>('/intern/angebote')
      },
      get(id: string): Promise<Angebot> {
        return req<Angebot>(`/intern/angebote/${id}`)
      },
      update(id: string, data: AngebotUpdate): Promise<Angebot> {
        return req<Angebot>(`/intern/angebote/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
      },
      bereitstellen(id: string): Promise<Angebot> {
        return req<Angebot>(`/intern/angebote/${id}/bereitstellen`, { method: 'POST' })
      },
    },

    bestellungen: {
      list(): Promise<Bestellung[]> {
        return req<Bestellung[]>('/intern/bestellungen')
      },
      get(id: string): Promise<Bestellung> {
        return req<Bestellung>(`/intern/bestellungen/${id}`)
      },
    },

    auftraege: {
      list(): Promise<Auftrag[]> {
        return req<Auftrag[]>('/intern/auftraege')
      },
      get(id: string): Promise<Auftrag> {
        return req<Auftrag>(`/intern/auftraege/${id}`)
      },
      getAuftragsbestaetigung(id: string): Promise<Auftragsbestaetigung> {
        return req<Auftragsbestaetigung>(`/intern/auftraege/${id}/auftragsbestaetigung`)
      },
    },

    leistungsscheine: {
      list(): Promise<LeistungsscheinIntern[]> {
        return req<LeistungsscheinIntern[]>('/intern/leistungsscheine')
      },
      get(id: string): Promise<LeistungsscheinIntern> {
        return req<LeistungsscheinIntern>(`/intern/leistungsscheine/${id}`)
      },
      update(id: string, data: LeistungsscheinInternUpdate): Promise<LeistungsscheinIntern> {
        return req<LeistungsscheinIntern>(`/intern/leistungsscheine/${id}`, {
          method: 'PATCH',
          body: JSON.stringify(data),
        })
      },
      kundenrueckfrage(id: string): Promise<LeistungsscheinIntern> {
        return req<LeistungsscheinIntern>(`/intern/leistungsscheine/${id}/kundenrueckfrage`, { method: 'POST' })
      },
      abschliessen(id: string): Promise<LeistungsscheinIntern> {
        return req<LeistungsscheinIntern>(`/intern/leistungsscheine/${id}/abschliessen`, { method: 'POST' })
      },
      aufgaben: {
        create(lsId: string, data: AufgabeCreate): Promise<Aufgabe> {
          return req<Aufgabe>(`/intern/leistungsscheine/${lsId}/aufgaben`, {
            method: 'POST',
            body: JSON.stringify(data),
          })
        },
        update(lsId: string, aufgabeId: string, data: AufgabeUpdate): Promise<Aufgabe> {
          return req<Aufgabe>(`/intern/leistungsscheine/${lsId}/aufgaben/${aufgabeId}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          })
        },
        delete(lsId: string, aufgabeId: string): Promise<void> {
          return req<void>(`/intern/leistungsscheine/${lsId}/aufgaben/${aufgabeId}`, { method: 'DELETE' })
        },
      },
      workshops: {
        create(lsId: string, data: WorkshopCreate): Promise<Workshop> {
          return req<Workshop>(`/intern/leistungsscheine/${lsId}/workshops`, {
            method: 'POST',
            body: JSON.stringify(data),
          })
        },
        update(lsId: string, workshopId: string, data: WorkshopUpdate): Promise<Workshop> {
          return req<Workshop>(`/intern/leistungsscheine/${lsId}/workshops/${workshopId}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
          })
        },
      },
    },

    avv: {
      list(): Promise<AVV[]> {
        return req<AVV[]>('/intern/avv')
      },
      get(id: string): Promise<AVV> {
        return req<AVV>(`/intern/avv/${id}`)
      },
      vorlagen: {
        list(): Promise<AVVVorlage[]> {
          return req<AVVVorlage[]>('/intern/avv-vorlagen')
        },
        create(data: AVVVorlageCreate): Promise<AVVVorlage> {
          return req<AVVVorlage>('/intern/avv-vorlagen', { method: 'POST', body: JSON.stringify(data) })
        },
        update(id: string, data: AVVVorlageUpdate): Promise<AVVVorlage> {
          return req<AVVVorlage>(`/intern/avv-vorlagen/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
        },
      },
    },

    signaturen: {
      list(): Promise<Signaturvorgang[]> {
        return req<Signaturvorgang[]>('/intern/signaturen')
      },
      get(id: string): Promise<Signaturvorgang> {
        return req<Signaturvorgang>(`/intern/signaturen/${id}`)
      },
      erinnerung(id: string): Promise<Signaturvorgang> {
        return req<Signaturvorgang>(`/intern/signaturen/${id}/erinnerung`, { method: 'POST' })
      },
      retry(id: string): Promise<Signaturvorgang> {
        return req<Signaturvorgang>(`/intern/signaturen/${id}/retry`, { method: 'POST' })
      },
    },

    dokumente: {
      list(params?: { bezugstyp?: string; bezugs_id?: string; customer_id?: string }): Promise<Dokument[]> {
        const q = new URLSearchParams()
        if (params?.bezugstyp) q.set('bezugstyp', params.bezugstyp)
        if (params?.bezugs_id) q.set('bezugs_id', params.bezugs_id)
        if (params?.customer_id) q.set('customer_id', params.customer_id)
        const qs = q.toString()
        return req<Dokument[]>(`/intern/dokumente${qs ? `?${qs}` : ''}`)
      },
      async download(id: string, dateiname: string): Promise<void> {
        const res = await fetch(`${BASE}/intern/dokumente/${id}/download`, {
          headers: { Authorization: `Bearer ${getToken()}` },
        })
        if (!res.ok) throw new Error('Download fehlgeschlagen')
        const blob = await res.blob()
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = dateiname
        document.body.appendChild(a)
        a.click()
        a.remove()
        URL.revokeObjectURL(url)
      },
    },

    monitoring: {
      uebersicht(): Promise<MonitoringUebersicht> {
        return req<MonitoringUebersicht>('/intern/monitoring/uebersicht')
      },
      ereignisse(params?: { verarbeitet?: boolean; ereignis_typ?: string; limit?: number }): Promise<Ereignis[]> {
        const query = new URLSearchParams()
        if (params?.verarbeitet !== undefined) query.set('verarbeitet', String(params.verarbeitet))
        if (params?.ereignis_typ) query.set('ereignis_typ', params.ereignis_typ)
        if (params?.limit) query.set('limit', String(params.limit))
        const qs = query.toString()
        return req<Ereignis[]>(`/intern/monitoring/ereignisse${qs ? `?${qs}` : ''}`)
      },
    },

    kunden: {
      list(): Promise<Customer[]> {
        return req<Customer[]>('/intern/kunden')
      },
      get(id: string): Promise<Customer> {
        return req<Customer>(`/intern/kunden/${id}`)
      },
      create(data: CustomerCreate): Promise<Customer> {
        return req<Customer>('/intern/kunden', { method: 'POST', body: JSON.stringify(data) })
      },
      update(id: string, data: CustomerUpdate): Promise<Customer> {
        return req<Customer>(`/intern/kunden/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
      },
    },

    leistungen: {
      list(): Promise<Leistung[]> {
        return req<Leistung[]>('/intern/leistungen')
      },
      get(id: string): Promise<Leistung> {
        return req<Leistung>(`/intern/leistungen/${id}`)
      },
      create(data: LeistungCreate): Promise<Leistung> {
        return req<Leistung>('/intern/leistungen', { method: 'POST', body: JSON.stringify(data) })
      },
      update(id: string, data: LeistungUpdate): Promise<Leistung> {
        return req<Leistung>(`/intern/leistungen/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
      },
    },

    umfragen: {
      list(): Promise<Umfrage[]> {
        return req<Umfrage[]>('/intern/umfragen')
      },
      get(id: string): Promise<Umfrage> {
        return req<Umfrage>(`/intern/umfragen/${id}`)
      },
    },

    statusregeln: {
      list(): Promise<StatusRegel[]> {
        return req<StatusRegel[]>('/intern/statusregeln')
      },
      update(id: string, data: StatusRegelUpdate): Promise<StatusRegel> {
        return req<StatusRegel>(`/intern/statusregeln/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
      },
    },

    users: {
      list(): Promise<InternUser[]> {
        return req<InternUser[]>('/intern/users')
      },
      get(id: string): Promise<InternUser> {
        return req<InternUser>(`/intern/users/${id}`)
      },
      create(data: InternUserCreate): Promise<InternUser> {
        return req<InternUser>('/intern/users', { method: 'POST', body: JSON.stringify(data) })
      },
      update(id: string, data: InternUserUpdate): Promise<InternUser> {
        return req<InternUser>(`/intern/users/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
      },
      resetPassword(id: string, new_password: string): Promise<void> {
        return req<void>(`/intern/users/${id}/reset-password`, {
          method: 'POST',
          body: JSON.stringify({ new_password }),
        })
      },
      reset2FA(id: string): Promise<{ totp_enabled: boolean }> {
        return req<{ totp_enabled: boolean }>(`/intern/users/${id}/reset-2fa`, { method: 'POST' })
      },
    },
  },
}

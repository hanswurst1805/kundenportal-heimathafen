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
}

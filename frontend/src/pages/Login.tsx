import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { Anchor, KeyRound } from 'lucide-react'

// Nur interne Pfade als Redirect-Ziel zulassen (kein offener Redirect).
function sicheresZiel(redirect: string | null): string | null {
  if (!redirect || !redirect.startsWith('/') || redirect.startsWith('//')) return null
  return redirect
}

export default function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [code, setCode] = useState('')
  const [mfaToken, setMfaToken] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function afterLogin() {
    const me = await api.auth.me()
    const ziel = sicheresZiel(searchParams.get('redirect'))
    if (me.role === 'kunde') {
      navigate(ziel ?? '/portal')
    } else if (me.totp_required && !me.totp_enabled) {
      navigate('/einstellungen')
    } else {
      navigate(ziel ?? '/intern')
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const result = await api.auth.login(username, password)
      if (result.mfa_required && result.mfa_token) {
        setMfaToken(result.mfa_token)
      } else {
        await afterLogin()
      }
    } catch {
      setError('Benutzername oder Passwort falsch')
    } finally {
      setLoading(false)
    }
  }

  async function submitCode(e: React.FormEvent) {
    e.preventDefault()
    if (!mfaToken) return
    setError('')
    setLoading(true)
    try {
      await api.auth.verify2FA(mfaToken, code)
      await afterLogin()
    } catch {
      setError('Code ungültig')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-sky-600 rounded-2xl mb-4">
            <Anchor size={28} />
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white">Heimathafen</h1>
          <p className="text-slate-500 text-sm mt-1">Kundenportal</p>
        </div>

        {!mfaToken && (
          <form onSubmit={submit} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Benutzername</label>
              <input
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoFocus
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">Passwort</label>
              <input
                type="password"
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
                value={password}
                onChange={e => setPassword(e.target.value)}
              />
            </div>

            {error && (
              <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium py-2 rounded-lg transition-colors"
            >
              {loading ? 'Anmelden…' : 'Anmelden'}
            </button>
          </form>
        )}

        {mfaToken && (
          <form onSubmit={submitCode} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-slate-300">
              <KeyRound size={16} />
              <span className="text-sm font-medium">Zwei-Faktor-Authentifizierung</span>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">
                Code aus der Authenticator-App oder Backup-Code
              </label>
              <input
                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-sky-500 font-mono tracking-widest"
                value={code}
                onChange={e => setCode(e.target.value)}
                placeholder="123456"
                autoFocus
              />
            </div>

            {error && (
              <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading || !code}
              className="w-full bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium py-2 rounded-lg transition-colors"
            >
              {loading ? 'Prüfe…' : 'Bestätigen'}
            </button>
            <button
              type="button"
              onClick={() => { setMfaToken(null); setCode(''); setError('') }}
              className="w-full text-xs text-slate-500 hover:text-slate-300"
            >
              Zurück zum Login
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

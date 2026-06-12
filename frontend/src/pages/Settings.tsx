import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { KeyRound, ShieldCheck, ShieldOff, Lock } from 'lucide-react'

export default function Settings() {
  const queryClient = useQueryClient()
  const { data: me, isLoading } = useQuery({ queryKey: ['me'], queryFn: api.auth.me })

  const [setupSecret, setSetupSecret] = useState<string | null>(null)
  const [setupUri, setSetupUri] = useState<string | null>(null)
  const [enableCode, setEnableCode] = useState('')
  const [disableCode, setDisableCode] = useState('')
  const [backupCodes, setBackupCodes] = useState<string[] | null>(null)
  const [error, setError] = useState('')

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [pwInfo, setPwInfo] = useState('')

  async function startSetup() {
    setError('')
    try {
      const setup = await api.auth.setup2FA()
      setSetupSecret(setup.secret)
      setSetupUri(setup.provisioning_uri)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Setup fehlgeschlagen')
    }
  }

  async function confirmEnable(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      const result = await api.auth.enable2FA(enableCode)
      setBackupCodes(result.backup_codes)
      setSetupSecret(null)
      setSetupUri(null)
      setEnableCode('')
      await queryClient.invalidateQueries({ queryKey: ['me'] })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Code ungültig')
    }
  }

  async function disable(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api.auth.disable2FA(disableCode)
      setDisableCode('')
      await queryClient.invalidateQueries({ queryKey: ['me'] })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Code ungültig')
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault()
    setPwInfo('')
    try {
      await api.auth.changePassword(currentPw, newPw)
      setCurrentPw('')
      setNewPw('')
      setPwInfo('Passwort wurde geändert.')
    } catch (e) {
      setPwInfo(e instanceof Error ? e.message : 'Änderung fehlgeschlagen')
    }
  }

  if (isLoading || !me) {
    return <p className="text-slate-500 text-sm">Lade…</p>
  }

  return (
    <div className="max-w-xl space-y-6">
      <h1 className="text-xl font-semibold text-white">Einstellungen</h1>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-2">
        <h2 className="text-sm font-medium text-slate-300">Konto</h2>
        <p className="text-sm text-slate-400">
          Benutzername: <span className="text-slate-200">{me.username}</span>
        </p>
        <p className="text-sm text-slate-400">
          Rolle: <span className="text-slate-200">{me.role}</span>
        </p>
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-slate-300">
          <KeyRound size={16} />
          <h2 className="text-sm font-medium">Zwei-Faktor-Authentifizierung</h2>
        </div>

        {me.totp_enabled ? (
          <div className="space-y-3">
            <p className="text-sm text-emerald-400 flex items-center gap-1.5">
              <ShieldCheck size={14} /> Aktiviert
            </p>
            {me.totp_required ? (
              <p className="text-xs text-slate-500">
                Für deine Rolle ist 2FA verpflichtend und kann nicht deaktiviert werden.
              </p>
            ) : (
              <form onSubmit={disable} className="space-y-2">
                <label className="block text-xs text-slate-400">
                  Zum Deaktivieren aktuellen Code eingeben
                </label>
                <div className="flex gap-2">
                  <input
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono tracking-widest focus:outline-none focus:ring-1 focus:ring-sky-500"
                    value={disableCode}
                    onChange={e => setDisableCode(e.target.value)}
                    placeholder="123456"
                  />
                  <button
                    type="submit"
                    disabled={!disableCode}
                    className="bg-red-700 hover:bg-red-600 disabled:opacity-40 text-white text-sm font-medium px-4 rounded-lg flex items-center gap-1.5"
                  >
                    <ShieldOff size={14} /> Deaktivieren
                  </button>
                </div>
              </form>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <p className="text-sm text-amber-400">
              {me.totp_required
                ? 'Zwei-Faktor-Authentifizierung ist für deine Rolle erforderlich.'
                : '2FA ist derzeit nicht aktiviert.'}
            </p>

            {!setupSecret && !backupCodes && (
              <button
                onClick={startSetup}
                className="bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium px-4 py-2 rounded-lg"
              >
                2FA einrichten
              </button>
            )}

            {setupSecret && (
              <form onSubmit={confirmEnable} className="space-y-3">
                <div className="text-sm text-slate-400 space-y-1">
                  <p>
                    Secret manuell in der Authenticator-App hinterlegen:
                  </p>
                  <p className="font-mono text-xs bg-slate-800 rounded-lg px-3 py-2 break-all text-slate-200">
                    {setupSecret}
                  </p>
                  {setupUri && (
                    <p className="font-mono text-xs bg-slate-800 rounded-lg px-3 py-2 break-all text-slate-400">
                      {setupUri}
                    </p>
                  )}
                </div>
                <label className="block text-xs text-slate-400">Code aus der App eingeben</label>
                <div className="flex gap-2">
                  <input
                    className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 font-mono tracking-widest focus:outline-none focus:ring-1 focus:ring-sky-500"
                    value={enableCode}
                    onChange={e => setEnableCode(e.target.value)}
                    placeholder="123456"
                    autoFocus
                  />
                  <button
                    type="submit"
                    disabled={!enableCode}
                    className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 rounded-lg"
                  >
                    Aktivieren
                  </button>
                </div>
              </form>
            )}

            {backupCodes && (
              <div className="space-y-2">
                <p className="text-sm text-emerald-400 flex items-center gap-1.5">
                  <ShieldCheck size={14} /> 2FA wurde aktiviert.
                </p>
                <p className="text-xs text-slate-400">
                  Backup-Codes (jeweils einmal verwendbar, bitte sicher aufbewahren):
                </p>
                <div className="grid grid-cols-2 gap-2 font-mono text-xs text-slate-200 bg-slate-800 rounded-lg p-3">
                  {backupCodes.map(c => (
                    <span key={c}>{c}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {error && (
          <p className="text-sm text-red-400 bg-red-950 border border-red-800 rounded-lg px-3 py-2">
            {error}
          </p>
        )}
      </section>

      <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
        <div className="flex items-center gap-2 text-slate-300">
          <Lock size={16} />
          <h2 className="text-sm font-medium">Passwort ändern</h2>
        </div>
        <form onSubmit={changePassword} className="space-y-2">
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Aktuelles Passwort</label>
            <input
              type="password"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
              value={currentPw}
              onChange={e => setCurrentPw(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Neues Passwort</label>
            <input
              type="password"
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-sky-500"
              value={newPw}
              onChange={e => setNewPw(e.target.value)}
            />
          </div>
          {pwInfo && <p className="text-sm text-slate-400">{pwInfo}</p>}
          <button
            type="submit"
            disabled={!currentPw || !newPw}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
          >
            Passwort ändern
          </button>
        </form>
      </section>
    </div>
  )
}

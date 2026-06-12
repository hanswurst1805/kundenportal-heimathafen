import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../api/client'
import { Plus, KeyRound, ShieldOff } from 'lucide-react'

const ROLES = ['admin', 'user', 'kunde'] as const

export default function Benutzer() {
  const queryClient = useQueryClient()
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<string>('user')
  const [displayName, setDisplayName] = useState('')
  const [customerId, setCustomerId] = useState('')

  const { data: users, isLoading } = useQuery({ queryKey: ['intern', 'users'], queryFn: api.intern.users.list })
  const { data: kunden } = useQuery({ queryKey: ['intern', 'kunden'], queryFn: api.intern.kunden.list, enabled: role === 'kunde' })

  const create = useMutation({
    mutationFn: () => api.intern.users.create({
      username,
      password,
      role,
      display_name: displayName || undefined,
      customer_id: role === 'kunde' ? (customerId || undefined) : undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['intern', 'users'] })
      setUsername('')
      setPassword('')
      setDisplayName('')
      setCustomerId('')
      setRole('user')
      setShowForm(false)
    },
    onError: (e: Error) => setError(e.message),
  })

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => api.intern.users.update(id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'users'] }),
    onError: (e: Error) => setError(e.message),
  })

  const resetPassword = useMutation({
    mutationFn: (id: string) => {
      const newPassword = window.prompt('Neues Passwort eingeben:')
      if (!newPassword) return Promise.reject(new Error('Abgebrochen'))
      return api.intern.users.resetPassword(id, newPassword)
    },
    onError: (e: Error) => { if (e.message !== 'Abgebrochen') setError(e.message) },
  })

  const reset2FA = useMutation({
    mutationFn: (id: string) => api.intern.users.reset2FA(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['intern', 'users'] }),
    onError: (e: Error) => setError(e.message),
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">Benutzerverwaltung</h1>
        <button
          onClick={() => setShowForm(s => !s)}
          className="flex items-center gap-1 bg-sky-600 hover:bg-sky-500 text-white text-sm font-medium px-3 py-1.5 rounded-lg"
        >
          <Plus size={14} /> Neuer Benutzer
        </button>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {showForm && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 grid grid-cols-2 gap-3">
          <input
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Benutzername"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <input
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Passwort"
            type="password"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <input
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            placeholder="Anzeigename"
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <select
            value={role}
            onChange={e => setRole(e.target.value)}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
          >
            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
          {role === 'kunde' && (
            <select
              value={customerId}
              onChange={e => setCustomerId(e.target.value)}
              className="col-span-2 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
            >
              <option value="">– Kunde wählen –</option>
              {kunden?.map(k => <option key={k.id} value={k.id}>{k.kundennummer} – {k.name}</option>)}
            </select>
          )}
          <div className="col-span-2">
            <button
              onClick={() => { setError(''); create.mutate() }}
              disabled={!username || !password || create.isPending}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Anlegen
            </button>
          </div>
        </div>
      )}

      {isLoading || !users ? (
        <p className="text-sm text-slate-500">Lade…</p>
      ) : users.length === 0 ? (
        <p className="text-sm text-slate-500">Keine Benutzer vorhanden.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl divide-y divide-slate-800">
          {users.map(u => (
            <div key={u.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm text-white">{u.display_name ?? u.username} <span className="text-xs text-slate-500">({u.username})</span></p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {u.role}
                  {u.totp_enabled ? ' · 2FA aktiv' : u.totp_required ? ' · 2FA erforderlich (nicht eingerichtet)' : ''}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => { setError(''); resetPassword.mutate(u.id) }}
                  title="Passwort zurücksetzen"
                  className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                >
                  <KeyRound size={12} /> Passwort
                </button>
                {u.totp_enabled && (
                  <button
                    onClick={() => { setError(''); reset2FA.mutate(u.id) }}
                    title="2FA zurücksetzen"
                    className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    <ShieldOff size={12} /> 2FA
                  </button>
                )}
                <button
                  onClick={() => toggleActive.mutate({ id: u.id, is_active: !u.is_active })}
                  className={`text-xs font-medium px-3 py-1.5 rounded-lg ${u.is_active ? 'bg-emerald-900 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}
                >
                  {u.is_active ? 'Aktiv' : 'Inaktiv'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

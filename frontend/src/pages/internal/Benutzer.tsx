import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Customer, type InternUser, type InternUserUpdate } from '../../api/client'
import { Plus, KeyRound, ShieldOff, Pencil, Building2 } from 'lucide-react'

const ROLES = ['admin', 'user', 'kunde'] as const

function kundeLabel(kunden: Customer[] | undefined, id: string | null): string | null {
  if (!id) return null
  const k = kunden?.find(c => c.id === id)
  return k ? `${k.kundennummer} – ${k.name}` : null
}

function UserRow({ user, kunden }: { user: InternUser; kunden: Customer[] | undefined }) {
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [error, setError] = useState('')
  const [displayName, setDisplayName] = useState(user.display_name ?? '')
  const [role, setRole] = useState(user.role)
  const [customerId, setCustomerId] = useState(user.customer_id ?? '')

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['intern', 'users'] })

  const update = useMutation({
    mutationFn: (data: InternUserUpdate) => api.intern.users.update(user.id, data),
    onSuccess: () => { invalidate(); setOpen(false) },
    onError: (e: Error) => setError(e.message),
  })
  const toggleActive = useMutation({
    mutationFn: () => api.intern.users.update(user.id, { is_active: !user.is_active }),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })
  const resetPassword = useMutation({
    mutationFn: () => {
      const pw = window.prompt('Neues Passwort eingeben:')
      if (!pw) return Promise.reject(new Error('Abgebrochen'))
      return api.intern.users.resetPassword(user.id, pw)
    },
    onError: (e: Error) => { if (e.message !== 'Abgebrochen') setError(e.message) },
  })
  const reset2FA = useMutation({
    mutationFn: () => api.intern.users.reset2FA(user.id),
    onSuccess: invalidate,
    onError: (e: Error) => setError(e.message),
  })

  function speichern() {
    setError('')
    update.mutate({
      display_name: displayName || undefined,
      role,
      customer_id: role === 'kunde' ? (customerId || null) : null,
    })
  }

  const zugeordnet = kundeLabel(kunden, user.customer_id)

  return (
    <div>
      <div className="flex items-center justify-between px-5 py-3">
        <div>
          <p className="text-sm text-white">
            {user.display_name ?? user.username} <span className="text-xs text-slate-500">({user.username})</span>
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {user.role}
            {zugeordnet && (
              <span className="text-slate-400"> · <Building2 size={11} className="inline -mt-0.5" /> {zugeordnet}</span>
            )}
            {user.role === 'kunde' && !zugeordnet && (
              <span className="text-amber-400"> · kein Kunde zugeordnet</span>
            )}
            {user.totp_enabled ? ' · 2FA aktiv' : user.totp_required ? ' · 2FA erforderlich' : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setError(''); setOpen(o => !o) }}
            title="Bearbeiten / zuordnen"
            className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
          >
            <Pencil size={12} /> Bearbeiten
          </button>
          <button
            onClick={() => { setError(''); resetPassword.mutate() }}
            title="Passwort zurücksetzen"
            className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
          >
            <KeyRound size={12} /> Passwort
          </button>
          {user.totp_enabled && (
            <button
              onClick={() => { setError(''); reset2FA.mutate() }}
              title="2FA zurücksetzen"
              className="flex items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium px-3 py-1.5 rounded-lg"
            >
              <ShieldOff size={12} /> 2FA
            </button>
          )}
          <button
            onClick={() => toggleActive.mutate()}
            className={`text-xs font-medium px-3 py-1.5 rounded-lg ${user.is_active ? 'bg-emerald-900 text-emerald-300' : 'bg-slate-800 text-slate-400'}`}
          >
            {user.is_active ? 'Aktiv' : 'Inaktiv'}
          </button>
        </div>
      </div>

      {open && (
        <div className="px-5 pb-5 pt-1 space-y-3 bg-slate-950/40">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-400 mb-1">Anzeigename</label>
              <input
                value={displayName}
                onChange={e => setDisplayName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-1">Rolle</label>
              <select
                value={role}
                onChange={e => setRole(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
              >
                {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            {role === 'kunde' && (
              <div className="col-span-2">
                <label className="block text-xs text-slate-400 mb-1">Kunde (Mandant)</label>
                <select
                  value={customerId}
                  onChange={e => setCustomerId(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-sky-600"
                >
                  <option value="">– kein Kunde –</option>
                  {kunden?.map(k => <option key={k.id} value={k.id}>{k.kundennummer} – {k.name}</option>)}
                </select>
              </div>
            )}
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2">
            <button
              onClick={speichern}
              disabled={update.isPending}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Speichern
            </button>
            <button
              onClick={() => setOpen(false)}
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium px-4 py-2 rounded-lg"
            >
              Abbrechen
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

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
  const { data: kunden } = useQuery({ queryKey: ['intern', 'kunden'], queryFn: api.intern.kunden.list })

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
            <UserRow key={u.id} user={u} kunden={kunden} />
          ))}
        </div>
      )}
    </div>
  )
}

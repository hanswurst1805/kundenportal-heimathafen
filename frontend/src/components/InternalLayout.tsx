import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageSquareText,
  FileSignature,
  ShoppingCart,
  ClipboardList,
  ShieldCheck,
  FileSignature as Signature,
  Smile,
  Activity,
  Building2,
  Boxes,
  SlidersHorizontal,
  Users,
  Settings,
  LogOut,
  Anchor,
} from 'lucide-react'
import { api, getRole } from '../api/client'

const nav = [
  { to: '/intern', icon: LayoutDashboard, label: 'Übersicht', adminOnly: false },
  { to: '/intern/anfragen', icon: MessageSquareText, label: 'Anfragen', adminOnly: false },
  { to: '/intern/angebote', icon: FileSignature, label: 'Angebote', adminOnly: false },
  { to: '/intern/bestellungen', icon: ShoppingCart, label: 'Bestellungen', adminOnly: false },
  { to: '/intern/auftraege', icon: ClipboardList, label: 'Aufträge', adminOnly: false },
  { to: '/intern/leistungsscheine', icon: ClipboardList, label: 'Leistungsscheine', adminOnly: false },
  { to: '/intern/avv', icon: ShieldCheck, label: 'AVV', adminOnly: false },
  { to: '/intern/signaturen', icon: Signature, label: 'Signaturen', adminOnly: false },
  { to: '/intern/umfragen', icon: Smile, label: 'Umfragen', adminOnly: false },
  { to: '/intern/monitoring', icon: Activity, label: 'Monitoring', adminOnly: false },
  { to: '/intern/kunden', icon: Building2, label: 'Kunden', adminOnly: false },
  { to: '/intern/leistungen', icon: Boxes, label: 'Katalog-Editor', adminOnly: false },
  { to: '/intern/statusregeln', icon: SlidersHorizontal, label: 'Statusregeln', adminOnly: true },
  { to: '/intern/benutzer', icon: Users, label: 'Benutzerverwaltung', adminOnly: true },
]

export default function InternalLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const isAdmin = getRole() === 'admin'

  function logout() {
    api.auth.logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <aside className="w-60 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="px-4 py-5 border-b border-slate-800 flex items-center gap-2">
          <Anchor size={20} className="text-sky-500" />
          <div>
            <span className="text-lg font-black tracking-tight text-white">Heimathafen</span>
            <p className="text-xs text-slate-500 -mt-0.5">Interne Sicht</p>
          </div>
        </div>
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {nav
            .filter(item => !item.adminOnly || isAdmin)
            .map(({ to, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/intern'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-sky-600 text-white'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
        </nav>
        <div className="p-2 border-t border-slate-800 space-y-1">
          <NavLink
            to="/einstellungen"
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                isActive ? 'bg-sky-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
              }`
            }
          >
            <Settings size={16} /> Einstellungen
          </NavLink>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-md text-sm text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
          >
            <LogOut size={16} /> Abmelden
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  )
}

import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Workflow,
  ShoppingCart,
  MessageSquareText,
  FileText,
  FileSignature,
  ShieldCheck,
  ClipboardList,
  FolderOpen,
  Smile,
  Settings,
  LogOut,
  Anchor,
} from 'lucide-react'
import { api } from '../api/client'

const nav = [
  { to: '/portal', icon: LayoutDashboard, label: 'Übersicht' },
  { to: '/portal/vorgaenge', icon: Workflow, label: 'Meine Vorgänge' },
  { to: '/portal/katalog', icon: ShoppingCart, label: 'Katalog' },
  { to: '/portal/anfragen', icon: MessageSquareText, label: 'Anfragen' },
  { to: '/portal/angebote', icon: FileText, label: 'Angebote' },
  { to: '/portal/signaturen', icon: FileSignature, label: 'Zu signieren' },
  { to: '/portal/avv', icon: ShieldCheck, label: 'AVV' },
  { to: '/portal/auftraege', icon: ClipboardList, label: 'Aufträge' },
  { to: '/portal/leistungsscheine', icon: ClipboardList, label: 'Leistungsscheine' },
  { to: '/portal/dokumente', icon: FolderOpen, label: 'Dokumente' },
  { to: '/portal/umfragen', icon: Smile, label: 'Umfragen' },
]

export default function CustomerLayout({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()

  function logout() {
    api.auth.logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100">
      <aside className="w-56 shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="px-4 py-5 border-b border-slate-800 flex items-center gap-2">
          <Anchor size={20} className="text-sky-500" />
          <div>
            <span className="text-lg font-black tracking-tight text-white">Heimathafen</span>
            <p className="text-xs text-slate-500 -mt-0.5">Kundenportal</p>
          </div>
        </div>
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {nav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/portal'}
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

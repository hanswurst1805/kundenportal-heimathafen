import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { api, type UserMe } from './api/client'
import CustomerLayout from './components/CustomerLayout'
import InternalLayout from './components/InternalLayout'
import Login from './pages/Login'
import Settings from './pages/Settings'
import Dashboard from './pages/customer/Dashboard'
import Katalog from './pages/customer/Katalog'
import Anfragen from './pages/customer/Anfragen'
import Angebote from './pages/customer/Angebote'
import AVV from './pages/customer/AVV'
import Auftraege from './pages/customer/Auftraege'
import Leistungsscheine from './pages/customer/Leistungsscheine'
import LeistungsscheinDetail from './pages/customer/LeistungsscheinDetail'
import Dokumente from './pages/customer/Dokumente'
import Umfragen from './pages/customer/Umfragen'
import Signatur from './pages/customer/Signatur'
import PortalSignaturen from './pages/customer/Signaturen'
import Vorgaenge from './pages/customer/Vorgaenge'
import VorgangDetail from './pages/customer/VorgangDetail'
import InternDashboard from './pages/internal/Dashboard'
import InternAnfragen from './pages/internal/Anfragen'
import AngebotErstellen from './pages/internal/AngebotErstellen'
import AngebotBearbeiten from './pages/internal/AngebotBearbeiten'
import AngebotUpload from './pages/internal/AngebotUpload'
import InternAngebote from './pages/internal/Angebote'
import InternBestellungen from './pages/internal/Bestellungen'
import InternAuftraege from './pages/internal/Auftraege'
import InternLeistungsscheine from './pages/internal/Leistungsscheine'
import LeistungsscheinBearbeitung from './pages/internal/LeistungsscheinBearbeitung'
import InternAVV from './pages/internal/AVV'
import Signaturen from './pages/internal/Signaturen'
import InternUmfragen from './pages/internal/Umfragen'
import Monitoring from './pages/internal/Monitoring'
import Kunden from './pages/internal/Kunden'
import Leistungen from './pages/internal/Leistungen'
import Statusregeln from './pages/internal/Statusregeln'
import Benutzer from './pages/internal/Benutzer'
import SystemReset from './pages/internal/SystemReset'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

function AuthGate({ children }: { children: (me: UserMe) => React.ReactNode }) {
  const location = useLocation()
  const token = api.auth.getToken()
  const { data: me, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: api.auth.me,
    enabled: !!token,
  })

  if (!token) {
    const ziel = location.pathname + location.search
    const suffix = ziel && ziel !== '/' ? `?redirect=${encodeURIComponent(ziel)}` : ''
    return <Navigate to={`/login${suffix}`} replace />
  }
  if (isLoading || !me) return <div className="min-h-screen bg-slate-950" />

  return <>{children(me)}</>
}

function CustomerRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/portal" replace />} />
      <Route path="/portal" element={<CustomerLayout><Dashboard /></CustomerLayout>} />
      <Route path="/portal/vorgaenge" element={<CustomerLayout><Vorgaenge /></CustomerLayout>} />
      <Route path="/portal/vorgaenge/:typ/:id" element={<CustomerLayout><VorgangDetail /></CustomerLayout>} />
      <Route path="/portal/katalog" element={<CustomerLayout><Katalog /></CustomerLayout>} />
      <Route path="/portal/anfragen" element={<CustomerLayout><Anfragen /></CustomerLayout>} />
      <Route path="/portal/angebote" element={<CustomerLayout><Angebote /></CustomerLayout>} />
      <Route path="/portal/avv" element={<CustomerLayout><AVV /></CustomerLayout>} />
      <Route path="/portal/auftraege" element={<CustomerLayout><Auftraege /></CustomerLayout>} />
      <Route path="/portal/leistungsscheine" element={<CustomerLayout><Leistungsscheine /></CustomerLayout>} />
      <Route
        path="/portal/leistungsscheine/:id"
        element={<CustomerLayout><LeistungsscheinDetail /></CustomerLayout>}
      />
      <Route path="/portal/dokumente" element={<CustomerLayout><Dokumente /></CustomerLayout>} />
      <Route path="/portal/umfragen" element={<CustomerLayout><Umfragen /></CustomerLayout>} />
      <Route path="/portal/signaturen" element={<CustomerLayout><PortalSignaturen /></CustomerLayout>} />
      <Route path="/portal/signatur/:token" element={<CustomerLayout><Signatur /></CustomerLayout>} />
      <Route path="/einstellungen" element={<CustomerLayout><Settings /></CustomerLayout>} />
      <Route path="*" element={<Navigate to="/portal" replace />} />
    </Routes>
  )
}

function InternalRoutes({ me }: { me: UserMe }) {
  const isAdmin = me.role === 'admin'
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/intern" replace />} />
      <Route path="/intern" element={<InternalLayout><InternDashboard /></InternalLayout>} />
      <Route path="/intern/anfragen" element={<InternalLayout><InternAnfragen /></InternalLayout>} />
      <Route path="/intern/anfragen/:id/angebot" element={<InternalLayout><AngebotErstellen /></InternalLayout>} />
      <Route path="/intern/angebote" element={<InternalLayout><InternAngebote /></InternalLayout>} />
      <Route path="/intern/angebote/upload" element={<InternalLayout><AngebotUpload /></InternalLayout>} />
      <Route path="/intern/angebote/:id/bearbeiten" element={<InternalLayout><AngebotBearbeiten /></InternalLayout>} />
      <Route
        path="/intern/bestellungen"
        element={<InternalLayout><InternBestellungen /></InternalLayout>}
      />
      <Route path="/intern/auftraege" element={<InternalLayout><InternAuftraege /></InternalLayout>} />
      <Route
        path="/intern/leistungsscheine"
        element={<InternalLayout><InternLeistungsscheine /></InternalLayout>}
      />
      <Route
        path="/intern/leistungsscheine/:id"
        element={<InternalLayout><LeistungsscheinBearbeitung /></InternalLayout>}
      />
      <Route path="/intern/avv" element={<InternalLayout><InternAVV /></InternalLayout>} />
      <Route
        path="/intern/signaturen"
        element={<InternalLayout><Signaturen /></InternalLayout>}
      />
      <Route path="/intern/umfragen" element={<InternalLayout><InternUmfragen /></InternalLayout>} />
      <Route
        path="/intern/monitoring"
        element={<InternalLayout><Monitoring /></InternalLayout>}
      />
      <Route path="/intern/kunden" element={<InternalLayout><Kunden /></InternalLayout>} />
      <Route
        path="/intern/leistungen"
        element={<InternalLayout><Leistungen /></InternalLayout>}
      />
      <Route
        path="/intern/statusregeln"
        element={
          isAdmin
            ? <InternalLayout><Statusregeln /></InternalLayout>
            : <Navigate to="/intern" replace />
        }
      />
      <Route
        path="/intern/benutzer"
        element={
          isAdmin
            ? <InternalLayout><Benutzer /></InternalLayout>
            : <Navigate to="/intern" replace />
        }
      />
      <Route
        path="/intern/system-reset"
        element={
          isAdmin
            ? <InternalLayout><SystemReset /></InternalLayout>
            : <Navigate to="/intern" replace />
        }
      />
      <Route path="/einstellungen" element={<InternalLayout><Settings /></InternalLayout>} />
      <Route path="*" element={<Navigate to="/intern" replace />} />
    </Routes>
  )
}

function TwoFactorSetupRequired({ Layout }: { Layout: typeof CustomerLayout }) {
  return (
    <Routes>
      <Route path="/einstellungen" element={<Layout><Settings /></Layout>} />
      <Route path="*" element={<Navigate to="/einstellungen" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <AuthGate>
                {me => {
                  const needs2FA = me.role !== 'kunde' && me.totp_required && !me.totp_enabled
                  if (needs2FA) {
                    return <TwoFactorSetupRequired Layout={InternalLayout} />
                  }
                  if (me.role === 'kunde') return <CustomerRoutes />
                  return <InternalRoutes me={me} />
                }}
              </AuthGate>
            }
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

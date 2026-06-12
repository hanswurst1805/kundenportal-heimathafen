import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query'
import { api, type UserMe } from './api/client'
import CustomerLayout from './components/CustomerLayout'
import InternalLayout from './components/InternalLayout'
import Login from './pages/Login'
import Settings from './pages/Settings'
import Placeholder from './pages/Placeholder'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

function AuthGate({ children }: { children: (me: UserMe) => React.ReactNode }) {
  const token = api.auth.getToken()
  const { data: me, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: api.auth.me,
    enabled: !!token,
  })

  if (!token) return <Navigate to="/login" replace />
  if (isLoading || !me) return <div className="min-h-screen bg-slate-950" />

  return <>{children(me)}</>
}

function CustomerRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/portal" replace />} />
      <Route path="/portal" element={<CustomerLayout><Placeholder title="Übersicht" /></CustomerLayout>} />
      <Route path="/portal/katalog" element={<CustomerLayout><Placeholder title="Katalog" /></CustomerLayout>} />
      <Route path="/portal/anfragen" element={<CustomerLayout><Placeholder title="Anfragen" /></CustomerLayout>} />
      <Route path="/portal/angebote" element={<CustomerLayout><Placeholder title="Angebote" /></CustomerLayout>} />
      <Route path="/portal/avv" element={<CustomerLayout><Placeholder title="AVV" /></CustomerLayout>} />
      <Route path="/portal/auftraege" element={<CustomerLayout><Placeholder title="Aufträge" /></CustomerLayout>} />
      <Route
        path="/portal/leistungsscheine"
        element={<CustomerLayout><Placeholder title="Leistungsscheine" /></CustomerLayout>}
      />
      <Route path="/portal/dokumente" element={<CustomerLayout><Placeholder title="Dokumente" /></CustomerLayout>} />
      <Route path="/portal/umfragen" element={<CustomerLayout><Placeholder title="Umfragen" /></CustomerLayout>} />
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
      <Route path="/intern" element={<InternalLayout><Placeholder title="Übersicht" /></InternalLayout>} />
      <Route path="/intern/anfragen" element={<InternalLayout><Placeholder title="Anfragen" /></InternalLayout>} />
      <Route path="/intern/angebote" element={<InternalLayout><Placeholder title="Angebote" /></InternalLayout>} />
      <Route
        path="/intern/bestellungen"
        element={<InternalLayout><Placeholder title="Bestellungen" /></InternalLayout>}
      />
      <Route path="/intern/auftraege" element={<InternalLayout><Placeholder title="Aufträge" /></InternalLayout>} />
      <Route
        path="/intern/leistungsscheine"
        element={<InternalLayout><Placeholder title="Leistungsscheine" /></InternalLayout>}
      />
      <Route path="/intern/avv" element={<InternalLayout><Placeholder title="AVV" /></InternalLayout>} />
      <Route
        path="/intern/signaturen"
        element={<InternalLayout><Placeholder title="Signaturen" /></InternalLayout>}
      />
      <Route path="/intern/umfragen" element={<InternalLayout><Placeholder title="Umfragen" /></InternalLayout>} />
      <Route
        path="/intern/monitoring"
        element={<InternalLayout><Placeholder title="Monitoring" /></InternalLayout>}
      />
      <Route path="/intern/kunden" element={<InternalLayout><Placeholder title="Kunden" /></InternalLayout>} />
      <Route
        path="/intern/leistungen"
        element={<InternalLayout><Placeholder title="Katalogpflege" /></InternalLayout>}
      />
      <Route
        path="/intern/statusregeln"
        element={
          isAdmin
            ? <InternalLayout><Placeholder title="Statusregeln" /></InternalLayout>
            : <Navigate to="/intern" replace />
        }
      />
      <Route
        path="/intern/benutzer"
        element={
          isAdmin
            ? <InternalLayout><Placeholder title="Benutzerverwaltung" /></InternalLayout>
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

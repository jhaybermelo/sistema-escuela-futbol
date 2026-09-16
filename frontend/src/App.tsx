import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider } from './context/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import { Layout } from './components/Layout'

const LoginPage = lazy(() => import('./pages/LoginPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const CategoriasPage = lazy(() => import('./pages/CategoriasPage'))
const AlumnosListPage = lazy(() => import('./pages/AlumnosListPage'))
const AlumnoFormPage = lazy(() => import('./pages/AlumnoFormPage'))
const AlumnoDetailPage = lazy(() => import('./pages/AlumnoDetailPage'))
const CarnetPage = lazy(() => import('./pages/CarnetPage'))
const SchoolConfigPage = lazy(() => import('./pages/SchoolConfigPage'))
const MensualidadesPage = lazy(() => import('./pages/MensualidadesPage'))
const NotificacionesLogPage = lazy(() => import('./pages/NotificacionesLogPage'))
const ReportesPage = lazy(() => import('./pages/ReportesPage'))
const UsuariosPage = lazy(() => import('./pages/UsuariosPage'))
const ReciboPage = lazy(() => import('./pages/ReciboPage'))
const ReciboPublicoPage = lazy(() => import('./pages/ReciboPublicoPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Toaster position="top-right" />
          <Suspense fallback={<div className="p-6">Cargando...</div>}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/r/:token" element={<ReciboPublicoPage />} />
              <Route
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route path="/" element={<DashboardPage />} />
                <Route path="/categorias" element={<CategoriasPage />} />
                <Route path="/alumnos" element={<AlumnosListPage />} />
                <Route path="/alumnos/nuevo" element={<AlumnoFormPage />} />
                <Route path="/alumnos/:id" element={<AlumnoDetailPage />} />
                <Route path="/alumnos/:id/editar" element={<AlumnoFormPage />} />
                <Route path="/alumnos/:id/carnet" element={<CarnetPage />} />
                <Route
                  path="/mensualidades"
                  element={
                    <ProtectedRoute requireAdmin>
                      <MensualidadesPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/config"
                  element={
                    <ProtectedRoute requireAdmin>
                      <SchoolConfigPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/notificaciones"
                  element={
                    <ProtectedRoute requireAdmin>
                      <NotificacionesLogPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reportes"
                  element={
                    <ProtectedRoute requireAdmin>
                      <ReportesPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/usuarios"
                  element={
                    <ProtectedRoute requireAdmin>
                      <UsuariosPage />
                    </ProtectedRoute>
                  }
                />
              </Route>
              <Route
                path="/recibos/:pagoId"
                element={
                  <ProtectedRoute requireAdmin>
                    <ReciboPage />
                  </ProtectedRoute>
                }
              />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App

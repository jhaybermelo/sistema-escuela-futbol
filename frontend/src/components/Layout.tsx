import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { clsx } from 'clsx'
import { LayoutDashboard, Users, Shield, LogOut, Receipt, Settings, Bell, UserCog, Menu, X, BarChart3 } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, adminOnly: false },
  { to: '/alumnos', label: 'Alumnos', icon: Users, adminOnly: false },
  { to: '/categorias', label: 'Categorías', icon: Shield, adminOnly: false },
  { to: '/mensualidades', label: 'Mensualidades', icon: Receipt, adminOnly: true },
  { to: '/reportes', label: 'Reportes', icon: BarChart3, adminOnly: true },
  { to: '/notificaciones', label: 'Notificaciones', icon: Bell, adminOnly: true },
  { to: '/usuarios', label: 'Usuarios', icon: UserCog, adminOnly: true },
  { to: '/config', label: 'Configuración', icon: Settings, adminOnly: true },
]

export function Layout() {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="flex min-h-screen bg-slate-50">
      {menuOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 md:hidden"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 flex w-64 -translate-x-full flex-col border-r border-slate-200 bg-white transition-transform duration-200 ease-in-out',
          'md:relative md:z-auto md:w-56 md:translate-x-0',
          menuOpen && 'translate-x-0',
        )}
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-4">
          <h1 className="text-lg font-semibold text-green-700">Escuela de Futbol</h1>
          <button
            className="text-slate-400 hover:text-slate-600 md:hidden"
            onClick={() => setMenuOpen(false)}
            aria-label="Cerrar menú"
          >
            <X size={20} />
          </button>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {navItems
            .filter((item) => !item.adminOnly || user?.rol === 'admin')
            .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) =>
                  clsx(
                    'flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium',
                    isActive ? 'bg-green-100 text-green-800' : 'text-slate-600 hover:bg-slate-100',
                  )
                }
              >
                <item.icon size={18} />
                {item.label}
              </NavLink>
            ))}
        </nav>
        <div className="border-t border-slate-200 p-3">
          <div className="mb-2 text-xs text-slate-500">
            {user?.nombre} · {user?.rol}
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-100"
          >
            <LogOut size={18} />
            Cerrar sesión
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
          <button
            className="text-slate-600 hover:text-slate-800"
            onClick={() => setMenuOpen(true)}
            aria-label="Abrir menú"
          >
            <Menu size={22} />
          </button>
          <h1 className="text-base font-semibold text-green-700">Escuela de Futbol</h1>
          <div className="w-[22px]" />
        </header>
        <main className="flex-1 overflow-x-hidden p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

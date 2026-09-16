import { NavLink, Outlet } from 'react-router-dom'
import { clsx } from 'clsx'
import { LayoutDashboard, Users, Shield, LogOut, Receipt, Settings, Bell, UserCog } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, adminOnly: false },
  { to: '/alumnos', label: 'Alumnos', icon: Users, adminOnly: false },
  { to: '/categorias', label: 'Categorías', icon: Shield, adminOnly: false },
  { to: '/mensualidades', label: 'Mensualidades', icon: Receipt, adminOnly: true },
  { to: '/notificaciones', label: 'Notificaciones', icon: Bell, adminOnly: true },
  { to: '/usuarios', label: 'Usuarios', icon: UserCog, adminOnly: true },
  { to: '/config', label: 'Configuración', icon: Settings, adminOnly: true },
]

export function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="flex min-h-screen bg-slate-50">
      <aside className="flex w-56 flex-col border-r border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-4">
          <h1 className="text-lg font-semibold text-green-700">Escuela de Futbol</h1>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {navItems
            .filter((item) => !item.adminOnly || user?.rol === 'admin')
            .map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
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
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}

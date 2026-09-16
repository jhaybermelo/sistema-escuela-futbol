import { useQuery } from '@tanstack/react-query'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { Users, DollarSign, Clock, AlertTriangle } from 'lucide-react'
import * as dashboardApi from '../api/dashboard'
import { useAuth } from '../context/AuthContext'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

function StatTile({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: typeof Users
  label: string
  value: string | number
  color: string
}) {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-slate-200 bg-white p-4">
      <div className={`rounded-full p-2 ${color}`}>
        <Icon size={20} />
      </div>
      <div>
        <div className="text-xl font-semibold text-slate-800">{value}</div>
        <div className="text-xs text-slate-500">{label}</div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard-resumen'],
    queryFn: dashboardApi.getResumen,
  })

  const formatMoney = (v: string) => Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">Bienvenido, {user?.nombre}</h1>

      {isLoading || !data ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatTile
              icon={Users}
              label="Alumnos activos"
              value={data.alumnos_activos}
              color="bg-green-100 text-green-700"
            />
            {data.ingresos_mes !== null && (
              <StatTile
                icon={DollarSign}
                label="Ingresos del mes"
                value={formatMoney(data.ingresos_mes)}
                color="bg-blue-100 text-blue-700"
              />
            )}
            {data.mensualidades_pendientes !== null && (
              <StatTile
                icon={Clock}
                label="Mensualidades pendientes"
                value={data.mensualidades_pendientes}
                color="bg-amber-100 text-amber-700"
              />
            )}
            {data.mensualidades_vencidas !== null && (
              <StatTile
                icon={AlertTriangle}
                label="Mensualidades vencidas"
                value={data.mensualidades_vencidas}
                color="bg-red-100 text-red-700"
              />
            )}
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="mb-4 text-sm font-semibold text-slate-500">Alumnos por categoría</h2>
            {data.alumnos_por_categoria.length === 0 ? (
              <p className="text-sm text-slate-400">Sin datos.</p>
            ) : (
              <Bar
                data={{
                  labels: data.alumnos_por_categoria.map((c) => c.categoria_nombre),
                  datasets: [
                    {
                      label: 'Alumnos',
                      data: data.alumnos_por_categoria.map((c) => c.total),
                      backgroundColor: '#15803d',
                      borderRadius: 4,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  plugins: { legend: { display: false } },
                  scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
                }}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

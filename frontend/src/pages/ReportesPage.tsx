import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Wallet, Banknote, Smartphone, CircleDollarSign } from 'lucide-react'
import * as reportesApi from '../api/reportes'
import { Input } from '../components/ui/Input'

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

const METODO_LABEL: Record<string, string> = {
  efectivo: 'Efectivo',
  transferencia: 'Transferencia',
  nequi: 'Nequi',
  otro: 'Otro',
}

const METODO_ICON: Record<string, typeof Wallet> = {
  efectivo: Banknote,
  transferencia: Wallet,
  nequi: Smartphone,
  otro: CircleDollarSign,
}

const formatMoney = (v: string) => Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })

export default function ReportesPage() {
  const hoy = new Date()
  const [mes, setMes] = useState(hoy.getMonth() + 1)
  const [anio, setAnio] = useState(hoy.getFullYear())

  const { data, isLoading } = useQuery({
    queryKey: ['reportes-pagos', mes, anio],
    queryFn: () => reportesApi.getReportePagos(mes, anio),
  })

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-800">Reportes de pagos</h1>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={mes}
            onChange={(e) => setMes(Number(e.target.value))}
          >
            {MESES.map((nombre, i) => (
              <option key={nombre} value={i + 1}>
                {nombre}
              </option>
            ))}
          </select>
          <Input
            type="number"
            className="w-24"
            value={anio}
            onChange={(e) => setAnio(Number(e.target.value))}
          />
        </div>
      </div>

      {isLoading ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <>
          <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-lg border border-green-200 bg-green-50 p-4">
              <p className="text-xs font-medium text-green-700">Total del mes</p>
              <p className="mt-1 text-xl font-semibold text-green-800">
                {formatMoney(data?.total_general ?? '0')}
              </p>
              <p className="text-xs text-green-600">{data?.cantidad_total ?? 0} pago(s)</p>
            </div>
            {data?.por_metodo.map((m) => {
              const Icon = METODO_ICON[m.metodo_pago] ?? CircleDollarSign
              return (
                <div key={m.metodo_pago} className="rounded-lg border border-slate-200 bg-white p-4">
                  <p className="flex items-center gap-1 text-xs font-medium text-slate-500">
                    <Icon size={14} /> {METODO_LABEL[m.metodo_pago] ?? m.metodo_pago}
                  </p>
                  <p className="mt-1 text-xl font-semibold text-slate-800">{formatMoney(m.total)}</p>
                  <p className="text-xs text-slate-400">{m.cantidad} pago(s)</p>
                </div>
              )
            })}
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-4 py-3">Fecha</th>
                  <th className="px-4 py-3">Alumno</th>
                  <th className="px-4 py-3">Periodo</th>
                  <th className="px-4 py-3">Método</th>
                  <th className="px-4 py-3">Monto</th>
                </tr>
              </thead>
              <tbody>
                {data?.pagos.map((p) => (
                  <tr key={p.id} className="border-t border-slate-100">
                    <td className="px-4 py-3 text-slate-600">{p.fecha_pago}</td>
                    <td className="px-4 py-3 text-slate-800">{p.alumno_nombre || '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{p.periodo_texto || '—'}</td>
                    <td className="px-4 py-3 text-slate-600">{METODO_LABEL[p.metodo_pago] ?? p.metodo_pago}</td>
                    <td className="px-4 py-3 text-slate-800">{formatMoney(p.monto)}</td>
                  </tr>
                ))}
                {data?.pagos.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                      No hay pagos registrados en este periodo.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

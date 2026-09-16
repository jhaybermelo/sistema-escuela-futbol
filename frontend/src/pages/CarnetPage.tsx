import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Download } from 'lucide-react'
import * as alumnosApi from '../api/alumnos'
import { Button } from '../components/ui/Button'
import { getErrorMessage } from '../lib/errors'

function descargarBlob(blob: Blob, nombreArchivo: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = nombreArchivo
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export default function CarnetPage() {
  const { id } = useParams()
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false)
  const [imagenUrl, setImagenUrl] = useState<string | null>(null)

  const { data: alumno, isLoading: isLoadingAlumno } = useQuery({
    queryKey: ['alumno', id],
    queryFn: () => alumnosApi.getAlumno(Number(id)),
  })

  const { data: pngBlob, isLoading: isLoadingImagen } = useQuery({
    queryKey: ['carnet-png', id],
    queryFn: () => alumnosApi.getCarnetBlob(Number(id), 'png'),
  })

  useEffect(() => {
    if (!pngBlob) return
    const url = URL.createObjectURL(pngBlob)
    // Object URL solo puede crearse/liberarse como efecto secundario de un blob asíncrono.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setImagenUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [pngBlob])

  async function handleDescargarPng() {
    if (!pngBlob || !alumno) return
    descargarBlob(pngBlob, `carnet-${alumno.numero_identificacion}.png`)
  }

  async function handleDescargarPdf() {
    if (!alumno) return
    setIsDownloadingPdf(true)
    try {
      const blob = await alumnosApi.getCarnetBlob(Number(id), 'pdf')
      descargarBlob(blob, `carnet-${alumno.numero_identificacion}.pdf`)
    } catch (err) {
      toast.error(getErrorMessage(err, 'Error al descargar el carnet en PDF'))
    } finally {
      setIsDownloadingPdf(false)
    }
  }

  if (isLoadingAlumno || !alumno) {
    return <p className="text-slate-500">Cargando...</p>
  }

  return (
    <div className="max-w-xl">
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">
        Carnet — {alumno.nombres} {alumno.apellidos}
      </h1>

      <div className="overflow-hidden rounded-lg border border-slate-200 shadow-sm">
        {isLoadingImagen || !imagenUrl ? (
          <div className="flex h-64 items-center justify-center text-slate-400">Generando carnet...</div>
        ) : (
          <img src={imagenUrl} alt="Carnet del alumno" className="w-full" />
        )}
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="secondary" className="gap-2" onClick={handleDescargarPng} disabled={!pngBlob}>
          <Download size={16} /> Descargar PNG
        </Button>
        <Button className="gap-2" onClick={handleDescargarPdf} disabled={isDownloadingPdf}>
          <Download size={16} /> Descargar PDF
        </Button>
      </div>
    </div>
  )
}

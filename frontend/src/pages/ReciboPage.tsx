import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MessageCircle } from 'lucide-react'
import * as pagosApi from '../api/pagos'
import { ReciboView } from '../components/ReciboView'
import './ReciboPage.css'

export default function ReciboPage() {
  const { pagoId } = useParams()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['recibo-data', pagoId],
    queryFn: () => pagosApi.getReciboData(Number(pagoId)),
  })

  if (isLoading) {
    return <div className="recibo-page">Cargando recibo...</div>
  }
  if (isError || !data) {
    return <div className="recibo-page">No se pudo cargar el recibo.</div>
  }

  function enviarPorWhatsapp() {
    if (!data) return
    const numero = pagosApi.formatearNumeroWhatsapp(data.acudiente_telefono)
    const link = pagosApi.getReciboPublicoUrl(data.token)
    const mensaje =
      `Hola ${data.acudiente_nombre}, te compartimos el recibo de pago #${data.numero_recibo} ` +
      `de ${data.alumno_nombre} (${data.periodo_texto}). Puedes verlo aquí: ${link}`
    window.open(`https://wa.me/${numero}?text=${encodeURIComponent(mensaje)}`, '_blank')
  }

  return (
    <ReciboView
      data={data}
      extraActions={
        <button className="print-button whatsapp-button" onClick={enviarPorWhatsapp}>
          <MessageCircle size={16} style={{ verticalAlign: 'text-bottom', marginRight: 6 }} />
          Enviar por WhatsApp
        </button>
      }
    />
  )
}

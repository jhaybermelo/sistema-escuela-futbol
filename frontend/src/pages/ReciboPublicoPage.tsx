import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import * as pagosApi from '../api/pagos'
import { ReciboView } from '../components/ReciboView'
import './ReciboPage.css'

export default function ReciboPublicoPage() {
  const { token } = useParams()

  const { data, isLoading, isError } = useQuery({
    queryKey: ['recibo-publico', token],
    queryFn: () => pagosApi.getReciboDataPublico(token as string),
    enabled: Boolean(token),
  })

  if (isLoading) {
    return <div className="recibo-page">Cargando recibo...</div>
  }
  if (isError || !data) {
    return <div className="recibo-page">Recibo no encontrado.</div>
  }

  return <ReciboView data={data} />
}

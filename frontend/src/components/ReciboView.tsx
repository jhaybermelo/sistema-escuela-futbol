import { useLayoutEffect, useRef, type ReactNode } from 'react'
import type { ReciboData } from '../api/pagos'
import '../pages/ReciboPage.css'

const RECEIPT_NATURAL_WIDTH = 1120

const METODOS = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'nequi', label: 'Nequi' },
  { value: 'otro', label: 'Otro' },
]

function formatCOP(value: number) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(value)
}

function formatFecha(iso: string) {
  const [y, m, d] = iso.split('-')
  return `${d}/${m}/${y}`
}

export function ReciboView({ data, extraActions }: { data: ReciboData; extraActions?: ReactNode }) {
  const wrapperRef = useRef<HTMLDivElement>(null)
  const receiptRef = useRef<HTMLDivElement>(null)

  // El recibo tiene un diseño de ancho fijo (1120px, ver ReciboPage.css) para respetar
  // el diseño oficial impreso; en pantallas angostas lo escalamos visualmente con
  // transform en vez de dejar que sus hijos de tamaño fijo se encimen/desborden.
  useLayoutEffect(() => {
    const wrapper = wrapperRef.current
    const receipt = receiptRef.current
    if (!wrapper || !receipt) return

    function updateScale() {
      const scale = Math.min(1, wrapper!.clientWidth / RECEIPT_NATURAL_WIDTH)
      receipt!.style.transform = scale < 1 ? `scale(${scale})` : ''
      wrapper!.style.height = scale < 1 ? `${receipt!.offsetHeight * scale}px` : ''
    }

    updateScale()
    const observer = new ResizeObserver(updateScale)
    observer.observe(wrapper)
    return () => observer.disconnect()
  }, [])

  return (
    <div className="recibo-page">
      <div className="receipt-scale-wrapper" ref={wrapperRef}>
      <div className="receipt" ref={receiptRef}>
        <header className="header">
          <div className="logo-frame">
            <img src="/logo-yiverth.jpeg" alt="Club Deportivo Yiverth Estrella" className="logo" />
          </div>

          <div className="club-info">
            <div className="club-small">CLUB DEPORTIVO</div>
            <div className="club-name">
              YIVERTH <span>ESTRELLA</span>
            </div>
            <div className="school-name">ESCUELA DE FÚTBOL</div>
            <div className="motto">FORMANDO TALENTOS PARA UN MEJOR MAÑANA</div>
          </div>

          <div className="header-message">
            Más que fútbol,
            <br />
            <strong>mejores personas</strong>
          </div>
        </header>

        <main className="content">
          <div className="receipt-heading">
            <div className="title">RECIBO DE PAGO</div>
            <div className="receipt-number">
              <div className="number">
                N.º <span>{data.numero_recibo}</span>
              </div>
              <div className="date">
                FECHA: <strong>{formatFecha(data.fecha)}</strong>
              </div>
            </div>
          </div>

          <section className="info-grid">
            <div>
              <div className="field">
                <div className="label">NOMBRE DEL ALUMNO:</div>
                <div className="value">{data.alumno_nombre}</div>
              </div>
              <div className="field">
                <div className="label">CATEGORÍA:</div>
                <div className="value">{data.categoria_nombre}</div>
              </div>
              <div className="field">
                <div className="label">ACUDIENTE:</div>
                <div className="value">{data.acudiente_nombre}</div>
              </div>
              <div className="field">
                <div className="label">TELÉFONO:</div>
                <div className="value">{data.acudiente_telefono}</div>
              </div>
            </div>

            <div>
              <div className="field">
                <div className="label">PERÍODO:</div>
                <div className="value">{data.periodo_texto}</div>
              </div>
              <div className="field">
                <div className="label">MÉTODO DE PAGO:</div>
                <div className="value payment-methods">
                  {METODOS.map((m) => (
                    <span className="check" key={m.value}>
                      <span className={`box${m.value === data.metodo_pago ? ' checked' : ''}`}>
                        {m.value === data.metodo_pago ? '✓' : ''}
                      </span>
                      {m.label}
                    </span>
                  ))}
                </div>
              </div>
              <div className="field">
                <div className="label">REFERENCIA:</div>
                <div className="value">{data.referencia || '—'}</div>
              </div>
            </div>
          </section>

          <table className="payment-table">
            <thead>
              <tr>
                <th>Concepto</th>
                <th>Descripción</th>
                <th>Valor</th>
              </tr>
            </thead>
            <tbody>
              {data.conceptos.map((item, idx) => (
                <tr key={idx}>
                  <td>{item.concepto}</td>
                  <td>{item.descripcion}</td>
                  <td className="amount">{formatCOP(Number(item.monto))}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="total-row">
                <td colSpan={2} className="total-label">
                  TOTAL PAGADO
                </td>
                <td className="total-value">{formatCOP(Number(data.total))}</td>
              </tr>
            </tfoot>
          </table>

          <div className="observations">
            <strong>OBSERVACIONES:</strong>
            <div className="observation-text">{data.observaciones || ''}</div>
          </div>

          <div className="footer">
            <div className="thanks">
              ¡Gracias por ser parte
              <br />
              de esta gran familia!
              <span></span>
            </div>

            <div className="responsible">
              <div className="signature"></div>
              <strong>RESPONSABLE</strong>
              Club Deportivo Yiverth Estrella
            </div>
          </div>
        </main>

        <footer className="contact-bar">
          <div className="contact-item">
            <div className="contact-icon">☎</div>
            <span>312 828 7380</span>
          </div>
          <div className="contact-item">
            <div className="contact-icon">◎</div>
            <span>@yiverth.estrella</span>
          </div>
          <div className="contact-item">
            <div className="contact-icon">●</div>
            <span>Consacá - Nariño</span>
          </div>
        </footer>
      </div>
      </div>

      <div className="actions">
        <button className="print-button" onClick={() => window.print()}>
          Imprimir / Guardar PDF
        </button>
        {extraActions}
      </div>
    </div>
  )
}

import os
from datetime import date
from io import BytesIO

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.alumno import Alumno
from app.models.categoria import Categoria

# Logo oficial del club. La fuente de verdad es frontend/public/logo-yiverth.jpeg
# (el mismo archivo que usa el recibo en el frontend); se mantiene una copia aquí
# porque este PDF se genera server-side con reportlab y el backend no comparte
# filesystem con el contenedor del frontend. Si el logo del club cambia, hay que
# actualizar ambas copias.
LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo-yiverth.jpeg")

VERDE_OSCURO = colors.HexColor("#122A1C")
NEGRO = colors.HexColor("#0D0D0D")
DORADO = colors.HexColor("#C9A227")
VERDE_CLARO = colors.HexColor("#6FCF8F")
GRIS_FILA = colors.HexColor("#F2F3F1")
CREMA_TARJETA = colors.HexColor("#FBF8F0")
BLANCO = colors.white

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGEN = 15 * mm
ANCHO_UTIL = PAGE_WIDTH - 2 * MARGEN
ALTO_ENCABEZADO = 32 * mm
ALTO_PIE = 16 * mm

ESTILOS = getSampleStyleSheet()
_ESTILO_TITULO = ParagraphStyle(
    "TituloOficial",
    parent=ESTILOS["Title"],
    fontName="Helvetica-Bold",
    fontSize=18,
    textColor=NEGRO,
    alignment=1,
    spaceAfter=10,
)
_ESTILO_TARJETA = ParagraphStyle("TarjetaInfo", fontName="Helvetica", fontSize=9.5, leading=13, textColor=NEGRO)
_ESTILO_CELDA = ParagraphStyle("CeldaOficial", fontName="Helvetica", fontSize=9, leading=11)
_ESTILO_CELDA_HEADER = ParagraphStyle(
    "CeldaOficialHeader", fontName="Helvetica-Bold", fontSize=9, leading=11, textColor=BLANCO
)


# El logo no cambia en tiempo de ejecución, así que ambas variantes se calculan una
# sola vez por proceso y se reutiliza el mismo ImageReader en todas las páginas y en
# todas las generaciones de PDF — pasar un ImageReader *nuevo* en cada página hacía
# que reportlab incrustara la imagen una vez por página (PDF pesado y lento de
# generar en documentos de varias páginas).
_logo_nitido_cache: ImageReader | None = None
_logo_marca_agua_cache: ImageReader | None = None


def _logo_nitido() -> ImageReader | None:
    global _logo_nitido_cache
    if _logo_nitido_cache is None and os.path.exists(LOGO_PATH):
        _logo_nitido_cache = ImageReader(LOGO_PATH)
    return _logo_nitido_cache


def _logo_marca_agua() -> ImageReader | None:
    """Copia del logo con el canal alfa reducido al 6%, para usarla como marca de
    agua detrás de la tabla sin afectar la lectura — se genera en memoria a partir
    del archivo original, sin modificarlo. Se reduce también la resolución (no hace
    falta el tamaño completo del logo para un watermark apenas visible), que es lo
    que más pesaba del PDF."""
    global _logo_marca_agua_cache
    if _logo_marca_agua_cache is not None:
        return _logo_marca_agua_cache
    if not os.path.exists(LOGO_PATH):
        return None
    imagen = PILImage.open(LOGO_PATH).convert("RGBA")
    imagen.thumbnail((400, 400))
    alfa = imagen.split()[3].point(lambda a: int(a * 0.06))
    imagen.putalpha(alfa)
    buffer = BytesIO()
    imagen.save(buffer, format="PNG", optimize=True)
    buffer.seek(0)
    _logo_marca_agua_cache = ImageReader(buffer)
    return _logo_marca_agua_cache


class _CanvasConPaginacion(Canvas):
    """Permite mostrar 'Página X de Y' en el pie — reportlab solo sabe el total de
    páginas al terminar de construir el documento, así que se guarda el estado de
    cada página y se dibuja el número en una segunda pasada, justo antes de
    guardar el PDF."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas_guardadas: list[dict] = []

    def showPage(self):
        self._paginas_guardadas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas_guardadas)
        for estado in self._paginas_guardadas:
            self.__dict__.update(estado)
            self.setFont("Helvetica", 7.5)
            self.setFillColor(BLANCO)
            self.drawRightString(PAGE_WIDTH - MARGEN, 6 * mm, f"Página {self._pageNumber} de {total}")
            super().showPage()
        super().save()


def _dibujar_encabezado(c: Canvas, _doc) -> None:
    y_bottom = PAGE_HEIGHT - ALTO_ENCABEZADO

    c.setFillColor(NEGRO)
    c.rect(0, y_bottom, PAGE_WIDTH, ALTO_ENCABEZADO, fill=1, stroke=0)
    c.setFillColor(VERDE_OSCURO)
    c.rect(0, y_bottom, PAGE_WIDTH, ALTO_ENCABEZADO - 3.5 * mm, fill=1, stroke=0)
    c.setFillColor(DORADO)
    c.rect(0, y_bottom - 1.2 * mm, PAGE_WIDTH, 1.2 * mm, fill=1, stroke=0)

    logo_size = ALTO_ENCABEZADO - 8 * mm
    logo = _logo_nitido()
    if logo:
        c.drawImage(
            logo,
            MARGEN,
            y_bottom + 4 * mm,
            width=logo_size,
            height=logo_size,
            preserveAspectRatio=True,
            mask="auto",
        )

    texto_x = MARGEN + logo_size + 6 * mm

    c.setFont("Helvetica", 8)
    c.setFillColor(DORADO)
    c.drawString(texto_x, PAGE_HEIGHT - 9 * mm, "C L U B   D E P O R T I V O")

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(BLANCO)
    c.drawString(texto_x, PAGE_HEIGHT - 17.5 * mm, "YIVERTH ")
    ancho_yiverth = c.stringWidth("YIVERTH ", "Helvetica-Bold", 20)
    c.setFillColor(DORADO)
    c.drawString(texto_x + ancho_yiverth, PAGE_HEIGHT - 17.5 * mm, "ESTRELLA")

    c.setFont("Helvetica", 9)
    c.setFillColor(BLANCO)
    c.drawString(texto_x, PAGE_HEIGHT - 23 * mm, "ESCUELA DE FÚTBOL")

    c.setFont("Helvetica", 7.5)
    c.setFillColor(VERDE_CLARO)
    c.drawString(texto_x, PAGE_HEIGHT - 27.5 * mm, "CONSACÁ - NARIÑO")

    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(BLANCO)
    c.drawRightString(PAGE_WIDTH - MARGEN, PAGE_HEIGHT - 11 * mm, "Más que fútbol,")
    c.setFont("Helvetica-BoldOblique", 9)
    c.setFillColor(VERDE_CLARO)
    c.drawRightString(PAGE_WIDTH - MARGEN, PAGE_HEIGHT - 16 * mm, "mejores personas")


def _dibujar_pie(c: Canvas, _doc) -> None:
    c.setFillColor(NEGRO)
    c.rect(0, 0, PAGE_WIDTH, ALTO_PIE, fill=1, stroke=0)
    c.setFillColor(VERDE_OSCURO)
    c.rect(0, 2 * mm, PAGE_WIDTH, ALTO_PIE - 2 * mm, fill=1, stroke=0)
    c.setFillColor(DORADO)
    c.rect(0, ALTO_PIE - 1 * mm, PAGE_WIDTH, 1 * mm, fill=1, stroke=0)

    c.setFont("Helvetica", 7.5)
    c.setFillColor(BLANCO)
    c.drawString(MARGEN, 6 * mm, "Consacá - Nariño")

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(DORADO)
    c.drawCentredString(PAGE_WIDTH / 2, 6 * mm, "FORMANDO TALENTOS PARA UN MEJOR MAÑANA")


def _dibujar_marca_agua(c: Canvas, _doc) -> None:
    marca_agua = _logo_marca_agua()
    if not marca_agua:
        return
    tamano = 110 * mm
    c.drawImage(
        marca_agua,
        (PAGE_WIDTH - tamano) / 2,
        (PAGE_HEIGHT - tamano) / 2,
        width=tamano,
        height=tamano,
        mask="auto",
    )


def _dibujar_pagina(c: Canvas, doc: SimpleDocTemplate) -> None:
    _dibujar_marca_agua(c, doc)
    _dibujar_encabezado(c, doc)
    _dibujar_pie(c, doc)


def _texto_profesores(categoria: Categoria | None) -> str:
    if not categoria:
        return "Sin profesor asignado"
    textos = [f"{p.nombre} (C.C. {p.numero_identificacion})" for p in categoria.profesores if p.activo]
    return ", ".join(textos) if textos else "Sin profesor asignado"


def _tarjeta_info(categoria_nombre: str, anio: int, total: int, profesor_texto: str) -> Table:
    ancho_col = ANCHO_UTIL / 2
    data = [
        [
            Paragraph(f"<b>Categoría:</b><br/>{categoria_nombre}", _ESTILO_TARJETA),
            Paragraph(f"<b>Año:</b><br/>{anio}", _ESTILO_TARJETA),
        ],
        [
            Paragraph(f"<b>Total de estudiantes:</b><br/>{total}", _ESTILO_TARJETA),
            Paragraph(f"<b>Profesor(es):</b><br/>{profesor_texto}", _ESTILO_TARJETA),
        ],
    ]
    tabla = Table(data, colWidths=[ancho_col, ancho_col])
    tabla.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, DORADO),
                ("INNERGRID", (0, 0), (-1, -1), 0.75, DORADO),
                ("BACKGROUND", (0, 0), (-1, -1), CREMA_TARJETA),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    return tabla


def _tabla_estudiantes(alumnos: list[Alumno]) -> Table:
    anchos = [ANCHO_UTIL * 0.08, ANCHO_UTIL * 0.21, ANCHO_UTIL * 0.44, ANCHO_UTIL * 0.27]
    encabezado = [
        Paragraph("N.º", _ESTILO_CELDA_HEADER),
        Paragraph("IDENTIFICACIÓN", _ESTILO_CELDA_HEADER),
        Paragraph("NOMBRE COMPLETO", _ESTILO_CELDA_HEADER),
        Paragraph("FECHA DE NACIMIENTO", _ESTILO_CELDA_HEADER),
    ]
    filas = [encabezado]
    for i, alumno in enumerate(alumnos, start=1):
        filas.append(
            [
                Paragraph(f"{i:02d}", _ESTILO_CELDA),
                Paragraph(alumno.numero_identificacion, _ESTILO_CELDA),
                Paragraph(f"{alumno.nombres} {alumno.apellidos}", _ESTILO_CELDA),
                Paragraph(alumno.fecha_nacimiento.strftime("%d/%m/%Y"), _ESTILO_CELDA),
            ]
        )
    tabla = Table(filas, colWidths=anchos, repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), VERDE_OSCURO),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [BLANCO, GRIS_FILA]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D9D9D9")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (1, -1), "CENTER"),
                ("ALIGN", (3, 0), (3, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tabla


def generar_listado_pdf(alumnos: list[Alumno], categoria_filtrada: Categoria | None) -> bytes:
    """Genera el listado oficial de estudiantes (A4, con la identidad del club).

    Sin filtro de categoría, agrupa por categoría (una sección por categoría, cada
    una en su propia página, ordenadas de menor a mayor año de nacimiento mínimo);
    con filtro, genera una única sección solo con esa categoría. Dentro de cada
    sección, los alumnos quedan ordenados alfabéticamente por nombre completo.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=ALTO_ENCABEZADO + 8 * mm,
        bottomMargin=ALTO_PIE + 8 * mm,
        leftMargin=MARGEN,
        rightMargin=MARGEN,
    )

    elementos: list = []

    def _agregar_seccion(categoria: Categoria | None, alumnos_grupo: list[Alumno]) -> None:
        alumnos_ordenados = sorted(alumnos_grupo, key=lambda a: f"{a.nombres} {a.apellidos}".upper())
        nombre_categoria = categoria.nombre.strip() if categoria else "Sin categoría"
        elementos.append(Paragraph("LISTADO OFICIAL DE ESTUDIANTES", _ESTILO_TITULO))
        elementos.append(
            _tarjeta_info(
                nombre_categoria, date.today().year, len(alumnos_ordenados), _texto_profesores(categoria)
            )
        )
        elementos.append(Spacer(1, 10 * mm))
        if alumnos_ordenados:
            elementos.append(_tabla_estudiantes(alumnos_ordenados))
        else:
            elementos.append(Paragraph("No hay alumnos registrados en esta categoría.", ESTILOS["Normal"]))

    if categoria_filtrada is not None:
        _agregar_seccion(categoria_filtrada, alumnos)
    elif alumnos:
        grupos: dict[int | None, list[Alumno]] = {}
        for alumno in alumnos:
            grupos.setdefault(alumno.categoria_id, []).append(alumno)

        def _orden_grupo(categoria_id: int | None) -> int:
            categoria = grupos[categoria_id][0].categoria
            return categoria.anio_nacimiento_min if categoria else 9999

        for indice, categoria_id in enumerate(sorted(grupos, key=_orden_grupo)):
            if indice > 0:
                elementos.append(PageBreak())
            alumnos_grupo = grupos[categoria_id]
            categoria = alumnos_grupo[0].categoria
            _agregar_seccion(categoria, alumnos_grupo)
    else:
        elementos.append(Paragraph("LISTADO OFICIAL DE ESTUDIANTES", _ESTILO_TITULO))
        elementos.append(Paragraph("No hay alumnos que coincidan con los filtros.", ESTILOS["Normal"]))

    doc.build(elementos, onFirstPage=_dibujar_pagina, onLaterPages=_dibujar_pagina, canvasmaker=_CanvasConPaginacion)
    return buffer.getvalue()

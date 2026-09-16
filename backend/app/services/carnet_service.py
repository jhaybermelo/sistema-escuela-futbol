import os
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.lib.pagesizes import landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.config import settings
from app.models.alumno import Alumno
from app.models.school_config import SchoolConfig

CARD_SIZE = (640, 400)
VERDE = "#15803d"
GRIS = "#6b7280"
NEGRO = "#111827"


def _font(size: int, negrita: bool = False) -> ImageFont.ImageFont:
    """Fuente TrueType con soporte de tildes/ñ (DejaVu Sans, instalada vía apt en
    la imagen Docker). El bitmap font por defecto de Pillow no soporta acentos,
    por eso no se usa `ImageFont.load_default()` aquí."""
    nombre_archivo = "DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf"
    ruta = f"/usr/share/fonts/truetype/dejavu/{nombre_archivo}"
    if os.path.exists(ruta):
        return ImageFont.truetype(ruta, size)
    return ImageFont.load_default(size=size)


def _resolver_foto(alumno: Alumno) -> Image.Image | None:
    if not alumno.foto_path:
        return None
    relative = alumno.foto_path.removeprefix("/uploads/")
    file_path = os.path.join(settings.UPLOAD_DIR, relative)
    if not os.path.exists(file_path):
        return None
    return Image.open(file_path).convert("RGB")


def generar_carnet_png(alumno: Alumno, config: SchoolConfig) -> bytes:
    width, height = CARD_SIZE
    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, width, 64], fill=VERDE)
    draw.text((20, 16), config.nombre_escuela, fill="white", font=_font(26, negrita=True))

    photo_box = (20, 90, 220, 290)
    foto = _resolver_foto(alumno)
    if foto:
        foto_fit = ImageOps.fit(foto, (photo_box[2] - photo_box[0], photo_box[3] - photo_box[1]))
        img.paste(foto_fit, (photo_box[0], photo_box[1]))
    else:
        draw.rectangle(photo_box, fill="#e5e7eb")
        draw.text((photo_box[0] + 40, photo_box[1] + 65), "Sin foto", fill=GRIS, font=_font(18))
    draw.rectangle(photo_box, outline=GRIS, width=1)

    campos = [
        ("Nombre", f"{alumno.nombres} {alumno.apellidos}"),
        ("Identificación", alumno.numero_identificacion),
        ("Categoría", alumno.categoria.nombre if alumno.categoria else "-"),
        ("Fecha de ingreso", alumno.fecha_ingreso.isoformat()),
    ]
    x, y = 240, 100
    for etiqueta, valor in campos:
        draw.text((x, y), f"{etiqueta}:", fill=GRIS, font=_font(15))
        y += 22
        draw.text((x, y), valor, fill=NEGRO, font=_font(21, negrita=True))
        y += 38

    draw.rectangle([0, 0, width - 1, height - 1], outline="#d1d5db", width=2)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generar_carnet_pdf(alumno: Alumno, config: SchoolConfig) -> bytes:
    png_bytes = generar_carnet_png(alumno, config)
    width_px, height_px = CARD_SIZE
    card_width_mm = 85.6
    card_height_mm = card_width_mm * height_px / width_px

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape((card_width_mm * mm, card_height_mm * mm)))
    c.drawImage(
        ImageReader(BytesIO(png_bytes)),
        0,
        0,
        width=card_width_mm * mm,
        height=card_height_mm * mm,
    )
    c.showPage()
    c.save()
    return buffer.getvalue()

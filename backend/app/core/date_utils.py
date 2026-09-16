from datetime import date

_MESES_ABREV = [
    "ene", "feb", "mar", "abr", "may", "jun",
    "jul", "ago", "sep", "oct", "nov", "dic",
]


def formatear_periodo(inicio: date, fin: date) -> str:
    """Texto legible de un rango de periodo, ej. '08 sep - 07 oct 2026' o,
    si cae dentro del mismo mes, '01 - 15 mar 2026'."""
    mes_inicio = _MESES_ABREV[inicio.month - 1]
    mes_fin = _MESES_ABREV[fin.month - 1]

    if inicio.year == fin.year and inicio.month == fin.month:
        return f"{inicio.day:02d} - {fin.day:02d} {mes_fin} {fin.year}"
    if inicio.year == fin.year:
        return f"{inicio.day:02d} {mes_inicio} - {fin.day:02d} {mes_fin} {fin.year}"
    return f"{inicio.day:02d} {mes_inicio} {inicio.year} - {fin.day:02d} {mes_fin} {fin.year}"

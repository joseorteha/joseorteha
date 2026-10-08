#!/usr/bin/env python3
"""Dibuja contrib-heatmap.svg: el calendario 53x7 de contribuciones con
animacion diagonal (las celdas aparecen una por una). Solo usa la libreria
estandar. Lee data/contributions.json."""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# Paleta estilo GitHub (fondo + 5 niveles) sobre tema oscuro
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
BG = "#0d1117"
TEXT = "#8b949e"

CELL = 13       # lado de cada celda
GAP = 3         # separacion
PAD = 20        # margen interior
TOP = 34        # espacio para etiquetas de meses
LEFT = 30       # espacio para etiquetas de dias

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def row_of(iso: str) -> int:
    """Fila 0..6 con Domingo=0 (como GitHub)."""
    return (date.fromisoformat(iso).weekday() + 1) % 7


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    days = data.get("days", [])
    if not days:
        raise SystemExit("No hay dias en contributions.json")

    # Asigna (col, row) a cada dia
    cells = []
    col = 0
    prev_row = None
    month_cols = {}  # col -> nombre de mes (para la primera semana del mes)
    for i, d in enumerate(days):
        r = row_of(d["date"])
        if i == 0:
            col = 0
        elif r == 0:  # nuevo domingo -> nueva columna
            col += 1
        cells.append((col, r, d["level"], d["date"]))
        prev_row = r

    # Etiquetas de mes: marca la columna donde empieza cada mes
    seen_month = set()
    for col_i, r, lvl, iso in cells:
        mnum = int(iso[5:7])
        if mnum not in seen_month:
            seen_month.add(mnum)
            month_cols[col_i] = MONTHS[mnum - 1]

    ncols = max(c[0] for c in cells) + 1
    width = LEFT + PAD + ncols * (CELL + GAP) + PAD
    height = TOP + PAD + 7 * (CELL + GAP) + PAD

    step = 0.012  # retardo por diagonal (segundos)
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace">'
    )
    parts.append(
        "<style>"
        "@keyframes pop{from{opacity:0;transform:scale(.2)}"
        "to{opacity:1;transform:scale(1)}}"
        ".c{opacity:0;transform-box:fill-box;transform-origin:center;"
        "animation:pop .45s ease-out forwards}"
        ".lbl{fill:" + TEXT + ";font-size:10px;opacity:0;"
        "animation:pop .4s ease-out forwards}"
        "</style>"
    )
    parts.append(f'<rect width="{width}" height="{height}" rx="10" fill="{BG}"/>')

    # Etiquetas de meses
    for col_i, name in sorted(month_cols.items()):
        x = LEFT + PAD + col_i * (CELL + GAP)
        parts.append(f'<text class="lbl" x="{x}" y="{TOP - 10}">{name}</text>')

    # Etiquetas de dias (Mon/Wed/Fri)
    for r, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        y = TOP + PAD + r * (CELL + GAP) + CELL - 2
        parts.append(f'<text class="lbl" x="2" y="{y}">{name}</text>')

    # Celdas
    for col_i, r, lvl, iso in cells:
        x = LEFT + PAD + col_i * (CELL + GAP)
        y = TOP + PAD + r * (CELL + GAP)
        delay = (col_i + r) * step
        color = PALETTE[min(lvl, 4)]
        parts.append(
            f'<rect class="c" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="3" fill="{color}" style="animation-delay:{delay:.3f}s"/>'
        )

    parts.append("</svg>")
    OUT.write_text("".join(parts), encoding="utf-8")
    print(f"OK -> {OUT.name} ({ncols} semanas, {len(cells)} dias)")


if __name__ == "__main__":
    main()

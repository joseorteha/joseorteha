#!/usr/bin/env python3
"""Convierte una foto en un retrato ASCII animado (jose-ascii.svg).

Uso:
    python scripts/make_ascii_svg.py [ruta_imagen] [--invert] [--cols N]

Por defecto usa assets/profile_prepped.png si existe, si no assets/profile.png.
El fondo claro se mapea a espacios (vacio) y el sujeto oscuro a caracteres
densos, igual que un retrato tipo neofetch. Las lineas aparecen escalonadas
como si se fueran "escribiendo" en la terminal.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "jose-ascii.svg"

# De claro -> oscuro. El espacio inicial deja el fondo vacio.
RAMP = " .`:-=+*csoe#%@"

# Lienzo (mismo aspecto que stats.svg para que a igual ancho queden a igual alto)
W, H = 420, 440
PAD = 16
BG = "#0d1117"
GREEN_BRIGHT = (57, 211, 83)   # #39d353
GREEN_DARK = (14, 68, 41)      # #0e4429


def pick_input():
    for name in ("profile_prepped.png", "profile.png", "profile.jpg", "profile.jpeg"):
        p = ROOT / "assets" / name
        if p.exists():
            return p
    return None


def main():
    args = sys.argv[1:]
    invert = "--invert" in args
    cols = 84
    if "--cols" in args:
        cols = int(args[args.index("--cols") + 1])
    paths = [a for a in args if not a.startswith("--")
             and a != str(cols) ]
    src = Path(paths[0]) if paths else pick_input()
    if not src or not Path(src).exists():
        raise SystemExit(
            "No encontre la foto. Pon tu imagen en assets/profile.png "
            "o pasa la ruta: python scripts/make_ascii_svg.py mi_foto.png"
        )

    img = Image.open(src)
    # Fondo transparente (rembg) -> blanco, para que el fondo quede vacio
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        img = Image.alpha_composite(white, rgba).convert("RGB")
    img = img.convert("L")
    img = ImageOps.autocontrast(img, cutoff=2)  # estira el contraste
    if invert:
        img = ImageOps.invert(img)

    # Auto-recorte al sujeto: descarta el borde (casi) blanco para que la cara
    # llene el lienzo en vez de quedar chica en una esquina.
    gray = np.asarray(img)
    mask = gray < 240
    if mask.sum() > 50:
        ys, xs = np.where(mask)
        x1, x2 = xs.min(), xs.max()
        y1, y2 = ys.min(), ys.max()
        padx = int((x2 - x1) * 0.06) + 2
        pady = int((y2 - y1) * 0.06) + 2
        x1, y1 = max(0, x1 - padx), max(0, y1 - pady)
        x2 = min(gray.shape[1] - 1, x2 + padx)
        y2 = min(gray.shape[0] - 1, y2 + pady)
        img = img.crop((x1, y1, x2 + 1, y2 + 1))

    # Redimensiona al grid (los caracteres son ~2x mas altos que anchos)
    w0, h0 = img.size
    rows = max(1, int(cols * (h0 / w0) * 0.52))
    small = img.resize((cols, rows), Image.LANCZOS)
    arr = np.asarray(small, dtype=np.float32) / 255.0  # 0=oscuro .. 1=claro

    # Ajusta tamano de fuente para caber en el lienzo
    char_w_ratio = 0.6
    fs_w = (W - 2 * PAD) / (cols * char_w_ratio)
    line_ratio = 1.05
    fs_h = (H - 2 * PAD) / (rows * line_ratio)
    fs = min(fs_w, fs_h)
    char_w = fs * char_w_ratio
    line_h = fs * line_ratio
    block_w = cols * char_w
    block_h = rows * line_h
    x0 = (W - block_w) / 2
    y0 = (H - block_h) / 2 + fs  # baseline de la primera fila

    def shade(bright):
        """Verde mas intenso para lo mas oscuro (el sujeto)."""
        t = 1.0 - bright  # 0 claro .. 1 oscuro
        r = int(GREEN_DARK[0] + (GREEN_BRIGHT[0] - GREEN_DARK[0]) * t)
        g = int(GREEN_DARK[1] + (GREEN_BRIGHT[1] - GREEN_DARK[1]) * t)
        b = int(GREEN_DARK[2] + (GREEN_BRIGHT[2] - GREEN_DARK[2]) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="ui-monospace,Consolas,monospace">'
    )
    p.append(
        "<style>"
        "@keyframes type{from{opacity:0;transform:translateX(-6px)}"
        "to{opacity:1;transform:translateX(0)}}"
        ".r{opacity:0;animation:type .35s ease-out forwards;"
        "white-space:pre}"
        "</style>"
    )
    p.append(f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>')

    per_row = 0.045  # retardo entre filas
    for ri in range(rows):
        y = y0 + ri * line_h
        delay = ri * per_row
        # Agrupa caracteres contiguos del mismo tono para achicar el SVG
        spans = []
        cur_chars = []
        cur_color = None
        for ci in range(cols):
            bright = float(arr[ri, ci])
            idx = int((1.0 - bright) * (len(RAMP) - 1) + 0.5)
            ch = RAMP[idx]
            color = shade(bright)
            if color == cur_color:
                cur_chars.append(ch)
            else:
                if cur_chars:
                    spans.append((cur_color, "".join(cur_chars)))
                cur_chars = [ch]
                cur_color = color
        if cur_chars:
            spans.append((cur_color, "".join(cur_chars)))

        tspans = "".join(
            f'<tspan fill="{col}" xml:space="preserve">{escape(txt)}</tspan>'
            for col, txt in spans
        )
        p.append(
            f'<text class="r" x="{x0:.1f}" y="{y:.1f}" '
            f'font-size="{fs:.2f}" letter-spacing="{char_w - fs*0.6:.3f}" '
            f'style="animation-delay:{delay:.3f}s" '
            f'xml:space="preserve">{tspans}</text>'
        )

    p.append("</svg>")
    OUT.write_text("".join(p), encoding="utf-8")
    print(f"OK -> {OUT.name} ({cols}x{rows} caracteres desde {src})")


if __name__ == "__main__":
    main()

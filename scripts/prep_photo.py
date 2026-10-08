#!/usr/bin/env python3
"""Prepara la foto para el retrato ASCII.

Uso:
    python scripts/prep_photo.py [assets/profile.png]

Intenta: (1) quitar el fondo con rembg, (2) mejorar contraste con OpenCV CLAHE,
(3) componer sobre fondo blanco. Si rembg u OpenCV no estan instalados, hace una
version mas simple con Pillow y avisa. Guarda assets/profile_prepped.png.
"""
import sys
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = ROOT / "assets" / "profile.png"
OUT = ROOT / "assets" / "profile_prepped.png"


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IN
    if not src.exists():
        raise SystemExit(f"No existe {src}. Pon tu foto en assets/profile.png")

    img = Image.open(src).convert("RGB")

    # 1) Quitar fondo (opcional)
    cut = None
    try:
        from rembg import remove  # type: ignore
        cut = remove(img)  # RGBA con fondo transparente
        print("rembg OK: fondo removido")
    except Exception as e:  # noqa: BLE001
        print(f"(sin rembg: {type(e).__name__}) -> sigo sin quitar el fondo")

    # 2) Contraste CLAHE (opcional)
    try:
        import cv2  # type: ignore
        import numpy as np
        base = cut.convert("RGB") if cut is not None else img
        lab = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2RGB)
        base = Image.fromarray(enhanced)
        if cut is not None:  # devuelve el alpha
            base.putalpha(cut.split()[-1])
            cut = base
        else:
            img = base
        print("OpenCV CLAHE OK: contraste mejorado")
    except Exception as e:  # noqa: BLE001
        print(f"(sin OpenCV: {type(e).__name__}) -> contraste con Pillow")
        if cut is None:
            img = ImageOps.autocontrast(img, cutoff=2)

    # 3) Componer sobre blanco
    if cut is not None:
        white = Image.new("RGBA", cut.size, (255, 255, 255, 255))
        final = Image.alpha_composite(white, cut.convert("RGBA")).convert("RGB")
    else:
        final = img

    OUT.parent.mkdir(parents=True, exist_ok=True)
    final.save(OUT)
    print(f"OK -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

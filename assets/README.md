# assets/

Pon aquí tu foto con el nombre **`profile.png`** (o `.jpg`).

Recomendaciones para un buen retrato ASCII:
- De frente, cara bien visible y con buena luz.
- Fondo simple si puedes (aunque el script intenta quitarlo).
- Resolución media/alta (500px+ por lado).

Luego genera el retrato:

```bash
# (opcional) limpia la foto: quita fondo + mejora contraste
python scripts/prep_photo.py assets/profile.png

# genera el retrato ASCII animado -> jose-ascii.svg
python scripts/make_ascii_svg.py
```

Si tu foto queda "invertida" (fondo lleno de caracteres en vez del sujeto),
agrega `--invert`:

```bash
python scripts/make_ascii_svg.py --invert
```

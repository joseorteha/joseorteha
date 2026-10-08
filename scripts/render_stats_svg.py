#!/usr/bin/env python3
"""Dibuja stats.svg: una tarjeta estilo terminal con las estadisticas de
contribucion (total, racha actual, racha mas larga, mejor dia), con las lineas
apareciendo escalonadas. Solo libreria estandar. Lee data/contributions.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "stats.svg"

BG = "#0d1117"
BAR = "#161b22"
GREEN = "#39d353"
CYAN = "#22d3ee"
DIM = "#8b949e"
FG = "#e6edf3"

W, H = 420, 440


def line(x, y, delay, spans):
    """spans = [(texto, color, bold?), ...] en una misma linea."""
    tspans = "".join(
        f'<tspan fill="{c}"{" font-weight=\"700\"" if b else ""}>{t}</tspan>'
        for t, c, b in spans
    )
    return (
        f'<text class="ln" x="{x}" y="{y}" style="animation-delay:{delay:.2f}s">'
        f"{tspans}</text>"
    )


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    user = d.get("username", "joseorteha")
    total = d.get("total", 0)
    cur = d.get("current_streak", 0)
    longest = d.get("longest_streak", 0)
    best = d.get("max_day", {}) or {}
    best_c = best.get("count", 0)
    best_d = best.get("date") or "-"

    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace">'
    )
    p.append(
        "<style>"
        "@keyframes rise{from{opacity:0;transform:translateY(8px)}"
        "to{opacity:1;transform:translateY(0)}}"
        ".ln{opacity:0;font-size:15px;animation:rise .5s ease-out forwards}"
        "@keyframes blink{50%{opacity:0}}"
        ".cur{animation:blink 1s step-end infinite}"
        "@keyframes big{from{opacity:0;transform:scale(.6)}"
        "to{opacity:1;transform:scale(1)}}"
        ".num{opacity:0;transform-box:fill-box;transform-origin:left center;"
        "animation:big .6s cubic-bezier(.2,1.4,.4,1) forwards}"
        "</style>"
    )
    # ventana
    p.append(f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>')
    p.append(f'<rect width="{W}" height="36" rx="12" fill="{BAR}"/>')
    p.append(f'<rect y="24" width="{W}" height="12" fill="{BAR}"/>')
    p.append('<circle cx="20" cy="18" r="6" fill="#ff5f56"/>')
    p.append('<circle cx="40" cy="18" r="6" fill="#ffbd2e"/>')
    p.append('<circle cx="60" cy="18" r="6" fill="#27c93f"/>')
    p.append(
        f'<text x="{W/2}" y="23" text-anchor="middle" fill="{DIM}" '
        f'font-size="13">{user} — contribution stats</text>'
    )

    x = 24
    p.append(line(x, 78, 0.0, [(f"{user}@github", GREEN, True),
                               (":", FG, False), ("~", CYAN, False),
                               ("$ ", FG, False), ("./stats.sh", FG, False)]))

    # Numerote de racha actual
    p.append(
        f'<text class="num" x="{x}" y="150" fill="{GREEN}" '
        f'font-size="64" font-weight="800" style="animation-delay:.25s">'
        f"{cur}</text>"
    )
    p.append(line(x + 10, 182, 0.55, [("dias de racha actual \U0001f525", DIM, False)]))

    # Lista de metricas
    rows = [
        ("Total (ultimo ano)", f"{total}", GREEN),
        ("Racha mas larga", f"{longest} dias", CYAN),
        ("Mejor dia", f"{best_c}", FG),
        ("Fecha mejor dia", best_d, DIM),
    ]
    y = 230
    for i, (k, v, color) in enumerate(rows):
        delay = 0.7 + i * 0.12
        p.append(line(x, y, delay, [(f"{k:<20}", DIM, False),
                                    (": ", FG, False), (v, color, True)]))
        y += 34

    # pie con cursor
    p.append(line(x, y + 8, 0.7 + len(rows) * 0.12,
                  [(f"{user}@github", GREEN, True), (":", FG, False),
                   ("~", CYAN, False), ("$ ", FG, False)]))
    p.append(
        f'<rect class="cur" x="{x + 118}" y="{y - 4}" width="9" height="16" '
        f'fill="{GREEN}" style="animation-delay:{0.7 + len(rows)*0.12:.2f}s"/>'
    )

    p.append("</svg>")
    OUT.write_text("".join(p), encoding="utf-8")
    print(f"OK -> {OUT.name} (total={total}, racha={cur}/{longest})")


if __name__ == "__main__":
    main()

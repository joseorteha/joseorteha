#!/usr/bin/env python3
"""Baja las contribuciones publicas de un usuario de GitHub (sin token).

Lee el HTML de https://github.com/users/<user>/contributions, saca el nivel
y el conteo de cada dia, calcula estadisticas (total, racha actual, racha mas
larga, mejor dia) y lo guarda en data/contributions.json.
"""
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "joseorteha"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

URL = f"https://github.com/users/{USERNAME}/contributions"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
}


def parse_count(text: str) -> int:
    """'3 contributions on ...' -> 3 ; 'No contributions ...' -> 0."""
    if not text:
        return 0
    low = text.lower()
    if low.startswith("no "):
        return 0
    m = re.search(r"([\d,]+)\s+contribution", low)
    return int(m.group(1).replace(",", "")) if m else 0


def fetch_days(username: str):
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Mapa id-de-celda -> conteo (los conteos viven en <tool-tip for="...">)
    tip_by_id = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tip_by_id[target] = parse_count(tip.get_text(strip=True))

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        d = cell.get("data-date")
        if not d:
            continue
        level = int(cell.get("data-level", 0) or 0)
        cid = cell.get("id")
        count = tip_by_id.get(cid)
        if count is None:
            # Respaldo: aproxima el conteo desde el nivel si no hay tooltip
            count = {0: 0, 1: 1, 2: 4, 3: 8, 4: 12}.get(level, 0)
        days.append({"date": d, "count": count, "level": level})

    days.sort(key=lambda x: x["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)
    max_day = max(days, key=lambda d: d["count"]) if days else {"count": 0, "date": None}

    # Racha mas larga (dias consecutivos con count > 0)
    longest = cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    # Racha actual: cuenta hacia atras desde hoy. Si hoy aun no hay commits,
    # no rompe la racha (todavia queda el dia por delante).
    today = date.today().isoformat()
    current = 0
    for d in reversed(days):
        if d["date"] > today:
            continue
        if d["count"] > 0:
            current += 1
        elif d["date"] == today:
            continue  # hoy sin commits aun: no rompe la racha
        else:
            break

    return {
        "total": total,
        "longest_streak": longest,
        "current_streak": current,
        "max_day": {"count": max_day["count"], "date": max_day.get("date")},
    }


def main():
    days = fetch_days(USERNAME)
    if not days:
        print("ADVERTENCIA: no se encontraron dias. GitHub pudo cambiar el HTML.")
    stats = compute_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        **stats,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"OK -> {OUT.name}: {len(days)} dias, total={stats['total']}, "
        f"racha_actual={stats['current_streak']}, "
        f"racha_max={stats['longest_streak']}"
    )


if __name__ == "__main__":
    main()

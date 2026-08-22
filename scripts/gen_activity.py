#!/usr/bin/env python3
"""Regenerate activity.svg — last 53 weeks of GitHub contributions.

Fetches GitHub's own contribution calendar (public) and renders a heatmap
styled to match the profile banner. Runs weekly via GitHub Actions.
Highlights the current (latest) week with a pulsing accent frame.
"""
import datetime
import os
import re
import sys
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "activity.svg")
URL = "https://github.com/users/cgycorey/contributions"

MONO = "ui-monospace, 'Cascadia Mono', 'SF Mono', 'Ubuntu Mono', Menlo, Consolas, monospace"
CELL, GAP, PAD = 11, 3, 16
LV = ["#161d1a", "#22382a", "#3d5f36", "#6f9e3f", "#9dff3d"]


def fetch_levels() -> dict:
    req = urllib.request.Request(URL, headers={"User-Agent": "profile-activity"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", "replace")
    pairs = re.findall(r'data-date="([^"]+)"[^>]*data-level="(\d+)"', html)
    if not pairs:
        raise RuntimeError("no contribution data found in response")
    return {datetime.date.fromisoformat(d): int(l) for d, l in pairs}


def main() -> int:
    days = fetch_levels()
    start = min(days)
    if start.weekday() != 6:  # 6 = Sunday
        start -= datetime.timedelta(days=start.weekday() + 1)
    last = max(days)
    weeks = []
    cur = start
    while cur <= last:
        weeks.append((cur, [days.get(cur + datetime.timedelta(days=i), 0) for i in range(7)]))
        cur += datetime.timedelta(days=7)
    if len(weeks) > 53:
        weeks = weeks[-53:]

    n = len(weeks)
    active = sum(1 for l in days.values() if l > 0)
    w = PAD * 2 + n * CELL + (n - 1) * GAP
    h = 72 + 7 * CELL + 6 * GAP + 18

    def x_of(i):
        return PAD + i * (CELL + GAP)

    def y_of(r):
        return 84 + r * (CELL + GAP)

    labels, last_m = [], None
    for ws, _ in weeks:
        if ws.month != last_m:
            labels.append((ws, ws.month))
            last_m = ws.month
    ml = "".join(
        f'<text x="{x_of(i) + 1}" y="78" font-family="{MONO}" font-size="9" fill="#46524d">{m}</text>'
        for i, (_, m) in enumerate(labels)
    )

    cells = ""
    for ci, (_, wk) in enumerate(weeks):
        for ri, lvl in enumerate(wk):
            fill = LV[lvl] if 0 <= lvl < len(LV) else LV[0]
            cells += f'<rect x="{x_of(ci)}" y="{y_of(ri)}" width="{CELL}" height="{CELL}" rx="2" fill="{fill}"/>'

    # highlight: pulsing frame + NOW tag on the current (latest) week column
    last_ci = n - 1
    fx, fy = x_of(last_ci) - 2, y_of(0) - 2
    fw, fh = CELL + 4, 7 * CELL + 6 * GAP + 4
    highlight = (
        f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="3" fill="none" stroke="#9dff3d" stroke-width="1.5">'
        f'<animate attributeName="opacity" values="1;0.25;1" dur="2.4s" repeatCount="indefinite"/></rect>'
        f'<text x="{fx + fw / 2}" y="{fy - 6}" font-family="{MONO}" font-size="9" fill="#9dff3d" text-anchor="middle">NOW</text>'
    )

    legend = ""
    for i, c in enumerate(LV):
        x = w - PAD - (len(LV) - i) * (CELL + 2)
        legend += f'<rect x="{x}" y="{h - 20}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
    legend += (
        f'<text x="{w - PAD - len(LV) * (CELL + 2) - 34}" y="{h - 10}" font-family="{MONO}" font-size="9" fill="#46524d" text-anchor="end">less</text>'
        f'<text x="{w - PAD}" y="{h - 10}" font-family="{MONO}" font-size="9" fill="#46524d" text-anchor="end">more</text>'
    )

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="commit activity heatmap">
  <title>commit activity — last {n} weeks</title>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" fill="#0b0e0d" stroke="#1c2421" rx="6"/>
  <text x="{PAD}" y="30" font-family="{MONO}" font-size="10" letter-spacing="2" fill="#46524d">ACTIVITY — LAST {n} WEEKS</text>
  <rect x="{PAD}" y="38" width="24" height="2" fill="#9dff3d"/>
  <text x="{PAD}" y="60" font-family="{MONO}" font-size="26" font-weight="700" fill="#9dff3d">{active}</text>
  <text x="{PAD + 70}" y="60" font-family="{MONO}" font-size="11" fill="#64746e">active days</text>
  {ml}
  {cells}
  {highlight}
  <text x="{PAD}" y="{h - 10}" font-family="{MONO}" font-size="10" fill="#3fe06f">▸ auto-refreshed weekly</text>
  {legend}
</svg>
'''
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"activity.svg: {n} weeks, {active} active days, current week highlighted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
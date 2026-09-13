"""
render_heatmap_svg.py
Renders data/contributions.json as the classic 53-week x 7-day
contribution calendar: rounded, colored boxes that reveal in a
diagonal, line-after-line slide-down. Plays once on load, then
freezes. Adds a Less->More legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py
Output:
    contrib-heatmap.svg (repo root)
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
# none -> brightest (level 5 is a neon top end, above GitHub's usual 4)

BG = "#0a0e14"
BORDER = "#1b2230"
TEXT_MUTED = "#6e7681"
TEXT_BRIGHT = "#c9d1d9"
ACCENT = "#39d353"

CELL = 11
GAP = 3
LEFT_PAD = 28
TOP_PAD = 34
RIGHT_PAD = 20
BOTTOM_PAD = 46

MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

STEP_DUR = 0.03      # seconds each diagonal step takes to animate in
CELL_ANIM_DUR = 0.28


def clamp_level(lvl: int) -> int:
    return max(0, min(lvl, len(PALETTE) - 1))


def build(data: dict) -> str:
    days = data["days"]
    if not days:
        raise SystemExit("No contribution days in data — did fetch_contributions.py run?")

    parsed = [
        (datetime.strptime(d["date"], "%Y-%m-%d").date(), d["level"])
        for d in days
    ]
    parsed.sort(key=lambda t: t[0])
    first_date = parsed[0][0]
    first_sunday = first_date - timedelta(days=(first_date.weekday() + 1) % 7)

    cells = []       # (week, dow, level, date)
    max_week = 0
    month_markers = {}  # week_index -> month label, first week that month appears
    last_month_labeled = None
    for date, level in parsed:
        offset = (date - first_sunday).days
        week = offset // 7
        dow = offset % 7
        max_week = max(max_week, week)
        cells.append((week, dow, clamp_level(level), date))
        month_key = (date.year, date.month)
        if date.day <= 7 and month_key != last_month_labeled:
            month_markers[week] = MONTH_ABBR[date.month - 1]
            last_month_labeled = month_key

    cols = max_week + 1
    grid_w = cols * (CELL + GAP) - GAP
    grid_h = 7 * (CELL + GAP) - GAP
    width = LEFT_PAD + grid_w + RIGHT_PAD
    height = TOP_PAD + grid_h + BOTTOM_PAD

    # Diagonal stagger: order by (week + dow) so it reveals as a diagonal wave
    def begin_time(week, dow):
        return (week + dow) * STEP_DUR

    cell_svgs = []
    for week, dow, level, date in cells:
        x = LEFT_PAD + week * (CELL + GAP)
        y = TOP_PAD + dow * (CELL + GAP)
        color = PALETTE[level]
        begin = begin_time(week, dow)
        cell_svgs.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
            f'fill="{color}" opacity="0">'
            f'<title>{date.isoformat()}: {"no" if level == 0 else level} '
            f'contribution{"s" if level != 1 else ""}</title>'
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.3f}s" dur="{CELL_ANIM_DUR}s" fill="freeze" />'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="0 -6" to="0 0" begin="{begin:.3f}s" dur="{CELL_ANIM_DUR}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1" />'
            f'</rect>'
        )

    month_svgs = []
    for week, label in sorted(month_markers.items()):
        x = LEFT_PAD + week * (CELL + GAP)
        month_svgs.append(
            f'<text x="{x}" y="{TOP_PAD - 10}" font-family="\'SF Mono\', Consolas, monospace" '
            f'font-size="10" fill="{TEXT_MUTED}">{label}</text>'
        )

    total_begin = begin_time(max_week, 6) + CELL_ANIM_DUR + 0.05

    legend_x = LEFT_PAD
    legend_y = TOP_PAD + grid_h + 22
    legend_svgs = [
        f'<text x="{legend_x}" y="{legend_y + 9}" font-family="\'SF Mono\', Consolas, monospace" '
        f'font-size="10" fill="{TEXT_MUTED}">Less</text>'
    ]
    swatch_x = legend_x + 34
    for i, color in enumerate(PALETTE):
        legend_svgs.append(
            f'<rect x="{swatch_x + i * (CELL + GAP)}" y="{legend_y}" width="{CELL}" '
            f'height="{CELL}" rx="2.5" fill="{color}"/>'
        )
    more_x = swatch_x + len(PALETTE) * (CELL + GAP) + 6
    legend_svgs.append(
        f'<text x="{more_x}" y="{legend_y + 9}" font-family="\'SF Mono\', Consolas, monospace" '
        f'font-size="10" fill="{TEXT_MUTED}">More</text>'
    )

    stats = (
        f'{data["total_contributions"]} contributions in the last year  ·  '
        f'current streak {data["current_streak"]}  ·  longest streak {data["longest_streak"]}'
    )
    stats_svg = (
        f'<text x="{width - RIGHT_PAD}" y="{legend_y + 9}" text-anchor="end" '
        f'font-family="\'SF Mono\', Consolas, monospace" font-size="10.5" '
        f'fill="{TEXT_BRIGHT}" opacity="0">{stats}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{total_begin:.3f}s" '
        f'dur="0.5s" fill="freeze" /></text>'
    )

    svg = f'''<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="heatClip"><rect width="{width}" height="{height}" rx="12"/></clipPath>
  </defs>
  <g clip-path="url(#heatClip)">
    <rect width="{width}" height="{height}" fill="{BG}"/>
    <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12"
          fill="none" stroke="{BORDER}" stroke-width="1"/>
    {"".join(month_svgs)}
    {"".join(cell_svgs)}
    {"".join(legend_svgs)}
    {stats_svg}
  </g>
</svg>'''
    return svg


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    data = json.loads((repo_root / "data" / "contributions.json").read_text())
    svg = build(data)
    out_path = repo_root / "contrib-heatmap.svg"
    out_path.write_text(svg)
    print(f"Wrote {out_path}")

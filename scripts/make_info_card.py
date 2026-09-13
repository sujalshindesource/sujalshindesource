"""
make_info_card.py
Hand-authored neofetch-style SVG: a title bar + key/value rows that
fade and slide in on a stagger, like the panel is printing next to
the ASCII portrait. Set STATIC=1 to emit a frozen (already-settled)
frame for local previews.

Usage:
    python scripts/make_info_card.py
Output:
    info-card.svg (repo root)
"""
import os
from pathlib import Path

BG = "#0a0e14"
PANEL_BORDER = "#1b2230"
TITLE_BAR = "#10151f"
ACCENT = "#39d353"       # neon green — matches the heatmap + portrait
ACCENT_DIM = "#2ea043"
KEY_COLOR = "#39d353"
VALUE_COLOR = "#c9d1d9"
MUTED = "#6e7681"
DOT_RED = "#ff5f56"
DOT_YELLOW = "#ffbd2e"
DOT_GREEN = "#27c93f"

WIDTH = 490
ROW_H = 25
PADDING_TOP = 62
PADDING_X = 22
STAGGER = 0.09
FADE_DUR = 0.4

ROWS = [
    ("whoami", "sujal · Full-Stack + AI/ML developer"),
    ("stack", "React · React Native · Flask · Supabase"),
    ("ml", "YOLOv8 · OpenCV · OCR · TensorFlow/Keras"),
    ("shipped", "Eagle Eye · SAAPT · ReviewTap · Bhairavnath"),
    ("fastest_ship", "SAAPT — full attendance system, 1 week"),
    ("status", "open to internships & freelance work"),
]

SWATCHES = ["#0a0e14", "#ff5f56", "#39d353", "#ffbd2e",
            "#58a6ff", "#bc8cff", "#39d3c8", "#c9d1d9"]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(static: bool = False) -> str:
    height = PADDING_TOP + ROW_H * len(ROWS) + 46

    rows_svg = []
    for i, (key, value) in enumerate(ROWS):
        y = PADDING_TOP + i * ROW_H
        begin = i * STAGGER

        if static:
            opacity_attr = 'opacity="1"'
            transform_attr = ""
            extra = ""
        else:
            opacity_attr = 'opacity="0"'
            transform_attr = f' transform="translate(-14 0)"'
            extra = (
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.3f}s" dur="{FADE_DUR}s" fill="freeze" />'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-14 0" to="0 0" begin="{begin:.3f}s" dur="{FADE_DUR}s" '
                f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1" />'
            )

        rows_svg.append(
            f'<g {opacity_attr}{transform_attr}>'
            f'{extra}'
            f'<text x="{PADDING_X}" y="{y}" font-family="\'SF Mono\', \'Fira Code\', '
            f'Consolas, monospace" font-size="13.5" font-weight="600" '
            f'fill="{KEY_COLOR}">{esc(key)}</text>'
            f'<text x="{PADDING_X + 118}" y="{y}" font-family="\'SF Mono\', '
            f'\'Fira Code\', Consolas, monospace" font-size="13.5" '
            f'fill="{VALUE_COLOR}">{esc(value)}</text>'
            f'</g>'
        )

    # Color swatch strip (classic neofetch touch), fades in last
    swatch_y = PADDING_TOP + ROW_H * len(ROWS) + 14
    swatch_begin = len(ROWS) * STAGGER
    swatch_size = 18
    swatches_svg = []
    for i, color in enumerate(SWATCHES):
        x = PADDING_X + i * (swatch_size + 4)
        swatches_svg.append(
            f'<rect x="{x}" y="{swatch_y}" width="{swatch_size}" height="{swatch_size}" '
            f'rx="3" fill="{color}" stroke="{PANEL_BORDER}" stroke-width="1"/>'
        )
    swatch_group_opacity = '1' if static else '0'
    swatch_extra = "" if static else (
        f'<animate attributeName="opacity" from="0" to="1" '
        f'begin="{swatch_begin:.3f}s" dur="{FADE_DUR}s" fill="freeze" />'
    )

    svg = f'''<svg viewBox="0 0 {WIDTH} {height:.0f}" width="{WIDTH}" height="{height:.0f}"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="panelClip"><rect width="{WIDTH}" height="{height:.0f}" rx="12"/></clipPath>
  </defs>
  <g clip-path="url(#panelClip)">
    <rect width="{WIDTH}" height="{height:.0f}" fill="{BG}"/>
    <rect width="{WIDTH}" height="34" fill="{TITLE_BAR}"/>
    <circle cx="20" cy="17" r="6" fill="{DOT_RED}"/>
    <circle cx="40" cy="17" r="6" fill="{DOT_YELLOW}"/>
    <circle cx="60" cy="17" r="6" fill="{DOT_GREEN}"/>
    <text x="{WIDTH/2}" y="21" text-anchor="middle" font-family="'SF Mono', Consolas, monospace"
          font-size="12" fill="{MUTED}">sujal@github: ~</text>
    <rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1:.0f}" rx="12"
          fill="none" stroke="{PANEL_BORDER}" stroke-width="1"/>
    {"".join(rows_svg)}
    <g opacity="{swatch_group_opacity}">{swatch_extra}{"".join(swatches_svg)}</g>
  </g>
</svg>'''
    return svg


if __name__ == "__main__":
    static = os.environ.get("STATIC") == "1"
    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / "info-card.svg"
    out_path.write_text(build_svg(static=static))
    print(f"Wrote {out_path}{' (static)' if static else ''}")

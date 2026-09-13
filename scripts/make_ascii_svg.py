"""
make_ascii_svg.py
Converts source-prepped.png into a self-typing, monochrome ASCII-art SVG.
Each row wipes in left-to-right with a small cursor block riding the
edge, staggered top to bottom. Prints once, freezes (no looping).

Usage:
    python scripts/make_ascii_svg.py
Output:
    avi-ascii.svg  (repo root)
"""
from pathlib import Path

import cv2
import numpy as np

# bright (sparse) -> dark (dense); leading space clears background to nothing
RAMP = " .`:-=+*cs#%@"

COLS = 100
FONT_SIZE = 9
CHAR_W_RATIO = 0.6           # monospace cell width as a fraction of height
ROW_STAGGER = 0.045          # seconds between each row starting its wipe
WIPE_DUR = 0.35              # seconds for a single row to fully wipe in

FILL_COLOR = "#39d353"       # neon green, matches the heatmap accent
BG_COLOR = "#0a0e14"
CURSOR_COLOR = "#7ee89a"


def load_and_crop(path: str, pad_frac: float = 0.04, bust_frac: float = 0.60) -> np.ndarray:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    subject_mask = img < 248
    ys, xs = np.where(subject_mask)
    y0, y1 = ys.min(), ys.max()
    x0, x1 = xs.min(), xs.max()
    h, w = img.shape
    pad_y = int((y1 - y0) * pad_frac)
    pad_x = int((x1 - x0) * pad_frac)
    y0 = max(0, y0 - pad_y)
    y1 = min(h, y1 + pad_y)
    x0 = max(0, x0 - pad_x)
    x1 = min(w, x1 + pad_x)
    # Bust crop: keep head/neck/top-of-shoulders, drop most of the torso
    # so busy shirt texture doesn't dominate the art.
    y1 = y0 + int((y1 - y0) * bust_frac)
    cropped = img[y0:y1, x0:x1]
    # Light blur smooths fabric/hair micro-texture into clean tonal bands
    return cv2.GaussianBlur(cropped, (0, 0), sigmaX=1.4)


def to_ascii_grid(img: np.ndarray, cols: int) -> list[str]:
    h, w = img.shape
    rows = max(1, round(cols * (h / w) * CHAR_W_RATIO))
    small = cv2.resize(img, (cols, rows), interpolation=cv2.INTER_AREA)
    ramp_len = len(RAMP)
    lines = []
    for r in range(rows):
        line_chars = []
        for c in range(cols):
            brightness = small[r, c]  # 0 dark .. 255 bright
            idx = int((255 - brightness) / 256 * ramp_len)
            idx = min(idx, ramp_len - 1)
            line_chars.append(RAMP[idx])
        lines.append("".join(line_chars))
    return lines


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_svg(lines: list[str]) -> str:
    char_w = FONT_SIZE * CHAR_W_RATIO
    char_h = FONT_SIZE * 1.15
    cols = max(len(l) for l in lines)
    rows = len(lines)
    width = cols * char_w + 20
    height = rows * char_h + 20

    clip_defs = []
    row_groups = []
    for i, line in enumerate(lines):
        y = 10 + i * char_h + FONT_SIZE
        row_w = len(line) * char_w
        begin = i * ROW_STAGGER
        clip_id = f"clip{i}"

        clip_defs.append(
            f'<clipPath id="{clip_id}">'
            f'<rect x="0" y="{10 + i * char_h}" width="0" height="{char_h + 2}">'
            f'<animate attributeName="width" from="0" to="{row_w}" '
            f'begin="{begin:.3f}s" dur="{WIPE_DUR}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1" />'
            f'</rect></clipPath>'
        )

        row_groups.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="10" y="{y}" font-family="\'SF Mono\', \'Fira Code\', '
            f'Consolas, monospace" font-size="{FONT_SIZE}" fill="{FILL_COLOR}" '
            f'xml:space="preserve">{escape_xml(line)}</text>'
            f'</g>'
        )

        cursor_x = 10 + row_w
        row_groups.append(
            f'<rect x="{cursor_x - char_w:.2f}" y="{10 + i * char_h + 1}" '
            f'width="{char_w:.2f}" height="{char_h - 2:.2f}" fill="{CURSOR_COLOR}">'
            f'<animate attributeName="opacity" values="0;0;1;1;0" '
            f'keyTimes="0;0.01;0.05;0.9;1" begin="{begin:.3f}s" dur="{WIPE_DUR}s" '
            f'fill="freeze" />'
            f'<animate attributeName="x" from="{10 - char_w:.2f}" to="{cursor_x - char_w:.2f}" '
            f'begin="{begin:.3f}s" dur="{WIPE_DUR}s" fill="freeze" />'
            f'</rect>'
        )

    svg = f'''<svg viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    {"".join(clip_defs)}
  </defs>
  <rect width="{width:.0f}" height="{height:.0f}" fill="{BG_COLOR}" rx="10"/>
  {"".join(row_groups)}
</svg>'''
    return svg


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent
    cropped = load_and_crop(str(repo_root / "source-prepped.png"))
    lines = to_ascii_grid(cropped, COLS)
    svg = build_svg(lines)
    out_path = repo_root / "avi-ascii.svg"
    out_path.write_text(svg)
    print(f"Wrote {out_path} ({len(lines)} rows x {COLS} cols)")

"""
prep_photo.py
Turns a normal photo into a clean, high-contrast grayscale image ready
for ASCII conversion:
  1. Remove the background (rembg) so only the subject remains.
  2. Boost local contrast with CLAHE so flat lighting gets real
     highlights/shadows.
  3. Composite onto pure white so the background maps to the blank
     end of the ASCII ramp.

Usage:
    python scripts/prep_photo.py source-photo.jpg
Output:
    source-prepped.png (grayscale, same folder as input)
"""
import sys
import io
from pathlib import Path

import numpy as np
import cv2
from PIL import Image
from rembg import remove, new_session

_SESSION = new_session("u2net")  # lighter model than the new default


def prep_photo(input_path: str) -> str:
    in_path = Path(input_path)
    out_path = in_path.with_name("source-prepped.png")

    raw = in_path.read_bytes()
    print("Removing background...")
    cutout_bytes = remove(raw, session=_SESSION)
    cutout = Image.open(io.BytesIO(cutout_bytes)).convert("RGBA")

    # Composite the transparent cutout onto pure white
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    # Convert to grayscale for CLAHE
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)

    print("Boosting local contrast (CLAHE)...")
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # Re-composite: keep background pure white using the alpha mask,
    # subject uses the contrast-boosted grayscale values
    alpha = np.array(cutout.split()[-1])  # alpha channel of cutout
    mask = alpha > 10
    final = np.full_like(contrasted, 255)
    final[mask] = contrasted[mask]

    Image.fromarray(final).save(out_path)
    print(f"Wrote {out_path}")
    return str(out_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/prep_photo.py <photo path>")
        sys.exit(1)
    prep_photo(sys.argv[1])

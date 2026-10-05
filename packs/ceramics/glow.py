"""Glowing-crevice panels: make the glow colour periodic + export an emissive map.

Panel renders already line up geometrically, but the glow hue drifts across the
image (e.g. magenta on the left, orange on the right), so copies meet with a
colour jump. Only the glow is re-hued, with a periodic magenta -> orange field,
keeping its saturation, brightness and detail. Emissive = glow mask x colour.

Usage: python glow.py raw/name.png textures/  [hue_a hue_b]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

src, out = Path(sys.argv[1]), Path(sys.argv[2])
hue_a = float(sys.argv[3]) if len(sys.argv) > 3 else 0.86    # magenta
hue_b = float(sys.argv[4]) if len(sys.argv) > 4 else 1.06    # orange (wraps via red)
name = src.stem

img = Image.open(src).convert("RGB")
hsv = np.asarray(img.convert("HSV"), np.float32) / 255
h, w = hsv.shape[:2]
s, v = hsv[..., 1], hsv[..., 2]
mask = np.clip((s - 0.35) / 0.3, 0, 1) * np.clip((v - 0.35) / 0.3, 0, 1)

ys, xs = np.mgrid[0:h, 0:w]
t = 0.5 - 0.3 * np.cos(2 * np.pi * xs / w) - 0.2 * np.cos(2 * np.pi * ys / h)   # periodic 0..1
new_h = (hue_a + (hue_b - hue_a) * t) % 1.0
hsv2 = hsv.copy()
hsv2[..., 0] = new_h
rehued = np.asarray(Image.fromarray((hsv2 * 255).round().astype(np.uint8), "HSV").convert("RGB"), np.float32)
orig = np.asarray(img, np.float32)
# Blend in RGB: blending hue values directly sweeps the colour wheel (rainbow fringes).
rgb = (orig * (1 - mask[..., None]) + rehued * mask[..., None]).round().astype(np.uint8)
Image.fromarray(rgb).save(out / f"{name}.png", optimize=True)

emis = (rgb.astype(np.float32) * mask[..., None]).round().astype(np.uint8)
Image.fromarray(emis).save(out / f"{name}_emissive.png", optimize=True)
print("ok", name, "glow coverage", round(float((mask > 0.5).mean()), 3))

"""Crystalline glaze PBR set: matte blue ground, metallic gold/silver crystals.

Input is the seamless albedo from make_seamless.py. Crystals are detected as
anything that is not the saturated blue ground; then:
  albedo    +20% saturation (blue deepened slightly)
  metallic  1 on crystals, 0 on ground
  roughness 0.75 ground (matte), 0.22 crystals (glinting, not chrome)
  normal    gentle relief from crystal luminance so the fans catch light

Usage: python crystalline.py textures/crystalline_glaze.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

p = Path(sys.argv[1])
img = Image.open(p).convert("RGB")
hsv = np.asarray(img.convert("HSV"), np.float32) / 255
hue, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
blue = np.clip((s - 0.30) / 0.2, 0, 1) * ((hue > 0.42) & (hue < 0.70))
crystal = 1 - blue


def wrap_blur(a, sigma):
    f = np.fft.fftfreq(a.shape[0])
    k = np.exp(-2 * (np.pi * sigma) ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * k))


crystal = np.clip(wrap_blur(crystal, 1.0), 0, 1)

hsv2 = hsv.copy()
hsv2[..., 1] = np.clip(s * 1.2, 0, 1)
hsv2[..., 2] = v * (1 - 0.06 * blue)                     # deepen the blue a touch
Image.fromarray((hsv2 * 255).round().astype(np.uint8), "HSV").convert("RGB").save(p, optimize=True)

stem = p.with_suffix("")
Image.fromarray((crystal * 255).round().astype(np.uint8)).save(f"{stem}_metallic.png", optimize=True)
rough = 0.75 * (1 - crystal) + 0.22 * crystal
Image.fromarray((rough * 255).round().astype(np.uint8)).save(f"{stem}_roughness.png", optimize=True)

height = wrap_blur(v * crystal, 1.2) + 0.15 * crystal
dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * 3.0
dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * 3.0
n = np.dstack([-dx, dy, np.ones_like(height)])
n /= np.linalg.norm(n, axis=-1, keepdims=True)
Image.fromarray(((n * 0.5 + 0.5) * 255).round().astype(np.uint8)).save(f"{stem}_normal.png", optimize=True)
print("ok crystalline, crystal coverage", round(float((crystal > 0.5).mean()), 3))

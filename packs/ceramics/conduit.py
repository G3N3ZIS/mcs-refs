"""Hide a horizontal wrap seam in glowing-channel textures with a conduit.

Some AI renders tile left/right but not top/bottom. For channel layouts the
honest fix is a full-width glowing channel along the seam, built from the
image's own strongest horizontal channel (its median cross-section), so new
T-junctions look like part of the design.

Usage: python conduit.py raw/name.png textures/name.png [half_width]
"""
import sys

import numpy as np
from PIL import Image

src, dst = sys.argv[1], sys.argv[2]
R = int(sys.argv[3]) if len(sys.argv) > 3 else 22
img = np.asarray(Image.open(src).convert("RGB"), np.float32)
h, w, _ = img.shape
hsv = np.asarray(Image.fromarray(img.astype(np.uint8)).convert("HSV"), np.float32) / 255
glow = (hsv[..., 1] > 0.5) & (hsv[..., 2] > 0.6)

# Strongest horizontal channel, away from the seam.
rows = glow.mean(1)
rows[:R * 2] = rows[-R * 2:] = 0
y0 = int(np.argmax(rows))
# Columns where that row is a straight run (glow at y0, dark well above/below).
cols = glow[y0] & ~glow[(y0 - R) % h] & ~glow[(y0 + R) % h]
band = img[(y0 + np.arange(-R, R + 1)) % h][:, cols]          # (2R+1, n, 3)
profile = np.percentile(band, 80, axis=1)                        # (2R+1, 3); median runs dim

out = img.copy()
d = np.abs(np.arange(-R, R + 1))
alpha = np.clip((R - d) / 6, 0, 1)[:, None, None]                # feather outer 6 px
idx = np.arange(-R, R + 1) % h
out[idx] = out[idx] * (1 - alpha) + profile[:, None, :] * alpha
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(dst, optimize=True)
print(f"conduit from row {y0} using {cols.sum()} columns")

"""White porcelain PBR set: flat albedo with micro detail + normal + roughness.

The AI render has a big baked-in "bulge" (lighting). That is removed by dividing
out the low-frequency shading, leaving only the real specks. Micro surface
(orange-peel glaze ripple, fine grain, pinholes) is built from FFT-filtered
noise, which is periodic by construction, so every map tiles exactly.

Glaze optics: porcelain is an opaque white body under a thin clear glass glaze.
Glaze IOR ~1.50-1.55 -> F0 = ((n-1)/(n+1))^2 ~= 0.040-0.046. It reads as "glossy
but not glass" because it is opaque (no transmission), very smooth (roughness
~0.05-0.1) and the orange-peel ripple gently wobbles reflections.

Usage: python porcelain.py raw/white_porcelain.png textures/
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

import make_seamless

N = 1024
IOR = 1.5
F0 = ((IOR - 1) / (IOR + 1)) ** 2          # 0.04
ALBEDO_SRGB = np.array([236, 239, 241])     # bright white, faintly cool (~0.84 linear)
rng = np.random.default_rng(7)


def band_noise(lo_px, hi_px, n=N):
    """Periodic noise keeping wavelengths between lo_px and hi_px; std 1."""
    f = np.fft.fftfreq(n)
    r = np.hypot(*np.meshgrid(f, f))
    keep = (r >= 1 / hi_px) & (r <= 1 / lo_px)
    spec = np.fft.fft2(rng.standard_normal((n, n))) * keep
    out = np.real(np.fft.ifft2(spec))
    return out / out.std()


def blur(a, r):
    """Wrap-around Gaussian blur of a 2-D float array via FFT."""
    f = np.fft.fftfreq(a.shape[0])
    k = np.exp(-2 * (np.pi * r) ** 2 * (f[:, None] ** 2 + f[None, :] ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * k))


def pinholes(count=140):
    """Tiny glaze pinholes as a 0..1 depth map (wrapping)."""
    m = np.zeros((N, N))
    ys, xs = rng.integers(0, N, count), rng.integers(0, N, count)
    rad = rng.uniform(0.8, 2.2, count)
    yy, xx = np.mgrid[-4:5, -4:5]
    for y, x, rr in zip(ys, xs, rad):
        d = np.clip(1 - (xx ** 2 + yy ** 2) / rr ** 2, 0, 1)
        m[np.ix_((y + np.arange(-4, 5)) % N, (x + np.arange(-4, 5)) % N)] = np.maximum(
            m[np.ix_((y + np.arange(-4, 5)) % N, (x + np.arange(-4, 5)) % N)], d)
    return m


def build(src: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    img = np.asarray(Image.open(src).convert("RGB").resize((N, N), Image.LANCZOS), np.float32)

    # 1. Remove baked lighting: divide by heavy blur, keep only fine specks.
    lum = img.mean(-1)
    low = np.asarray(Image.fromarray(lum.clip(0, 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(48)), np.float32)
    detail = lum / np.maximum(low, 1)                       # ~1.0, specks < 1
    detail = 1 + (detail - 1) * 0.8
    detail = make_seamless.quilt(np.repeat(detail[..., None], 3, -1) * 200)[..., 0] / 200

    # 2. Micro surface height (all periodic).
    peel = band_noise(10, 48)            # orange-peel ripple
    grain = band_noise(1.5, 4)           # fine body grain
    holes = pinholes()
    height = 0.55 * peel + 0.12 * grain - 2.5 * holes

    # 3. Albedo: flat white x specks, whisper of glaze-thickness variation.
    tint = 1 + 0.006 * blur(band_noise(60, 300), 2)
    alb = ALBEDO_SRGB[None, None, :] * (detail * tint)[..., None]
    alb -= 30 * blur(holes, 0.6)[..., None]                 # pinholes catch grime
    Image.fromarray(alb.clip(0, 255).astype(np.uint8)).save(out / "white_porcelain.png", optimize=True)

    # 4. Normal map (OpenGL / Y+), wrap-around gradients.
    strength = 0.05                          # orange peel: reflections stay crisp, edges just wobble
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5 * strength
    nrm = np.dstack([-dx, dy, np.ones_like(height)])
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    Image.fromarray(((nrm * 0.5 + 0.5) * 255).round().astype(np.uint8)).save(
        out / "white_porcelain_normal.png", optimize=True)

    # 5. Roughness: very smooth glaze, slightly rougher in pinholes.
    rough = 0.07 + 0.012 * band_noise(20, 200) + 0.35 * blur(holes, 0.8)
    rough = rough.clip(0.03, 0.6)
    Image.fromarray((rough * 255).round().astype(np.uint8)).save(
        out / "white_porcelain_roughness.png", optimize=True)

    # 6. Height (for parallax / displacement), 0..1.
    h = (height - height.min()) / np.ptp(height)
    Image.fromarray((h * 255).round().astype(np.uint8)).save(out / "white_porcelain_height.png", optimize=True)
    return alb, nrm, rough


def render_preview(alb, nrm, rough, path: Path):
    """Lit 2x2 preview. Gloss on porcelain is seen as a sharp reflection of an
    extended light, so the view ray is mirrored off the normal map into a
    synthetic studio: one softbox + soft ceiling gradient. Reflection strength
    uses Schlick Fresnel with F0 from the glaze IOR; roughness blurs it."""
    a = np.tile((alb / 255) ** 2.2, (2, 2, 1))
    n = np.tile(nrm, (2, 2, 1))
    r = np.tile(rough, (2, 2))
    hh, ww = r.shape
    ys, xs = np.mgrid[0:hh, 0:ww] / hh
    # Perspective camera above the centre, so the view ray varies across frame.
    cam = np.array([0.5, 0.5, 1.6])
    p = np.dstack([xs, ys, np.zeros_like(xs)])
    v = cam - p
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    ndv = np.clip((n * v).sum(-1, keepdims=True), 1e-3, 1)
    refl = 2 * ndv * n - v                                    # mirrored view ray
    t = 1.0 / np.clip(refl[..., 2:3], 1e-3, None)              # hit plane z = 1
    hit = p + refl * t
    hx, hy = hit[..., 0], hit[..., 1]
    box = ((hx > 0.15) & (hx < 0.55) & (hy > 0.05) & (hy < 0.35)).astype(np.float32)
    # Roughness widens the reflection: blur in proportion to mean roughness.
    box = np.asarray(Image.fromarray((box * 255).astype(np.uint8))
                     .filter(ImageFilter.GaussianBlur(1 + 40 * float(r.mean()))), np.float32) / 255
    env = 0.35 * (1 - 0.5 * np.clip(np.hypot(hx - 0.5, hy - 0.5), 0, 1)) + 2.2 * box
    fres = F0 + (1 - F0) * (1 - ndv[..., 0]) ** 5
    # Diffuse from the same softbox-ish overhead light (flat surface: ~uniform).
    light = np.array([-0.3, -0.5, 1.0]); light /= np.linalg.norm(light)
    ndl = np.clip((n * light).sum(-1), 0, 1)
    col = a * (0.35 + 0.65 * ndl)[..., None] * (1 - fres[..., None]) + (fres * env)[..., None]
    col = 1.2 * col / (1 + 0.12 * col)                         # exposure + soft shoulder
    col = col.clip(0, 1) ** (1 / 2.2)
    Image.fromarray((col * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS).save(path, quality=90)


if __name__ == "__main__":
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    alb, nrm, rough = build(src, out)
    prev = Path(__file__).parent / "previews"
    prev.mkdir(exist_ok=True)
    render_preview(alb, nrm, rough, prev / "white_porcelain_lit_2x2.jpg")
    print("ok white_porcelain")

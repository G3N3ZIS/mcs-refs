"""Make AI-generated 1K ceramic textures tile seamlessly.

Grid textures (tiles with grout) are cropped to a whole number of repeats and
resized, so the grout lands exactly on the edges. Organic textures (glazes,
cracks, clay) default to "quilt": the image is half-shifted so its seams sit in
the middle, then the original is patched back over them along minimum-difference
cuts (image quilting), which avoids the ghosting of a plain cross-fade.
"blend" (offset cross-fade) is kept as a fallback.

Usage: python make_seamless.py raw/ textures/
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

SIZE = 1024


def offset_blend(img: np.ndarray, border: float = 0.22) -> np.ndarray:
    """Cross-fade with a (h/2, w/2)-rolled copy. The rolled copy is seamless at
    the frame edges; the original dominates the centre where it has no seam."""
    h, w = img.shape[:2]
    rolled = np.roll(img, (h // 2, w // 2), axis=(0, 1))

    def ramp(n):
        t = np.abs(np.linspace(-1, 1, n))          # 0 centre, 1 edges
        m = np.clip((t - (1 - 2 * border)) / (2 * border), 0, 1)
        return m * m * (3 - 2 * m)                  # smoothstep

    mask = np.maximum.outer(ramp(h), ramp(w))[..., None]  # 1 near edges
    # Rolled copy has the original's seam through its centre, so keep the
    # mask from reaching the middle (border < 0.5 guarantees that).
    out = img * (1 - mask) + rolled * mask
    # Restore fine grain lost to blending: re-add high-pass of the dominant layer.
    blur = lambda a: np.asarray(
        Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)),
        dtype=np.float32)
    hp_img, hp_rol = img - blur(img), rolled - blur(rolled)
    dominant_hp = np.where(mask > 0.5, hp_rol, hp_img)
    out = blur(out) + dominant_hp
    return out


def _min_cut(cost: np.ndarray) -> np.ndarray:
    """Minimum-cost vertical path through cost (h, w); returns column per row.
    Start and end columns are forced equal so the cut itself wraps cleanly."""
    h, w = cost.shape
    ends = cost[0] + cost[-1]
    c0 = int(np.argmin(ends))
    dp = np.full((h, w), np.inf)
    back = np.zeros((h, w), dtype=np.int64)
    dp[0, c0] = cost[0, c0]
    for y in range(1, h):
        prev = dp[y - 1]
        cand = np.stack([np.r_[np.inf, prev[:-1]], prev, np.r_[prev[1:], np.inf]])
        k = np.argmin(cand, axis=0)
        dp[y] = cost[y] + cand[k, np.arange(w)]
        back[y] = np.arange(w) + k - 1
    path = np.empty(h, dtype=np.int64)
    path[-1] = c0
    for y in range(h - 1, 0, -1):
        path[y - 1] = back[y, path[y]]
    return path


def _quilt_x(img: np.ndarray, band: int) -> np.ndarray:
    """Make img tile left/right: roll by w/2 (seam moves to the centre), then
    patch the centre with the original, joined along two min-cost cuts."""
    h, w = img.shape[:2]
    rolled = np.roll(img, w // 2, axis=1)
    c = w // 2
    # Colour difference, smoothed so cuts prefer areas that agree over a
    # neighbourhood (cracks then meet their continuation instead of stopping).
    diff = np.sqrt(((rolled - img) ** 2).sum(-1))
    diff = np.asarray(Image.fromarray(diff.clip(0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(3)), np.float32) ** 2
    gap = 24                                  # keep cuts off the seam itself
    left = _min_cut(diff[:, c - band:c - gap]) + c - band
    right = _min_cut(diff[:, c + gap:c + band]) + c + gap
    xs = np.arange(w)[None, :]
    mask = ((xs > left[:, None]) & (xs < right[:, None])).astype(np.float32)
    hard = _wrap_blur(mask, 1.5)[..., None]
    soft = _wrap_blur(mask, 40)[..., None]
    # Fine detail follows the hard cut (no ghosting); broad colour follows a
    # wide feather (no visible patch outlines where large colour zones differ).
    lo_r, lo_i = _wrap_blur(rolled, 24), _wrap_blur(img, 24)
    low = lo_r * (1 - soft) + lo_i * soft
    high = (rolled - lo_r) * (1 - hard) + (img - lo_i) * hard
    return low + high


def _wrap_blur(a: np.ndarray, sigma: float) -> np.ndarray:
    """Gaussian blur with wrap-around edges (FFT), for 2-D or HxWxC arrays."""
    h, w = a.shape[:2]
    fy, fx = np.fft.fftfreq(h)[:, None], np.fft.fftfreq(w)[None, :]
    k = np.exp(-2 * (np.pi * sigma) ** 2 * (fy ** 2 + fx ** 2))
    if a.ndim == 3:
        k = k[..., None]
    return np.real(np.fft.ifft2(np.fft.fft2(a, axes=(0, 1)) * k, axes=(0, 1)))


def quilt(img: np.ndarray, band: int = 300) -> np.ndarray:
    """Seam-cut tiling: no ghosting, cuts follow the texture's own edges."""
    img = _quilt_x(img, band)
    return np.swapaxes(_quilt_x(np.swapaxes(img, 0, 1), band), 0, 1)


def grid_crop(img: Image.Image, box) -> Image.Image:
    """Crop to (left, top, right, bottom) — a whole number of tile repeats."""
    return img.crop(box)


def process(src: Path, cfg: dict) -> Image.Image:
    img = Image.open(src).convert("RGB")
    if "crop" in cfg:
        img = grid_crop(img, cfg["crop"])
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    method = cfg.get("method", "quilt")
    if method != "none":
        arr = np.asarray(img, dtype=np.float32)
        arr = quilt(arr) if method == "quilt" else offset_blend(arr, cfg.get("border", 0.22))
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    return img


if __name__ == "__main__":
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    config = json.loads((Path(__file__).parent / "seamless.json").read_text())
    for name, cfg in config.items():
        if cfg.get("method") in ("conduit", "glow"):   # handled by conduit.py / glow.py
            continue
        src = raw / f"{name}.png"
        if not src.exists():
            print("missing", src)
            continue
        process(src, cfg).save(out / f"{name}.png", optimize=True)
        print("ok", name)

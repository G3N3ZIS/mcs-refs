"""Make AI-generated 1K ceramic textures tile seamlessly.

Grid textures (tiles with grout) are cropped to a whole number of repeats and
resized, so the grout lands exactly on the edges. Organic textures (glazes,
cracks, clay) use an offset cross-fade: the image is blended with a half-shifted
copy of itself through a soft mask that hides the original seams.

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


def grid_crop(img: Image.Image, box) -> Image.Image:
    """Crop to (left, top, right, bottom) — a whole number of tile repeats."""
    return img.crop(box)


def process(src: Path, cfg: dict) -> Image.Image:
    img = Image.open(src).convert("RGB")
    if "crop" in cfg:
        img = grid_crop(img, cfg["crop"])
    img = img.resize((SIZE, SIZE), Image.LANCZOS)
    if cfg.get("blend", True):
        arr = np.asarray(img, dtype=np.float32)
        arr = offset_blend(arr, cfg.get("border", 0.22))
        img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    return img


if __name__ == "__main__":
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    config = json.loads((Path(__file__).parent / "seamless.json").read_text())
    for name, cfg in config.items():
        src = raw / f"{name}.png"
        if not src.exists():
            print("missing", src)
            continue
        process(src, cfg).save(out / f"{name}.png", optimize=True)
        print("ok", name)

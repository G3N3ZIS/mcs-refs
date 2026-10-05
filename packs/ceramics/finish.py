"""Backlog batch (PC session 2026-10-05): raw/<name>.png -> textures/<name>.png + previews/<name>_2x2.jpg.

Grid/organic textures go through make_seamless.process with their seamless.json entry.
The "manual" ones are done here, with the measurement behind each step noted inline.

Usage: python finish.py [name ...]     (default: every name in BATCH)
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from make_seamless import _min_cut, process

HERE = Path(__file__).parent
CFG = json.loads((HERE / "seamless.json").read_text())


def period_box(name, box):
    """Resample a whole number of measured repeats (sub-pixel box) to 1024."""
    return Image.open(HERE / f"raw/{name}.png").convert("RGB").resize((1024, 1024), Image.LANCZOS, box=box)


def period_quilt(img: Image.Image, shift: int, band=220, gap=12) -> Image.Image:
    """Period-cropped mosaics line up but hand-glazed cell colours still flip at the
    wrap. A copy rolled by whole periods has the same geometry with its seam
    elsewhere; swap it in around the wrap along min-cost cuts. The two copies
    only agree on grout, so the cuts run along joints and never slice a cell."""
    def x(a):
        w = a.shape[1]
        c = w // 2
        a = np.roll(a, c, axis=1)                         # wrap seam -> centre
        b = np.roll(a, shift, axis=1)                     # same lattice, seam away from centre
        d = np.asarray(Image.fromarray(np.sqrt(((a - b) ** 2).sum(-1)).clip(0, 255).astype(np.uint8))
                       .filter(ImageFilter.GaussianBlur(2)), np.float32) ** 2
        left = _min_cut(d[:, c - band:c - gap]) + c - band
        right = _min_cut(d[:, c + gap:c + band]) + c + gap
        xs = np.arange(w)[None, :]
        m = ((xs > left[:, None]) & (xs < right[:, None]))[..., None]
        return np.roll(np.where(m, b, a), -c, axis=1)
    a = x(np.asarray(img, np.float32))
    a = np.swapaxes(x(np.swapaxes(a, 0, 1)), 0, 1)
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def grout_copy(name, cols, rows):
    """Tiles whose render has grout inside but not on the edges: copy the centre
    grout band onto the wrap, keeping its offset from the centre line."""
    a = np.asarray(Image.open(HERE / f"raw/{name}.png").convert("RGB")).copy()
    c0, c1 = cols
    a[:, (np.arange(c0, c1) + 512) % 1024] = a[:, c0:c1]
    r0, r1 = rows
    a[(np.arange(r0, r1) + 512) % 1024] = a[r0:r1]
    return Image.fromarray(a)


MANUAL = {
    # autocorrelation: 511.66 / 511.73 px repeat -> two periods
    "zellige_star": lambda: period_quilt(period_box("zellige_star", (0, 0, 1023.46, 1023.32)), 512),
    # 170.6 px across x 171.4 px down -> 5 x 5 repeats (~20 % upscale); 2 periods = 409.6 px
    "fishscale_pastel": lambda: period_quilt(period_box("fishscale_pastel", (0, 0, 5 * 170.6, 5 * 171.4)), 410),
    # oak frame is 50 px on every edge -> keep 25 so neighbours share one 50 px strip
    "hex_oak": lambda: period_box("hex_oak", (25, 25, 999, 999)),
    "greige_concrete": lambda: grout_copy("greige_concrete", (509, 514), (510, 517)),
    "terrazzo_pastel": lambda: grout_copy("terrazzo_pastel", (508, 516), (508, 516)),
}

BATCH = ["azulejo_tile", "zellige_star", "encaustic_tile", "kintsugi_clay", "kintsugi_celadon",
         "iznik_tulip", "artdeco_emerald", "hex_oak", "terrazzo_pastel", "scandi_arches",
         "marble_calacatta", "greige_concrete", "fishscale_pastel", "plank_sage", "plank_beige",
         "plank_rustic"]


def preview(img: Image.Image, name: str):
    t = Image.new("RGB", (2048, 2048))
    for x in (0, 1024):
        for y in (0, 1024):
            t.paste(img, (x, y))
    t.resize((1024, 1024), Image.LANCZOS).save(HERE / f"previews/{name}_2x2.jpg", quality=88)
    return t.crop((768, 768, 1280, 1280))      # full-res join, for eyeballing


if __name__ == "__main__":
    names = sys.argv[1:] or BATCH
    joins = Image.new("RGB", (512 * 5, 512 * (-(-len(names) // 5))), (24, 24, 24))
    for i, n in enumerate(names):
        img = MANUAL[n]() if n in MANUAL else process(HERE / f"raw/{n}.png", CFG[n])
        img.save(HERE / f"textures/{n}.png", optimize=True)
        joins.paste(preview(img, n), ((i % 5) * 512, (i // 5) * 512))
        print("ok", n)
    joins.save(HERE / "previews/_joins.jpg", quality=90)

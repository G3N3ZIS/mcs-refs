"""Assemble the Ceramics resource pack (Minecraft Java 1.21.x).

Each finished 1024px texture replaces a vanilla block that never rotates
(concrete / terracotta), so seamless textures stay continuous across a wall.
Glazed terracotta is avoided on purpose: it rotates with placement direction.

Pack rules are Genesis's, applied through Genesis's own code (one pipeline for
every pack we ship): LabPBR _n + _s generated from each albedo by build.py,
normals at HALF resolution (all-or-nothing, the atlas scales sprites to the
largest), every PNG through oxipng (lossless). Needs Genesis's Python 3.12.

Outputs:
  dist/Ceramics/              unpacked pack
  dist/Ceramics.zip           drop into .minecraft/resourcepacks
  previews/contact_sheet.jpg  all textures with names

Usage: <Python312>/python.exe build_pack.py
"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, r"G:\PROJECTS\G3N3ZIS\pack\_tools")
import build as G          # noqa: E402  Genesis pipeline: build_normal/_spec, sanitise, oxipng
import materials as M      # noqa: E402

HERE = Path(__file__).parent
PACK_FORMAT = 88  # same declaration as Genesis: loads 1.21.1 (34) through 1.21.11

# LabPBR material per texture (Genesis materials.py fields). smooth = the
# smoothness range the albedo is remapped into, blue = porosity.
GLAZE = dict(smooth=(0.70, 0.92), blue=6)                 # glossy glaze (default)
MATTE = dict(smooth=(0.18, 0.45), blue=30)                # unglazed clay / cement
GOLD = ("kintsugi", M.METAL["gold"], 28, 52, 0.50, 0.85)  # measured: seam hue 30-40  # gold seams as real metal
MAT = {
    # Petur 2026-10-05: "much more glossy" - near-mirror white dielectric (IOR 1.5)
    "white_porcelain":     dict(smooth=(0.94, 0.99), blue=0, nrm_strength=0.5),  # "tone down the normal a bit"
    "black_porcelain":     dict(smooth=(0.94, 0.99), blue=0, nrm_strength=0.5),  # same glaze as the white
    "kintsugi_raku":      dict(GLAZE, metal_mask=GOLD),
    "kintsugi_celadon":    dict(GLAZE, metal_mask=GOLD),
    "kintsugi_clay":       dict(MATTE, metal_mask=GOLD),
    "voronoi_glaze_gold":  dict(GLAZE, metal_mask=GOLD),
    "crystalline_glaze":   dict(smooth=(0.35, 0.65), blue=8, metal_mask=GOLD),
    "tech_cyan_glow":      dict(smooth=(0.45, 0.75), blue=6, emissive=0.85,
                                emis_map="hue", emis_hue=(165, 205, 0.40, 0.45)),
    "glow_voronoi_plasma": dict(GLAZE, emissive=0.85, emis_map="hue",
                                emis_hue=(290, 40, 0.35, 0.40)),   # magenta..coral, wraps 0
    "saltillo_terracotta": MATTE,
    "encaustic_tile":      dict(smooth=(0.30, 0.55), blue=20),
    "scandi_arches":       dict(smooth=(0.30, 0.55), blue=20),
    "greige_concrete":     dict(smooth=(0.20, 0.45), blue=24),
    "matte_black_hex":     dict(smooth=(0.25, 0.50), blue=14),
    "plank_rustic":        dict(smooth=(0.30, 0.65), blue=18),
    "ash_glaze_stoneware": dict(smooth=(0.35, 0.75), blue=12),
    "hex_oak":             dict(smooth=(0.40, 0.80), blue=12),
    "terrazzo_pastel":     dict(smooth=(0.55, 0.85), blue=8),
    "marble_calacatta":    dict(smooth=(0.78, 0.95), blue=4),
}

# texture -> (display name, vanilla block it replaces)
PACK = {
    "kintsugi_raku":       ("Black Raku Kintsugi",        "black_concrete"),
    "white_porcelain":     ("Pure White Porcelain",       "white_concrete"),
    "flambe_oxblood":      ("Oxblood Flambé Glaze",       "red_concrete"),
    "voronoi_glaze_gold":  ("Jade Voronoi Gold",          "green_concrete"),
    "pastel_zellige":      ("Pastel Zellige Grid",        "pink_concrete"),
    "plank_sage":          ("Sage Wave Planks",           "lime_concrete"),   # Petur 2026-10-05: 1x3, not the 2x8 stack
    "tech_cyan_glow":      ("Cyan Neon Tech Panels",      "cyan_concrete"),
    "plank_white_black":   ("Monochrome Wave Planks",     "gray_concrete"),
    "plank_white":         ("Arctic White Wave Planks",   "light_gray_concrete"),
    "crystalline_glaze":   ("Frost Crystal Glaze",        "blue_concrete"),
    "glow_voronoi_plasma": ("Plasma Voronoi Panel",       "magenta_concrete"),
    "saltillo_terracotta": ("Saltillo Terracotta Floor",  "orange_concrete"),
    "ash_glaze_stoneware": ("Anagama Ash-Glaze Stoneware", "brown_concrete"),
    "fluted_white_relief": ("Fluted White Relief",        "white_terracotta"),
    "matte_black_hex":     ("Matte Black Hex",            "black_terracotta"),
    "delft_tile":          ("Delft Blue Rosettes",        "light_blue_concrete"),
    "kintsugi_clay":       ("Terracotta Kintsugi",        "terracotta"),
    "kintsugi_celadon":    ("Celadon Crackle Kintsugi",   "green_terracotta"),
    "azulejo_tile":        ("Azulejo Quatrefoil",         "blue_terracotta"),
    "zellige_star":        ("Zellige Star Mosaic",        "cyan_terracotta"),
    "encaustic_tile":      ("Victorian Encaustic",        "red_terracotta"),
    "iznik_tulip":         ("Iznik Tulips",               "light_blue_terracotta"),
    "artdeco_emerald":     ("Art Deco Emerald",           "lime_terracotta"),
    "hex_oak":             ("Hex Tiles in Oak",           "brown_terracotta"),
    "terrazzo_pastel":     ("Pastel Terrazzo",            "pink_terracotta"),
    "scandi_arches":       ("Scandi Pastel Arches",       "magenta_terracotta"),
    "marble_calacatta":    ("Calacatta Marble",           "light_gray_terracotta"),
    "greige_concrete":     ("Greige Concrete Tiles",      "gray_terracotta"),
    "fishscale_pastel":    ("Pastel Fish Scales",         "purple_terracotta"),
    "plank_beige":         ("Beige Wave Planks",          "yellow_terracotta"),
    "plank_rustic":        ("Rustic Brick Planks",        "orange_terracotta"),
    "black_porcelain":     ("Jet Black Porcelain",        "purple_concrete"),
}

# extra blocks that reuse a PACK texture (Petur 2026-10-05: keep yellow_concrete)
# polished_diorite / polished_andesite: their block, slab and stairs all read ONE
# texture, so this gives porcelain slabs + stairs (Genesis leaves both alone).
ALIAS = {"yellow_concrete": "plank_sage",
         "polished_diorite": "white_porcelain",
         "polished_andesite": "black_porcelain"}


def build():
    tex = HERE / "textures"
    dist = HERE / "dist"
    root = dist / "Ceramics"
    shutil.rmtree(root, ignore_errors=True)
    blocks = root / "assets/minecraft/textures/block"
    blocks.mkdir(parents=True)

    for name, (_, block) in PACK.items():
        alb = Image.open(tex / f"{name}.png").convert("RGB")
        (blocks / f"{block}.png").write_bytes(G.png_bytes(alb))
        n, s = labpbr(name, alb)
        (blocks / f"{block}_n.png").write_bytes(n)
        (blocks / f"{block}_s.png").write_bytes(s)
        print("  ", name)

    for block, name in ALIAS.items():
        src = PACK[name][1]
        for suf in ("", "_n", "_s"):
            shutil.copy(blocks / f"{src}{suf}.png", blocks / f"{block}{suf}.png")

    (root / "pack.mcmeta").write_text(json.dumps({"pack": {
        "pack_format": PACK_FORMAT,
        "supported_formats": {"min_inclusive": 34, "max_inclusive": PACK_FORMAT},
        "min_format": 34,
        "max_format": PACK_FORMAT,
        "description": f"Ceramics: {len(PACK)} seamless 1K ceramic blocks",
    }}, indent=2))

    sheet = contact_sheet(tex)
    sheet.save(HERE / "previews/contact_sheet.jpg", quality=88)
    icon = Image.new("RGB", (256, 256))
    for i, name in enumerate(list(PACK)[:4]):
        icon.paste(Image.open(tex / f"{name}.png").convert("RGB").resize((128, 128), Image.LANCZOS),
                   ((i % 2) * 128, (i // 2) * 128))
    icon.save(root / "pack.png")

    (root / "MAPPING.txt").write_text("\n".join(
        [f"{block:22s} <- {label}" for _, (label, block) in PACK.items()]
        + [f"{block:22s} <- {PACK[name][0]}" for block, name in ALIAS.items()]) + "\n")

    zpath = dist / "Ceramics.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(root.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(root))
    print(f"ok {len(PACK)} textures -> {zpath} ({zpath.stat().st_size / 1e6:.1f} MB)")


def labpbr(name, alb):
    """_n at half resolution and _s at full, exactly as Genesis build.py writes them."""
    mat = dict(M.DEFAULT, **MAT.get(name, GLAZE))
    G.CURRENT[0], G.TILING[0] = name, True
    a = np.asarray(alb.convert("RGBA"), np.float64)
    w = a.shape[1]
    *nrm, hn = G.build_normal(a, None, mat, w, w)
    spc = G.build_spec(a, None, mat, hn, w, w)
    out = []
    for arr, suf, size, metal in ((nrm, "_n", w // G.NORMAL_DIV, False),
                                  (spc, "_s", w, mat["metal_mask"] is not None)):
        arr = G.sanitise(G.downscale_labpbr(np.stack(arr, -1), (size, size), metal).copy(), suf, mat)
        out.append(G.png_bytes(Image.fromarray(G.u8(arr), "RGBA")))
    return out


def contact_sheet(tex: Path, cell=256, cols=5) -> Image.Image:
    rows = -(-len(PACK) // cols)
    pad = 28
    sheet = Image.new("RGB", (cols * cell, rows * (cell + pad)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except OSError:
        font = ImageFont.truetype("arial.ttf", 15)
    for i, (name, (label, _)) in enumerate(PACK.items()):
        x, y = (i % cols) * cell, (i // cols) * (cell + pad)
        sheet.paste(Image.open(tex / f"{name}.png").convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y))
        draw.text((x + 8, y + cell + 5), label, fill=(235, 235, 235), font=font)
    return sheet


if __name__ == "__main__":
    build()

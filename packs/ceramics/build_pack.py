"""Assemble the Ceramics resource pack (Minecraft Java 1.21.x).

Each finished 1024px texture replaces a vanilla block that never rotates
(concrete / terracotta), so seamless textures stay continuous across a wall.
Glazed terracotta is avoided on purpose: it rotates with placement direction.

Outputs:
  dist/Ceramics/              unpacked pack
  dist/Ceramics.zip           drop into .minecraft/resourcepacks
  previews/contact_sheet.jpg  all textures with names

Usage: python build_pack.py
"""
import json
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
PACK_FORMAT = 34  # Java 1.21 / 1.21.1

# texture -> (display name, vanilla block it replaces)
PACK = {
    "kintsugi_raku":       ("Black Raku Kintsugi",        "black_concrete"),
    "white_porcelain":     ("Pure White Porcelain",       "white_concrete"),
    "flambe_oxblood":      ("Oxblood Flambé Glaze",       "red_concrete"),
    "voronoi_glaze_gold":  ("Jade Voronoi Gold",          "green_concrete"),
    "pastel_zellige":      ("Pastel Zellige Grid",        "pink_concrete"),
    "sage_stack_bond":     ("Sage Subway Stack",          "lime_concrete"),
    "tech_cyan_glow":      ("Cyan Neon Tech Panels",      "cyan_concrete"),
    "plank_white_black":   ("Monochrome Wave Planks",     "gray_concrete"),
    "plank_white":         ("Arctic White Wave Planks",   "light_gray_concrete"),
    "crystalline_glaze":   ("Frost Crystal Glaze",        "blue_concrete"),
    "glow_voronoi_plasma": ("Plasma Voronoi Panel",       "magenta_concrete"),
    "saltillo_terracotta": ("Saltillo Terracotta Floor",  "orange_concrete"),
    "ash_glaze_stoneware": ("Anagama Ash-Glaze Stoneware", "brown_concrete"),
    "fluted_white_relief": ("Fluted White Relief",        "white_terracotta"),
    "matte_black_hex":     ("Matte Black Hex",            "black_terracotta"),
}


def build():
    tex = HERE / "textures"
    dist = HERE / "dist"
    root = dist / "Ceramics"
    shutil.rmtree(root, ignore_errors=True)
    blocks = root / "assets/minecraft/textures/block"
    blocks.mkdir(parents=True)

    for name, (_, block) in PACK.items():
        shutil.copy(tex / f"{name}.png", blocks / f"{block}.png")

    (root / "pack.mcmeta").write_text(json.dumps({"pack": {
        "pack_format": PACK_FORMAT,
        "supported_formats": [34, 48],
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
        f"{block:22s} <- {label}" for _, (label, block) in PACK.items()) + "\n")

    zpath = dist / "Ceramics.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(root.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(root))
    print(f"ok {len(PACK)} textures -> {zpath} ({zpath.stat().st_size / 1e6:.1f} MB)")


def contact_sheet(tex: Path, cell=256, cols=5) -> Image.Image:
    rows = -(-len(PACK) // cols)
    pad = 28
    sheet = Image.new("RGB", (cols * cell, rows * (cell + pad)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    for i, (name, (label, _)) in enumerate(PACK.items()):
        x, y = (i % cols) * cell, (i // cols) * (cell + pad)
        sheet.paste(Image.open(tex / f"{name}.png").convert("RGB").resize((cell, cell), Image.LANCZOS), (x, y))
        draw.text((x + 8, y + cell + 5), label, fill=(235, 235, 235), font=font)
    return sheet


if __name__ == "__main__":
    build()

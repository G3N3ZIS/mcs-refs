# Ceramics Texture Pack (1K, seamless)

12 hyperrealistic ceramic textures at 1024×1024, made with Nano Banana 2 (OpenArt) and then made tileable by `make_seamless.py`.

| Texture | Style | Replaces (vanilla) |
|---|---|---|
| `delft_tile` | Dutch Delft blue hand-painted tiles, 3×3 | blue_glazed_terracotta |
| `azulejo_tile` | Portuguese azulejo, blue/white/mustard quatrefoil | light_blue_glazed_terracotta |
| `zellige_mosaic` | Moroccan zellige, emerald/cobalt star mosaic | cyan_glazed_terracotta |
| `encaustic_tile` | Victorian encaustic floor, red/black/ochre | red_glazed_terracotta |
| `kintsugi_raku` | Black raku glaze, gold kintsugi seams | black_glazed_terracotta |
| `kintsugi_clay` | Broken unglazed clay, gold kintsugi | brown_glazed_terracotta |
| `kintsugi_celadon` | Celadon crackle glaze with gold repairs | green_glazed_terracotta |
| `white_porcelain` | Clean white porcelain glaze | white_glazed_terracotta |
| `porcelain_hex_tiles` | White porcelain hexagon tiles | light_gray_glazed_terracotta |
| `terracotta_meander` | Greek terracotta, black Greek-key bands | orange_glazed_terracotta |
| `terracotta_scales` | Terracotta fish-scale roof tiles | terracotta |
| `tenmoku_hares_fur` | Tenmoku hare's-fur iron glaze | gray_glazed_terracotta |

## Build

```bash
pip install pillow numpy
./fetch.sh                                  # raw renders -> raw/
python3 make_seamless.py raw textures       # seamless 1K -> textures/ (previews/ = 2×2 tiling check)
```

`seamless.json` sets the method per texture. The default, `quilt`, half-shifts the image and patches the seams back along minimum-difference cuts, so cracks join up with no ghosting. `blend` (an offset cross-fade) is kept as a fallback. For grid textures (Delft, azulejo, encaustic, hex), add `"crop": [l, t, r, b]` set to a whole number of tile repeats so the grout falls exactly on the edges.

The prompts are kept in the OpenArt history. They all share the same suffix: *flat orthographic top-down scan, even diffuse lighting, no shadows/vignette/perspective, fills frame edge to edge, PBR albedo, hyperrealistic, ultra-detailed.*

## White porcelain (PBR set)

`porcelain.py` builds `white_porcelain` as a full PBR set: albedo, `_normal` (OpenGL, Y+), `_roughness` and `_height`. It flattens the baked-in lighting from the AI render. The micro surface (orange-peel ripple, fine grain and pinholes) is built from periodic noise, so every map tiles exactly.

Material settings: dielectric with **IOR 1.5** (porcelain glaze is 1.50–1.55, so F0 ≈ 0.04), roughness ≈ 0.07 and an albedo of about 0.84 linear. It reads as glossy without looking like glass because the white body is opaque, with no transmission. In engines with a clearcoat, an alternative is base roughness 0.3 plus clearcoat 1.0 at clearcoat roughness 0.05. A little subsurface scattering in a warm white softens the edges.

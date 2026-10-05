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
python3 make_seamless.py raw textures       # seamless 1K -> textures/
```

`seamless.json` sets the method per texture. The default is an offset cross-fade, which suits organic surfaces such as glazes, cracks and clay. For grid textures (Delft, azulejo, encaustic, hex), add `"crop": [l, t, r, b]` set to a whole number of tile repeats so the grout falls exactly on the edges.

The prompts are kept in the OpenArt history. They all share the same suffix: *flat orthographic top-down scan, even diffuse lighting, no shadows/vignette/perspective, fills frame edge to edge, PBR albedo, hyperrealistic, ultra-detailed.*

# Ceramics Texture Pack: Handoff

**Repo / branch:** `G3N3ZIS/mcs-refs` @ `claude/ceramics-texture-pack-2h8hmq` (all pushed)
**Folder:** `packs/ceramics/`
**Goal:** 1K (1024²), seamless, hyperrealistic ceramic textures, generated with OpenArt Nano Banana 2 and made tileable locally.

## Finished: 11 textures (+ PBR/emissive maps)

| # | File | Descriptive name |
|---|------|------------------|
| 1 | `kintsugi_raku.png` | Black Raku Kintsugi: charcoal glaze shards with gold seams |
| 2 | `white_porcelain.png` (+`_normal`, `_roughness`, `_height`) | Pure White Porcelain Glaze: flat, glossy, IOR 1.5 PBR set |
| 3 | `flambe_oxblood.png` | Oxblood Flambé Glaze: sang-de-boeuf red with plum and turquoise runs |
| 4 | `voronoi_glaze_gold.png` | Jade Voronoi Mosaic with Gold Joints: celadon, teal, cream, oxblood |
| 5 | `pastel_zellige.png` | Pastel Zellige Grid: blush, mint, sky, butter and lilac handmade squares |
| 6 | `sage_stack_bond.png` | Sage Gloss Subway Stack: 2×8 slim stacked planks |
| 7 | `tech_cyan_glow.png` | Cyan Neon Tech Panels: graphite plates with glowing channels |
| 8 | `plank_white_black.png` | Monochrome Wave Planks: white/black/white long gloss tiles |
| 9 | `plank_white.png` | Arctic White Wave Planks: three long rippled gloss tiles |

Each one has a 2×2 tiling check in `previews/`.

## Picked but file never received (re-send each as a normal message): 15

Clay kintsugi · Flat celadon kintsugi (approved remake) · Delft blue tiles · Victorian encaustic · Crystalline glaze (wants matte blue + metallic crystals + saturation up) · Iznik tulips · White/black-carbon Voronoi (fewer cells) · Hex-in-oak panel (user chose: TRIM frame to half width) · Scandi pastel arches · Pastel fish-scale · Calacatta marble 2×2 · Pastel terrazzo · Greige concrete (needs grout painted on edges) · Sage 1×3 planks · Beige 1×3 planks · Rustic 1×3 planks (that's 16 counting all three plank colours)

## Rendered in OpenArt, not yet reviewed: ~14

Hybrid hex→Voronoi · Walnut-lattice Voronoi · Plasma Voronoi panel · Pearl hex + ice-blue glow · Acid-green armour kintsugi · Pastel hex & tech · Hex-oak ×2 · Thicker cyan ×2 (1 used) · Marble/sage/greige/blush herringbone bathroom set · Sage 1×3 ×2 · B/W, beige, rustic planks

**Credits:** ≈960 of 13,300 OpenArt credits used.

## Tools (in `packs/ceramics/`)

- `make_seamless.py` + `seamless.json`, with a method per texture:
  - `quilt`: for organic textures (glazes, cracks). Half-shifts the image, cuts fine detail along low-difference paths and feathers broad colour 40 px.
  - `none`: for grid/panel renders whose grout already sits on the edges. Check with a grout-run scan.
  - `conduit`: `conduit.py` hides a top/bottom seam with a full-width glowing channel.
- `porcelain.py`: flattens baked lighting and builds normal/roughness/height maps from periodic noise.

## Key decisions / gotchas

- The container can't reach `cdn.openart.ai` (network policy), so the user uploads images. **Images sent mid-reply never reach disk**; only normal messages do.
- **Never quilt cell mosaics**: the cuts slice cells. Ask for "a panel whose four edges run along joints" in the prompt instead.
- Grid textures: measure the grout pitch, and make sure the wrap grout matches the inner grout width (crop a few px if needed).

## Next step

The user sends the backlog images in batches in normal messages. Process each one, add an entry to `seamless.json` and a 2×2 preview, then commit and push.

### Added after the first handoff
| 10 | `crystalline_glaze.png` (+`_metallic`, `_roughness`, `_normal`) | Frost Crystal Glaze: teal-cobalt matte with metallic gold/silver crystals |
| 11 | `glow_voronoi_plasma.png` (+`_emissive`) | Plasma Voronoi Panel: obsidian cells, magenta-to-coral glowing crevices |

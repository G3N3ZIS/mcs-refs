# Ceramics pack: finish locally (Claude Code on PC)

Repo `G3N3ZIS/mcs-refs`, branch `claude/ceramics-texture-pack-2h8hmq`, folder `packs/ceramics/`.
Source images: `C:\Users\Petur Reynisson\Downloads\ceramics` (1024px PNG/WebP from OpenArt).

## State
- 16 textures done in `textures/`. Delft has a raw file and a config entry, but the pack hasn't been rebuilt with it yet.
- `build_pack.py` → `dist/Ceramics.zip` (Java 1.21.x, pack_format 34). Each texture replaces a non-rotating concrete/terracotta block, set in the `PACK` table.
- Every tool reads per-texture settings from `seamless.json` (`method`: quilt | none | conduit | glow | manual).
- Read `README.md` and `HANDOFF.md` first. They cover the tools and the gotchas.

## Already done (skip these source images)
kintsugi_raku, white_porcelain, flambe_oxblood, voronoi_glaze_gold, pastel_zellige, sage_stack_bond (2×8),
tech_cyan_glow, plank_white_black, plank_white, crystalline_glaze, glow_voronoi_plasma, saltillo_terracotta,
ash_glaze_stoneware, fluted_white_relief, matte_black_hex, delft_tile

## To do: identify each image in the folder by looking at it, copy it to raw/<name>.png, then process
| name | how |
|---|---|
| kintsugi_clay (terracotta shards, gold seams) | quilt |
| kintsugi_celadon (green crackle, gold) | quilt |
| zellige_star (blue/green/white star mosaic) | mosaic: never quilt. Find the period with autocorrelation (as for matte_black_hex) and crop whole periods |
| encaustic_tile (red/black/ochre 4×4) | grid: check the wrap join; crop to whole tiles if the edge grout differs |
| iznik_tulip (2×2) | grid: same check |
| voronoi_carbon_white (white cells, black carbon) | check the wrap; if cells jam, skip it or regenerate as a panel |
| hex_oak (hex tiles in oak frame) | **trim the oak frame to half width** so copies share one strip |
| greige_concrete (2×2) | no grout on the edges: copy the centre grout line onto the wrap edges (see fluted_white_relief) |
| terrazzo_pastel (2×2) | check the wrap |
| scandi_arches (4×4) | check the wrap |
| marble_calacatta (2×2) | check; paint grout on the edges if missing |
| fishscale_pastel | find the period with autocorrelation and crop whole periods |
| plank_rustic / plank_sage / plank_beige (1×3) | like plank_white_black: trim L/R so the edge grout width matches the row joints |
| artdeco_emerald (4×4) | grid check |
| armour_kintsugi_green (glowing cracks) | quilt + emissive mask (adapt `glow.py`, keeping the original hue) |
| pearl_hex_glow (panel) | `glow.py`-style: check edges, add emissive |

For each one: make a 2×2 preview in `previews/`, look at it, then add a row to `PACK` in `build_pack.py`. Free slots: yellow_concrete, purple_concrete, and every terracotta colour except white/black. Finish with `python build_pack.py`, check `previews/contact_sheet.jpg`, then commit and push.

## Gotchas
- `white_porcelain` must stay `manual`. Quilting its raw image brings the bulge back.
- Never quilt cell or tile mosaics: the cuts slice through cells.
- Look at the actual 2×2 join (crop around 1024,1024) before calling a texture done.

## Done 2026-10-05 (PC session): 32 textures in dist/Ceramics.zip
- 16 backlog renders processed by `finish.py` (seamless.json holds the per-texture method/crop), and every 2×2 join checked at full resolution.
- Mosaics (zellige_star, fishscale_pastel): crop to whole autocorrelation periods, then `period_quilt` swaps in a copy rolled by whole periods around the wrap. The two copies only agree on grout, so the min-cut follows joints and fixes the hand-glaze colour flips without slicing cells.
- Free slots left: purple_concrete only.
- **Not done:** `voronoi_carbon_white` (random Voronoi with no period; the cells jam at the wrap; raw kept, regenerate as a panel). `armour_kintsugi_green` and `pearl_hex_glow` were not in the Downloads folder. Two extra renders were not processed: a jade Voronoi with brown grout and a dark multi-glow Voronoi.
- 2026-10-05 later: lime_concrete = 1x3 sage planks (2x8 stack dropped); yellow_concrete = alias of the same (`ALIAS`); porcelain near-mirror (smooth 0.94-0.99) with nrm_strength 0.5; **black_porcelain** on purple_concrete = OpenArt GPT Image 2.5 Flare i2i, 1K, 32 credits, historyId fD3lrcj5Af4UJsZQUEGt, refs = 256px purple_concrete + flattened white_porcelain 512. No free slots left. Test world: `make_world.py` -> Everything Voxy "Ceramic pack" (re-run after PACK changes; it rewrites the load function).
- 2026-10-06: porcelain slabs + stairs via ALIAS: polished_diorite family = white porcelain, polished_andesite family = black porcelain (each family reads one texture; Genesis leaves both alone). Test world has a 'shapes' row for them.

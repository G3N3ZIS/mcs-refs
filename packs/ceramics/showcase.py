"""Ceramics showcase stage for the Hub's AutoShoot: every PACK block as a 2x2x2
cube, 8 per row, plus two overviews and one camera per block - Petur's framing
(2026-10-05): 1.5 blocks out, just above the top, slightly off-axis, aiming down.

Writes <out>/ceramics-showcase.schem + .shots.json (build-relative coords).
Usage: python showcase.py G:/MCS/mcs-overlay/run/schematics [texture ...]
       (textures given -> a ceramics-test stage with just those, no overviews)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"G:\MCS\blockforge\ref-to-build\scripts")
from vox import Build, write_schem   # noqa: E402

from build_pack import PACK           # noqa: E402

COLS, DX, DZ = 8, 6, 10

out, only = Path(sys.argv[1]), sys.argv[2:]
items = [(n, v) for n, v in PACK.items() if not only or n in only]
b, shots = Build(), []
for i, (name, (label, block)) in enumerate(items):
    x, z = (i % COLS) * DX, (i // COLS) * DZ
    b.box(x, 0, z, x + 1, 1, z + 1, "minecraft:" + block)        # 2 x 2 x 2 cube, front faces +z
    # aim: middle of the top front edge, where the two top blocks meet (Petur's mark);
    # camera 1.2 out from the front face, 1.2 above the top, slightly off-axis.
    # Shot at FOV 30 (run/options.txt fov:-1.0, the game minimum) so the cube fills the frame.
    shots.append({"name": label, "eye": [x + 1.4, 3.2, z + 3.2], "look": [x + 1.0, 2.0, z + 2.0]})
w, d = COLS * DX, -(-len(items) // COLS) * DZ
stem = "ceramics-test" if only else "ceramics-showcase"
shots = shots if only else [{"name": "overview", "eye": [w / 2, 16, d + 14], "look": [w / 2, 1, d / 2]},
         {"name": "overview low", "eye": [-6, 4, d + 6], "look": [w / 2, 2, d / 2]}] + shots
write_schem(b, out / f"{stem}.schem")
(out / f"{stem}.shots.json").write_text(json.dumps({"time": 1500, "shots": shots}, indent=1))
print("ok", stem, len(items), "blocks,", len(shots), "shots")

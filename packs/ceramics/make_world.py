"""Build the "Ceramic pack" test world in Everything Voxy: every PACK block as a
2x2x2 cube, lined up 8 per row, each with a sign (name + vanilla block).

Reuses Genesis's make_showcase_world.py (level.dat from a world Minecraft wrote,
datapack on the load tag that places + self-heals the exhibits) - only the
block list, the cube shape and the names are swapped in.

Usage: <Python312>/python.exe make_world.py
"""
import os
import sys

import nbtlib

sys.path.insert(0, r"G:\PROJECTS\G3N3ZIS\pack\_tools")
import make_showcase_world as S          # noqa: E402

from build_pack import PACK              # noqa: E402

NAME = "Ceramic pack"
S.WORLD = os.path.join(S.PROFILE, "saves", NAME)
S.PITCH = 5                              # 2-block cube + 3 empty
S.COLS = 8
S.GROUPS = [("ceramics", [(label, "minecraft:" + block, S.SOLID) for label, block in PACK.values()])]
def place_cube(label, block, rule, group, cx, cz):
    y = S.Y0
    out = [f"fill {cx} {y} {cz} {cx + 1} {y + 1} {cz + 1} {block} replace"]
    msgs = ",".join(f'"{t}"' for t in (label, block.split(":")[1].split("[")[0], "", ""))
    out.append(f"setblock {cx} {y} {cz - 1} minecraft:oak_sign[rotation=8]"
               f"{{front_text:{{messages:[{msgs}]}},is_waxed:1b}} replace")
    return out


S.place_column = place_cube
NL = chr(10)

def update_function():
    """World already exists: rewrite only the load function. It clears the whole
    gallery first, so a changed PACK never leaves a stale cube or sign behind."""
    lines, slots = S.commands()
    x1 = max(s[4] for s in slots) + 1
    z1 = max(s[5] for s in slots) + 1
    clear = f"fill -1 {S.Y0} -2 {x1 + 1} {S.Y0 + 2} {z1 + 1} minecraft:air replace"
    fn = os.path.join(S.WORLD, "datapacks", "g3n_showcase", "data", "g3n", "function", "place.mcfunction")
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines[:1] + [clear] + lines[1:]) + NL)
    print("updated", fn, len(slots), "cubes")


if __name__ == "__main__":
    if os.path.exists(S.WORLD):
        update_function()
        sys.exit(0)
    if not S.build_world():
        sys.exit(1)
    f = nbtlib.load(os.path.join(S.WORLD, "level.dat"))
    f["Data"]["LevelName"] = nbtlib.String(NAME)
    f.save()
    print("named:", NAME)

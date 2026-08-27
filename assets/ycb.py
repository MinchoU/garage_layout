"""Real YCB meshes, loaded from the Isaac Gym asset tree.

These are the only assets here that are not procedural. The source OBJs are in
centimetres (the URDFs apply scale="0.01"), authored Z-up, and centred on their
own centroid — so each one is scaled, then dropped so its base sits on z=0 and
its footprint is centred, matching every other asset's origin convention.

If the Isaac Gym tree is missing, `available()` returns nothing and the registry
simply has no ycb_* entries.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import trimesh

# Point ROOM_BUILDER_YCB_DIR at any directory of <id>_<name>/textured.obj folders;
# the default is where Isaac Gym keeps them.
YCB_DIR = Path(os.environ.get("ROOM_BUILDER_YCB_DIR",
                              Path.home() / "isaacgym/assets/urdf/ycb"))
OBJ_SCALE = 0.01                      # OBJ units are cm, as the URDFs declare
TEX_PX = 512                          # source PNGs are 1-2k; that is wasted on a tabletop

PARAMS = [("scale", 1.00, (0.20, 3.00, 0.05))]


def available() -> dict[str, str]:
    """{short name: source directory} for every YCB object we can actually load."""
    if not YCB_DIR.is_dir():
        return {}
    out = {}
    for d in sorted(YCB_DIR.iterdir()):
        if (d / "textured.obj").is_file():
            out[d.name.split("_", 1)[1]] = d.name      # 010_potted_meat_can -> potted_meat_can
    return out


@lru_cache(maxsize=32)
def _base_mesh(dirname: str) -> trimesh.Trimesh:
    """Load once, normalise to metres with its base on z=0, shrink the texture."""
    mesh = trimesh.load(YCB_DIR / dirname / "textured.obj", force="mesh", process=False)
    mesh.apply_scale(OBJ_SCALE)
    lo, hi = mesh.bounds
    mesh.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])

    mat = getattr(mesh.visual, "material", None)
    img = getattr(mat, "baseColorTexture", None) or getattr(mat, "image", None)
    if img is not None and max(img.size) > TEX_PX:
        img.thumbnail((TEX_PX, TEX_PX))
        if hasattr(mat, "baseColorTexture"):
            mat.baseColorTexture = img
        else:
            mat.image = img
    return mesh


def make_builder(dirname: str):
    def build(scale=1.00):
        mesh = _base_mesh(dirname).copy()
        if abs(scale - 1.0) > 1e-6:
            mesh.apply_scale(float(scale))
        scene = trimesh.Scene()
        scene.add_geometry(mesh, geom_name=dirname)
        return scene
    build.__name__ = f"build_{dirname}"
    build.__doc__ = f"YCB {dirname}, real mesh, true scale."
    return build

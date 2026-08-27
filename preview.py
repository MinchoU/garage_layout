"""Matplotlib rasteriser for asset sanity checks (no GL on this machine)."""
import sys
from pathlib import Path

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assets  # noqa: E402
from partlib import MATERIALS  # noqa: E402


def preview(name, out, views=((22, -60), (10, -90), (60, -45)), params=None):
    scene = assets.build(name, params)
    fig = plt.figure(figsize=(5 * len(views), 5))
    for k, (elev, azim) in enumerate(views):
        ax = fig.add_subplot(1, len(views), k + 1, projection="3d")
        for gname, g in scene.geometry.items():
            if gname in MATERIALS:
                rgb = np.array(MATERIALS[gname][0]) / 255.0
            else:  # textured part: fall back to its base color factor
                mat = getattr(g.visual, "material", None)
                rgb = np.array(getattr(mat, "baseColorFactor", [0.8, 0.7, 0.55, 1])[:3], float)
                if rgb.max() > 1.0:
                    rgb = rgb / 255.0
            tris = g.vertices[g.faces]
            n = g.face_normals
            shade = 0.45 + 0.55 * np.abs(n @ np.array([0.4, 0.5, 0.75]))
            cols = np.clip(rgb[None] * shade[:, None], 0, 1)
            ax.add_collection3d(Poly3DCollection(tris, facecolors=cols, edgecolors="none"))
        lo, hi = scene.bounds
        c, r = (lo + hi) / 2, (hi - lo).max() / 2
        ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev, azim); ax.set_axis_off()
    fig.tight_layout(); fig.savefig(out, dpi=90); print("wrote", out)


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "stairs_4step"
    out = sys.argv[2] if len(sys.argv) > 2 else f"{name}_preview.png"
    preview(name, out)

"""Wall panel with a hinged door that swings outward.

Same frame convention as the other walls: XZ plane, origin on the floor at the
center of the footprint, front face (room side) toward +Y. "Outward" therefore
means the leaf swings toward -Y, away from the room.

With `pegboard=1` the solid parts of the wall keep the pegboard skin, and the
hole grid is computed for the whole panel — so the pattern runs continuously
past the opening instead of restarting on each pier.
"""

from __future__ import annotations

import numpy as np
import trimesh

from partlib import PartSet, box, tube
from assets.pegboard import face_quads, hole_grid

PARAMS = [
    ("length", 4.00, (0.30, 12.0, 0.05)),
    ("height", 2.60, (0.30, 5.0, 0.05)),
    ("thickness", 0.100, (0.02, 0.5, 0.01)),
    ("door_w", 0.90, (0.50, 1.80, 0.01)),
    ("door_h", 2.05, (1.20, 3.00, 0.01)),
    ("door_x", 0.00, (-5.0, 5.0, 0.05)),
    ("open_deg", 35.0, (0.0, 120.0, 1.0)),
    ("hinge_right", 0, (0, 1, 1)),
    ("leaf_t", 0.040, (0.020, 0.080, 0.002)),
    ("pegboard", 1, (0, 1, 1)),
    ("pitch", 0.075, (0.020, 0.30, 0.005)),
    ("hole_d", 0.022, (0.004, 0.10, 0.002)),
]


def build(length=4.00, height=2.60, thickness=0.100, door_w=0.90, door_h=2.05,
          door_x=0.00, open_deg=35.0, hinge_right=0, leaf_t=0.040,
          pegboard=1, pitch=0.075, hole_d=0.022):
    ps = PartSet()
    hl = length / 2.0
    # keep the opening inside the panel
    door_w = min(door_w, length - 0.02)
    door_h = min(door_h, height - 0.02)
    x0 = float(np.clip(door_x - door_w / 2.0, -hl, hl - door_w))
    x1 = x0 + door_w

    # --- wall in three solid pieces around the opening ---------------------
    rects = [(-hl, x0, 0.0, height),            # pier on the -x side
             (x1, hl, 0.0, height),             # pier on the +x side
             (x0, x1, door_h, height)]          # header over the opening
    mat = "plywood" if pegboard else "wall"
    for rx0, rx1, rz0, rz1 in rects:
        if rx1 - rx0 > 1e-4 and rz1 - rz0 > 1e-4:
            ps.add(mat, box((rx1 - rx0, thickness, rz1 - rz0),
                            ((rx0 + rx1) / 2.0, 0.0, (rz0 + rz1) / 2.0)))
    if pegboard:
        xs, zs = hole_grid(length, height, pitch, 0.055)
        if len(xs) and len(zs):
            face_quads(ps, rects, xs, zs, pitch, hole_d, thickness / 2.0 + 0.0004)

    # --- jamb lining the reveal, plus architrave on the room face ----------
    jamb = 0.020
    for x in (x0, x1):
        ps.add("wall", box((jamb, thickness, door_h),
                           (x + (jamb / 2 if x == x0 else -jamb / 2), 0.0, door_h / 2.0)))
    ps.add("wall", box((door_w, thickness, jamb), ((x0 + x1) / 2.0, 0.0, door_h - jamb / 2)))
    casing, cz = 0.045, 0.012
    for x in (x0, x1):
        ps.add("wall", box((casing, cz, door_h + casing),
                           (x + (-casing / 2 if x == x0 else casing / 2),
                            thickness / 2 + cz / 2, (door_h + casing) / 2.0)))
    ps.add("wall", box((door_w + 2 * casing, cz, casing),
                       ((x0 + x1) / 2.0, thickness / 2 + cz / 2, door_h + casing / 2)))

    # --- the leaf, hinged on one jamb, swinging toward -y ------------------
    gap = 0.004
    lw, lh = door_w - 2 * gap, door_h - gap
    y_out = -thickness / 2.0                    # closed leaf hangs on the outer face
    sign = -1.0 if not hinge_right else 1.0     # +x-side leaf turns -z, -x-side turns +z
    x_h = x0 + gap if not hinge_right else x1 - gap

    leaf = PartSet()
    d0, d1 = (0.0, lw) if not hinge_right else (-lw, 0.0)
    leaf.add("plywood", box((lw, leaf_t, lh), ((d0 + d1) / 2.0, y_out - leaf_t / 2.0, lh / 2.0)))
    # recessed panel detail, so the leaf does not read as a bare slab
    for zc, zh in ((lh * 0.30, lh * 0.42), (lh * 0.75, lh * 0.30)):
        leaf.add("seam", box((lw - 0.16, 0.002, zh - 0.10),
                             ((d0 + d1) / 2.0, y_out - leaf_t - 0.0012, zc)))
    # hinges on the pivot edge, handle on the free edge
    for hz in (0.22 * lh, 0.55 * lh, 0.88 * lh):
        leaf.add("metal_black", tube((d0 if not hinge_right else d1, y_out, hz - 0.05),
                                     (d0 if not hinge_right else d1, y_out, hz + 0.05), 0.011))
    x_handle = (d1 - 0.07) if not hinge_right else (d0 + 0.07)
    for side, y_h in ((1, y_out + 0.004), (-1, y_out - leaf_t - 0.004)):
        leaf.add("metal_black", tube((x_handle, y_h, 1.05),
                                     (x_handle, y_h + side * 0.030, 1.05), 0.024))
        leaf.add("metal_black", box((0.115, 0.022, 0.022),
                                    (x_handle - side * 0.045, y_h + side * 0.030, 1.05)))

    # pivot in the plane of the leaf (not the wall centreline), on the hinge edge
    # the leaf was modelled around, then carry the hinge to its place on the jamb
    T = trimesh.transformations.rotation_matrix(np.radians(open_deg) * sign, [0, 0, 1],
                                                point=[0.0, y_out, 0.0])
    T = trimesh.transformations.translation_matrix([x_h, 0.0, 0.0]) @ T
    for name, meshes in leaf.parts.items():
        for m in meshes:
            ps.add(name, m.apply_transform(T))
    return ps.to_scene()

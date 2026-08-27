"""Pegboard panels — arbitrary size, hole pitch that never stretches.

`pegboard_wall` stands in the XZ plane: origin on the floor at the center of its
footprint, holes facing +Y. `pegboard_ceiling` is the same board laid flat with
its holes facing down (-Z); its origin sits on its underside, so you drop it in
at position.z = wall height.

Resizing rule: size params change the *number* of holes, never their spacing,
and the grid is re-centered so the border margins stay even. Do NOT resize these
with the editor's Scale slider (it stretches the grid) — the editor disables it.
"""

from __future__ import annotations

import numpy as np

from partlib import PartSet, box, hole_texture, quad_xy, quad_xz

# Above this many holes the drilled-geometry path gets slow (~0.3 s / 90k tris
# at 1300 holes), so `real_holes` silently falls back to the textured board.
MAX_DRILLED_HOLES = 2600

PARAMS = [
    ("length", 4.00, (0.20, 12.0, 0.05)),
    ("height", 2.60, (0.20, 5.0, 0.05)),
    ("thickness", 0.018, (0.006, 0.06, 0.002)),
    ("pitch", 0.075, (0.020, 0.30, 0.005)),
    ("hole_d", 0.022, (0.004, 0.10, 0.002)),
    ("margin", 0.055, (0.0, 0.5, 0.005)),
    ("panel_w", 1.00, (0.0, 4.0, 0.05)),
    ("panel_h", 1.20, (0.0, 4.0, 0.05)),
    ("real_holes", 0, (0, 1, 1)),
]

CEILING_PARAMS = [
    ("size_x", 4.00, (0.20, 12.0, 0.05)),
    ("size_y", 4.00, (0.20, 12.0, 0.05)),
    ("thickness", 0.060, (0.006, 0.30, 0.002)),
    ("pitch", 0.075, (0.020, 0.30, 0.005)),
    ("hole_d", 0.022, (0.004, 0.10, 0.002)),
    ("margin", 0.055, (0.0, 0.5, 0.005)),
    ("panel_w", 1.00, (0.0, 4.0, 0.05)),
    ("panel_h", 1.00, (0.0, 4.0, 0.05)),
]


# --------------------------------------------------------------------- grid
def grid_1d(span, pitch, margin):
    """Hole coordinates along one axis, fixed pitch, centered on 0."""
    usable = span - 2.0 * margin
    n = int(np.floor(usable / pitch)) + 1 if usable >= 0 else 0
    if n < 1:
        return np.zeros(0)
    return -(n - 1) * pitch / 2.0 + np.arange(n) * pitch


def hole_grid(length, height, pitch, margin):
    """Hole centers of an upright board: x centered on 0, z measured from the floor."""
    return grid_1d(length, pitch, margin), grid_1d(height, pitch, margin) + height / 2.0


def mapper(first, pitch, flip=False):
    """Coordinate -> texture uv, putting every hole center on a cell center."""
    if flip:
        return lambda t: (first - t) / pitch + 0.5
    return lambda t: (t - first) / pitch + 0.5


def texture_for(hole_d, pitch):
    return hole_texture(hole_frac=float(np.clip(hole_d / pitch, 0.04, 0.9)))


# ---------------------------------------------------------------- the boards
def build(length=4.00, height=2.60, thickness=0.018, pitch=0.075, hole_d=0.022,
          margin=0.055, panel_w=1.00, panel_h=1.20, real_holes=0):
    ps = PartSet()
    xs, zs = hole_grid(length, height, pitch, margin)
    y_front = thickness / 2.0

    if real_holes and len(xs) and len(zs) and len(xs) * len(zs) <= MAX_DRILLED_HOLES:
        _drilled_board(ps, length, height, thickness, hole_d, xs, zs)
    else:
        ps.add("plywood", box((length, thickness, height), (0.0, 0.0, height / 2.0)))
        if len(xs) and len(zs):
            face_quads(ps, [(-length / 2, length / 2, 0.0, height)],
                       xs, zs, pitch, hole_d, y_front + 0.0004)

    _wall_seams(ps, length, height, panel_w, panel_h, y_front + 0.0008)
    return ps.to_scene()


def build_ceiling(size_x=4.00, size_y=4.00, thickness=0.060, pitch=0.075,
                  hole_d=0.022, margin=0.055, panel_w=1.00, panel_h=1.00):
    """Pegboard laid flat overhead. Origin on the underside, holes facing down."""
    ps = PartSet()
    ps.add("plywood", box((size_x, size_y, thickness), (0.0, 0.0, thickness / 2.0)))
    xs = grid_1d(size_x, pitch, margin)
    ys = grid_1d(size_y, pitch, margin)
    if len(xs) and len(ys):
        ps.add_raw("pegboard_face", quad_xy(
            -size_x / 2, size_x / 2, -size_y / 2, size_y / 2, -0.0004,
            mapper(xs[0], pitch), mapper(ys[0], pitch), texture_for(hole_d, pitch)))

    groove = 0.004
    for x in _seam_positions(size_x, panel_w):
        ps.add("seam", box((groove, size_y, 0.001), (x - size_x / 2, 0.0, -0.0008)))
    for y in _seam_positions(size_y, panel_h):
        ps.add("seam", box((size_x, groove, 0.001), (0.0, y - size_y / 2, -0.0008)))
    return ps.to_scene()


# ------------------------------------------------------------------ helpers
def face_quads(ps, rects, xs, zs, pitch, hole_d, y):
    """Textured pegboard skin over `rects` = [(x0, x1, z0, z1), ...].

    All rects share one uv mapping keyed to the board's global hole grid, so the
    pattern stays continuous across a door opening instead of restarting on each
    piece.
    """
    img = texture_for(hole_d, pitch)
    u = mapper(xs[0], pitch)
    v = mapper(zs[0], pitch, flip=True)          # v grows downward
    for i, (x0, x1, z0, z1) in enumerate(rects):
        if x1 - x0 > 1e-4 and z1 - z0 > 1e-4:
            ps.add_raw(f"pegboard_face_{i}" if i else "pegboard_face",
                       quad_xz(x0, x1, z0, z1, y, u, v, img))


def _wall_seams(ps, length, height, panel_w, panel_h, y):
    groove = 0.004
    for x in _seam_positions(length, panel_w):
        ps.add("seam", box((groove, 0.001, height), (x - length / 2, y, height / 2.0)))
    for z in _seam_positions(height, panel_h):
        ps.add("seam", box((length, 0.001, groove), (0.0, y, z)))


def _seam_positions(span, panel):
    if panel <= 0.01 or panel >= span:
        return []
    n = int(round(span / panel))
    return [span * i / n for i in range(1, n)] if n > 1 else []


def _drilled_board(ps, length, height, thickness, hole_d, xs, zs):
    """Actually punch the holes: 2D board polygon minus one circle per hole."""
    import shapely.geometry as sg
    import trimesh

    r = max(hole_d / 2.0, 1e-4)
    board = sg.box(-length / 2.0, 0.0, length / 2.0, height)
    holes = sg.MultiPolygon([sg.Point(float(x), float(z)).buffer(r, quad_segs=3)
                             for x in xs for z in zs])
    plate = trimesh.creation.extrude_polygon(board.difference(holes), height=thickness)
    plate.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    plate.apply_translation([0.0, thickness / 2.0, 0.0])
    ps.add("plywood", plate)

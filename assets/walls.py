"""Plain wall and ceiling panels, sharing the pegboard's frame convention.

Wall panels stand in the XZ plane: origin on the floor at the center of the
footprint, front face toward +Y. So a pegboard and a plain wall placed at the
same pose line up exactly, and a wall run is just several panels side by side.

The ceiling panel is the one exception to "origin on the floor": its origin sits
on its *underside*, so you drop it in at position.z = wall height.
"""

from __future__ import annotations

from partlib import PartSet, box

WALL_PARAMS = [
    ("length", 4.00, (0.20, 20.0, 0.05)),
    ("height", 2.60, (0.20, 6.0, 0.05)),
    ("thickness", 0.10, (0.01, 0.5, 0.01)),
    ("baseboard_h", 0.09, (0.0, 0.4, 0.005)),
    ("baseboard_t", 0.012, (0.0, 0.05, 0.002)),
]


def build_wall(length=4.00, height=2.60, thickness=0.10, baseboard_h=0.09, baseboard_t=0.012):
    ps = PartSet()
    ps.add("wall", box((length, thickness, height), (0.0, 0.0, height / 2.0)))
    if baseboard_h > 0.001 and baseboard_t > 0.0005:
        ps.add("wall", box((length, baseboard_t, baseboard_h),
                           (0.0, thickness / 2.0 + baseboard_t / 2.0, baseboard_h / 2.0)))
    return ps.to_scene()


CEILING_PARAMS = [
    ("size_x", 5.00, (0.3, 20.0, 0.05)),
    ("size_y", 4.00, (0.3, 20.0, 0.05)),
    ("thickness", 0.12, (0.01, 0.6, 0.01)),
    ("cornice", 0.0, (0.0, 0.2, 0.005)),
]


def build_ceiling(size_x=5.00, size_y=4.00, thickness=0.12, cornice=0.0):
    """Slab hanging above its origin, so position.z = the wall height it sits on."""
    ps = PartSet()
    ps.add("ceiling", box((size_x, size_y, thickness), (0.0, 0.0, thickness / 2.0)))
    if cornice > 0.002:                      # thin trim dropping around the edge
        t = 0.02
        for sx in (-1, 1):
            ps.add("ceiling", box((t, size_y, cornice),
                                  (sx * (size_x / 2 - t / 2), 0.0, -cornice / 2.0)))
        for sy in (-1, 1):
            ps.add("ceiling", box((size_x, t, cornice),
                                  (0.0, sy * (size_y / 2 - t / 2), -cornice / 2.0)))
    return ps.to_scene()

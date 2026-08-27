"""Light bulb, and a two-socket plate that screws to the ceiling.

Both hang downward: their origin is the *mounting face* (the top of the bulb's
screw cap, the top of the plate), with the geometry below it in -Z. So you place
a ceiling fitting at position.z = ceiling height and it hangs into the room.
"""

from __future__ import annotations

import numpy as np
import trimesh

from partlib import PartSet, box, tube

BULB_PARAMS = [
    ("bulb_d", 0.060, (0.025, 0.16, 0.002)),
    ("cap_d", 0.027, (0.010, 0.06, 0.001)),
    ("lit", 1, (0, 1, 1)),
]

PLATE_PARAMS = [
    ("plate_w", 0.300, (0.10, 1.00, 0.01)),
    ("plate_d", 0.130, (0.06, 0.60, 0.01)),
    ("plate_t", 0.022, (0.008, 0.08, 0.002)),
    ("spacing", 0.150, (0.04, 0.80, 0.005)),
    ("socket_h", 0.055, (0.02, 0.20, 0.005)),
    ("bulb_d", 0.060, (0.025, 0.16, 0.002)),
    ("lit", 1, (0, 1, 1)),
]


def _bulb_parts(ps: PartSet, at, bulb_d=0.060, cap_d=0.027, lit=1):
    """Add one bulb hanging from `at` (the top face of its screw cap)."""
    x, y, z = at
    cap_h = cap_d * 0.95
    ps.add("brass", tube((x, y, z), (x, y, z - cap_h), cap_d / 2.0, sections=16))
    for i in range(3):                                   # thread ridges
        zr = z - cap_h * (0.25 + 0.22 * i)
        ps.add("brass", tube((x, y, zr), (x, y, zr - 0.002), cap_d / 2.0 * 1.08, sections=16))

    neck_h = bulb_d * 0.22
    ps.add("bulb_glass" if lit else "white_plastic",
           tube((x, y, z - cap_h), (x, y, z - cap_h - neck_h), bulb_d * 0.31, sections=16))

    r = bulb_d / 2.0
    glass = trimesh.creation.icosphere(subdivisions=2, radius=r)
    glass.apply_scale([1.0, 1.0, 1.12])                  # slightly egg shaped
    glass.apply_translation([x, y, z - cap_h - neck_h - r * 0.85])
    ps.add("bulb_glass" if lit else "white_plastic", glass)

    if lit:                                              # filament, just a suggestion of one
        zc = z - cap_h - neck_h - r * 0.85
        for dx in (-0.004, 0.004):
            ps.add("brass", tube((x + dx, y, zc + r * 0.45), (x + dx, y, zc - r * 0.1), 0.0012, sections=6))


def build_bulb(bulb_d=0.060, cap_d=0.027, lit=1):
    ps = PartSet()
    _bulb_parts(ps, (0.0, 0.0, 0.0), bulb_d, cap_d, lit)
    return ps.to_scene()


def build_ceiling_light(plate_w=0.300, plate_d=0.130, plate_t=0.022, spacing=0.150,
                        socket_h=0.055, bulb_d=0.060, lit=1):
    """Backplate + two sockets + two bulbs. Origin on the face that meets the ceiling."""
    ps = PartSet()
    spacing = min(spacing, plate_w - 0.06)
    ps.add("white_plastic", box((plate_w, plate_d, plate_t), (0.0, 0.0, -plate_t / 2.0)))
    ps.add("steel", box((plate_w * 0.92, plate_d * 0.86, 0.004), (0.0, 0.0, -plate_t - 0.002)))

    socket_r = max(bulb_d * 0.36, 0.018)
    for sx in (-spacing / 2.0, spacing / 2.0):
        z0 = -plate_t - 0.004
        ps.add("white_plastic", tube((sx, 0.0, z0), (sx, 0.0, z0 - socket_h), socket_r, sections=20))
        ps.add("brass", tube((sx, 0.0, z0 - socket_h), (sx, 0.0, z0 - socket_h - 0.006),
                             socket_r * 0.92, sections=20))
        _bulb_parts(ps, (sx, 0.0, z0 - socket_h - 0.006), bulb_d, min(0.027, socket_r * 1.4), lit)
    return ps.to_scene()

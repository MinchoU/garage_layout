"""Cordless drill sitting in a pegboard hook.

Wall-mounted, so it follows the wall convention: origin on the board face, the
tool growing toward +Y (out of the board). The two hook prongs run back through
the origin into the board, so placing it exactly on a pegboard's front face
looks right.
"""

from __future__ import annotations

import numpy as np
import trimesh

from partlib import PartSet, box, tube

PARAMS = [
    ("size", 1.00, (0.40, 2.00, 0.05)),
    ("bit_len", 0.090, (0.0, 0.30, 0.005)),
    ("prong_gap", 0.100, (0.02, 0.30, 0.005)),
    ("hook", 1, (0, 1, 1)),
]


def build(size=1.00, bit_len=0.090, prong_gap=0.100, hook=1):
    ps = PartSet()

    if hook:                                   # two prongs into the board, tips turned up
        for sx in (-1, 1):
            x = sx * prong_gap / 2.0
            ps.add("steel", tube((x, -0.014, 0.0), (x, 0.086, 0.0), 0.005, sections=10))
            ps.add("steel", tube((x, 0.086, 0.0), (x, 0.086, 0.024), 0.005, sections=10))
        ps.add("steel", tube((-prong_gap / 2, -0.010, 0.0), (prong_gap / 2, -0.010, 0.0),
                             0.004, sections=8))

    z_axis = 0.036                              # the drill rests on the prong tips
    ps.add("tool_yellow", tube((0.0, 0.020, z_axis), (0.0, 0.150, z_axis), 0.032, sections=20))
    ps.add("metal_black", tube((0.0, 0.012, z_axis), (0.0, 0.022, z_axis), 0.029, sections=20))
    ps.add("metal_black", tube((0.0, 0.140, z_axis), (0.0, 0.152, z_axis), 0.026, sections=20))
    ps.add("steel", tube((0.0, 0.152, z_axis), (0.0, 0.198, z_axis), 0.021, sections=16))
    if bit_len > 0.002:
        ps.add("steel", tube((0.0, 0.198, z_axis), (0.0, 0.198 + bit_len, z_axis),
                             0.0035, sections=8))

    ps.add("tool_yellow", box((0.042, 0.052, 0.112), (0.0, 0.058, -0.048)))
    ps.add("metal_black", box((0.020, 0.018, 0.032), (0.0, 0.090, -0.014)))   # trigger
    ps.add("metal_black", box((0.076, 0.066, 0.046), (0.0, 0.058, -0.126)))   # battery
    ps.add("tool_yellow", box((0.048, 0.058, 0.012), (0.0, 0.058, -0.100)))

    if abs(size - 1.0) > 1e-6:
        ps.apply(trimesh.transformations.scale_matrix(size))
    return ps.to_scene()

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


# ---------------------------------------------------------------- hand tools

def _hook(ps, gap, reach=0.055, rise=0.020):
    """The pegboard hook every hand tool hangs from.

    Same convention as the drill's: the prongs start behind the origin (y<0) so
    they bury themselves in the board when the tool is placed on its front face.
    """
    xs = (-gap / 2.0, gap / 2.0) if gap > 1e-6 else (0.0,)
    for x in xs:
        ps.add("steel", tube((x, -0.014, 0.0), (x, reach, 0.0), 0.004, sections=10))
        ps.add("steel", tube((x, reach, 0.0), (x, reach, rise), 0.004, sections=10))
    if len(xs) > 1:
        ps.add("steel", tube((xs[0], -0.010, 0.0), (xs[1], -0.010, 0.0), 0.0035, sections=8))


SCREWDRIVER_PARAMS = [
    ("size", 1.00, (0.40, 2.00, 0.05)),
    ("shaft_len", 0.100, (0.030, 0.300, 0.005)),
    ("phillips", 1, (0, 1, 1)),
    ("hook", 1, (0, 1, 1)),
]


def build_screwdriver(size=1.00, shaft_len=0.100, phillips=1, hook=1):
    """Screwdriver hanging shaft-down, its handle shoulder resting on the hook."""
    ps = PartSet()
    if hook:
        _hook(ps, 0.0, reach=0.040, rise=0.016)
    y = 0.026
    ps.add("plastic_red", tube((0, y, 0.006), (0, y, 0.098), 0.016, sections=18))
    for i in range(6):                       # grip flutes
        a = 2 * np.pi * i / 6
        ps.add("plastic_red", tube((0.014 * np.cos(a), y + 0.014 * np.sin(a), 0.010),
                                   (0.014 * np.cos(a), y + 0.014 * np.sin(a), 0.094),
                                   0.004, sections=8))
    ps.add("plastic_gray", tube((0, y, 0.098), (0, y, 0.104), 0.014, sections=16))
    ps.add("steel", tube((0, y, 0.006), (0, y, 0.006 - shaft_len), 0.0035, sections=12))
    tip_z = 0.006 - shaft_len
    if phillips:
        for a in (0.0, np.pi / 2):
            ps.add("steel", box((0.010, 0.0016, 0.012), (0, y, tip_z + 0.006)) if a == 0
                   else box((0.0016, 0.010, 0.012), (0, y, tip_z + 0.006)))
    else:
        ps.add("steel", box((0.010, 0.0016, 0.014), (0, y, tip_z + 0.007)))
    if abs(size - 1.0) > 1e-6:
        ps.apply(trimesh.transformations.scale_matrix(size))
    return ps.to_scene()


WRENCH_PARAMS = [
    ("size", 1.00, (0.40, 2.00, 0.05)),
    ("length", 0.150, (0.060, 0.400, 0.005)),
    ("hook", 1, (0, 1, 1)),
]


def build_wrench(size=1.00, length=0.150, hook=1):
    """Combination wrench hung by its ring end, open end pointing down."""
    ps = PartSet()
    if hook:
        _hook(ps, 0.0, reach=0.030, rise=0.014)
    y = 0.022
    ring = trimesh.creation.annulus(r_min=0.009, r_max=0.016, height=0.005, sections=24)
    ring.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    ps.add("steel", ring.apply_translation([0, y, -0.009]))
    ps.add("steel", box((0.014, 0.005, length - 0.040), (0, y, -0.025 - (length - 0.040) / 2)))
    z_open = -0.025 - (length - 0.040)
    ps.add("steel", box((0.026, 0.006, 0.020), (0, y, z_open - 0.010)))
    ps.add("metal_black", box((0.011, 0.008, 0.013), (0, y, z_open - 0.017)))   # jaw gap
    if abs(size - 1.0) > 1e-6:
        ps.apply(trimesh.transformations.scale_matrix(size))
    return ps.to_scene()

"""Containers for staged parts: a compartment tray and a stacking tote.

Both are open-topped and follow the floor convention, so `position.z` is
whatever surface they stand on and a part dropped into a compartment only needs
that compartment's centre.

A tray is not a box with dividers drawn on it -- `compartments()` hands back the
world-space centre and floor height of every cell, which is what makes it usable
as a reset pose table rather than scenery.
"""

from __future__ import annotations

import numpy as np

from partlib import PartSet, box

TRAY_PARAMS = [
    ("width", 0.320, (0.100, 0.800, 0.010)),
    ("depth", 0.220, (0.080, 0.600, 0.010)),
    ("height", 0.045, (0.015, 0.200, 0.005)),
    ("cols", 4, (1, 10, 1)),
    ("rows", 3, (1, 10, 1)),
    ("wall_t", 0.003, (0.001, 0.012, 0.001)),
]


def compartments(width=0.320, depth=0.220, height=0.045, cols=4, rows=3, wall_t=0.003):
    """Centres of every cell as (x, y, z_floor), row-major from -X -Y.

    z is the inside floor, so a part sits at `tray.position + this`.
    """
    cols, rows = int(round(cols)), int(round(rows))
    cw = (width - wall_t * (cols + 1)) / cols
    ch = (depth - wall_t * (rows + 1)) / rows
    out = []
    for j in range(rows):
        y = -depth / 2 + wall_t * (j + 1) + ch * (j + 0.5)
        for i in range(cols):
            x = -width / 2 + wall_t * (i + 1) + cw * (i + 0.5)
            out.append((x, y, wall_t))
    return out


def build_tray(width=0.320, depth=0.220, height=0.045, cols=4, rows=3, wall_t=0.003):
    """Small-parts organiser: cols x rows compartments in a shallow shell."""
    ps = PartSet()
    cols, rows = int(round(cols)), int(round(rows))
    ps.add("metal_black", box((width, depth, wall_t), (0, 0, wall_t / 2.0)))
    for sx in (-1, 1):
        ps.add("metal_black", box((wall_t, depth, height),
                                  (sx * (width - wall_t) / 2.0, 0, height / 2.0)))
        ps.add("metal_black", box((width, wall_t, height),
                                  (0, sx * (depth - wall_t) / 2.0, height / 2.0)))
    inner_h = height - 0.004                      # dividers stop below the rim
    cw = (width - wall_t * (cols + 1)) / cols
    ch = (depth - wall_t * (rows + 1)) / rows
    for i in range(1, cols):
        x = -width / 2 + wall_t * i + cw * i + wall_t / 2.0
        ps.add("plastic_gray", box((wall_t, depth - 2 * wall_t, inner_h), (x, 0, inner_h / 2.0)))
    for j in range(1, rows):
        y = -depth / 2 + wall_t * j + ch * j + wall_t / 2.0
        ps.add("plastic_gray", box((width - 2 * wall_t, wall_t, inner_h), (0, y, inner_h / 2.0)))
    return ps.to_scene()


TOTE_PARAMS = [
    ("width", 0.300, (0.100, 0.800, 0.010)),
    ("depth", 0.200, (0.080, 0.600, 0.010)),
    ("height", 0.150, (0.040, 0.500, 0.005)),
    ("taper", 0.030, (0.0, 0.120, 0.005)),
    ("wall_t", 0.004, (0.002, 0.015, 0.001)),
]


def build_tote(width=0.300, depth=0.200, height=0.150, taper=0.030, wall_t=0.004):
    """Open stacking bin. `taper` narrows the base so totes nest when empty."""
    ps = PartSet()
    ps.add("tote_gray", box((width - 2 * taper, depth - 2 * taper, wall_t), (0, 0, wall_t / 2.0)))
    n = 5                                        # the slope, as a short stack of rings
    for k in range(n):
        f0, f1 = k / n, (k + 1) / n
        z0, z1 = wall_t + (height - wall_t) * f0, wall_t + (height - wall_t) * f1
        w = width - 2 * taper * (1.0 - (f0 + f1) / 2.0)
        d = depth - 2 * taper * (1.0 - (f0 + f1) / 2.0)
        for sx in (-1, 1):
            ps.add("tote_gray", box((wall_t, d, z1 - z0),
                                    (sx * (w - wall_t) / 2.0, 0, (z0 + z1) / 2.0)))
            ps.add("tote_gray", box((w, wall_t, z1 - z0),
                                    (0, sx * (d - wall_t) / 2.0, (z0 + z1) / 2.0)))
    for sx in (-1, 1):                           # rim lip, doubles as the hand hold
        ps.add("tote_gray", box((width + 0.008, 0.010, 0.008),
                                (0, sx * depth / 2.0, height)))
        ps.add("tote_gray", box((0.010, depth + 0.008, 0.008),
                                (sx * width / 2.0, 0, height)))
    return ps.to_scene()

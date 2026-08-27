"""4-step slatted platform stair with tubular handrails (RV / pool step style).

Modelled from a product photo: black square-tube frame, one leg set per step,
gray composite slat treads, two round handrails on tall verticals.

Local frame: origin on the floor at the center of the footprint (the shared
convention), steps ascending toward +X. Internally the run is built from x=0 so
the step arithmetic stays readable, then shifted onto its center at the end.
"""

from __future__ import annotations

import numpy as np

from partlib import PartSet, box, box_between, polytube, slat_deck

# name, default, (min, max, step) -- drives the viser parameter GUI.
PARAMS = [
    ("n_steps", 4, (1, 8, 1)),
    ("width", 0.76, (0.30, 1.60, 0.01)),
    ("tread", 0.32, (0.15, 0.70, 0.01)),
    ("riser", 0.20, (0.08, 0.35, 0.005)),
    ("tube_t", 0.030, (0.015, 0.06, 0.002)),
    ("deck_th", 0.028, (0.010, 0.06, 0.002)),
    ("n_slats", 6, (2, 12, 1)),
    ("rail_h", 0.92, (0.50, 1.30, 0.01)),
    ("rail_r", 0.019, (0.008, 0.04, 0.001)),
    ("handrails", 1, (0, 1, 1)),
]


def build(n_steps=4, width=0.76, tread=0.32, riser=0.20, tube_t=0.030,
          deck_th=0.028, n_slats=6, rail_h=0.92, rail_r=0.019, handrails=1):
    n_steps = int(round(n_steps))
    n_slats = int(round(n_slats))
    ps = PartSet()

    hw = width / 2.0
    y_rail = hw - tube_t / 2.0          # centerline of the side frame tubes
    slat_gap = 0.008

    for i in range(n_steps):
        x0, x1 = i * tread, (i + 1) * tread
        z_top = (i + 1) * riser          # walking surface
        z_frame = z_top - deck_th        # top of the steel frame
        zc = z_frame - tube_t / 2.0      # centerline of the horizontal frame tubes

        # --- perimeter frame under the tread -------------------------------
        for y in (-y_rail, y_rail):
            ps.add("metal_black", box((x1 - x0, tube_t, tube_t), ((x0 + x1) / 2, y, zc)))
        for x in (x0 + tube_t / 2, x1 - tube_t / 2):
            ps.add("metal_black", box((tube_t, width - 2 * tube_t, tube_t), (x, 0.0, zc)))

        # --- legs, one set per step ----------------------------------------
        leg_h = z_frame - tube_t
        leg_x = (x0 + tube_t / 2, x1 - tube_t / 2)
        for x in leg_x:
            for y in (-y_rail, y_rail):
                ps.add("metal_black", box((tube_t, tube_t, leg_h), (x, y, leg_h / 2)))

        # --- side bracing: a low kick rail, plus a diagonal on tall steps ---
        if leg_h > 0.18:
            for y in (-y_rail, y_rail):
                ps.add("metal_black",
                       box((x1 - x0, tube_t, tube_t), ((x0 + x1) / 2, y, 0.055)))
        if leg_h > 0.30:
            for y in (-y_rail, y_rail):
                ps.add("metal_black",
                       polytube([(leg_x[0], y, 0.055), (leg_x[1], y, leg_h)],
                                tube_t * 0.42, sections=6))

        # --- slatted tread --------------------------------------------------
        ps.add("deck_gray",
               slat_deck(x0, x1, -hw, hw, z_top, deck_th, n_slats, slat_gap, along="y"))

    if not handrails:
        return _centered(ps, n_steps, tread)

    # ---- handrails: straight run parallel to the nose line, hooked at both ends
    slope = riser / tread
    rail_z = lambda x: slope * x + rail_h            # noqa: E731
    x_lo = 0.9 * tread
    x_hi = n_steps * tread - 0.02

    path_xz = [
        (x_lo - 0.13, rail_z(x_lo) - 0.16),          # front hook, curving down
        (x_lo, rail_z(x_lo)),
        (x_hi, rail_z(x_hi)),
        (x_hi + 0.16, rail_z(x_hi) + 0.05),          # shallow bend at the top
    ]
    post_x = [x_lo + 0.02, x_hi - 0.03]

    for y in (-y_rail, y_rail):
        ps.add("metal_black",
               polytube([(x, y, z) for x, z in path_xz], rail_r, sections=14))
        for px in post_x:
            step_i = min(int(px / tread), n_steps - 1)
            z_bot = (step_i + 1) * riser - deck_th - tube_t   # bolted to the frame side
            ps.add("metal_black",
                   polytube([(px, y, z_bot), (px, y, rail_z(px))], rail_r, sections=14))
            ps.add("metal_black",
                   box((0.055, tube_t * 1.6, 0.055), (px, y, z_bot + 0.02)))

    return _centered(ps, n_steps, tread)


def _centered(ps, n_steps, tread):
    """Move the run so its footprint straddles the origin, as every asset does."""
    return ps.translate([-n_steps * tread / 2.0, 0.0, 0.0]).to_scene()

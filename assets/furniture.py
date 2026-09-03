"""Chair, leaning ladder, and a wall-hung cabinet.

The chair and ladder are floor pieces: origin on the floor at the center of the
footprint. The chair faces +Y (backrest on the -Y side) and the ladder leans
toward -Y, so giving either the same yaw as a wall puts it against that wall.

The cabinet is wall-hung, so it follows the wall convention instead: origin on
the *wall face*, body growing toward +Y (out of the wall), z=0 at the underside.
Place it at (x along wall, wall face y, mounting height).
"""

from __future__ import annotations

import numpy as np
import trimesh

from partlib import PartSet, beam, box, tube

CHAIR_PARAMS = [
    ("seat_w", 0.420, (0.25, 0.80, 0.01)),
    ("seat_d", 0.420, (0.25, 0.80, 0.01)),
    ("seat_h", 0.450, (0.25, 0.80, 0.005)),
    ("back_h", 0.900, (0.45, 1.30, 0.01)),
    ("leg", 0.042, (0.02, 0.10, 0.002)),
    ("n_slats", 3, (0, 6, 1)),
]


def build_chair(seat_w=0.420, seat_d=0.420, seat_h=0.450, back_h=0.900,
                leg=0.042, n_slats=3):
    """Plain wooden chair, seat at `seat_h` -- solid enough to stand on."""
    ps = PartSet()
    n_slats = int(round(n_slats))
    back_h = max(back_h, seat_h + 0.08)
    seat_t = 0.035
    lx, ly = seat_w / 2 - leg / 2, seat_d / 2 - leg / 2

    for sx in (-1, 1):
        for sy in (-1, 1):
            h = back_h if sy < 0 else seat_h - seat_t   # back posts run up to the backrest
            ps.add("wood", box((leg, leg, h), (sx * lx, sy * ly, h / 2)))

    ps.add("wood", box((seat_w, seat_d, seat_t), (0.0, 0.0, seat_h - seat_t / 2)))

    rail, zr = 0.024, seat_h * 0.42                     # stretchers, the step-on bracing
    for sx in (-1, 1):
        ps.add("wood", box((rail, seat_d - 2 * leg, rail), (sx * lx, 0.0, zr)))
    for sy in (-1, 1):
        ps.add("wood", box((seat_w - 2 * leg, rail, rail), (0.0, sy * ly, zr)))

    if n_slats:                                          # backrest slats between the posts
        z0, z1 = seat_h + 0.16, back_h - 0.03
        sh = (z1 - z0) / (2 * n_slats - 1)
        for i in range(n_slats):
            zc = z0 + (2 * i) * sh + sh / 2
            ps.add("wood", box((seat_w - 2 * leg + 0.01, 0.018, sh), (0.0, -ly, zc)))
    return ps.to_scene()


LADDER_PARAMS = [
    ("length", 2.40, (0.8, 6.0, 0.05)),
    ("width", 0.420, (0.20, 0.90, 0.01)),
    ("rung_pitch", 0.280, (0.12, 0.50, 0.005)),
    ("lean_deg", 16.0, (0.0, 45.0, 0.5)),
    ("rail_w", 0.045, (0.02, 0.12, 0.002)),
    ("rail_t", 0.030, (0.015, 0.08, 0.002)),
]


def build_ladder(length=2.40, width=0.420, rung_pitch=0.280, lean_deg=16.0,
                 rail_w=0.045, rail_t=0.030):
    """Straight ladder, feet at the origin, leaning back toward -Y."""
    ps = PartSet()
    hx = width / 2 - rail_w / 2
    for sx in (-1, 1):
        ps.add("wood", box((rail_w, rail_t, length), (sx * hx, 0.0, length / 2)))
        ps.add("metal_black", box((rail_w * 1.15, rail_t * 1.6, 0.022), (sx * hx, 0.0, 0.011)))

    n = max(int((length - 0.30) / rung_pitch), 1)
    z0 = (length - (n - 1) * rung_pitch) / 2.0
    for i in range(n):
        z = z0 + i * rung_pitch
        ps.add("wood", tube((-hx, 0.0, z), (hx, 0.0, z), 0.016, sections=12))

    # tilt about X so the top falls toward -Y, then set the feet back down on z=0
    ps.apply(trimesh.transformations.rotation_matrix(np.radians(lean_deg), [1, 0, 0]))
    scene = ps.to_scene()
    drop = scene.bounds[0][2]
    return ps.translate([0.0, 0.0, -drop]).to_scene() if abs(drop) > 1e-6 else scene


CABINET_PARAMS = [
    ("width", 0.800, (0.20, 2.50, 0.01)),
    ("height", 0.600, (0.15, 2.00, 0.01)),
    ("depth", 0.320, (0.10, 0.80, 0.01)),
    ("n_doors", 2, (0, 2, 1)),
    ("open_deg", 0.0, (0.0, 120.0, 1.0)),
    ("shelves", 1, (0, 4, 1)),
    ("panel_t", 0.016, (0.008, 0.04, 0.002)),
]


def build_cabinet(width=0.800, height=0.600, depth=0.320, n_doors=2,
                  open_deg=0.0, shelves=1, panel_t=0.016):
    """Wall cabinet. Origin sits on the wall face; doors open into the room (+Y)."""
    ps = PartSet()
    t, hw = panel_t, width / 2
    n_doors, shelves = int(round(n_doors)), int(round(shelves))

    ps.add("plywood", box((width, t, height), (0.0, t / 2, height / 2)))          # back
    for sx in (-1, 1):                                                            # sides
        ps.add("plywood", box((t, depth, height), (sx * (hw - t / 2), depth / 2, height / 2)))
    for z in (t / 2, height - t / 2):                                             # top, bottom
        ps.add("plywood", box((width - 2 * t, depth, t), (0.0, depth / 2, z)))
    for i in range(shelves):
        z = height * (i + 1) / (shelves + 1)
        ps.add("plywood", box((width - 2 * t, depth - t, t), (0.0, (depth - t) / 2 + t, z)))

    if n_doors:
        leaf_t, gap = 0.018, 0.003
        y0 = depth
        lw = (width - (n_doors + 1) * gap) / n_doors
        for i in range(n_doors):
            # hinge on the outer edge of each leaf; +x-side leaf turns +z, -x-side turns -z
            left = (i == 0)
            x_h = -hw + gap if left else hw - gap
            d0, d1 = (0.0, lw) if left else (-lw, 0.0)
            leaf = PartSet()
            leaf.add("plywood", box((lw, leaf_t, height - 2 * gap),
                                    ((d0 + d1) / 2, y0 + leaf_t / 2, height / 2)))
            xg = (d1 - 0.045) if left else (d0 + 0.045)
            leaf.add("metal_black", box((0.016, 0.016, 0.11),
                                        (xg, y0 + leaf_t + 0.022, height * 0.5)))
            for dz in (-0.045, 0.045):
                leaf.add("metal_black", tube((xg, y0 + leaf_t, height * 0.5 + dz),
                                             (xg, y0 + leaf_t + 0.022, height * 0.5 + dz), 0.006))
            # pivot on the leaf's own front edge (local x=0), otherwise an opening
            # door swings away from the carcass instead of hinging on it
            ang = np.radians(open_deg) * (1.0 if left else -1.0)
            T = trimesh.transformations.rotation_matrix(ang, [0, 0, 1], point=[0.0, y0, 0.0])
            T = trimesh.transformations.translation_matrix([x_h, 0.0, 0.0]) @ T
            for name, meshes in leaf.parts.items():
                for m in meshes:
                    ps.add(name, m.apply_transform(T))
    return ps.to_scene()


STEP_LADDER_PARAMS = [
    ("n_steps", 3, (1, 8, 1)),
    ("rise", 0.260, (0.12, 0.40, 0.005)),
    ("width", 0.400, (0.20, 0.90, 0.01)),
    ("spread_deg", 14.0, (0.0, 30.0, 0.5)),
    ("tread_d", 0.115, (0.05, 0.30, 0.005)),
    ("rail_w", 0.050, (0.02, 0.12, 0.002)),
    ("rail_t", 0.028, (0.012, 0.08, 0.002)),
    ("top_tray", 1, (0, 1, 1)),
]


def build_step_ladder(n_steps=3, rise=0.260, width=0.400, spread_deg=14.0,
                      tread_d=0.115, rail_w=0.050, rail_t=0.028, top_tray=1):
    """A-frame step ladder. Treads on the +Y side; both leg pairs splay off the top."""
    ps = PartSet()
    n_steps = int(round(n_steps))
    H = (n_steps + 1) * rise                       # top cap one rise above the last tread
    a = H * np.tan(np.radians(spread_deg))         # how far each foot sits from the centre
    hw = width / 2 - rail_w / 2

    for sx in (-1, 1):
        x = sx * hw
        for sy in (1, -1):                         # +1 = step side, -1 = back legs
            ps.add("wood", beam((x, sy * a, 0.0), (x, 0.0, H), rail_w, rail_t))
            ps.add("metal_black", box((rail_w * 1.15, rail_t * 2.2, 0.020),
                                      (x, sy * (a - 0.005), 0.010)))

    for i in range(1, n_steps + 1):                # treads, on the front rail line
        z = i * rise
        y = a * (1.0 - z / H)
        ps.add("wood", box((width - 2 * rail_w + 0.004, tread_d, 0.022), (0.0, y, z - 0.011)))

    ps.add("wood", box((width - 2 * rail_w, 0.030, 0.030), (0.0, -a * 0.45, H * 0.55)))

    if top_tray:
        ps.add("wood", box((width, tread_d * 1.7, 0.024), (0.0, 0.0, H - 0.012)))
        ps.add("metal_black", box((width * 0.9, 0.012, 0.030), (0.0, tread_d * 0.85, H + 0.015)))

    for sx in (-1, 1):                             # spreader arms, what stops the A opening
        x = sx * (hw - rail_t * 0.6)
        zf = H * 0.42
        ps.add("steel", beam((x, a * (1 - zf / H), zf), (x, -a * (1 - zf / H), zf),
                             0.006, 0.022, u_axis=(1, 0, 0)))

    # the splayed rails are mitred by the beam ends, so drop the feet back onto z=0
    scene = ps.to_scene()
    drop = scene.bounds[0][2]
    return ps.translate([0.0, 0.0, -drop]).to_scene() if abs(drop) > 1e-6 else scene


RACK_PARAMS = [
    ("width", 1.000, (0.30, 3.00, 0.05)),
    ("depth", 0.450, (0.20, 1.20, 0.01)),
    ("height", 1.800, (0.40, 3.00, 0.05)),
    ("n_shelves", 4, (2, 8, 1)),
    ("post", 0.045, (0.02, 0.12, 0.005)),
    ("shelf_t", 0.022, (0.010, 0.06, 0.002)),
    ("braces", 1, (0, 1, 1)),
]


def shelf_heights(height=1.800, n_shelves=4, shelf_t=0.022, bottom=0.120):
    """Top surface of each shelf, bottom first -- so callers can sit a box on one."""
    n_shelves = int(round(n_shelves))
    if n_shelves < 2:
        return np.array([bottom])
    return np.linspace(bottom, height - shelf_t, n_shelves) + shelf_t / 2.0


def build_rack(width=1.000, depth=0.450, height=1.800, n_shelves=4, post=0.045,
               shelf_t=0.022, braces=1):
    """Open shelving rack. Origin on the floor, footprint centred, open side toward +Y."""
    ps = PartSet()
    hx, hy = width / 2 - post / 2, depth / 2 - post / 2
    for sx in (-1, 1):
        for sy in (-1, 1):
            ps.add("metal_black", box((post, post, height), (sx * hx, sy * hy, height / 2)))

    for z in shelf_heights(height, n_shelves, shelf_t):
        ps.add("plywood", box((width - 2 * post, depth - 2 * post, shelf_t),
                              (0.0, 0.0, z - shelf_t / 2)))
        for sy in (-1, 1):                          # shelf edge rails
            ps.add("metal_black", box((width - 2 * post, post * 0.55, post * 0.55),
                                      (0.0, sy * hy, z - shelf_t - post * 0.28)))

    if braces:                                      # diagonal on the closed side
        ps.add("metal_black", beam((-hx, -hy, 0.05), (hx, -hy, height - 0.05), 0.020, 0.010,
                                   u_axis=(0, 1, 0)))
    return ps.to_scene()


WORKBENCH_PARAMS = [
    ("width", 1.600, (0.60, 3.00, 0.05)),
    ("depth", 0.700, (0.35, 1.20, 0.05)),
    ("height", 0.900, (0.60, 1.20, 0.01)),
    ("top_t", 0.045, (0.018, 0.100, 0.001)),
    ("drawers", 3, (0, 6, 1)),
    ("lower_shelf", 1, (0, 1, 1)),
]


def build_workbench(width=1.600, depth=0.700, height=0.900, top_t=0.045,
                    drawers=3, lower_shelf=1):
    """Steel-framed bench with a thick top, a drawer bank, and a lower shelf.

    Floor piece facing +Y: the drawer bank sits on the -X end and the working
    edge is +Y, so giving it a wall's yaw backs it onto that wall.
    """
    ps = PartSet()
    z_top = height - top_t
    ps.add("wood", box((width, depth, top_t), (0, 0, z_top + top_t / 2.0)))
    ps.add("seam", box((width + 0.010, 0.008, top_t * 0.6),
                       (0, depth / 2.0, z_top + top_t / 2.0)))          # front edge band
    leg, inset = 0.045, 0.060
    xs = (-(width / 2 - inset), width / 2 - inset)
    ys = (-(depth / 2 - inset), depth / 2 - inset)
    for x in xs:
        for y in ys:
            ps.add("metal_black", box((leg, leg, z_top), (x, y, z_top / 2.0)))
    for y in ys:                                                        # long rails
        ps.add("metal_black", box((width - 2 * inset, 0.030, 0.040), (0, y, z_top - 0.070)))
    for x in xs:
        ps.add("metal_black", box((0.030, depth - 2 * inset, 0.040), (x, 0, z_top - 0.070)))
    if lower_shelf:
        ps.add("plywood", box((width - 2 * inset + leg, depth - 2 * inset + leg, 0.018),
                              (0, 0, 0.160)))
    drawers = int(round(drawers))
    if drawers:
        bank_w = min(0.420, width * 0.35)
        x0 = -width / 2 + inset - leg / 2
        cx = x0 + bank_w / 2.0
        top_of_bank = z_top - 0.010
        ps.add("plastic_gray", box((bank_w, depth - 2 * inset, top_of_bank - 0.220),
                                   (cx, 0, (top_of_bank + 0.220) / 2.0)))
        h = (top_of_bank - 0.230) / drawers
        for i in range(drawers):
            zc = 0.230 + h * (i + 0.5)
            ps.add("plastic_blue", box((bank_w - 0.008, 0.014, h - 0.006),
                                       (cx, (depth - 2 * inset) / 2.0, zc)))
            ps.add("steel", box((bank_w * 0.5, 0.020, 0.012),
                                (cx, (depth - 2 * inset) / 2.0 + 0.014, zc)))
    return ps.to_scene()

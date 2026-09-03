"""RoboTTT task parts: fasteners, drivetrain pieces, and snap-circuit modules.

The robot picks these up, so they follow the floor convention -- origin at the
base, centred on the footprint -- and a part dropped at `position.z = table_top`
sits on the table.

Nothing here is scanned; RoboTTT ships no assets. These are stand-ins sized
from the real hardware (an M4 screw really is 4 mm across), built so each part
type is instantly distinguishable, not so any one of them is accurate.
"""

from __future__ import annotations

import numpy as np
import trimesh

from partlib import PartSet, box, tube

# A snap-circuit grid unit. Modules span a whole number of these, which is what
# makes them snap onto the base board at all -- keep every module in multiples.
U = 0.0254
SNAP_R = 0.0055                       # radius of the press stud on each end
BASE_T = 0.007

SIZE = ("size", 1.00, (0.30, 3.00, 0.05))     # shared "make it big enough to see" knob


def _finish(ps, size=1.0):
    """Scale, then sit the part on z=0 centred on its footprint, as everything is.

    Worth doing here rather than by hand per builder: these are the assets most
    likely to be dropped onto a shelf or a tray, and "position.z = the surface"
    only works if the base really is at zero.
    """
    if abs(size - 1.0) > 1e-6:
        ps.apply(trimesh.transformations.scale_matrix(size))
    scene = ps.to_scene()
    lo, hi = scene.bounds
    ps.translate([-(lo[0] + hi[0]) / 2.0, -(lo[1] + hi[1]) / 2.0, -lo[2]])
    return ps.to_scene()


# --------------------------------------------------------------------- fasteners

SCREW_PARAMS = [SIZE, ("length", 0.020, (0.008, 0.060, 0.002)),
                ("shaft_d", 0.004, (0.002, 0.010, 0.0005))]


def build_screw(size=1.0, length=0.020, shaft_d=0.004):
    """Pan-head machine screw standing on its head, thread pointing up."""
    ps = PartSet()
    r = shaft_d / 2.0
    head_h, head_r = 0.0022, shaft_d * 0.85
    ps.add("steel", tube((0, 0, 0), (0, 0, head_h), head_r, sections=16))
    ps.add("metal_black", box((head_r * 1.7, 0.0009, 0.0008),
                              (0, 0, head_h - 0.0003)))          # the drive slot
    ps.add("steel", tube((0, 0, head_h), (0, 0, head_h + length - 0.003), r, sections=12))
    # a few thread ridges: enough to read as threaded at a glance, 3 rings not 30
    for i in range(4):
        z = head_h + 0.004 + i * (length - 0.010) / 3.0
        ps.add("steel", tube((0, 0, z), (0, 0, z + 0.0012), r * 1.28, sections=12))
    tip = trimesh.creation.cone(radius=r, height=0.003, sections=12)
    ps.add("steel", tip.apply_translation([0, 0, head_h + length - 0.003]))
    return _finish(ps, size)


GEAR_PARAMS = [SIZE, ("outer_d", 0.040, (0.015, 0.120, 0.002)),
               ("thickness", 0.008, (0.003, 0.030, 0.001)),
               ("teeth", 14, (6, 40, 1)), ("bore_d", 0.005, (0.002, 0.020, 0.001))]


def build_gear(size=1.0, outer_d=0.040, thickness=0.008, teeth=14, bore_d=0.005):
    """Spur gear lying flat. Teeth are boxes on the rim -- involute is overkill."""
    ps = PartSet()
    teeth = int(round(teeth))
    r_root = outer_d / 2.0 * 0.86
    body = trimesh.creation.annulus(r_min=bore_d / 2.0, r_max=r_root,
                                    height=thickness, sections=48)
    ps.add("plastic_gray", body.apply_translation([0, 0, thickness / 2.0]))
    tw = 2.0 * np.pi * r_root / teeth * 0.55
    for i in range(teeth):
        a = 2.0 * np.pi * i / teeth
        T = trimesh.transformations.rotation_matrix(a, [0, 0, 1])
        T[:3, 3] = [np.cos(a) * (r_root + outer_d / 2 * 0.07), 
                    np.sin(a) * (r_root + outer_d / 2 * 0.07), thickness / 2.0]
        ps.add("plastic_gray",
               trimesh.creation.box(extents=(outer_d / 2 * 0.16, tw, thickness), transform=T))
    ps.add("metal_black", trimesh.creation.annulus(
        r_min=bore_d / 2.0, r_max=bore_d, height=thickness * 1.05,
        sections=16).apply_translation([0, 0, thickness / 2.0]))
    return _finish(ps, size)


WHEEL_PARAMS = [SIZE, ("diameter", 0.060, (0.020, 0.200, 0.005)),
                ("width", 0.022, (0.006, 0.080, 0.002))]


def build_wheel(size=1.0, diameter=0.060, width=0.022):
    """Toy wheel standing upright on its tread, axle along Y."""
    ps = PartSet()
    r = diameter / 2.0
    y0, y1 = (0.0, -width / 2.0), (0.0, width / 2.0)
    p0, p1 = (0.0, -width / 2.0, r), (0.0, width / 2.0, r)
    tyre = trimesh.creation.annulus(r_min=r * 0.62, r_max=r, height=width, sections=32)
    tyre.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    ps.add("rubber", tyre.apply_translation([0, 0, r]))
    ps.add("tool_yellow", tube(p0, p1, r * 0.62, sections=28))
    for sy in (-1, 1):                      # hub cap so the axle face is not blank
        y = sy * (width / 2.0 + 0.001)
        ps.add("plastic_gray", tube((0, y, r), (0, y + sy * 0.002, r), r * 0.22, sections=14))
    return _finish(ps, size)


# ------------------------------------------------------------------ car / bot parts

ROOF_PARAMS = [SIZE, ("width", 0.120, (0.040, 0.400, 0.005)),
               ("depth", 0.080, (0.030, 0.300, 0.005))]


def build_roof(size=1.0, width=0.120, depth=0.080):
    """The yellow roof panel of the model car: a shallow gable with two tabs."""
    ps = PartSet()
    t, rise = 0.004, depth * 0.22
    for sy in (-1, 1):                      # two slopes meeting at the ridge
        p0 = (0.0, sy * depth / 2.0, 0.0)
        p1 = (0.0, 0.0, rise)
        ps.add("tool_yellow", _slab(p0, p1, width, t))
    ps.add("tool_yellow", box((width, 0.006, 0.006), (0, 0, rise)))      # ridge
    for sx in (-1, 1):                      # locating tabs that drop into the body
        ps.add("plastic_gray", box((0.008, 0.010, 0.010),
                                   (sx * (width / 2 - 0.012), 0, -0.005)))
    return _finish(ps, size)


def _slab(p0, p1, width, t):
    """Flat plate of `width` in X, spanning p0->p1 in the YZ plane."""
    from partlib import beam
    return beam(p0, p1, width, t, u_axis=(1.0, 0.0, 0.0))


CHASSIS_PARAMS = [SIZE, ("length", 0.160, (0.060, 0.500, 0.005)),
                  ("width", 0.090, (0.040, 0.300, 0.005)),
                  ("axles", 2, (1, 4, 1))]


def build_chassis(size=1.0, length=0.160, width=0.090, axles=2):
    """Flat bot chassis with axle stubs -- gears and wheels mount on the stubs."""
    ps = PartSet()
    t, z = 0.006, 0.018
    ps.add("plastic_gray", box((length, width, t), (0, 0, z)))
    for sx in (-1, 1):                                   # side rails
        ps.add("plastic_gray", box((length, 0.006, 0.016),
                                   (0, sx * (width / 2 - 0.003), z + 0.008)))
    axles = int(round(axles))
    xs = np.linspace(-length / 2 + 0.030, length / 2 - 0.030, max(axles, 1))
    for x in xs:
        for sy in (-1, 1):
            y = sy * width / 2.0
            ps.add("steel", tube((x, y, z), (x, y + sy * 0.012, z), 0.0035, sections=12))
        ps.add("plastic_gray", box((0.014, width * 0.5, 0.014), (x, 0, z - t)))   # bearing block
    for sx in (-1, 1):                                   # standoffs the head screws into
        ps.add("plastic_gray", box((0.012, 0.012, 0.018),
                                   (sx * (length / 2 - 0.022), 0, z + 0.012)))
    return _finish(ps, size)


HEAD_PARAMS = [SIZE, ("width", 0.070, (0.030, 0.250, 0.005)),
               ("height", 0.055, (0.020, 0.200, 0.005))]


def build_head(size=1.0, width=0.070, height=0.055):
    """The red robot head that plugs onto the chassis."""
    ps = PartSet()
    d = width * 0.82
    body = trimesh.creation.box(extents=(width, d, height))
    ps.add("plastic_red", body.apply_translation([0, 0, height / 2.0]))
    for sx in (-1, 1):                                   # eyes on the +Y face
        ps.add("white_plastic", tube((sx * width * 0.20, d / 2 - 0.001, height * 0.62),
                                     (sx * width * 0.20, d / 2 + 0.004, height * 0.62),
                                     width * 0.11, sections=16))
        ps.add("metal_black", tube((sx * width * 0.20, d / 2 + 0.003, height * 0.62),
                                   (sx * width * 0.20, d / 2 + 0.006, height * 0.62),
                                   width * 0.05, sections=12))
    ps.add("metal_black", box((width * 0.42, 0.004, 0.006), (0, d / 2, height * 0.28)))
    ps.add("steel", tube((0, 0, height), (0, 0, height + 0.020), 0.0018, sections=10))
    ps.add("plastic_red", trimesh.creation.icosphere(subdivisions=1, radius=0.005)
           .apply_translation([0, 0, height + 0.022]))
    ps.add("plastic_gray", box((0.012, 0.012, 0.010), (0, 0, -0.005)))   # socket spigot
    return _finish(ps, size)


REMOTE_PARAMS = [SIZE, ("length", 0.130, (0.050, 0.400, 0.005)),
                 ("buttons", 6, (0, 16, 1))]


def build_remote(size=1.0, length=0.130, buttons=6):
    """RC transmitter lying face up."""
    ps = PartSet()
    w, h = 0.055, 0.018
    ps.add("metal_black", box((length, w, h), (0, 0, h / 2.0)))
    ps.add("plastic_gray", box((length - 0.008, w - 0.008, 0.002), (0, 0, h)))
    buttons = int(round(buttons))
    if buttons:
        cols = int(np.ceil(buttons / 2.0))
        xs = np.linspace(-length / 2 + 0.018, length / 2 - 0.018, max(cols, 1))
        for i in range(buttons):
            x, sy = xs[i % cols], (-1) ** (i // cols)
            ps.add("plastic_red" if i % 2 == 0 else "plastic_green",
                   tube((x, sy * 0.012, h), (x, sy * 0.012, h + 0.004), 0.006, sections=14))
    ps.add("steel", tube((length / 2 - 0.004, 0, h), (length / 2 - 0.004, 0, h + 0.075),
                         0.0022, sections=10))
    return _finish(ps, size)


# ----------------------------------------------------------------- snap circuits

BOARD_PARAMS = [("cols", 10, (3, 20, 1)), ("rows", 7, (3, 20, 1)),
                ("thickness", 0.006, (0.003, 0.020, 0.001)), ("studs", 1, (0, 1, 1))]


def build_board(cols=10, rows=7, thickness=0.006, studs=1):
    """Snap-circuit base board: a stud grid on `U` pitch, origin at its centre.

    Grid pitch is U regardless of how many columns you ask for -- same rule as
    the pegboard. A module spanning n units always lands on n studs.
    """
    ps = PartSet()
    cols, rows = int(round(cols)), int(round(rows))
    sx, sy = cols * U, rows * U
    ps.add("plastic_gray", box((sx, sy, thickness), (0, 0, thickness / 2.0)))
    for s in (-1, 1):                                    # raised border
        ps.add("plastic_gray", box((sx, 0.004, thickness + 0.004), (0, s * (sy / 2 - 0.002), thickness)))
        ps.add("plastic_gray", box((0.004, sy, thickness + 0.004), (s * (sx / 2 - 0.002), 0, thickness)))
    if studs:
        xs = (np.arange(cols) - (cols - 1) / 2.0) * U
        ys = (np.arange(rows) - (rows - 1) / 2.0) * U
        for x in xs:
            for y in ys:
                ps.add("copper", tube((x, y, thickness), (x, y, thickness + 0.002),
                                      0.0022, sections=8))
    return _finish(ps)


_LED_MAT = {0: "led_red", 1: "led_green", 2: "led_rgb"}


def _snap_base(ps, units, mat="plastic_gray"):
    """Module body plus the two press studs that snap it onto the board."""
    span = units * U
    ps.add(mat, box((span - 0.003, U * 0.92, BASE_T), (0, 0, BASE_T / 2.0)))
    for sx in (-1, 1):
        x = sx * (span / 2.0 - U / 2.0)
        ps.add("copper", tube((x, 0, BASE_T), (x, 0, BASE_T + 0.004), SNAP_R, sections=14))
        ps.add("copper", tube((x, 0, -0.003), (x, 0, 0.0), SNAP_R * 0.6, sections=10))
    return span


SNAP_PARAMS = [SIZE, ("units", 2, (1, 6, 1))]
LED_PARAMS = SNAP_PARAMS + [("color", 0, (0, 2, 1)), ("lit", 1, (0, 1, 1))]


def build_snap_led(size=1.0, units=2, color=0, lit=1):
    ps = PartSet()
    _snap_base(ps, int(round(units)))
    mat = _LED_MAT.get(int(round(color)), "led_red") if lit else "plastic_gray"
    ps.add("white_plastic", tube((0, 0, BASE_T), (0, 0, BASE_T + 0.004), 0.006, sections=16))
    ps.add(mat, tube((0, 0, BASE_T + 0.004), (0, 0, BASE_T + 0.012), 0.005, sections=16))
    ps.add(mat, trimesh.creation.icosphere(subdivisions=1, radius=0.005)
           .apply_translation([0, 0, BASE_T + 0.012]))
    return _finish(ps, size)


def build_snap_lamp(size=1.0, units=2):
    ps = PartSet()
    _snap_base(ps, int(round(units)))
    ps.add("brass", tube((0, 0, BASE_T), (0, 0, BASE_T + 0.006), 0.005, sections=16))
    ps.add("bulb_glass", trimesh.creation.icosphere(subdivisions=2, radius=0.008)
           .apply_translation([0, 0, BASE_T + 0.014]))
    return _finish(ps, size)


MOTOR_PARAMS = [SIZE, ("units", 3, (1, 6, 1))]     # the can needs three units


def build_snap_motor(size=1.0, units=3):
    ps = PartSet()
    _snap_base(ps, int(round(units)))
    z = BASE_T + 0.011
    can = tube((-0.014, 0, z), (0.014, 0, z), 0.011, sections=20)
    ps.add("steel", can)
    ps.add("steel", tube((0.014, 0, z), (0.028, 0, z), 0.0018, sections=10))   # shaft
    ps.add("plastic_red", box((0.006, 0.020, 0.020), (-0.015, 0, z)))
    return _finish(ps, size)


def build_snap_button(size=1.0, units=2):
    ps = PartSet()
    _snap_base(ps, int(round(units)))
    ps.add("white_plastic", tube((0, 0, BASE_T), (0, 0, BASE_T + 0.004), 0.010, sections=18))
    ps.add("plastic_red", tube((0, 0, BASE_T + 0.004), (0, 0, BASE_T + 0.010), 0.008, sections=18))
    return _finish(ps, size)


SWITCH_PARAMS = SNAP_PARAMS + [("on", 1, (0, 1, 1))]


def build_snap_switch(size=1.0, units=2, on=1):
    ps = PartSet()
    _snap_base(ps, int(round(units)))
    ps.add("white_plastic", box((0.018, 0.016, 0.006), (0, 0, BASE_T + 0.003)))
    sx = 1.0 if on else -1.0
    ps.add("plastic_red", box((0.012, 0.008, 0.005),
                              (sx * 0.004, 0, BASE_T + 0.008)))
    return _finish(ps, size)


def build_snap_wire(size=1.0, units=3):
    """Jumper: the same base studs, joined by a wire arcing over the gap."""
    ps = PartSet()
    units = int(round(units))
    span = units * U
    x = span / 2.0 - U / 2.0
    for sx in (-1, 1):
        ps.add("plastic_gray", tube((sx * x, 0, 0.0), (sx * x, 0, BASE_T), 0.009, sections=16))
        ps.add("copper", tube((sx * x, 0, BASE_T), (sx * x, 0, BASE_T + 0.004),
                              SNAP_R, sections=14))
        ps.add("copper", tube((sx * x, 0, -0.003), (sx * x, 0, 0.0), SNAP_R * 0.6, sections=10))
    n, rise = 12, 0.012
    pts = [(-x + 2 * x * i / n, 0.0, BASE_T + 0.002 + rise * np.sin(np.pi * i / n))
           for i in range(n + 1)]
    from partlib import polytube
    ps.add("plastic_red", polytube(pts, 0.0018, sections=8))
    return _finish(ps, size)

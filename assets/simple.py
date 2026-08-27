"""A few filler assets so a room can actually be laid out around the stair."""

from __future__ import annotations

from partlib import PartSet, box, slat_deck

ROOM_PARAMS = [("size_x", 5.0, (1.0, 20.0, 0.1)),
               ("size_y", 4.0, (1.0, 20.0, 0.1)),
               ("height", 2.6, (1.0, 6.0, 0.05)),
               ("wall_t", 0.10, (0.02, 0.4, 0.01)),
               ("n_walls", 3, (0, 4, 1))]


def build_room(size_x=5.0, size_y=4.0, height=2.6, wall_t=0.10, n_walls=3):
    """Floor slab plus up to 4 walls. Origin at floor center."""
    ps = PartSet()
    ps.add("floor", box((size_x, size_y, wall_t), (0, 0, -wall_t / 2)))
    hx, hy, zc = size_x / 2, size_y / 2, height / 2
    walls = [((wall_t, size_y + 2 * wall_t, height), (-hx - wall_t / 2, 0, zc)),   # -X
             ((size_x + 2 * wall_t, wall_t, height), (0, hy + wall_t / 2, zc)),    # +Y
             ((size_x + 2 * wall_t, wall_t, height), (0, -hy - wall_t / 2, zc)),   # -Y
             ((wall_t, size_y + 2 * wall_t, height), (hx + wall_t / 2, 0, zc))]    # +X
    for size, center in walls[:int(round(n_walls))]:
        ps.add("wall", box(size, center))
    return ps.to_scene()


TABLE_PARAMS = [("length", 1.40, (0.4, 3.0, 0.05)),
                ("depth", 0.70, (0.3, 1.5, 0.05)),
                ("height", 0.75, (0.3, 1.2, 0.01)),
                ("leg", 0.06, (0.02, 0.15, 0.005))]


def build_table(length=1.40, depth=0.70, height=0.75, leg=0.06):
    ps = PartSet()
    top_t = 0.04
    ps.add("wood", box((length, depth, top_t), (0, 0, height - top_t / 2)))
    h = height - top_t
    for sx in (-1, 1):
        for sy in (-1, 1):
            ps.add("metal_black",
                   box((leg, leg, h),
                       (sx * (length / 2 - leg), sy * (depth / 2 - leg), h / 2)))
    return ps.to_scene()


CRATE_PARAMS = [("size_x", 0.60, (0.1, 2.0, 0.02)),
                ("size_y", 0.40, (0.1, 2.0, 0.02)),
                ("size_z", 0.35, (0.1, 2.0, 0.02)),
                ("slatted", 1, (0, 1, 1))]


def build_crate(size_x=0.60, size_y=0.40, size_z=0.35, slatted=1):
    ps = PartSet()
    if not slatted:
        ps.add("wood", box((size_x, size_y, size_z), (0, 0, size_z / 2)))
        return ps.to_scene()
    t, e = 0.02, 0.03
    ps.add("wood", box((size_x, size_y, t), (0, 0, t / 2)))
    for sx in (-1, 1):
        ps.add("wood", box((t, size_y, size_z), (sx * (size_x / 2 - t / 2), 0, size_z / 2)))
    for sy in (-1, 1):
        ps.add("wood", slat_deck(-size_x / 2 + e, size_x / 2 - e,
                                 sy * (size_y / 2 - t), sy * (size_y / 2),
                                 size_z, size_z, 4, 0.02, along="x"))
    return ps.to_scene()

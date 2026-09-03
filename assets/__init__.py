"""Registry of procedural assets. Each entry: builder fn + GUI parameter spec."""

from . import (bins, door, furniture, lighting, parts, pegboard, simple, stairs,
               tools, walls, ycb)

REGISTRY = {
    "stairs_4step": (stairs.build, stairs.PARAMS),
    "pegboard_wall": (pegboard.build, pegboard.PARAMS),
    "pegboard_ceiling": (pegboard.build_ceiling, pegboard.CEILING_PARAMS),
    "wall_with_door": (door.build, door.PARAMS),
    "wall_panel": (walls.build_wall, walls.WALL_PARAMS),
    "ceiling_panel": (walls.build_ceiling, walls.CEILING_PARAMS),
    "wall_cabinet": (furniture.build_cabinet, furniture.CABINET_PARAMS),
    "ceiling_light": (lighting.build_ceiling_light, lighting.PLATE_PARAMS),
    "lightbulb": (lighting.build_bulb, lighting.BULB_PARAMS),
    "chair": (furniture.build_chair, furniture.CHAIR_PARAMS),
    "step_ladder": (furniture.build_step_ladder, furniture.STEP_LADDER_PARAMS),
    "ladder": (furniture.build_ladder, furniture.LADDER_PARAMS),
    "rack": (furniture.build_rack, furniture.RACK_PARAMS),
    "drill": (tools.build, tools.PARAMS),
    "room_shell": (simple.build_room, simple.ROOM_PARAMS),
    "table": (simple.build_table, simple.TABLE_PARAMS),
    "crate": (simple.build_crate, simple.CRATE_PARAMS),
    "workbench": (furniture.build_workbench, furniture.WORKBENCH_PARAMS),
    "parts_tray": (bins.build_tray, bins.TRAY_PARAMS),
    "tote": (bins.build_tote, bins.TOTE_PARAMS),
    "screwdriver": (tools.build_screwdriver, tools.SCREWDRIVER_PARAMS),
    "wrench": (tools.build_wrench, tools.WRENCH_PARAMS),
    # RoboTTT task parts. The paper ships no assets, so these are stand-ins built
    # to the real hardware's dimensions -- see assets/parts.py.
    "screw": (parts.build_screw, parts.SCREW_PARAMS),
    "gear": (parts.build_gear, parts.GEAR_PARAMS),
    "wheel": (parts.build_wheel, parts.WHEEL_PARAMS),
    "roof_panel": (parts.build_roof, parts.ROOF_PARAMS),
    "chassis": (parts.build_chassis, parts.CHASSIS_PARAMS),
    "robot_head": (parts.build_head, parts.HEAD_PARAMS),
    "remote_control": (parts.build_remote, parts.REMOTE_PARAMS),
    "circuit_board": (parts.build_board, parts.BOARD_PARAMS),
    "pupgo_car": (parts.build_pupgo_car, parts.CAR_PARAMS),
    "snap_lamp": (parts.build_snap_lamp, parts.SNAP_PARAMS),
    "snap_motor": (parts.build_snap_motor, parts.MOTOR_PARAMS),
    "snap_button": (parts.build_snap_button, parts.SNAP_PARAMS),
    "snap_switch": (parts.build_snap_switch, parts.SWITCH_PARAMS),
    "snap_wire": (parts.build_snap_wire, parts.SNAP_PARAMS),
}

# The three LEDs differ only in the colour default, so they share one builder and
# get one registry entry each -- a dropdown of real names beats a colour slider.
for _i, _name in enumerate(("snap_led_red", "snap_led_green", "snap_led_rgb")):
    REGISTRY[_name] = (parts.build_snap_led,
                       [(k, _i if k == "color" else v, r)
                        for k, v, r in parts.LED_PARAMS])


# Real YCB meshes, registered only if the Isaac Gym asset tree is present.
for _short, _dir in ycb.available().items():
    REGISTRY[f"ycb_{_short}"] = (ycb.make_builder(_dir), ycb.PARAMS)

# Assets with a baked-in grid or trim that scaling would distort. Resize these
# with their own length/height sliders instead; the editor disables Scale for them.
RESIZE_BY_PARAMS = {"pegboard_wall", "pegboard_ceiling", "wall_with_door",
                    "wall_panel", "ceiling_panel", "circuit_board", "parts_tray"}


def defaults(name: str) -> dict:
    return {k: v for k, v, _ in REGISTRY[name][1]}


def build(name: str, params: dict | None = None):
    fn, spec = REGISTRY[name]
    kwargs = defaults(name)
    kwargs.update(params or {})
    return fn(**kwargs)

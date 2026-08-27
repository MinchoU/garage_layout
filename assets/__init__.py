"""Registry of procedural assets. Each entry: builder fn + GUI parameter spec."""

from . import door, furniture, lighting, pegboard, simple, stairs, tools, walls, ycb

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
}


# Real YCB meshes, registered only if the Isaac Gym asset tree is present.
for _short, _dir in ycb.available().items():
    REGISTRY[f"ycb_{_short}"] = (ycb.make_builder(_dir), ycb.PARAMS)

# Assets with a baked-in grid or trim that scaling would distort. Resize these
# with their own length/height sliders instead; the editor disables Scale for them.
RESIZE_BY_PARAMS = {"pegboard_wall", "pegboard_ceiling", "wall_with_door",
                    "wall_panel", "ceiling_panel"}


def defaults(name: str) -> dict:
    return {k: v for k, v, _ in REGISTRY[name][1]}


def build(name: str, params: dict | None = None):
    fn, spec = REGISTRY[name]
    kwargs = defaults(name)
    kwargs.update(params or {})
    return fn(**kwargs)

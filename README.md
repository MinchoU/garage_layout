# garage_layout

Product photo → parametric 3D asset → lay out a room in [viser](https://github.com/nerfstudio-project/viser).

![room](room_preview.png)
![assets](new_assets.png)

```
partlib.py          box / beam / tube / slat helpers, PBR material table, hole texture
assets/stairs.py    4-step slatted platform stair (modelled from a product photo)
assets/pegboard.py  pegboard wall + ceiling (fixed hole pitch at any size)
assets/door.py      wall_with_door — wall with an outward-swinging leaf
assets/walls.py     wall_panel / ceiling_panel (plain wall and ceiling)
assets/lighting.py  lightbulb / ceiling_light (two-socket backplate)
assets/furniture.py chair / step_ladder / ladder / rack / wall_cabinet
assets/tools.py     drill, hanging in a pegboard hook
assets/ycb.py       real YCB meshes — the only assets that are not procedural
assets/simple.py    room_shell / table / crate
assets/__init__.py  REGISTRY: name -> (builder, GUI parameter spec)
editor.py           viser layout editor (add / gizmo / scale / save / load / GLB export)
build_assets.py     bake every asset to assets_out/*.glb
preview.py          matplotlib rasteriser, for machines with no GL
```

Requires `viser`, `trimesh`, `numpy`, `shapely`, `pillow`, and `matplotlib` for previews.

## Running

```bash
python editor.py --port 8080              # opens scene_demo.json if it is present
python editor.py --scene my_room.json     # reload a saved layout
python build_assets.py                    # every asset -> assets_out/*.glb
```

## Adding an asset

1. Write `build(**params) -> trimesh.Scene` under `assets/` (origin on the floor,
   centred on the footprint).
2. Put `PARAMS = [(name, default, (min, max, step)), ...]` next to it — the editor
   builds a slider per entry and rebuilds the object live as you drag.
3. Register one line in `REGISTRY` in `assets/__init__.py`.

Third-party GLB/OBJ files go in `assets_out/`; hit "Refresh GLB list" in the editor
and they show up in the dropdown.

## Frame conventions

Z-up, metres. **Every asset's origin sits on the floor at the centre of its
footprint**, so `position.z = 0` means "standing on the ground". Three groups
deviate, each for a reason:

| Group | Origin | Why |
|---|---|---|
| `pegboard_wall`, `wall_panel`, `wall_with_door` | floor, footprint centre, **front face toward +Y** | two walls at the same pose line up exactly; a wall run is just panels side by side |
| `wall_cabinet`, `drill` | on the **wall face**, body growing toward +Y | give it the wall's yaw and the wall face's coordinate and it mounts flush |
| `ceiling_panel`, `pegboard_ceiling`, `lightbulb`, `ceiling_light` | on the **mounting face**, geometry hanging in -Z | `position.z = ceiling height` and it hangs into the room |

A room is a floor (`room_shell` with `n_walls=0`) + four wall panels + a ceiling.
`scene_demo.json` is the worked example: a 4 × 4 × 2.6 m square with pegboard on
all four walls and the ceiling, and a door in the +X wall. Walls are pushed out by
half their thickness so their **front faces** land exactly on the room boundary
(18 mm pegboard → ±0.009, 100 mm door wall → ±0.05).

Scene files store `(asset name + parameters + pose + scale)`, never geometry — so
fixing a builder silently upgrades every saved room.

## Pegboard sizing

Changing `length` / `height` changes the **hole count, never the pitch**: 5 m gives
66 holes, 9 m gives 119, both at 75 mm. The grid is re-centred on the new board, so
the border margins stay even.

Because of that the editor **disables the Scale slider** for walls and ceilings —
scaling stretches the hole grid. Resize them with their own sliders.

Two ways to draw the holes:

- `real_holes=0` (default) — a one-cell tile texture, repeated. UVs are keyed to the
  hole grid (`(x - first_hole) / pitch + 0.5`), so every hole lands on a cell centre
  at any size. **50 triangles / 4 KB regardless of how big the wall is.**
- `real_holes=1` — actually punched with shapely. ~0.27 s and 87k triangles at 1300
  holes; past 2600 holes it falls back to the texture. Use it when you need the holes
  in collision geometry.

`wall_with_door` computes its hole grid **once for the whole panel** and shares the
UV mapping across the piers and the header, so the pattern runs continuously past the
opening instead of restarting on each piece.

## Doors

The wall's front face is +Y (the room side), so **the leaf swings toward -Y, outward**.
`open_deg` runs 0–120 and `hinge_right` flips the hinge.

Both the wall door and the cabinet doors pivot on **the hinge edge in the leaf's own
plane**. Pivoting on the wall centreline or the cabinet back panel makes an opening
door drift away from the body instead of hinging on it.

Once a room is closed you cannot see in, so the editor has a **Visible checkbox** —
switch the ceiling or the near wall off while you work inside.

## Racks

`furniture.shelf_heights(height, n_shelves, shelf_t)` returns the top surface of each
shelf, bottom first. Feed one straight into `position.z` and a box lands on that shelf.

## YCB objects

`assets/ycb.py` reads the original OBJs from `~/isaacgym/assets/urdf/ycb/`; override
the location with `ROOM_BUILDER_YCB_DIR`. The sources are **in centimetres**, so they
are scaled by 0.01 exactly as the URDFs declare, then dropped so the base sits on z=0
and the footprint is centred — matching every other asset. The 2k textures are
downsampled to 512 px, which keeps each GLB between 300 and 700 KB.

Four objects ship here: `potted_meat_can`, `banana`, `mug`, `foam_brick`. If the
Isaac Gym tree is missing, `available()` returns nothing and the registry simply has
no `ycb_*` entries — no error. Sources that only ship USD need converting to OBJ
first (with `pxr`); trimesh cannot read USD.

YCB data is **CC BY 4.0** — redistributable with attribution. See [NOTICE.md](NOTICE.md).

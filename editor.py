"""Viser room editor: spawn procedural / GLB assets, place and scale them, save the layout.

    python editor.py [--scene scene.json] [--port 8080]

Left panel: pick an asset, Add, then drag the gizmo or type numbers. Click any
object in the 3D view to select it. Save writes a JSON layout that reloads
exactly (procedural assets are stored as parameters, not geometry).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import trimesh
import viser
import viser.transforms as vtf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import assets  # noqa: E402
import viser_register  # noqa: E402

GLB_DIR = HERE / "assets_out"


def _glb_bytes(asset: str, params: dict) -> bytes:
    """asset is either 'proc:<registry name>' or 'glb:<path>'."""
    kind, ref = asset.split(":", 1)
    if kind == "proc":
        return assets.build(ref, params).export(file_type="glb")
    return Path(ref).read_bytes()


def _asset_scene(asset: str, params: dict) -> trimesh.Scene:
    kind, ref = asset.split(":", 1)
    if kind == "proc":
        return assets.build(ref, params)
    loaded = trimesh.load(ref, force="scene")
    return loaded


@dataclass
class Instance:
    uid: int
    asset: str
    params: dict = field(default_factory=dict)
    position: np.ndarray = field(default_factory=lambda: np.zeros(3))
    wxyz: np.ndarray = field(default_factory=lambda: np.array([1.0, 0, 0, 0]))
    scale: np.ndarray = field(default_factory=lambda: np.ones(3))
    visible: bool = True
    handle: object = None

    @property
    def label(self) -> str:
        return f"{self.uid:02d} · {self.asset.split(':')[-1].split('/')[-1]}"

    @property
    def node(self) -> str:
        return f"/objs/{self.uid}"

    def to_dict(self) -> dict:
        return {"asset": self.asset, "params": self.params,
                "position": self.position.tolist(), "wxyz": self.wxyz.tolist(),
                "scale": self.scale.tolist(), "visible": self.visible}


class Editor:
    def __init__(self, server: viser.ViserServer) -> None:
        self.server = server
        self.objs: list[Instance] = []
        self.sel: Instance | None = None
        self._next_uid = 0
        self._syncing = False
        self._param_gui: list = []

        server.scene.set_up_direction("+z")
        server.scene.world_axes.visible = False
        server.scene.add_grid("/grid", width=12.0, height=12.0, cell_size=0.5,
                              plane="xy", position=(0, 0, -0.001))
        server.scene.add_light_ambient("/l_amb", intensity=0.55)
        server.scene.add_light_directional("/l_dir", intensity=1.6,
                                           wxyz=vtf.SO3.from_rpy_radians(-0.9, 0.3, 0.6).wxyz)
        self.gizmo = server.scene.add_transform_controls("/gizmo", scale=0.5, visible=False)
        self.gizmo.on_update(self._on_gizmo)

        self._build_gui()

    # ------------------------------------------------------------------ GUI
    def _build_gui(self) -> None:
        gui = self.server.gui

        with gui.add_folder("Add object"):
            self.g_kind = gui.add_dropdown("Asset", self._asset_options(),
                                           initial_value=list(assets.REGISTRY)[0])
            gui.add_button("Refresh GLB list").on_click(
                lambda _: setattr(self.g_kind, "options", self._asset_options()))
            gui.add_button("＋ Add", icon=viser.Icon.PLUS).on_click(lambda _: self.add(self.g_kind.value))

        with gui.add_folder("Selection"):
            self.g_sel = gui.add_dropdown("Object", ["(none)"], initial_value="(none)")
            self.g_sel.on_update(lambda _: self._select_by_label(self.g_sel.value))
            self.g_pos = gui.add_vector3("Position", (0.0, 0.0, 0.0), step=0.01)
            self.g_yaw = gui.add_slider("Yaw °", -180.0, 180.0, 1.0, 0.0)
            self.g_uscale = gui.add_slider(
                "Scale", 0.05, 5.0, 0.01, 1.0,
                hint="Disabled for walls/pegboards — resize those with their own sliders, "
                     "so the hole grid keeps its pitch.")
            self.g_scale3 = gui.add_vector3("Scale xyz", (1.0, 1.0, 1.0), step=0.01, min=(0.02,) * 3)
            for h in (self.g_pos, self.g_yaw, self.g_uscale, self.g_scale3):
                h.on_update(self._on_gui_transform)
            self.g_vis = gui.add_checkbox("Visible", True)
            self.g_vis.on_update(lambda _: self._on_visible())
            with gui.add_folder("Actions"):
                gui.add_button("Drop to floor").on_click(lambda _: self._drop())
                gui.add_button("Duplicate").on_click(lambda _: self._duplicate())
                gui.add_button("Delete", color="red").on_click(lambda _: self._delete())

        self.f_params = gui.add_folder("Parameters")

        with gui.add_folder("Scene file"):
            self.g_path = gui.add_text("Path", str(HERE / "scene.json"))
            gui.add_button("Save").on_click(lambda _: self.save(self.g_path.value))
            gui.add_button("Load (replace)").on_click(lambda _: self.load(self.g_path.value))
            gui.add_button("Export room .glb").on_click(lambda _: self.export_glb())
            self.g_status = gui.add_text("Status", "ready", disabled=True)

    def _asset_options(self) -> list[str]:
        globs = sorted(p.name for p in GLB_DIR.glob("*.glb")) if GLB_DIR.exists() else []
        return list(assets.REGISTRY) + [f"glb/{g}" for g in globs]

    # ------------------------------------------------------------- scene ops
    def add(self, option: str, params: dict | None = None, select: bool = True,
            position=(0, 0, 0), wxyz=(1, 0, 0, 0), scale=(1, 1, 1),
            visible: bool = True) -> Instance:
        if option.startswith("glb/"):
            asset, params = "glb:" + str(GLB_DIR / option[4:]), {}
        elif option.startswith(("proc:", "glb:")):
            asset = option
        else:
            asset = "proc:" + option
        if params is None:
            params = assets.defaults(asset.split(":", 1)[1]) if asset.startswith("proc:") else {}

        inst = Instance(self._next_uid, asset, dict(params),
                        np.asarray(position, float), np.asarray(wxyz, float),
                        np.asarray(scale, float), bool(visible))
        self._next_uid += 1
        self._spawn(inst)
        self.objs.append(inst)
        self._refresh_list()
        if select:
            self._select(inst)
        return inst

    def _spawn(self, inst: Instance) -> None:
        if inst.handle is not None:
            inst.handle.remove()
        inst.handle = self.server.scene.add_glb(
            inst.node, _glb_bytes(inst.asset, inst.params),
            position=tuple(inst.position), wxyz=tuple(inst.wxyz), scale=tuple(inst.scale),
            visible=inst.visible)
        inst.handle.on_click(lambda _, i=inst: self._select(i))

    def _delete(self) -> None:
        if self.sel is None:
            return
        self.sel.handle.remove()
        self.objs.remove(self.sel)
        self.sel = None
        self.gizmo.visible = False
        self._clear_param_gui()
        self._refresh_list()

    def _duplicate(self) -> None:
        if self.sel is None:
            return
        s = self.sel
        self.add(s.asset, dict(s.params), position=s.position + np.array([0.3, 0.3, 0.0]),
                 wxyz=s.wxyz.copy(), scale=s.scale.copy())

    def _drop(self) -> None:
        """Put the object's lowest point on z=0, keeping x/y."""
        if self.sel is None:
            return
        sc = _asset_scene(self.sel.asset, self.sel.params)
        R = vtf.SO3(self.sel.wxyz).as_matrix()
        corners = trimesh.bounds.corners(sc.bounds * self.sel.scale[None, :])
        z_min = (corners @ R.T)[:, 2].min()
        self.sel.position[2] = -z_min
        self._push_transform()
        self._sync_gui()

    # ------------------------------------------------------------- selection
    def _refresh_list(self) -> None:
        labels = [o.label for o in self.objs] or ["(none)"]
        self.g_sel.options = labels
        if self.sel is not None:
            self.g_sel.value = self.sel.label
        elif labels:
            self.g_sel.value = labels[0]

    def _select_by_label(self, label: str) -> None:
        for o in self.objs:
            if o.label == label:
                if o is not self.sel:
                    self._select(o)
                return

    def _select(self, inst: Instance) -> None:
        self.sel = inst
        self.gizmo.visible = True
        fixed = inst.asset.split(":", 1)[1] in assets.RESIZE_BY_PARAMS
        self.g_uscale.disabled = self.g_scale3.disabled = fixed
        if fixed:
            self.g_status.value = "resize with the length/height sliders (scale would stretch it)"
        self._sync_gui()
        self._rebuild_param_gui()
        self._refresh_list()

    def _on_visible(self) -> None:
        if self._syncing or self.sel is None:
            return
        self.sel.visible = bool(self.g_vis.value)
        self.sel.handle.visible = self.sel.visible

    def _sync_gui(self) -> None:
        """Push instance state into the gizmo + number widgets."""
        s = self.sel
        if s is None:
            return
        self._syncing = True
        try:
            self.g_vis.value = s.visible
            self.gizmo.position = tuple(s.position)
            self.gizmo.wxyz = tuple(s.wxyz)
            self.g_pos.value = tuple(s.position)
            self.g_yaw.value = float(np.degrees(vtf.SO3(s.wxyz).compute_yaw_radians()))
            self.g_scale3.value = tuple(s.scale)
            self.g_uscale.value = float(np.clip(s.scale.mean(), 0.05, 5.0))
        finally:
            self._syncing = False

    def _push_transform(self) -> None:
        s = self.sel
        s.handle.position = tuple(s.position)
        s.handle.wxyz = tuple(s.wxyz)
        s.handle.scale = tuple(s.scale)

    # ------------------------------------------------------------- callbacks
    def _on_gizmo(self, _) -> None:
        if self._syncing or self.sel is None:
            return
        self.sel.position = np.array(self.gizmo.position, float)
        self.sel.wxyz = np.array(self.gizmo.wxyz, float)
        self._push_transform()
        self._syncing = True
        try:
            self.g_pos.value = tuple(self.sel.position)
            self.g_yaw.value = float(np.degrees(vtf.SO3(self.sel.wxyz).compute_yaw_radians()))
        finally:
            self._syncing = False

    def _on_gui_transform(self, _) -> None:
        if self._syncing or self.sel is None:
            return
        s = self.sel
        s.position = np.array(self.g_pos.value, float)
        s.wxyz = vtf.SO3.from_z_radians(np.radians(self.g_yaw.value)).wxyz
        u = float(self.g_uscale.value)
        if not np.isclose(u, s.scale.mean()):
            s.scale = np.full(3, u)                       # uniform slider wins
        else:
            s.scale = np.array(self.g_scale3.value, float)
        self._push_transform()
        self._sync_gui()

    # ------------------------------------------- per-asset parameter widgets
    def _clear_param_gui(self) -> None:
        for h in self._param_gui:
            h.remove()
        self._param_gui = []

    def _rebuild_param_gui(self) -> None:
        self._clear_param_gui()
        s = self.sel
        if s is None or not s.asset.startswith("proc:"):
            return
        _, spec = assets.REGISTRY[s.asset.split(":", 1)[1]]
        with self.f_params:
            for key, default, (lo, hi, step) in spec:
                val = s.params.get(key, default)
                h = self.server.gui.add_slider(key, lo, hi, step, val)
                h.on_update(lambda _, k=key, hh=h: self._on_param(k, hh))
                self._param_gui.append(h)

    def _on_param(self, key: str, handle) -> None:
        if self.sel is None:
            return
        self.sel.params[key] = handle.value
        self._spawn(self.sel)          # cheap: assets are a few thousand triangles

    # ------------------------------------------------------------- scene i/o
    def save(self, path: str) -> None:
        Path(path).write_text(json.dumps({"objects": [o.to_dict() for o in self.objs]}, indent=2))
        self.g_status.value = f"saved {len(self.objs)} objects"

    def load(self, path: str) -> None:
        data = json.loads(Path(path).read_text())
        self.g_path.value = str(path)      # so Save/Export land back on the file we opened
        for o in list(self.objs):
            o.handle.remove()
        self.objs.clear()
        self.sel = None
        self.gizmo.visible = False
        self._clear_param_gui()
        for d in data["objects"]:
            self.add(d["asset"], d.get("params"), select=False,
                     position=d["position"], wxyz=d["wxyz"], scale=d["scale"],
                     visible=d.get("visible", True))
        self._refresh_list()
        self.g_status.value = f"loaded {len(self.objs)} objects"

    def export_glb(self) -> None:
        out = trimesh.Scene()
        for o in self.objs:
            sc = _asset_scene(o.asset, o.params)
            T = np.eye(4)
            T[:3, :3] = vtf.SO3(o.wxyz).as_matrix() @ np.diag(o.scale)
            T[:3, 3] = o.position
            for name, geom in sc.geometry.items():
                out.add_geometry(geom, geom_name=f"{o.uid}_{name}", transform=T)
        path = Path(self.g_path.value).with_suffix(".glb")
        path.write_bytes(out.export(file_type="glb"))
        self.g_status.value = f"exported {path.name}"


def main() -> None:
    ap = argparse.ArgumentParser()
    # Hard-coded and unique: the port is the registry's primary key, and 8080 on
    # this cluster is already taken -- viser would silently drift to 8081 and the
    # tunnel would point at nothing.
    ap.add_argument("--port", type=int, default=8877)
    ap.add_argument("--scene", default=None, help="scene .json to load at startup")
    args = ap.parse_args()

    server = viser.ViserServer(host="0.0.0.0", port=args.port)
    # get_port(), never args.port: viser increments past a busy port without saying so.
    viser_register.register(server.get_port(), run="garage layout editor", kind="tool",
                            log_dir=str(HERE))
    ed = Editor(server)
    scene_path = args.scene or (HERE / "scene_demo.json")
    if Path(scene_path).exists():
        ed.g_path.value = str(scene_path)
        ed.load(str(scene_path))
    else:
        ed.add("room_shell", {"n_walls": 0}, select=False)
        ed.add("pegboard_wall")

    print(f"viser: http://localhost:{server.get_port()}", flush=True)
    while True:
        __import__("time").sleep(1.0)


if __name__ == "__main__":
    main()

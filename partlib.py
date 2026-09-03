"""Blocky/tubular asset construction helpers on top of trimesh primitives.

Convention for every asset in this package:
  * Z is up, meters.
  * The asset's origin sits on the floor, at the horizontal center of its
    footprint (so "drop it on the ground plane" is just position.z = 0).
"""

from __future__ import annotations

import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

# name -> (linear rgb 0-255, metallic, roughness)
MATERIALS: dict[str, tuple[tuple[int, int, int], float, float]] = {
    "metal_black": ((38, 38, 42), 0.85, 0.35),
    "deck_gray": ((124, 130, 136), 0.05, 0.80),
    "wood": ((172, 132, 88), 0.0, 0.75),
    "plywood": ((214, 178, 132), 0.0, 0.80),
    "seam": ((150, 116, 78), 0.0, 0.85),
    "ceiling": ((240, 238, 233), 0.0, 0.95),
    "wall": ((228, 224, 216), 0.0, 0.95),
    "floor": ((160, 148, 132), 0.0, 0.85),
    "plastic_blue": ((60, 110, 190), 0.0, 0.5),
    "bulb_glass": ((250, 238, 205), 0.0, 0.15),
    "brass": ((186, 148, 76), 0.90, 0.35),
    "white_plastic": ((238, 236, 230), 0.0, 0.55),
    "steel": ((168, 172, 178), 0.85, 0.30),
    "tool_yellow": ((226, 176, 38), 0.0, 0.45),
    "pcb_green": ((30, 108, 64), 0.05, 0.50),
    "plastic_red": ((190, 46, 42), 0.0, 0.50),
    "plastic_green": ((52, 150, 74), 0.0, 0.50),
    "plastic_gray": ((150, 152, 156), 0.0, 0.60),
    "copper": ((184, 115, 60), 0.90, 0.32),
    "rubber": ((40, 40, 44), 0.0, 0.92),
    "tote_gray": ((96, 102, 110), 0.0, 0.60),
    "cardboard": ((190, 158, 112), 0.0, 0.90),
    "led_red": ((220, 40, 36), 0.0, 0.25),
    "led_green": ((48, 200, 90), 0.0, 0.25),
    "led_rgb": ((236, 232, 244), 0.0, 0.20),
}

# Parts that glow. Rendered as emissive so a lit bulb reads as lit rather than
# as a pale plastic ball -- viser has no light bound to it, this is just shading.
EMISSIVE: dict[str, tuple[int, int, int]] = {
    "bulb_glass": (255, 206, 128),
    "led_red": (255, 60, 50),
    "led_green": (70, 255, 120),
    "led_rgb": (190, 130, 255),
}


def box(size, center) -> trimesh.Trimesh:
    """Axis-aligned box given (dx, dy, dz) and its center."""
    T = np.eye(4)
    T[:3, 3] = center
    return trimesh.creation.box(extents=size, transform=T)


def box_between(p0, p1, thickness) -> trimesh.Trimesh:
    """Square-tube style box spanning p0->p1 along whichever axis they differ on."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = np.abs(p1 - p0)
    size = np.where(d > 1e-9, d, thickness)
    return box(size, (p0 + p1) / 2.0)


def beam(p0, p1, size_u, size_v, u_axis=(1.0, 0.0, 0.0)) -> trimesh.Trimesh:
    """Rectangular beam spanning p0->p1 in any direction.

    The cross-section is `size_u` along `u_axis` (projected perpendicular to the
    beam) and `size_v` along the remaining axis -- so a splayed ladder rail can
    keep its wide face square to the world while the rail itself leans.
    """
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    length = float(np.linalg.norm(d))
    if length < 1e-9:
        return box((size_u, size_v, 1e-6), p0)
    d /= length
    u = np.asarray(u_axis, float)
    u = u - np.dot(u, d) * d
    if np.linalg.norm(u) < 1e-6:                      # u_axis parallel to the beam
        u = np.cross(d, [0.0, 0.0, 1.0])
        if np.linalg.norm(u) < 1e-6:
            u = np.cross(d, [1.0, 0.0, 0.0])
    u /= np.linalg.norm(u)
    v = np.cross(d, u)
    T = np.eye(4)
    T[:3, 0], T[:3, 1], T[:3, 2] = u, v, d
    T[:3, 3] = (p0 + p1) / 2.0
    return trimesh.creation.box(extents=(size_u, size_v, length), transform=T)


def tube(p0, p1, r, sections=14) -> trimesh.Trimesh:
    return trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections)


def polytube(points, r, sections=14, round_joints=True) -> list[trimesh.Trimesh]:
    """Round tube following a polyline, with spheres welding the bends."""
    pts = [np.asarray(p, float) for p in points]
    out = [tube(pts[i], pts[i + 1], r, sections) for i in range(len(pts) - 1)]
    if round_joints:
        for p in pts[1:-1]:
            out.append(trimesh.creation.icosphere(subdivisions=1, radius=r).apply_translation(p))
    return out


def slat_deck(x0, x1, y0, y1, z_top, thickness, n_slats, gap, along="y") -> list[trimesh.Trimesh]:
    """Slatted panel: `n_slats` planks with `gap` between them.

    along="y" means each plank is long in Y and they are stacked along X.
    """
    if along == "y":
        span, other = (x0, x1), (y0, y1)
    else:
        span, other = (y0, y1), (x0, x1)
    total = span[1] - span[0]
    w = (total - gap * (n_slats - 1)) / n_slats
    out = []
    for i in range(n_slats):
        a = span[0] + i * (w + gap)
        c = a + w / 2.0
        if along == "y":
            out.append(box((w, other[1] - other[0], thickness),
                           (c, (other[0] + other[1]) / 2.0, z_top - thickness / 2.0)))
        else:
            out.append(box((other[1] - other[0], w, thickness),
                           ((other[0] + other[1]) / 2.0, c, z_top - thickness / 2.0)))
    return out


def hole_texture(px=96, hole_frac=0.30, base=(214, 178, 132), hole=(96, 68, 42)):
    """One tileable pegboard cell: a hole centered in a square of board.

    Tiling this with uv = (position - first_hole) / pitch + 0.5 puts one hole per
    pitch square no matter how large the board gets, so the grid never stretches.
    """
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (px, px), base)
    d = ImageDraw.Draw(img)
    r = hole_frac * px / 2.0
    c = px / 2.0
    # soft rim first, then the bore, so the hole reads as drilled rather than painted
    d.ellipse([c - r * 1.22, c - r * 1.22, c + r * 1.22, c + r * 1.22],
              fill=tuple(int(b * 0.88) for b in base))
    d.ellipse([c - r, c - r, c + r, c + r], fill=hole)
    d.ellipse([c - r, c - r * 0.55, c + r, c + r], fill=tuple(int(h * 0.75) for h in hole))
    return img


def textured_quad(corners, uvs, image, roughness=0.85, name="pegboard"):
    """Flat quad carrying a repeating texture (uv may run outside [0, 1]).

    `corners` are the 4 points in counter-clockwise order *as seen from the front*,
    so the face normal ends up pointing at the viewer. `uvs` matches them 1:1.
    """
    verts = np.asarray(corners, float)
    mesh = trimesh.Trimesh(vertices=verts, faces=np.array([[0, 1, 2], [0, 2, 3]]),
                           process=False)
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=np.asarray(uvs, float),
        material=PBRMaterial(name=name, baseColorTexture=image,
                             baseColorFactor=[1.0, 1.0, 1.0, 1.0],
                             metallicFactor=0.0, roughnessFactor=roughness),
    )
    return mesh


def quad_xz(x0, x1, z0, z1, y, u_of_x, v_of_z, image, **kw):
    """Upright quad in the XZ plane, front face toward +Y."""
    corners = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
    uvs = [(u_of_x(x0), v_of_z(z0)), (u_of_x(x1), v_of_z(z0)),
           (u_of_x(x1), v_of_z(z1)), (u_of_x(x0), v_of_z(z1))]
    # CCW seen from +y: x increasing then z increasing is CW, so reverse.
    return textured_quad(corners[::-1], uvs[::-1], image, **kw)


def quad_xy(x0, x1, y0, y1, z, u_of_x, v_of_y, image, **kw):
    """Horizontal quad in the XY plane, front face toward -Z (a ceiling soffit)."""
    corners = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    uvs = [(u_of_x(x0), v_of_y(y0)), (u_of_x(x1), v_of_y(y0)),
           (u_of_x(x1), v_of_y(y1)), (u_of_x(x0), v_of_y(y1))]
    # CCW seen from below (-z) is the reverse of CCW seen from above.
    return textured_quad(corners[::-1], uvs[::-1], image, **kw)


class PartSet:
    """Collects meshes per material, then bakes them into one trimesh.Scene."""

    def __init__(self) -> None:
        self.parts: dict[str, list[trimesh.Trimesh]] = {}
        self.raw: list[tuple[str, trimesh.Trimesh]] = []

    def add(self, material: str, mesh) -> "PartSet":
        assert material in MATERIALS, f"unknown material {material}"
        bucket = self.parts.setdefault(material, [])
        bucket.extend(mesh if isinstance(mesh, (list, tuple)) else [mesh])
        return self

    def add_raw(self, name: str, mesh: trimesh.Trimesh) -> "PartSet":
        """Add a mesh that already carries its own visuals (e.g. a textured quad)."""
        self.raw.append((name, mesh))
        return self

    def translate(self, offset) -> "PartSet":
        """Shift every part, e.g. to re-center an asset on its footprint."""
        offset = np.asarray(offset, float)
        for meshes in self.parts.values():
            for m in meshes:
                m.apply_translation(offset)
        for _, m in self.raw:
            m.apply_translation(offset)
        return self

    def apply(self, matrix) -> "PartSet":
        """Apply one 4x4 transform to every part (scale, tilt, hinge swing)."""
        matrix = np.asarray(matrix, float)
        for meshes in self.parts.values():
            for m in meshes:
                m.apply_transform(matrix)
        for _, m in self.raw:
            m.apply_transform(matrix)
        return self

    def to_scene(self) -> trimesh.Scene:
        scene = trimesh.Scene()
        for name, mesh in self.raw:
            scene.add_geometry(mesh, geom_name=name)
        for name, meshes in self.parts.items():
            merged = trimesh.util.concatenate(meshes)
            rgb, metallic, rough = MATERIALS[name]
            kwargs = {}
            if name in EMISSIVE:
                kwargs["emissiveFactor"] = [c / 255 for c in EMISSIVE[name]]
            merged.visual = trimesh.visual.TextureVisuals(
                material=PBRMaterial(
                    name=name,
                    baseColorFactor=[rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1.0],
                    metallicFactor=metallic,
                    roughnessFactor=rough,
                    **kwargs,
                )
            )
            scene.add_geometry(merged, geom_name=name)
        return scene

"""Bake every procedural asset to assets_out/*.glb (for reuse outside viser)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import assets  # noqa: E402

OUT = HERE / "assets_out"
OUT.mkdir(exist_ok=True)
for name in assets.REGISTRY:
    scene = assets.build(name)
    path = OUT / f"{name}.glb"
    path.write_bytes(scene.export(file_type="glb"))
    print(f"{path.name:24s} {len(path.read_bytes())/1024:7.1f} KB  bounds={scene.bounds.round(3).tolist()}")

# Third-party assets

Everything under `assets/` is procedurally generated except `assets/ycb.py`, which
loads meshes from the **YCB Object and Model Set**. The baked copies in
`assets_out/ycb_*.glb` are derived from those meshes (scaled to metres, re-origined,
textures downsampled to 512 px).

> The YCB Object and Model Set: Towards Common Benchmarks for Manipulation Research
> Berk C. Calli, Arjun Singh, Aaron Walsman, Siddhartha Srinivasa, Pieter Abbeel, Aaron M. Dollar
>
> B. Calli, A. Walsman, A. Singh, S. Srinivasa, P. Abbeel and A. M. Dollar,
> "Benchmarking in Manipulation Research: Using the Yale-CMU-Berkeley Object and Model Set,"
> IEEE Robotics & Automation Magazine, vol. 22, no. 3, pp. 36-52, Sept. 2015.
> doi: 10.1109/MRA.2015.2448951
>
> B. Calli, A. Singh, A. Walsman, S. Srinivasa, P. Abbeel and A. M. Dollar,
> "The YCB object and Model set: Towards common benchmarks for manipulation research,"
> International Conference on Advanced Robotics (ICAR), Istanbul, 2015, pp. 510-517.
> doi: 10.1109/ICAR.2015.7251504

YCB data set license: **Creative Commons Attribution 4.0 International (CC BY 4.0)**
<https://creativecommons.org/licenses/by/4.0/> — <http://ycbbenchmarks.org/>

The source meshes here came via the Isaac Gym asset tree
(`assets/urdf/ycb/<id>_<name>/textured.obj`). Set `ROOM_BUILDER_YCB_DIR` to point
somewhere else. Without that directory the registry simply has no `ycb_*` entries.

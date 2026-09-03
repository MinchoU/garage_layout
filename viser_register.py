"""Register a viser server into the cluster port registry so the laptop-side
`~/.viser_ports/autoforward.py` opens an ssh tunnel to it automatically.

Drop this into any viser script right after the server starts:

    import viser_register
    server = viser.ViserServer(host="0.0.0.0", port=port)
    viser_register.register(port, run="jar refine viz", kind="viz")

It writes `~/.viser_ports/active/<port>.json`, heartbeats its mtime every 30 s
(the reader prunes entries older than 90 s), and removes the file at exit. Then
just open http://localhost:<port> on the laptop -- no manual `ssh -L` needed.
"""
import atexit
import json
import os
import socket
import threading
import time

REG_DIR = os.path.expanduser("~/.viser_ports/active")
_HEARTBEAT_S = 30


def register(port, run="viz", kind="viz", log_dir="", job=""):
    """Publish this viser server to the registry; returns the entry path.

    Safe to call even if the registry dir is missing/unwritable -- it just warns
    and returns None so a viz script never dies over forwarding bookkeeping.
    """
    try:
        os.makedirs(REG_DIR, exist_ok=True)
    except OSError as exc:
        print(f"[viser-register] cannot create {REG_DIR}: {exc}", flush=True)
        return None
    path = os.path.join(REG_DIR, f"{int(port)}.json")
    entry = {
        "port": int(port),
        "node": socket.gethostname(),
        "run": run,
        "kind": kind,
        "pid": os.getpid(),
        "job": job or os.environ.get("SLURM_JOB_ID", ""),
        "log_dir": log_dir,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    def _write():
        with open(path, "w") as f:
            f.write(json.dumps(entry))

    try:
        _write()
    except OSError as exc:
        print(f"[viser-register] cannot write {path}: {exc}", flush=True)
        return None
    print(f"[viser-register] {entry['node']}:{port} -> {path}  "
          f"(open http://localhost:{port} on the laptop)", flush=True)

    def _beat():
        while True:
            time.sleep(_HEARTBEAT_S)
            try:
                os.utime(path, None)
            except OSError:
                try:
                    _write()          # recreate if something pruned it
                except OSError:
                    return

    threading.Thread(target=_beat, daemon=True).start()

    def _cleanup():
        try:
            os.unlink(path)
        except OSError:
            pass

    atexit.register(_cleanup)
    return path

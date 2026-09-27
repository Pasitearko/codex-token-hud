"""Check whether resizing a layered bitmap can carry a smooth morph without capture."""
import statistics
import time
from pathlib import Path
from PIL import ImageGrab

import token_strip as ts
from smooth_capsule import SmoothCapsule

app = ts.TokenStrip(visual_only=True)
app.motion_allowed = True
app.root.attributes("-topmost", True)
app._geometry_controller(position=(460, 320))
app.root.deiconify(); app.root.update()
app.hwnd = int(ts.u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
app._place_z_order = lambda: None
app.smooth = SmoothCapsule(app.hwnd, input_surface=False)
app.smooth.enable_input_surface()
app.thread_id = "move-probe"
app.totals = ts.Totals(164_200_000, 411_500, 160_200_000, 0, time.time(), 1)
app._render(); app._geometry_controller(capture=True)
original_sync = app._sync_smooth_overlay
def move_only(capture=False, radius=None):
    original_sync(False, radius)
app._sync_smooth_overlay = move_only
app._pointer_inside_hud = lambda: False
app._watch_pointer = lambda: None
for expanded in (True, False):
    frames=[]; original_geometry=app._geometry_controller
    def wrapped(*args, **kwargs):
        if kwargs.get("size") is not None: frames.append(time.perf_counter())
        return original_geometry(*args, **kwargs)
    app._geometry_controller=wrapped
    app._start_morph(expanded)
    deadline=time.perf_counter()+.34
    capture_at = time.perf_counter() + .12
    captured = False
    while time.perf_counter()<deadline:
        app.root.update()
        if not captured and time.perf_counter() >= capture_at:
            x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
            ImageGrab.grab(bbox=(x, y, x + app.root.winfo_width(), y + app.root.winfo_height())).save(
                Path(__file__).with_name("ui-review") / ("layered-move-" + ("expand" if expanded else "collapse") + ".png"))
            captured = True
        time.sleep(.001)
    iv=[(b-a)*1000 for a,b in zip(frames,frames[1:])]
    print("move-only", "expand" if expanded else "collapse", "frames",len(frames),
          "mean",round(statistics.mean(iv),2) if iv else 0,
          "p95",round(sorted(iv)[min(len(iv)-1,int(len(iv)*.95))],2) if iv else 0, flush=True)
    app._geometry_controller=original_geometry
app.quit()

"""Measure the full per-pixel alpha morph path without DWM clipping."""
from __future__ import annotations

import statistics
import time

import token_strip as ts
from smooth_capsule import SmoothCapsule


app = ts.TokenStrip(visual_only=True)
app.motion_allowed = True
app.root.attributes("-topmost", True)
app._geometry_controller(position=(460, 320))
app.root.deiconify()
app.root.update()
app.hwnd = int(ts.u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
app._place_z_order = lambda: None
app.smooth = SmoothCapsule(app.hwnd, input_surface=False)
app.smooth.enable_input_surface()
app._dwm_rounding = False
app.thread_id = "layered-probe"
app.totals = ts.Totals(164_200_000, 411_500, 160_200_000, 0, time.time(), 1)
app._render()
app._geometry_controller(capture=True)
app._pointer_inside_hud = lambda: False
app._watch_pointer = lambda: None

for expanded in (True, False):
    frames = []
    original = app._geometry_controller

    def wrapped(*args, **kwargs):
        if kwargs.get("size") is not None:
            frames.append(time.perf_counter())
        return original(*args, **kwargs)

    app._geometry_controller = wrapped
    app._start_morph(expanded)
    deadline = time.perf_counter() + .34
    while time.perf_counter() < deadline:
        app.root.update()
        time.sleep(.001)
    intervals = [(b-a)*1000 for a, b in zip(frames, frames[1:])]
    print("layered", "expand" if expanded else "collapse", "frames", len(frames),
          "mean", round(statistics.mean(intervals), 2) if intervals else 0,
          "p95", round(sorted(intervals)[min(len(intervals)-1, int(len(intervals)*.95))], 2)
          if intervals else 0, flush=True)
    assert app.smooth.surface_enabled and not app._morph_using_fallback, (
        "morph left the transparent input-surface path",
        app.smooth.surface_enabled, app._morph_using_fallback, app._morph_state)
    app._geometry_controller = original

app.quit()

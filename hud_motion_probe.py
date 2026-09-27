"""Development-only timing and screen-pixel regression for HUD morphs."""
from __future__ import annotations

import ctypes
import statistics
import time
from ctypes import wintypes
from threading import Event, Thread

import token_strip as ts


def percentile(values, fraction):
    return round(sorted(values)[min(len(values)-1, int(len(values)*fraction))], 2) if values else 0


app = ts.TokenStrip(visual_only=True)
app.motion_allowed = True
app.root.attributes("-topmost", True)
app._geometry_controller(position=(460, 320))
app.root.deiconify()
app.root.update()
app.hwnd = int(ts.u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
app._place_z_order = lambda: None
app.thread_id = "motion-probe"
app.totals = ts.Totals(164_200_000, 411_500, 160_200_000, 0, time.time(), 1)
app._render()
app._geometry_controller(capture=True)
app._pointer_inside_hud = lambda: False
app._watch_pointer = lambda: None

durations = {name: [] for name in ("geometry", "draw", "region", "idletasks")}
frames = []
for name, key in (("_geometry_controller", "geometry"), ("_draw_hud", "draw"),
                  ("_apply_capsule_region", "region")):
    original = getattr(app, name)

    def wrapper(*args, _original=original, _key=key, **kwargs):
        started = time.perf_counter()
        if _key == "geometry" and kwargs.get("size") is not None:
            frames.append(started)
        result = _original(*args, **kwargs)
        durations[_key].append((time.perf_counter()-started)*1000)
        return result

    setattr(app, name, wrapper)

original_idle = app.root.update_idletasks


def timed_idle():
    started = time.perf_counter()
    result = original_idle()
    durations["idletasks"].append((time.perf_counter()-started)*1000)
    return result


app.root.update_idletasks = timed_idle
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
gdi32.GetPixel.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.GetPixel.restype = wintypes.COLORREF
samples = []
stop = Event()


def sample_pixels():
    dc = user32.GetDC(None)
    try:
        while not stop.is_set():
            color = int(gdi32.GetPixel(dc, app._geometry_x + 8, app._geometry_y + 8))
            samples.append(color)
            time.sleep(.001)
    finally:
        user32.ReleaseDC(None, dc)


sampler = Thread(target=sample_pixels, daemon=True)
sampler.start()
frame_counts = []
peak_intervals = []
for expanded in (True, False, True, False):
    frames.clear()
    app._start_morph(expanded)
    deadline = time.perf_counter() + .34
    while time.perf_counter() < deadline:
        app.root.update()
        time.sleep(.001)
    intervals = [(b-a)*1000 for a, b in zip(frames, frames[1:])]
    frame_counts.append(len(frames))
    peak_intervals.append(max(intervals, default=0))
    print("morph", "expand" if expanded else "collapse", "frames", len(frames),
          "mean", round(statistics.mean(intervals), 2) if intervals else 0,
          "p95", percentile(intervals, .95), "max", round(max(intervals, default=0), 2), flush=True)
stop.set()
sampler.join(timeout=2)
for name, values in durations.items():
    print(name, "count", len(values), "p50", percentile(values, .5),
          "p95", percentile(values, .95), flush=True)
bright = [color for color in samples if
          ((color & 255) + ((color >> 8) & 255) + ((color >> 16) & 255)) > 600]
print("pixels", len(samples), "bright", len(bright), flush=True)
app.quit()
assert not bright, "morph produced a bright flash on the HUD body"
assert min(frame_counts) >= 25 and max(peak_intervals) < 25, (
    "morph regressed toward the former 16ms-plus cadence", frame_counts, peak_intervals)

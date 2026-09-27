"""Focused regression for dragging and morph frame delivery."""
from __future__ import annotations

import ctypes
import time
from ctypes import wintypes
from types import SimpleNamespace

import token_strip as ts


def pump(app, milliseconds):
    until = time.perf_counter() + milliseconds / 1000
    while time.perf_counter() < until:
        app.root.update()
        time.sleep(.002)
    app.root.update()


target = (200, 180, 1200, 900)
config = {"edge": "safe", "along": .5}
ts.rect = lambda _hwnd: target
ts.monitor_rect = lambda _hwnd: (0, 0, 1920, 1080)
ts.get_dpi = lambda _hwnd: 96
ts.load_config = lambda: dict(config)
ts.save_config = lambda value: config.update(value)

app = ts.TokenStrip(visual_only=True)
app.root.attributes("-topmost", True)
app.root.deiconify()
app.root.update()
app.hwnd = int(ts.u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
app._place_z_order = lambda: None
app.target_hwnd = 123
app.thread_id = "synthetic-preview"
app.totals = ts.Totals(3_000_000, 129_388, 2_900_000, 0, time.time(), 1)
app._render()
app._follow_window(capture=True)

x, y = app._geometry_x, app._geometry_y
press = SimpleNamespace(x_root=x+40, y_root=y+20)
app._drag_start(press)
times = []
for step in range(1, 18):
    started = time.perf_counter()
    app._drag_move(SimpleNamespace(x_root=press.x_root+step*8,
                                   y_root=press.y_root+step*3))
    times.append((time.perf_counter()-started)*1000)
dragged = app._geometry_x, app._geometry_y
app._follow_window()
after_follow = app._geometry_x, app._geometry_y
print("drag p95 ms", round(sorted(times)[int(len(times)*.95)], 1),
      "dragged", dragged, "after poll", after_follow, flush=True)
drag_p95 = sorted(times)[int(len(times)*.95)]

app.drag = None
app._drag_moved = False
app._pointer_inside_hud = lambda: True
app.motion_allowed = True
frames = []
original_geometry = app._geometry_controller
def record_geometry(*args, **kwargs):
    if kwargs.get("size") is not None:
        frames.append(time.perf_counter())
    return original_geometry(*args, **kwargs)
app._geometry_controller = record_geometry
app._start_morph(True)
pump(app, 330)
intervals = [(b-a)*1000 for a, b in zip(frames, frames[1:])]
print("expand frames", len(frames), "max interval ms", round(max(intervals, default=0), 1),
      "state", app._morph_state, flush=True)

ts.u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
ts.u32.SetCursorPos.restype = wintypes.BOOL
ts.u32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                              wintypes.DWORD, ctypes.c_size_t]
ts.u32.mouse_event.restype = None
original_pointer = app.root.winfo_pointerxy()
item = app.canvas.find_withtag("metric-total")[0]
left, top, right, bottom = app.canvas.bbox(item)
px = app._geometry_x + (left+right)//2
py = app._geometry_y + (top+bottom)//2
ts.u32.SetCursorPos(px, py)
pump(app, 50)
before_metric_drag = app._geometry_x, app._geometry_y
ts.u32.mouse_event(0x0002, 0, 0, 0, 0)
pump(app, 20)
ts.u32.SetCursorPos(px+100, py+35)
pump(app, 65)
ts.u32.mouse_event(0x0004, 0, 0, 0, 0)
pump(app, 50)
after_metric_drag = app._geometry_x, app._geometry_y
app._follow_window()
after_snap_poll = app._geometry_x, app._geometry_y
ts.u32.SetCursorPos(*original_pointer)
print("metric drag", before_metric_drag, after_metric_drag,
      "after snap poll", after_snap_poll, flush=True)

app._pointer_inside_hud = lambda: False
app._start_morph(False)
pump(app, 250)
assert app._morph_state == "collapsed"
app._pointer_inside_hud = lambda: True
app._start_morph(True)
pump(app, 75)
assert 0 < app._morph_progress < 1
sx, sy = app._geometry_x, app._geometry_y
start = SimpleNamespace(x_root=sx+40, y_root=sy+20)
end = SimpleNamespace(x_root=start.x_root+70, y_root=start.y_root+28)
app._drag_start(start)
app._drag_move(end)
assert app._morph_state == "dragging"
expected_state = "expanded" if app._drag_resume_expanded else "collapsed"
app._drag_end(end)
pump(app, 320)
print("interrupted morph", app._morph_state, "visible", app.root.winfo_viewable(), flush=True)
completed_interrupted_morph = (app._morph_state == expected_state and
                               app.root.winfo_viewable())

ts.is_minimized_or_cloaked = lambda _hwnd: False
app._pointer_inside_hud = lambda: False
app._start_morph(False)
pump(app, 55)
app._toggle_visible()
assert not app.root.winfo_viewable()
app._toggle_visible()
assert app.root.winfo_viewable()

target = (500, 300, 1300, 700)
for wanted_edge, position in (("left", (175, 430)), ("right", (1315, 430)),
                              ("top", (850, 250)), ("bottom", (850, 715)),
                              ("safe", (850, 315))):
    app._geometry_controller(position=(position[0]-8, position[1]))
    start = SimpleNamespace(x_root=app._geometry_x+35, y_root=app._geometry_y+20)
    end = SimpleNamespace(x_root=start.x_root+8, y_root=start.y_root)
    app._drag_start(start)
    app._drag_move(end)
    app._drag_end(end)
    snapped = app._geometry_x, app._geometry_y
    app._follow_window()
    assert app.edge == wanted_edge and (app._geometry_x, app._geometry_y) == snapped, (
        wanted_edge, app.edge, snapped, (app._geometry_x, app._geometry_y))

app.quit()
assert dragged == after_follow, "follow poll reverted an active drag"
assert drag_p95 <= 20, "position-only dragging still blocks the event loop"
assert len(frames) >= 10 and max(intervals, default=0) <= 35, "morph delivered too few/uneven frames"
assert before_metric_drag != after_metric_drag, "dragging from a metric was treated as a click"
assert after_metric_drag == after_snap_poll, "snap position changed on the next follow poll"
assert completed_interrupted_morph, "dragging through a morph left an incomplete HUD"

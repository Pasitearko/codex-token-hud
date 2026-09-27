"""Development-only Win32/Tk HUD interaction and capture check."""
from __future__ import annotations

import time
import ctypes
from ctypes import wintypes
from pathlib import Path

from PIL import ImageGrab

import token_strip as ts

assert [(n, ts.format_token_count(n)) for n in
        (9999, 10_000, 31_000, 1_000_000, 3_129_388, 1_000_000_000, 3_100_000_000)] == [
            (9999, "9,999"), (10_000, "1W"), (31_000, "3.1W"),
            (1_000_000, "1M"), (3_129_388, "3.1M"),
            (1_000_000_000, "1B"), (3_100_000_000, "3.1B")]


def pump(app, milliseconds):
    deadline = time.perf_counter() + milliseconds / 1000
    while time.perf_counter() < deadline:
        app.root.update()
        time.sleep(.005)
    app.root.update()


def wait_for_state(app, state, timeout_ms=1000):
    started = time.perf_counter()
    while (time.perf_counter() - started) * 1000 < timeout_ms:
        app.root.update()
        if app._morph_state == state:
            return round((time.perf_counter() - started) * 1000)
        time.sleep(.005)
    raise AssertionError(f"HUD did not reach {state}: {app._morph_state}")


def capture(app, name):
    app.root.update()
    x, y = app.root.winfo_rootx(), app.root.winfo_rooty()
    width, height = app.root.winfo_width(), app.root.winfo_height()
    path = Path(__file__).with_name("ui-review") / f"hud-{name}.png"
    path.parent.mkdir(exist_ok=True)
    ImageGrab.grab(bbox=(x, y, x + width, y + height)).save(path)
    for item in app.canvas.find_all():
        if app.canvas.type(item) != "text":
            continue
        left, top, right, bottom = app.canvas.bbox(item)
        assert left >= 0 and top >= 0 and right <= width and bottom <= height, (
            name, app.canvas.itemcget(item, "text"), (left, top, right, bottom), (width, height))
    return path


app = ts.TokenStrip(visual_only=True)
app.motion_allowed = True
app.root.attributes("-topmost", True)
app._geometry_controller(position=(340, 260))
app.root.deiconify()
app.root.update()
app.hwnd = int(ts.u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
app._place_z_order = lambda: None
app.thread_id = "synthetic-preview"
app.totals = ts.Totals(164_200_000, 411_500, 160_200_000, 0, time.time()-3, 1)
app._render()
app._geometry_controller(capture=True)
collapsed = capture(app, "collapsed-dev")

hover_timing = {}
original_leave_handler = app._schedule_hide_detail
original_morph_start = app._start_morph
original_morph_finish = app._finish_morph
def on_leave(event):
    hover_timing["leave"] = time.perf_counter()
    original_leave_handler(event)
def on_morph_start(expand):
    hover_timing["expand_start" if expand else "collapse_start"] = time.perf_counter()
    return original_morph_start(expand)
def on_morph_finish(expanded):
    hover_timing["expand_end" if expanded else "collapse_end"] = time.perf_counter()
    return original_morph_finish(expanded)
app.canvas.bind("<Leave>", on_leave)
app._start_morph = on_morph_start
app._finish_morph = on_morph_finish
original_pointer = app.root.winfo_pointerxy()
ts.u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
ts.u32.SetCursorPos.restype = wintypes.BOOL
ts.u32.SetCursorPos(100, 100)
pump(app, 30)
ts.u32.SetCursorPos(app._geometry_x+79, app._geometry_y+20)
pump(app, 30)
ts.u32.SetCursorPos(app._geometry_x+80, app._geometry_y+20)
enter_ms = wait_for_state(app, "expanded")
ts.u32.SetCursorPos(100, 100)
pointer_left_at = time.perf_counter()
exit_ms = wait_for_state(app, "collapsed")
leave_ms = round((hover_timing["leave"]-pointer_left_at)*1000)
collapse_ms = round((hover_timing["collapse_end"]-hover_timing["collapse_start"])*1000)
ts.u32.SetCursorPos(*original_pointer)

# A brief enter must never start expansion.
app._pointer_inside_hud = lambda: False
app._show_detail()
pump(app, 45)
app._schedule_hide_detail()
pump(app, 125)
assert app._morph_state == "collapsed"

app._pointer_inside_hud = lambda: True
app._show_detail()
pump(app, 125)
assert app._morph_state == "expanding"
app._pointer_inside_hud = lambda: False
app._schedule_hide_detail()
pump(app, 220)
assert app._morph_state == "collapsing"
app._pointer_inside_hud = lambda: True
app._show_detail()
pump(app, 270)
assert app._morph_state == "expanded"
expanded = capture(app, "expanded-dev")

ts.u32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
                              wintypes.DWORD, ctypes.c_size_t]
ts.u32.mouse_event.restype = None
def click_metric(tag):
    item = app.canvas.find_withtag(tag)[0]
    left, top, right, bottom = app.canvas.bbox(item)
    ts.u32.SetCursorPos(app._geometry_x+(left+right)//2, app._geometry_y+(top+bottom)//2)
    pump(app, 40)
    ts.u32.mouse_event(0x0002, 0, 0, 0, 0)
    pump(app, 25)
    ts.u32.mouse_event(0x0004, 0, 0, 0, 0)
    pump(app, 50)

click_metric("metric-total")
assert app._exact_metric_keys["total"]
assert any(app.canvas.itemcget(item, "text") == "164611500"
           for item in app.canvas.find_withtag("metric-total"))
capture(app, "expanded-exact-dev")
click_metric("metric-total")
assert not app._exact_metric_keys["total"]
click_metric("metric-input")
assert app._exact_metric_keys["input"]
click_metric("metric-input")
assert not app._exact_metric_keys["input"]
ts.u32.SetCursorPos(*original_pointer)

# Reverse an active collapse and refresh the counters repeatedly while resizing.
app._start_morph(False)
pump(app, 55)
app._start_morph(True)
for step in range(20):
    app.totals.input += 1000
    app._render()
    pump(app, 10)
pump(app, 80)
assert app._morph_state == "expanded"
assert (app._geometry_width, app._geometry_height) == app._expanded_size()

# The follow loop keeps the HUD size fixed and only changes its dock position.
window = [200, 180, 1200, 900]
ts.rect = lambda _hwnd: tuple(window)
ts.monitor_rect = lambda _hwnd: (0, 0, 1920, 1080)
ts.get_dpi = lambda _hwnd: 96
ts.load_config = lambda: {"edge": "safe", "along": .5}
app.target_hwnd = 123
app._pointer_inside_hud = lambda: False
app._start_morph(False)
pump(app, 45)
size_before = app._geometry_width, app._geometry_height
app._follow_window()
window[:] = [240, 210, 1240, 930]
app._follow_window()
assert app._morph_state == "collapsing"
assert app._collapsed_size()[0] < app._geometry_width <= size_before[0]
assert app._collapsed_size()[1] < app._geometry_height <= size_before[1]
pump(app, 230)
assert app._morph_state == "collapsed"

window[:] = [1710, 940, 1910, 1070]
app._follow_window()
assert app._geometry_x + app._geometry_width <= 1920
assert app._geometry_y + app._geometry_height <= 1080
window[:] = [0, 0, 1920, 1080]
app._follow_window()
assert app._geometry_x >= 0 and app._geometry_y >= 0
window[:] = [240, 210, 1240, 930]
app._follow_window()
assert app._geometry_x + app._geometry_width <= 1920

# Closing, reopening, minimizing, and tray hiding all restore collapsed size.
minimized = [False]
ts.is_minimized_or_cloaked = lambda _hwnd: minimized[0]
app.details_pinned = True
app._start_morph(True)
pump(app, 280)
assert app._morph_state == "expanded"
minimized[0] = True
app._accept_poll([], 123, "测试聊天", "synthetic-preview", app.totals)
assert not app.root.winfo_viewable()
assert (app._geometry_width, app._geometry_height) == app._collapsed_size()
minimized[0] = False
app._accept_poll([], 123, "测试聊天", "synthetic-preview", app.totals)
assert app.root.winfo_viewable()
app._accept_poll([], None, "", None, ts.Totals())
assert not app.root.winfo_viewable()
assert (app._geometry_width, app._geometry_height) == app._collapsed_size()
app._accept_poll([], 123, "测试聊天", "synthetic-preview", app.totals)
assert app.root.winfo_viewable()
assert app._morph_state == "collapsed"
assert app.smooth is None
app._toggle_visible()
assert not app.root.winfo_viewable()
app._toggle_visible()
assert app.root.winfo_viewable()
assert app.smooth is None
assert (app._geometry_width, app._geometry_height) == app._collapsed_size()
app.thread_id = "synthetic-preview"
app.totals = ts.Totals(164_200_000, 411_500, 160_200_000, 0, time.time(), 1)
app._render()
app._toggle_metric_exact("total")
assert any(app.canvas.itemcget(item, "text") == ts.format_token_count(
           app.totals.input+app.totals.output) for item in app.canvas.find_withtag("metric"))

print(f"HUD regression passed; captures: {collapsed}, {expanded}")
print(f"Real pointer enter/exit: {enter_ms}ms / {exit_ms}ms")
print(f"Exit event latency: {leave_ms}ms; collapse morph: {collapse_ms}ms")
print(f"Morph frame interval: {app._morph_frame_interval}ms")
app.quit()

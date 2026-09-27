"""Regression for the HUD's position among ordinary Windows windows."""
import time

import token_strip as ts
from smooth_capsule import SmoothCapsule, user32, WS_POPUP


def stack_order():
    handles = []
    # GetTopWindow accepts NULL to start at the desktop's top-level windows.
    ts.u32.GetTopWindow.argtypes = [ts.HWND]
    ts.u32.GetTopWindow.restype = ts.HWND
    hwnd = ts.u32.GetTopWindow(None)
    while hwnd:
        handles.append(int(hwnd))
        hwnd = ts.u32.GetWindow(hwnd, 2)
    return handles


def raise_window(hwnd):
    assert ts.u32.SetWindowPos(hwnd, 0, 0, 0, 0, 0,
                               ts.SWP_NOMOVE | ts.SWP_NOSIZE |
                               ts.SWP_SHOWWINDOW)


app = ts.TokenStrip(visual_only=True)
native_windows = []
try:
    for title in ("HUD owner probe", "Other application probe"):
        hwnd = user32.CreateWindowExW(ts.WS_EX_TOOLWINDOW,
                                     "STATIC", title, WS_POPUP, 100, 100, 600, 400,
                                     None, None, None, None)
        assert hwnd
        native_windows.append(int(hwnd))
        raise_window(hwnd)
    owner, other = native_windows
    app._geometry_controller(position=(180, 140))
    app.root.deiconify()
    app.root.update()
    app.hwnd = int(ts.u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT))
    style = ts._get_window_long(app.hwnd, ts.GWL_EXSTYLE)
    ts._set_window_long(app.hwnd, ts.GWL_EXSTYLE,
                        style | ts.WS_EX_NOACTIVATE | ts.WS_EX_TOOLWINDOW)
    app.target_hwnd = owner
    raise_window(other)
    app._place_z_order()
    app.smooth = SmoothCapsule(app.hwnd)
    app._geometry_controller(capture=True)
    overlay = int(app.smooth.overlay)
    app._pointer_inside_hud = lambda: False
    app._watch_pointer = lambda: None
    foreground = ts.u32.GetForegroundWindow()

    def check(label, covered=True):
        order = stack_order()
        names = {other: "other", overlay: "overlay", app.hwnd: "input", owner: "owner"}
        visible_order = [names[h] for h in order if h in names]
        assert order.index(overlay) < order.index(app.hwnd) < order.index(owner), (
            label, "HUD must remain above its owner", visible_order)
        if covered:
            assert order.index(other) < order.index(overlay), (
                label, "HUD raised itself or its owner above another window", visible_order)
            assert ts.u32.GetForegroundWindow() == foreground, (label, "HUD stole focus")
        assert not any(ts._get_window_long(h, ts.GWL_EXSTYLE) & 8 for h in names), (
            label, "a window became globally topmost")
        assert ts.u32.GetWindow(app.hwnd, 4) == owner
        assert ts.u32.GetWindow(overlay, 4) == app.hwnd
        print("PASS", label, visible_order, flush=True)

    check("initial binding preserves covering window")
    raise_window(other)
    foreground = ts.u32.GetForegroundWindow()
    check("other window covers HUD")
    for _ in range(3):
        app._geometry_controller(capture=True)
    check("content refresh preserves covering window")
    app._geometry_controller(position=(190, 150), capture=False)
    check("position follow preserves covering window")
    app.smooth.hide()
    app._geometry_controller(capture=True)
    check("overlay redisplay preserves covering window")
    app.motion_allowed = True
    for expanded in (True, False):
        app._start_morph(expanded)
        deadline = time.perf_counter() + .5
        while time.perf_counter() < deadline:
            app.root.update()
            order = stack_order()
            assert order.index(other) < order.index(overlay), (
                "animation raised the HUD above another window")
            time.sleep(.001)
        check("expand" if expanded else "collapse")
    app._toggle_visible()
    assert not app.root.winfo_viewable() and not app.smooth.visible
    app._toggle_visible()
    assert app.root.winfo_viewable() and app.smooth.visible
    check("tray hide/show preserves covering window")
    user32.ShowWindow(owner, 6)
    app._accept_poll([], owner, "", None, ts.Totals())
    assert not ts.u32.IsWindowVisible(overlay)
    user32.ShowWindow(owner, 4)
    raise_window(other)
    foreground = ts.u32.GetForegroundWindow()
    app._accept_poll([], owner, "", None, ts.Totals())
    assert app.root.winfo_viewable() and ts.u32.IsWindowVisible(overlay)
    check("owner minimize/restore preserves covering window")
    raise_window(owner)
    check("return to owner restores HUD", covered=False)
    assert stack_order().index(overlay) < stack_order().index(other)
finally:
    app.quit()
    for hwnd in native_windows:
        user32.DestroyWindow(hwnd)

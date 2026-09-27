"""Interactive desktop regression for the per-pixel-alpha capsule implementation."""
import ctypes
from ctypes import wintypes
from pathlib import Path
import time
from PIL import Image, ImageGrab
import tkinter as tk
import token_strip as ts
from smooth_capsule import SmoothCapsule
from token_strip import TokenStrip, Totals

out = Path(__file__).with_name("docs")
out.mkdir(exist_ok=True)
u32 = ts.u32
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.SetCursorPos.restype = wintypes.BOOL
u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.WindowFromPoint.restype = wintypes.HWND
u32.GetLayeredWindowAttributes.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.COLORREF),
                                           ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(wintypes.DWORD)]
u32.GetLayeredWindowAttributes.restype = wintypes.BOOL
u32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
u32.mouse_event.restype = None

app = TokenStrip(visual_only=True)
app.motion_allowed = False
app.root.withdraw()
backdrop = tk.Toplevel(app.root)
backdrop.overrideredirect(True)
backdrop.attributes("-topmost", True)
backdrop.geometry("560x340+150+140")
backdrop.update_idletasks()
backdrop_hwnd = int(u32.GetAncestor(backdrop.winfo_id(), ts.GA_ROOT) or backdrop.winfo_id())
ts._set_window_long(backdrop_hwnd, ts.GWLP_HWNDPARENT, 0)
app.thread_id = "synthetic-preview"
app.totals = Totals(1_234_567, 12_345, 1_000_000, 0, time.time(), 1)
app._render()
app.root.geometry("228x60+300+300")
app.root.attributes("-topmost", True)
app.root.deiconify()
backdrop.lift()
app.root.lift()
app.root.update()
app.hwnd = int(u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
app._apply_capsule_region(228, 60)
app.root.update()
u32.SetWindowPos(backdrop_hwnd, wintypes.HWND(-1), 150, 140, 560, 340, ts.SWP_SHOWWINDOW)
u32.SetWindowPos(app.hwnd, wintypes.HWND(-1), 0, 0, 0, 0,
                 ts.SWP_NOMOVE | ts.SWP_NOSIZE | ts.SWP_NOACTIVATE | ts.SWP_SHOWWINDOW)
capsule = SmoothCapsule(app.hwnd)
app.smooth = capsule
capsule.update(300, 300, 228, 60)
app.root.update()

light = ImageGrab.grab(bbox=(300, 300, 528, 360)).convert("RGB")
light_path = out / "edge-aa-light.png"
light.save(light_path)
assert light.size == (228, 60)
assert max(abs(a-b) for a, b in zip(light.getpixel((0, 0)), (244, 245, 248))) < 12, "light backdrop is not behind the capsule"
edge_points = [(x, y) for y in range(30) for x in range(30)
               if 0 < round(255 * min(1, max(0, min((x+.5)/30, (29-x+.5)/30,
                                                     (y+.5)/30, (29-y+.5)/30)))) < 255]

# The screenshot must include fractional coverage against the known pale backdrop.
partial = sum(1 for y in range(30) for x in range(30)
              if all(80 < c < 240 for c in light.getpixel((x, y))))
assert partial >= 25, f"AA fringe missing in desktop capture: {partial}"
assert sum(1 for p in light.getdata() if max(p) < 100) > 5_000, "light screenshot lacks the capsule body"
assert sum(1 for p in light.getdata() if min(p) > 180) > 100, "light screenshot lacks readable text"

# Click overlay center through to the alpha=1 Tk hit surface, then drag and verify
# both the native input window and the visible overlay follow the same coordinates.
u32.SetCursorPos(414, 330)
print(f"window-at-click=0x{int(u32.WindowFromPoint(wintypes.POINT(414,330)) or 0):x} root=0x{app.hwnd:x} overlay=0x{int(capsule.overlay):x}")
u32.mouse_event(0x0002, 0, 0, 0, 0)
time.sleep(.05)
u32.mouse_event(0x0004, 0, 0, 0, 0)
app.root.update()
print(f"details_pinned={app.details_pinned} root_alpha={ts._get_window_long(app.hwnd,ts.GWL_EXSTYLE):x}")
assert app.details_pinned, "click through the AA overlay failed"
app._close_detail()
app.root.update()
u32.SetCursorPos(414, 330)
u32.mouse_event(0x0002, 0, 0, 0, 0)
u32.SetCursorPos(449, 344)
time.sleep(.06)
app.root.update()
u32.mouse_event(0x0004, 0, 0, 0, 0)
app.root.update()
assert app.root.winfo_x() >= 330 and app.root.winfo_y() >= 310, "drag did not move the Tk capsule"
assert capsule.visible, "overlay was not kept visible during drag"
overlay_rect = ts.rect(int(capsule.overlay))
root_rect = ts.rect(app.hwnd)
assert overlay_rect == root_rect, f"drag desynchronized overlay and input window: {overlay_rect} != {root_rect}"

# The release snap must synchronously recapture/move the AA layer as well.
prior_rect, prior_monitor, prior_save = ts.rect, ts.monitor_rect, ts.save_config
ts.rect = lambda h: (200, 160, 1400, 1000) if int(h) == 123 else prior_rect(h)
ts.monitor_rect = lambda _h: (0, 0, 1920, 1080)
ts.save_config = lambda _value: None
app.target_hwnd = 123
app.root.geometry("228x60+500+172")
app.root.update_idletasks()
capsule.update(500, 172, 228, 60)
app.drag = (0, 0, 500, 172)
app._drag_moved = True
app._drag_end(type("Mouse", (), {"x_root": 550, "y_root": 180})())
print(f"safe-snap edge={app.edge} root={prior_rect(app.hwnd)} overlay={prior_rect(capsule.overlay)}")
assert app.edge == "safe" and prior_rect(capsule.overlay) == prior_rect(app.hwnd), "safe-titlebar snap left overlay behind"
app.root.geometry("228x60+600+90")
app.root.update_idletasks()
capsule.update(600, 90, 228, 60)
app.drag = (0, 0, 600, 90)
app._drag_moved = True
app._drag_end(type("Mouse", (), {"x_root": 700, "y_root": 100})())
print(f"top-snap edge={app.edge} root={prior_rect(app.hwnd)} overlay={prior_rect(capsule.overlay)}")
assert app.edge == "top" and prior_rect(capsule.overlay) == prior_rect(app.hwnd), "outer-edge snap left overlay behind"
ts.rect, ts.monitor_rect, ts.save_config = prior_rect, prior_monitor, prior_save
app.target_hwnd = None

# A failed renderer can restore a normally visible Tk capsule (alpha 255) before
# hiding the overlay; a subsequent successful update re-enables alpha 1.
assert capsule.show_fallback(), "fallback failed to restore Tk visibility"
alpha = ctypes.c_ubyte()
assert u32.GetLayeredWindowAttributes(app.hwnd, None, ctypes.byref(alpha), None) and alpha.value == 255
assert not capsule.visible
capsule.update(600, 90, 228, 60)
assert u32.GetLayeredWindowAttributes(app.hwnd, None, ctypes.byref(alpha), None) and alpha.value == 1

capsule.hide()
app.root.withdraw()
assert not capsule.visible and not app.root.winfo_viewable(), "hide did not hide both windows"
app.root.geometry("228x60+300+300")
app.root.deiconify()
app.root.update()
capsule.update(300, 300, 228, 60)
app.root.update()
assert capsule.visible and app.root.winfo_viewable(), "show did not restore both windows"

# Re-render over a dark background as a separate compositing check.
backdrop.configure(bg="#252a33")
backdrop.geometry("560x340+150+140")
backdrop.lift()
app.root.lift()
app.root.update()
u32.SetWindowPos(backdrop_hwnd, wintypes.HWND(-1), 150, 140, 560, 340, ts.SWP_SHOWWINDOW)
u32.SetWindowPos(app.hwnd, wintypes.HWND(-1), 0, 0, 0, 0,
                 ts.SWP_NOMOVE | ts.SWP_NOSIZE | ts.SWP_NOACTIVATE | ts.SWP_SHOWWINDOW)
capsule.update(300, 300, 228, 60)
app.root.update()
dark = ImageGrab.grab(bbox=(300, 300, 528, 360)).convert("RGB")
dark_path = out / "edge-aa-dark.png"
dark.save(dark_path)
assert dark.size == (228, 60)
assert max(abs(a-b) for a, b in zip(dark.getpixel((0, 0)), (37, 42, 51))) < 12, "dark backdrop is not behind the capsule"
assert sum(1 for p in dark.getdata() if max(p) < 100) > 5_000, "dark screenshot lacks the capsule body"
assert sum(1 for p in dark.getdata() if min(p) > 180) > 100, "dark screenshot lacks readable text"

print(f"PASS smooth edge capture partial={partial}; click details; drag; hide/show; light={light_path}; dark={dark_path}")
capsule.close()
backdrop.destroy()
app.quit()

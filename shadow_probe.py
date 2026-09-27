"""Capture the layered HUD against a light backdrop to inspect compositor shadow."""
from pathlib import Path
import tkinter as tk
from PIL import ImageGrab

import token_strip as ts
from smooth_capsule import SmoothCapsule, user32 as smooth_user32, WS_EX_LAYERED, LWA_ALPHA

app = ts.TokenStrip(visual_only=True)
app.motion_allowed = False
backdrop = tk.Toplevel(app.root)
backdrop.overrideredirect(True)
backdrop.configure(bg="#eef3f8")
backdrop.geometry("500x300+180+180")
app.root.geometry("320x42+300+300")
app.root.attributes("-topmost", True)
app.root.deiconify()
backdrop.lower(app.root)
app.root.update()
app.hwnd = int(ts.u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
ts.disable_drop_shadow(app.hwnd)
ts._set_window_long(app.hwnd, ts.GWL_EXSTYLE,
                    ts._get_window_long(app.hwnd, ts.GWL_EXSTYLE) | WS_EX_LAYERED | 0x00200000)
smooth_user32.SetLayeredWindowAttributes(app.hwnd, 0, 1, LWA_ALPHA)
policy = ts.ctypes.c_int(ts.DWMNCRP_DISABLED)
ts.dwmapi.DwmSetWindowAttribute(app.hwnd, ts.DWMWA_NCRENDERING_POLICY,
                                ts.ctypes.byref(policy), ts.ctypes.sizeof(policy))
corner = ts.ctypes.c_int(2)
print("corner_hr", ts.dwmapi.DwmSetWindowAttribute(
    app.hwnd, ts.DWMWA_WINDOW_CORNER_PREFERENCE,
    ts.ctypes.byref(corner), ts.ctypes.sizeof(corner)))
print("policy_after_corner", ts.dwmapi.DwmSetWindowAttribute(
    app.hwnd, ts.DWMWA_NCRENDERING_POLICY,
    ts.ctypes.byref(policy), ts.ctypes.sizeof(policy)))
class AccentPolicy(ts.ctypes.Structure):
    _fields_ = [("state", ts.ctypes.c_int), ("flags", ts.ctypes.c_int),
                ("color", ts.ctypes.c_int), ("animation", ts.ctypes.c_int)]
class WindowCompositionAttributeData(ts.ctypes.Structure):
    _fields_ = [("attribute", ts.ctypes.c_int), ("data", ts.ctypes.c_void_p),
                ("size", ts.ctypes.c_size_t)]
set_composition = ts.ctypes.WinDLL("user32").SetWindowCompositionAttribute
set_composition.argtypes = [ts.HWND, ts.ctypes.POINTER(WindowCompositionAttributeData)]
set_composition.restype = ts.ctypes.c_int
accent = AccentPolicy(2, 0, 0, 0)  # ACCENT_ENABLE_TRANSPARENTGRADIENT
composition = WindowCompositionAttributeData(19, ts.ctypes.cast(ts.ctypes.byref(accent), ts.ctypes.c_void_p),
                                             ts.ctypes.sizeof(accent))
print("accent", set_composition(app.hwnd, ts.ctypes.byref(composition)))
app.smooth = SmoothCapsule(app.hwnd, input_surface=False)
app.smooth.enable_input_surface()
smooth_user32.SetLayeredWindowAttributes(app.hwnd, 0, 255, LWA_ALPHA)
app.thread_id = "shadow-probe"
app.totals = ts.Totals(164_200_000, 411_500, 160_200_000, 0, 1, 1)
app._render()
app.smooth.hide()
# Intentionally leave the root unregioned to inspect DWM's own corner clip.
root_only = ImageGrab.grab(bbox=(270, 270, 650, 370)).convert("RGB")
root_only.save(Path(__file__).with_name("ui-review") / "hud-shadow-root-only.png")
app._geometry_controller(capture=True)
app.root.update()
image = ImageGrab.grab(bbox=(270, 270, 650, 370)).convert("RGB")
out = Path(__file__).with_name("ui-review") / "hud-shadow-probe.png"
image.save(out)
print(out)
app.quit()
try:
    backdrop.destroy()
except tk.TclError:
    pass

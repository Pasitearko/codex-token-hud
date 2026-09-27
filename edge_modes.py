"""Compare region, DPI-boundary, frame, and DWM edge paths on the same pale backing."""
from pathlib import Path
import tkinter as tk
from PIL import ImageGrab
from PIL import Image, ImageDraw
import token_strip as ts
from token_strip import TokenStrip

OUT = Path(__file__).with_name("ui-review")
OUT.mkdir(exist_ok=True)
app = TokenStrip(visual_only=True)
app.root.withdraw()
backdrop = tk.Toplevel(app.root)
backdrop.overrideredirect(True)
backdrop.attributes("-topmost", True)
backdrop.configure(bg="#f4f5f8")
backdrop.geometry("500x300+180+180")
app.root.geometry("228x60+300+300")
app.root.attributes("-topmost", True)
app.root.deiconify()
app.root.update()
app.hwnd = int(ts.u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
app.root.lift()
app.root.update()
style = ts._get_window_long(app.hwnd, ts.GWL_EXSTYLE)
ts._set_window_long(app.hwnd, ts.GWL_EXSTYLE, style | ts.WS_EX_TOOLWINDOW | ts.WS_EX_NOACTIVATE)
pref = ts.wintypes.DWORD(2)
ts.dwmapi.DwmSetWindowAttribute.argtypes = [ts.HWND, ts.wintypes.DWORD, ts.ctypes.c_void_p, ts.wintypes.DWORD]
ts.dwmapi.DwmSetWindowAttribute.restype = ts.ctypes.c_long
ts.u32.SetWindowRgn(app.hwnd, 0, True)


def capture(name):
    app.root.update()
    image = ImageGrab.grab(bbox=(app.root.winfo_rootx(), app.root.winfo_rooty(),
                                app.root.winfo_rootx()+app.root.winfo_width(),
                                app.root.winfo_rooty()+app.root.winfo_height())).convert("RGB")
    partial = sum(1 for y in range(30) for x in range(30)
                  if all(90 < c < 230 for c in image.getpixel((x, y))))
    image.save(OUT / f"edge-{name}.png")
    corner = image.getpixel((0, 0))
    dark_in_corner = sum(1 for y in range(30) for x in range(30)
                         if max(image.getpixel((x, y))) < 90)
    print(f"mode={name} antialias_corner_pixels={partial} dark_corner_pixels={dark_in_corner} top_left={corner}")


app._apply_capsule_region(228, 60)
capture("region")
app.frame.configure(highlightthickness=0, bd=0)
app._apply_capsule_region(228, 60)
capture("region-frame0")
ts.u32.SetWindowRgn(app.hwnd, 0, True)
rgn = ts.gdi32.CreateRoundRectRgn(0, 0, 228, 60, 60, 60)
ts.u32.SetWindowRgn(app.hwnd, rgn, True)
capture("region-exact")
ts.u32.SetWindowRgn(app.hwnd, 0, True)
ts.dwmapi.DwmSetWindowAttribute(app.hwnd, 33, ts.ctypes.byref(pref), ts.ctypes.sizeof(pref))
capture("dwm-round")
ts.u32.SetWindowRgn(app.hwnd, 0, True)
pref = ts.wintypes.DWORD(0)
ts.dwmapi.DwmSetWindowAttribute(app.hwnd, 33, ts.ctypes.byref(pref), ts.ctypes.sizeof(pref))
capture("rectangle")

# Supersampled antialiased reference validates the pixel classifier.
scale = 4
reference = Image.new("RGBA", (228*scale, 60*scale), (244, 245, 248, 255))
draw = ImageDraw.Draw(reference)
draw.rounded_rectangle((0, 0, 228*scale-1, 60*scale-1), radius=30*scale,
                       fill=(26, 32, 43, 255), outline=(57, 68, 86, 255), width=scale)
reference = reference.resize((228, 60), Image.Resampling.LANCZOS).convert("RGB")
partial = sum(1 for y in range(30) for x in range(30)
              if all(90 < c < 230 for c in reference.getpixel((x, y))))
reference.save(OUT / "edge-aa-reference.png")
print(f"mode=antialiased-reference antialias_corner_pixels={partial}")
backdrop.destroy()
app.quit()

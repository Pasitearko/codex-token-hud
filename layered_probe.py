"""Prototype per-pixel-alpha display over Tk to test smooth capsule edges."""
import ctypes
from ctypes import wintypes
from pathlib import Path
import time
from PIL import Image, ImageDraw, ImageGrab
import tkinter as tk
import token_strip as ts
from token_strip import TokenStrip, Totals

u32, gdi = ts.u32, ts.gdi32
u32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                ts.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p]
u32.CreateWindowExW.restype = ts.HWND
u32.DestroyWindow.argtypes = [ts.HWND]
u32.DestroyWindow.restype = wintypes.BOOL
u32.ShowWindow.argtypes = [ts.HWND, ctypes.c_int]
u32.ShowWindow.restype = wintypes.BOOL
u32.SetLayeredWindowAttributes.argtypes = [ts.HWND, wintypes.COLORREF, ctypes.c_ubyte, wintypes.DWORD]
u32.SetLayeredWindowAttributes.restype = wintypes.BOOL
u32.PrintWindow.argtypes = [ts.HWND, wintypes.HDC, wintypes.UINT]
u32.PrintWindow.restype = wintypes.BOOL
gdi.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi.CreateCompatibleDC.restype = wintypes.HDC
gdi.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
                                 ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
gdi.CreateDIBSection.restype = wintypes.HBITMAP
gdi.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
gdi.SelectObject.restype = wintypes.HANDLE
gdi.DeleteDC.argtypes = [wintypes.HDC]
gdi.DeleteDC.restype = wintypes.BOOL
gdi.DeleteObject.argtypes = [wintypes.HANDLE]
gdi.DeleteObject.restype = wintypes.BOOL
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.SetCursorPos.restype = wintypes.BOOL
u32.WindowFromPoint.argtypes = [wintypes.POINT]
u32.WindowFromPoint.restype = ts.HWND
u32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
u32.mouse_event.restype = None


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [("BlendOp", ctypes.c_ubyte), ("BlendFlags", ctypes.c_ubyte),
                ("SourceConstantAlpha", ctypes.c_ubyte), ("AlphaFormat", ctypes.c_ubyte)]


app = TokenStrip(visual_only=True)
app.motion_allowed = False
app.root.withdraw()
backdrop = tk.Toplevel(app.root)
backdrop.overrideredirect(True)
backdrop.attributes("-topmost", True)
backdrop.configure(bg="#f4f5f8")
backdrop.geometry("500x300+180+180")
app.thread_id = "synthetic-preview"
app.totals = Totals(1_234_567, 12_345, 1_000_000, 0, time.time(), 1)
app._render()
app.root.geometry("228x60+300+300")
app.root.attributes("-topmost", True)
app.root.deiconify()
app.root.update()
app.hwnd = int(u32.GetAncestor(app.root.winfo_id(), ts.GA_ROOT) or app.root.winfo_id())
app._apply_capsule_region(228, 60)
app.root.update()

# Keep the bottom Tk window as a real input surface, but hide its aliased region
# almost completely. The per-pixel-alpha owner window above it supplies all visible pixels.
_set_window_long = ts._set_window_long
_set_window_long(app.hwnd, ts.GWL_EXSTYLE, _get_exstyle := (int(u32.GetWindowLongPtrW(app.hwnd, ts.GWL_EXSTYLE)) | 0x00080000))
assert u32.SetLayeredWindowAttributes(app.hwnd, 0, 1, 0x2), ctypes.get_last_error()

exstyle = 0x00080000 | ts.WS_EX_NOACTIVATE | ts.WS_EX_TOOLWINDOW | 0x20  # WS_EX_LAYERED and transparent hit-test
overlay = u32.CreateWindowExW(exstyle, "STATIC", "", 0x80000000 | 0x10000000,
                              300, 300, 228, 60, ts.HWND(app.hwnd), None, None, None)
assert overlay, ctypes.get_last_error()
u32.ShowWindow(overlay, 4)  # SW_SHOWNOACTIVATE

width, height = 228, 60
bmi = BITMAPINFO()
bmi.bmiHeader = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), width, -height, 1, 32,
                                0, width*height*4, 0, 0, 0, 0)
bits = ctypes.c_void_p()
hdc = gdi.CreateCompatibleDC(0)
bitmap = gdi.CreateDIBSection(hdc, ctypes.byref(bmi), 0, ctypes.byref(bits), None, 0)
assert hdc and bitmap and bits.value
old_bitmap = gdi.SelectObject(hdc, bitmap)
assert u32.PrintWindow(app.hwnd, hdc, 2), "PrintWindow failed to capture Tk capsule"
raw = ctypes.string_at(bits.value, width*height*4)
rgba = Image.frombytes("RGBA", (width, height), raw, "raw", "BGRA")
scale = 4
mask = Image.new("L", (width*scale, height*scale), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, width*scale-1, height*scale-1),
                                        radius=min(width, height)*scale//2, fill=255)
mask = mask.resize((width, height), Image.Resampling.LANCZOS)
background_rgb = (244, 245, 248)
partial_points = [(x, y) for y in range(height) for x in range(width) if 0 < mask.getpixel((x, y)) < 255]
# PrintWindow returns black for pixels cut away by SetWindowRgn. Those pixels
# must become the capsule fill before applying the antialiased mask.
pixels = rgba.load()
for x, y in partial_points:
    r, g, b, _ = pixels[x, y]
    if max(r, g, b) < 12:
        nearest = None
        for radius in range(1, 12):
            candidates = []
            for yy in range(max(0, y-radius), min(height, y+radius+1)):
                for xx in range(max(0, x-radius), min(width, x+radius+1)):
                    if mask.getpixel((xx, yy)) == 255:
                        rr, gg, bb, _ = pixels[xx, yy]
                        if max(rr, gg, bb) >= 12:
                            candidates.append(((xx-x)**2 + (yy-y)**2, (rr, gg, bb, 255)))
            if candidates:
                nearest = min(candidates, key=lambda item: item[0])[1]
                break
        pixels[x, y] = nearest or (26, 32, 43, 255)
ideal_rgba = rgba.copy()
ideal_rgba.putalpha(mask)
ideal = Image.alpha_composite(Image.new("RGBA", (width, height), (*background_rgb, 255)), ideal_rgba).convert("RGB")
rgba.putalpha(mask)
# UpdateLayeredWindow requires premultiplied BGRA pixels.
rgba.putdata([(r*a//255, g*a//255, b*a//255, a) for r, g, b, a in rgba.getdata()])
ctypes.memmove(bits.value, rgba.tobytes("raw", "BGRA"), width*height*4)
u32.UpdateLayeredWindow.argtypes = [ts.HWND, wintypes.HDC, ctypes.c_void_p, ctypes.c_void_p,
                                   wintypes.HDC, ctypes.c_void_p, wintypes.DWORD,
                                   ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD]
u32.UpdateLayeredWindow.restype = wintypes.BOOL
pt = wintypes.POINT(300, 300)
size = wintypes.SIZE(width, height)
src = wintypes.POINT(0, 0)
blend = BLENDFUNCTION(0, 0, 255, 1)
ok = u32.UpdateLayeredWindow(overlay, 0, ctypes.byref(pt), ctypes.byref(size), hdc,
                             ctypes.byref(src), 0, ctypes.byref(blend), 2)
assert ok, ctypes.get_last_error()
time.sleep(.2)
shot = ImageGrab.grab(bbox=(300, 300, 300+width, 300+height)).convert("RGB")
path = Path(__file__).with_name("ui-review") / "edge-layered-prototype.png"
shot.save(path)
partial = sum(1 for y in range(30) for x in range(30)
              if all(90 < c < 230 for c in shot.getpixel((x, y))))
print(f"UpdateLayeredWindow PrintWindow prototype partial-corner-pixels={partial} screenshot={path}")
assert partial > 0, "per-pixel alpha overlay did not produce antialiased coverage"
errors = [max(abs(a-b) for a, b in zip(shot.getpixel(p), ideal.getpixel(p))) for p in partial_points]
print(f"base-alpha=1 edge-pixels={len(errors)} mean-max-channel-error={sum(errors)/max(1,len(errors)):.2f} max-channel-error={max(errors, default=0)} sample-2-18={shot.getpixel((2,18))} ideal-2-18={ideal.getpixel((2,18))}")
assert sum(errors)/max(1,len(errors)) < 1.5 and max(errors, default=0) < 8, "bottom input surface still leaks visible aliased edge pixels"

pt_test = wintypes.POINT(414, 330)
print(f"window-at-click=0x{int(u32.WindowFromPoint(pt_test) or 0):x} root=0x{app.hwnd:x} overlay=0x{int(overlay):x}")
u32.SetCursorPos(414, 330)
u32.mouse_event(0x0002, 0, 0, 0, 0)
time.sleep(.05)
u32.mouse_event(0x0004, 0, 0, 0, 0)
time.sleep(.1)
app.root.update()
print(f"click-through details_pinned={app.details_pinned} tip_visible={app.tip.winfo_viewable()} root_alpha=1 overlay_style=0x{ts._get_window_long(overlay, ts.GWL_EXSTYLE):x}")

u32.DestroyWindow(overlay)
gdi.SelectObject(hdc, old_bitmap)
gdi.DeleteObject(bitmap)
gdi.DeleteDC(hdc)
backdrop.destroy()
app.quit()

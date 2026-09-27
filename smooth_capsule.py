"""Per-pixel-alpha capsule overlay with a nearly invisible Tk input surface."""
from __future__ import annotations

import ctypes
from ctypes import wintypes

from PIL import Image, ImageChops, ImageColor, ImageDraw, ImageFilter

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
HWND = wintypes.HWND
GWL_EXSTYLE = -20
GCL_STYLE = -26
CS_DROPSHADOW = 0x00020000
GWLP_HWNDPARENT = -8
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_POPUP = 0x80000000
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_HIDEWINDOW = 0x0080
SWP_NOZORDER = 0x0004
SWP_NOOWNERZORDER = 0x0200
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_FRAMECHANGED = 0x0020
GW_HWNDPREV = 3
ULW_ALPHA = 2
LWA_ALPHA = 2

_get_long = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
_set_long = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
_get_long.argtypes = [HWND, ctypes.c_int]
_get_long.restype = ctypes.c_ssize_t
_set_long.argtypes = [HWND, ctypes.c_int, ctypes.c_ssize_t]
_set_long.restype = ctypes.c_ssize_t
_get_class_long = getattr(user32, "GetClassLongPtrW", user32.GetClassLongW)
_set_class_long = getattr(user32, "SetClassLongPtrW", user32.SetClassLongW)
_get_class_long.argtypes = [HWND, ctypes.c_int]
_get_class_long.restype = ctypes.c_size_t
_set_class_long.argtypes = [HWND, ctypes.c_int, ctypes.c_size_t]
_set_class_long.restype = ctypes.c_size_t
user32.SetLayeredWindowAttributes.argtypes = [HWND, wintypes.COLORREF, ctypes.c_ubyte, wintypes.DWORD]
user32.SetLayeredWindowAttributes.restype = wintypes.BOOL
user32.GetLayeredWindowAttributes.argtypes = [HWND, ctypes.POINTER(wintypes.COLORREF),
                                               ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(wintypes.DWORD)]
user32.GetLayeredWindowAttributes.restype = wintypes.BOOL
user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                    wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                    HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p]
user32.CreateWindowExW.restype = HWND
user32.DestroyWindow.argtypes = [HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.SetWindowPos.argtypes = [HWND, HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL
user32.GetWindow.argtypes = [HWND, wintypes.UINT]
user32.GetWindow.restype = HWND
user32.SetWindowLongPtrW = _set_long
user32.PrintWindow.argtypes = [HWND, wintypes.HDC, wintypes.UINT]
user32.PrintWindow.restype = wintypes.BOOL
user32.UpdateLayeredWindow.argtypes = [HWND, wintypes.HDC, ctypes.c_void_p, ctypes.c_void_p,
                                       wintypes.HDC, ctypes.c_void_p, wintypes.DWORD,
                                       ctypes.POINTER(ctypes.c_ubyte * 4), wintypes.DWORD]
user32.UpdateLayeredWindow.restype = wintypes.BOOL
dwmapi.DwmSetWindowAttribute.argtypes = [HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long

gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT,
                                   ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
gdi32.CreateDIBSection.restype = wintypes.HBITMAP
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HANDLE]
gdi32.SelectObject.restype = wintypes.HANDLE
gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
gdi32.DeleteObject.restype = wintypes.BOOL


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


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


class SmoothCapsule:
    """A noninteractive per-pixel AA overlay owned by the Tk window."""

    # Area sampling avoids the ringing that Lanczos introduces around a
    # binary rounded-rectangle mask. Eight samples per logical pixel are
    # enough for the small HUD while keeping the morph inside its frame
    # budget.
    MASK_SCALE = 8

    def __init__(self, hwnd: int, fill=(26, 32, 43), border=(57, 68, 86),
                 input_surface=True):
        self.hwnd = HWND(hwnd)
        self.original_style = _get_long(self.hwnd, GWL_EXSTYLE)
        self.fill = fill
        self.border = border
        self.input_surface = bool(input_surface)
        self.surface_enabled = False
        self.overlay = user32.CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW,
            "STATIC", "", WS_POPUP, 0, 0, 1, 1, self.hwnd, None, None, None)
        if not self.overlay:
            raise ctypes.WinError(ctypes.get_last_error())
        class_style = int(_get_class_long(self.overlay, GCL_STYLE))
        if class_style & CS_DROPSHADOW:
            _set_class_long(self.overlay, GCL_STYLE, class_style & ~CS_DROPSHADOW)
        # Layered popups can inherit a compositor shadow. Disable the
        # non-client effect so the alpha edge is the only visible boundary.
        policy = ctypes.c_int(1)  # DWMNCRP_DISABLED
        dwmapi.DwmSetWindowAttribute(self.overlay, 2, ctypes.byref(policy), ctypes.sizeof(policy))
        self.dc = None
        self.bitmap = None
        self.old_bitmap = None
        self.bits = None
        self.size = (0, 0)
        self.bitmap_capacity = (0, 0)
        self.visible = False
        self._mask_cache = {}
        self.mask_scale = self.MASK_SCALE
        self.motion_blur = 0.35
        self.last_image = None
        try:
            if self.input_surface:
                self._ensure_input_surface()
        except Exception:
            _set_long(self.hwnd, GWL_EXSTYLE, self.original_style)
            user32.DestroyWindow(self.overlay)
            self.overlay = None
            raise

    def _ensure_input_surface(self):
        style = _get_long(self.hwnd, GWL_EXSTYLE)
        if not style & WS_EX_LAYERED:
            _set_long(self.hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
        if not user32.SetLayeredWindowAttributes(self.hwnd, 0, 1, LWA_ALPHA):
            raise ctypes.WinError(ctypes.get_last_error())
        self.surface_enabled = True

    def enable_input_surface(self):
        """Keep Tk available for hit testing while hiding its visual rectangle."""
        self._ensure_input_surface()

    def _ensure_bitmap(self, width: int, height: int):
        capacity_w, capacity_h = self.bitmap_capacity
        if (self.dc and self.bitmap and capacity_w >= width and capacity_h >= height):
            return
        self._release_bitmap()
        bmi = BITMAPINFO()
        bmi.bmiHeader = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), width, -height,
                                         1, 32, 0, width * height * 4, 0, 0, 0, 0)
        self.dc = gdi32.CreateCompatibleDC(0)
        self.bits = ctypes.c_void_p()
        self.bitmap = gdi32.CreateDIBSection(self.dc, ctypes.byref(bmi), 0,
                                              ctypes.byref(self.bits), None, 0)
        if not self.dc or not self.bitmap or not self.bits.value:
            self._release_bitmap()
            raise ctypes.WinError(ctypes.get_last_error())
        self.old_bitmap = gdi32.SelectObject(self.dc, self.bitmap)
        self.size = (width, height)
        self.bitmap_capacity = (width, height)

    def _release_bitmap(self):
        if self.dc and self.old_bitmap:
            gdi32.SelectObject(self.dc, self.old_bitmap)
        if self.bitmap:
            gdi32.DeleteObject(self.bitmap)
        if self.dc:
            gdi32.DeleteDC(self.dc)
        self.dc = self.bitmap = self.old_bitmap = self.bits = None
        self.size = (0, 0)
        self.bitmap_capacity = (0, 0)

    def _present(self, x, y, width, height):
        dest = POINT(int(x), int(y))
        size = SIZE(int(width), int(height))
        source = POINT(0, 0)
        blend = BLENDFUNCTION(0, 0, 255, 1)
        if not user32.UpdateLayeredWindow(self.overlay, 0, ctypes.byref(dest), ctypes.byref(size),
                                          self.dc, ctypes.byref(source), 0,
                                          ctypes.cast(ctypes.byref(blend), ctypes.POINTER(ctypes.c_ubyte * 4)),
                                          ULW_ALPHA):
            raise ctypes.WinError(ctypes.get_last_error())
        if not self.visible:
            # SetWindowPos inserts AFTER its reference. Use the window above
            # the input surface so an unrelated foreground window stays above us.
            previous = user32.GetWindow(self.hwnd, GW_HWNDPREV)
            flags = SWP_NOACTIVATE | SWP_SHOWWINDOW | SWP_NOOWNERZORDER
            if previous == self.overlay:
                flags |= SWP_NOZORDER
            if not user32.SetWindowPos(self.overlay, previous, int(x), int(y), int(width), int(height),
                                       flags):
                raise ctypes.WinError(ctypes.get_last_error())
        self.visible = True

    def _capture_image(self, width: int, height: int):
        # The Tk HUD is a borderless client-only popup. PW_CLIENTONLY keeps
        # PrintWindow on the fast client path; PW_RENDERFULLCONTENT adds a
        # several-millisecond compositor round-trip on every morph frame and
        # is unnecessary for this window.
        if not user32.PrintWindow(self.hwnd, self.dc, 1):
            raise ctypes.WinError(ctypes.get_last_error())
        # The DIB is reserved at the largest morph size, but only the visible
        # rows are needed for this frame. Reading the unused tail made every
        # collapsed frame copy the full expanded bitmap.
        capacity_w, _ = self.bitmap_capacity
        raw = ctypes.string_at(self.bits.value, capacity_w * height * 4)
        return (Image.frombytes("RGBA", (capacity_w, height), raw, "raw", "BGRA")
                .crop((0, 0, width, height)).convert("RGB"))

    def _compose_image(self, image, width: int, height: int, radius: float):
        scale = self.mask_scale
        # Quantize only to the supersample grid. Keeping subpixel radii makes
        # the corner evolve continuously while keeping the cache bounded.
        radius = round(float(radius) * scale) / scale
        mask_key = (width, height, radius)
        cached_masks = self._mask_cache.get(mask_key)
        if cached_masks is None:
            large_size = (width * scale, height * scale)
            large_mask = Image.new("L", large_size, 0)
            ImageDraw.Draw(large_mask).rounded_rectangle(
                (0, 0, large_size[0] - 1, large_size[1] - 1),
                radius=radius * scale, fill=255)
            # BOX is an area average. Unlike Lanczos it cannot create a
            # bright/dark halo or make alpha step backwards along an edge.
            if scale == 1:
                # A small Gaussian fringe is a fast coverage approximation for
                # motion frames. It touches only the alpha mask; text pixels
                # remain from the current full-resolution Canvas capture.
                mask = large_mask.filter(ImageFilter.GaussianBlur(self.motion_blur))
            else:
                mask = large_mask.resize((width, height), Image.Resampling.BOX)
            inner = Image.new("L", large_size, 0)
            inset = scale
            ImageDraw.Draw(inner).rounded_rectangle(
                (inset, inset, large_size[0] - 1 - inset, large_size[1] - 1 - inset),
                radius=max(0, (radius-1) * scale), fill=255)
            if scale == 1:
                inner_mask = inner.filter(ImageFilter.GaussianBlur(self.motion_blur))
            else:
                inner_mask = inner.resize((width, height), Image.Resampling.BOX)
            border_mask = ImageChops.subtract(mask, inner_mask)
            cached_masks = (mask, ImageChops.invert(mask), border_mask)
            if len(self._mask_cache) >= 64:
                self._mask_cache.pop(next(iter(self._mask_cache)))
            self._mask_cache[mask_key] = cached_masks
        mask, outside_mask, border_mask = cached_masks
        # _capture_image returns a new RGB image, so the fill and border can be
        # applied in place without another full-size copy.
        image.paste(self.fill, (0, 0, width, height), outside_mask)
        image.paste(self.border, (0, 0, width, height), border_mask)
        red, green, blue = image.split()
        # UpdateLayeredWindow expects premultiplied BGRA.
        return Image.merge("RGBA", tuple(ImageChops.multiply(channel, mask) for channel in
                                          (red, green, blue)) + (mask,))

    def set_mask_scale(self, scale: int):
        """Select motion/static edge quality without changing content pixels."""
        scale = max(1, int(scale))
        if scale != self.mask_scale:
            self.mask_scale = scale
            self._mask_cache.clear()

    def _write_image(self, image):
        width, height = image.size
        self._ensure_bitmap(width, height)
        capacity_w, capacity_h = self.bitmap_capacity
        # DIB rows use the capacity stride while the current image can be
        # smaller during Morph. Pad once and copy contiguously; row-by-row
        # ctypes calls are noticeably expensive at animation frequency.
        if (width, height) != (capacity_w, capacity_h):
            source = image.tobytes("raw", "BGRA")
            row_bytes = width * 4
            stride = capacity_w * 4
            # Rows beyond the presented height are outside UpdateLayeredWindow
            # and never need to be cleared.
            padded = bytearray(stride * height)
            for row in range(height):
                start = row * row_bytes
                padded[row * stride:row * stride + row_bytes] = source[start:start + row_bytes]
            raw = padded
        else:
            raw = image.tobytes("raw", "BGRA")
        if isinstance(raw, bytearray):
            raw_view = (ctypes.c_ubyte * len(raw)).from_buffer(raw)
            ctypes.memmove(self.bits.value, raw_view, len(raw))
        else:
            ctypes.memmove(self.bits.value, raw, len(raw))

    def present_cached(self, x: int, y: int, width: int, height: int):
        """Present the previous composed frame at a nearby size.

        Morph captures every other geometry tick. The intervening resize is
        only a few pixels, so this avoids a full PrintWindow/Pillow compose
        while keeping the visual surface in lockstep with the input window.
        """
        if self.last_image is None:
            return False
        width, height = max(2, int(width)), max(2, int(height))
        image = self.last_image.resize((width, height), Image.Resampling.BILINEAR)
        self._write_image(image)
        self._present(int(x), int(y), width, height)
        return True

    def _smooth_image(self, width: int, height: int, radius: float):
        image = self._capture_image(width, height)
        composed = self._compose_image(image, width, height, radius)
        # Keep the last real Canvas capture as the cache anchor. Cached resize
        # frames must never become the source for another cached resize.
        self.last_image = composed
        self._write_image(composed)

    def capture_frame(self, width: int, height: int, radius: float):
        """Capture and compose a frame without presenting it."""
        width, height = max(2, int(width)), max(2, int(height))
        radius = max(1.0, min(float(radius), width / 2, height / 2))
        self._ensure_bitmap(width, height)
        return self._compose_image(self._capture_image(width, height), width, height, radius)

    def present_transition(self, x: int, y: int, width: int, height: int,
                           start_image, end_image, progress: float):
        progress = max(0.0, min(1.0, float(progress)))
        # These are already premultiplied RGBA images; linear interpolation
        # avoids the overshoot that bicubic can introduce at transparent edges.
        start = start_image.resize((int(width), int(height)), Image.Resampling.BILINEAR)
        end = end_image.resize((int(width), int(height)), Image.Resampling.BILINEAR)
        self._write_image(Image.blend(start, end, progress))
        self._present(x, y, int(width), int(height))

    def update(self, x: int, y: int, width: int, height: int, radius: float | None = None,
               border=None, background=None, preserve_input=False):
        width, height = max(2, int(width)), max(2, int(height))
        radius = max(1.0, min(float(radius if radius is not None else min(width, height) / 2),
                               width / 2, height / 2))
        if border is not None:
            self.border = ImageColor.getrgb(border) if isinstance(border, str) else tuple(border)
        if background is not None:
            self.fill = ImageColor.getrgb(background) if isinstance(background, str) else tuple(background)
        if self.input_surface and not preserve_input:
            self._ensure_input_surface()
        self._ensure_bitmap(width, height)
        self._smooth_image(width, height, radius)
        self._present(x, y, width, height)

    def move(self, x: int, y: int, width: int, height: int):
        if self.visible:
            if not user32.SetWindowPos(self.overlay, 0, int(x), int(y), int(width), int(height),
                                       SWP_NOZORDER | SWP_NOACTIVATE | SWP_SHOWWINDOW):
                raise ctypes.WinError(ctypes.get_last_error())

    def hide(self):
        if self.visible:
            user32.ShowWindow(self.overlay, 0)
            self.visible = False

    def show_fallback(self):
        """Restore the normal Tk surface if the alpha overlay cannot be refreshed."""
        if not self.input_surface and not self.surface_enabled:
            self.hide()
            return True
        # Keep the AA layer over the Tk surface while restoring opacity, then
        # hide it. This prevents a transparent gap during morph startup.
        if user32.SetLayeredWindowAttributes(self.hwnd, 0, 255, LWA_ALPHA):
            self.hide()
            return True
        style = _get_long(self.hwnd, GWL_EXSTYLE)
        if _set_long(self.hwnd, GWL_EXSTYLE, style & ~WS_EX_LAYERED):
            user32.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0,
                                SWP_NOACTIVATE | SWP_NOZORDER | SWP_NOSIZE |
                                SWP_NOMOVE | SWP_FRAMECHANGED)
            return True
        # Keep the overlay visible if a readable input-surface fallback failed.
        return False

    def restore_input_opacity(self):
        if not self.surface_enabled:
            return True
        return bool(user32.SetLayeredWindowAttributes(self.hwnd, 0, 255, LWA_ALPHA))

    def close(self):
        self.restore_input_opacity()
        if self.surface_enabled:
            _set_long(self.hwnd, GWL_EXSTYLE, self.original_style)
            self.surface_enabled = False
        self._release_bitmap()
        if self.overlay:
            user32.DestroyWindow(self.overlay)
            self.overlay = None

from __future__ import annotations

import ctypes
import datetime as dt
import json
import math
import os
import queue
import sqlite3
import sys
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk
from smooth_capsule import SmoothCapsule

APP_NAME = "Codex Token Strip"
POLL_SECONDS = 1.0
TOKEN_FIELDS = ("input_tokens", "output_tokens", "cached_input_tokens", "cache_write_input_tokens")
DWMWA_CLOAKED = 14
DWMWA_NCRENDERING_POLICY = 2
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMNCRP_DISABLED = 1
GWL_EXSTYLE = -20
GWLP_HWNDPARENT = -8
GCL_STYLE = -26
CS_DROPSHADOW = 0x00020000
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
GW_HWNDPREV = 3
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_HIDEWINDOW = 0x0080
SWP_NOZORDER = 0x0004
SWP_NOOWNERZORDER = 0x0200
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_FRAMECHANGED = 0x0020
MONITOR_DEFAULTTONEAREST = 2
GA_ROOT = 2

u32 = ctypes.WinDLL("user32", use_last_error=True)
dwmapi = ctypes.WinDLL("dwmapi", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
winmm = ctypes.WinDLL("winmm", use_last_error=True)
HWND = wintypes.HWND
BOOL = wintypes.BOOL
LPARAM = wintypes.LPARAM
u32.IsWindow.argtypes = [HWND]; u32.IsWindow.restype = BOOL
u32.IsWindowVisible.argtypes = [HWND]; u32.IsWindowVisible.restype = BOOL
u32.IsIconic.argtypes = [HWND]; u32.IsIconic.restype = BOOL
u32.GetForegroundWindow.argtypes = []; u32.GetForegroundWindow.restype = HWND
u32.GetWindow.argtypes = [HWND, wintypes.UINT]; u32.GetWindow.restype = HWND
u32.GetWindowTextLengthW.argtypes = [HWND]; u32.GetWindowTextLengthW.restype = ctypes.c_int
u32.GetWindowTextW.argtypes = [HWND, wintypes.LPWSTR, ctypes.c_int]; u32.GetWindowTextW.restype = ctypes.c_int
u32.GetClassNameW.argtypes = [HWND, wintypes.LPWSTR, ctypes.c_int]; u32.GetClassNameW.restype = ctypes.c_int
u32.EnumWindows.argtypes = [ctypes.c_void_p, LPARAM]; u32.EnumWindows.restype = BOOL
u32.GetWindowRect.argtypes = [HWND, ctypes.POINTER(wintypes.RECT)]; u32.GetWindowRect.restype = BOOL
u32.GetClientRect.argtypes = [HWND, ctypes.POINTER(wintypes.RECT)]; u32.GetClientRect.restype = BOOL
u32.ClientToScreen.argtypes = [HWND, ctypes.POINTER(wintypes.POINT)]; u32.ClientToScreen.restype = BOOL
u32.MonitorFromWindow.argtypes = [HWND, wintypes.DWORD]; u32.MonitorFromWindow.restype = HWND
u32.GetMonitorInfoW.argtypes = [HWND, ctypes.c_void_p]; u32.GetMonitorInfoW.restype = BOOL
u32.GetDpiForWindow.argtypes = [HWND]; u32.GetDpiForWindow.restype = wintypes.UINT
u32.SetWindowPos.argtypes = [HWND, HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]; u32.SetWindowPos.restype = BOOL
u32.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(wintypes.DWORD)]; u32.GetWindowThreadProcessId.restype = wintypes.DWORD
u32.SystemParametersInfoW.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
u32.SystemParametersInfoW.restype = BOOL
u32.GetAncestor.argtypes = [HWND, wintypes.UINT]; u32.GetAncestor.restype = HWND
kernel32.OpenProcess.argtypes = [wintypes.DWORD, BOOL, wintypes.DWORD]; kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]; kernel32.QueryFullProcessImageNameW.restype = BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]; kernel32.CloseHandle.restype = BOOL
_set_window_long = getattr(u32, "SetWindowLongPtrW", u32.SetWindowLongW)
_get_window_long = getattr(u32, "GetWindowLongPtrW", u32.GetWindowLongW)
_set_window_long.argtypes = [HWND, ctypes.c_int, ctypes.c_ssize_t]; _set_window_long.restype = ctypes.c_ssize_t
_get_window_long.argtypes = [HWND, ctypes.c_int]; _get_window_long.restype = ctypes.c_ssize_t
_get_class_long = getattr(u32, "GetClassLongPtrW", u32.GetClassLongW)
_set_class_long = getattr(u32, "SetClassLongPtrW", u32.SetClassLongW)
_get_class_long.argtypes = [HWND, ctypes.c_int]; _get_class_long.restype = ctypes.c_size_t
_set_class_long.argtypes = [HWND, ctypes.c_int, ctypes.c_size_t]; _set_class_long.restype = ctypes.c_size_t
kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, BOOL, wintypes.LPCWSTR]; kernel32.CreateMutexW.restype = wintypes.HANDLE
kernel32.GetLastError.argtypes = []; kernel32.GetLastError.restype = wintypes.DWORD
gdi32.CreateRoundRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
gdi32.CreateRoundRectRgn.restype = wintypes.HRGN
gdi32.DeleteObject.argtypes = [wintypes.HANDLE]; gdi32.DeleteObject.restype = BOOL
u32.SetWindowRgn.argtypes = [HWND, wintypes.HRGN, BOOL]; u32.SetWindowRgn.restype = ctypes.c_int
winmm.timeBeginPeriod.argtypes = [wintypes.UINT]; winmm.timeBeginPeriod.restype = wintypes.UINT
winmm.timeEndPeriod.argtypes = [wintypes.UINT]; winmm.timeEndPeriod.restype = wintypes.UINT
dwmapi.DwmGetWindowAttribute.argtypes = [HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
dwmapi.DwmGetWindowAttribute.restype = ctypes.c_long
dwmapi.DwmSetWindowAttribute.argtypes = [HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
dwmapi.DwmSetWindowAttribute.restype = ctypes.c_long


def codex_dir() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))


def db_path() -> Path:
    return codex_dir() / "sqlite" / "codex-dev.db"


def get_catalog() -> list[tuple[str, str, float]]:
    path = db_path()
    if not path.exists():
        return []
    try:
        con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=0.4)
        try:
            return [(str(tid), str(title), float(updated or 0)) for tid, title, updated in con.execute(
                "SELECT thread_id, display_title, source_updated_at FROM local_thread_catalog WHERE trim(display_title) <> ''"
            )]
        finally:
            con.close()
    except (sqlite3.Error, OSError, ValueError):
        return []


def enum_windows() -> list[int]:
    result: list[int] = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    @callback_type
    def visit(hwnd, _):
        if u32.IsWindowVisible(hwnd):
            # The Windows Codex desktop client currently ships its main process as ChatGPT.exe.
            if _process_name(hwnd).casefold() in {"codex.exe", "chatgpt.exe"}:
                result.append(int(hwnd))
        return True
    u32.EnumWindows(visit, 0)
    return result


def _process_name(hwnd: int) -> str:
    pid = wintypes.DWORD()
    u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    proc = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not proc:
        return ""
    try:
        size = wintypes.DWORD(32768)
        buf = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(proc, 0, buf, ctypes.byref(size)):
            return Path(buf.value).name
    finally:
        kernel32.CloseHandle(proc)
    return ""


def uia_page_title(hwnd: int, catalog: list[tuple[str, str, float]]) -> str:
    """Read the renderer's UIA document/page name that uniquely maps to a chat."""
    try:
        from comtypes import CoInitialize, CoUninitialize
        from comtypes.client import CreateObject, GetModule
        CoInitialize()
        try:
            module = GetModule("UIAutomationCore.dll")
            automation = CreateObject("{FF48DBA4-60EF-4201-AA87-54103EEF594E}", interface=module.IUIAutomation)
            root = automation.ElementFromHandle(hwnd)
            # Chromium exposes its page surface as UIA Document (50030).
            cond = automation.CreatePropertyCondition(30003, 50030)  # UIA_ControlTypePropertyId
            items = root.FindAll(4, cond)  # TreeScope_Descendants
            known_titles = {name.strip() for _, name, *_ in catalog}
            page_titles = set()
            for i in range(items.Length):
                el = items.GetElement(i)
                name = str(el.CurrentName or "").strip()
                if name and len(name) <= 512:
                    page_titles.add(name)
            known_page_titles = page_titles & known_titles
            candidates = known_page_titles if known_page_titles else page_titles
            return next(iter(candidates)) if len(candidates) == 1 else ""
        finally:
            CoUninitialize()
    except Exception:
        return ""


def window_title(hwnd: int) -> str:
    n = u32.GetWindowTextLengthW(hwnd)
    if n <= 0:
        return ""
    b = ctypes.create_unicode_buffer(n + 1)
    u32.GetWindowTextW(hwnd, b, n + 1)
    return b.value.strip()


def is_minimized_or_cloaked(hwnd: int) -> bool:
    if not u32.IsWindow(hwnd) or u32.IsIconic(hwnd):
        return True
    cloaked = wintypes.DWORD()
    try:
        hr = dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, ctypes.byref(cloaked), ctypes.sizeof(cloaked))
        # If DWM cannot establish the cloak state, fail closed and hide the strip.
        return True if hr < 0 else bool(cloaked.value)
    except Exception:
        return True


def rect(hwnd: int) -> tuple[int, int, int, int]:
    r = wintypes.RECT()
    u32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def monitor_rect(hwnd: int) -> tuple[int, int, int, int]:
    class MONITORINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT), ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]
    mon = u32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(mi)
    u32.GetMonitorInfoW(mon, ctypes.byref(mi))
    r = mi.rcMonitor
    return r.left, r.top, r.right, r.bottom


def get_dpi(hwnd: int) -> int:
    try:
        return int(u32.GetDpiForWindow(hwnd)) or 96
    except Exception:
        return 96


def discover_thread_for_title(title: str, catalog: list[tuple[str, str, float]]) -> str | None:
    title = title.strip()
    if not title:
        return None
    # Electron window captions are commonly "Chat — Codex" or "Chat - Codex".
    matches = {tid for tid, name, *_ in catalog if name.strip() == title}
    return next(iter(matches)) if len(matches) == 1 else None


def session_files() -> list[Path]:
    root = codex_dir() / "sessions"
    try:
        return list(root.rglob("*.jsonl"))
    except OSError:
        return []


@dataclass
class Totals:
    input: int = 0
    output: int = 0
    cached: int = 0
    cache_write: int = 0
    last_update: float = 0.0
    logs: int = 0


TOKEN_UNITS = ("万", "亿", "兆", "京", "垓", "秭", "穰", "沟", "涧", "正", "载", "极")


def format_token_count(value: int) -> str:
    """Uniform compact HUD units: integer, W, M, then B; truncate to one decimal."""
    value = max(0, int(value))
    if value < 10_000:
        return format_integer_exact(value)
    if value < 1_000_000:
        divisor, suffix = 10_000, "W"
    elif value < 1_000_000_000:
        divisor, suffix = 1_000_000, "M"
    else:
        divisor, suffix = 1_000_000_000, "B"
    whole, remainder = divmod(value, divisor)
    tenth = remainder * 10 // divisor
    leading = format_scientific_tokens(whole) if whole >= 10**12 else str(whole)
    return f"{leading}{'.' + str(tenth) if tenth else ''}{suffix}"


def format_scientific_tokens(value: int) -> str:
    value = max(0, int(value))
    if value == 0:
        return "0"
    digits = int((value.bit_length() - 1) * math.log10(2)) + 1
    if value >= 10 ** digits:
        digits += 1
    elif value < 10 ** (digits - 1):
        digits -= 1
    lead = value // (10 ** max(0, digits - 2))
    text = str(lead)
    return f"{text[0]}{'.' + text[1:].rstrip('0') if len(text) > 1 and text[1:].rstrip('0') else ''}e{digits - 1}"


def format_integer_exact(value: int) -> str:
    """Thousands grouping without Python's large-int-to-string digit limit."""
    value = max(0, int(value))
    if value < 1_000:
        return str(value)
    groups = []
    while value >= 1_000:
        value, group = divmod(value, 1_000)
        groups.append(group)
    return str(value) + "".join(f",{part:03d}" for part in reversed(groups))


def format_millions(value: int) -> str:
    """Compatibility name for the same W/M/B notation used throughout the HUD."""
    return format_token_count(value)


def format_hit_rate(cached: int, input_tokens: int, decimals: int = 1) -> str:
    rate = (cached / input_tokens * 100) if input_tokens else 0.0
    if decimals == 1 and abs(rate - 100) < 0.05:
        return "100%"
    return f"{rate:.{decimals}f}%"


def rounded_rect_points(x1: float, y1: float, x2: float, y2: float, radius: float):
    radius = max(0, min(radius, (x2-x1)/2, (y2-y1)/2))
    return [x1+radius,y1, x2-radius,y1, x2,y1, x2,y1+radius,
            x2,y2-radius, x2,y2, x2-radius,y2, x1+radius,y2,
            x1,y2, x1,y2-radius, x1,y1+radius, x1,y1]


def client_area_animations_enabled() -> bool:
    try:
        enabled = wintypes.BOOL()
        ok = u32.SystemParametersInfoW(0x1042, 0, ctypes.byref(enabled), 0)  # SPI_GETCLIENTAREAANIMATION
        return bool(ok and enabled.value)
    except Exception:
        return False


def disable_drop_shadow(hwnd: int) -> None:
    """Remove the class-level shadow so alpha edges are not haloed by DWM."""
    try:
        style = int(_get_class_long(HWND(hwnd), GCL_STYLE))
        if style & CS_DROPSHADOW:
            _set_class_long(HWND(hwnd), GCL_STYLE, style & ~CS_DROPSHADOW)
    except (OSError, ctypes.ArgumentError):
        pass


_LOG_CACHE: dict[str, tuple[int, int, str | None, str | None, Totals]] = {}


def _read_log(path: Path) -> tuple[str | None, str | None, Totals]:
    key = str(path)
    try:
        st = path.stat()
        cached = _LOG_CACHE.get(key)
        if cached and cached[0] == st.st_mtime_ns and cached[1] == st.st_size:
            return cached[2], cached[3], cached[4]
    except OSError:
        return None, None, Totals()
    sid = parent = None
    values: dict[str, int] = {}
    snapshot_time = 0.0
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                if obj.get("type") == "session_meta":
                    payload = obj.get("payload", {})
                    sid = payload.get("id") or payload.get("session_id")
                    parent = payload.get("parent_thread_id")
                elif obj.get("type") == "event_msg":
                    payload = obj.get("payload", {})
                    if payload.get("type") != "token_count":
                        continue
                    info = payload.get("info", {})
                    usage = info.get("total_token_usage", {}) if isinstance(info, dict) else {}
                    if not isinstance(usage, dict):
                        continue
                    stamp = obj.get("timestamp")
                    if isinstance(stamp, str):
                        try:
                            snapshot_time = max(snapshot_time, dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp())
                        except ValueError:
                            pass
                    # token_count values are cumulative snapshots: keep the latest snapshot
                    # per field (max guards against stale/interleaved records).
                    for field in TOKEN_FIELDS:
                        value = usage.get(field)
                        if isinstance(value, int) and value >= 0:
                            values[field] = max(values.get(field, 0), value)
    except (OSError, PermissionError):
        pass
    totals = Totals(values.get("input_tokens", 0), values.get("output_tokens", 0),
                    values.get("cached_input_tokens", 0), values.get("cache_write_input_tokens", 0), snapshot_time, 1)
    _LOG_CACHE[key] = (st.st_mtime_ns, st.st_size, sid, parent, totals)
    return sid, parent, totals


def aggregate(thread_id: str) -> Totals:
    files = session_files()
    metadata = []
    target_ids = {thread_id}
    for path in files:
        sid, parent, _ = _read_log(path)
        metadata.append((path, sid, parent))
    # Include descendants to any depth. A child session becomes the parent id of
    # a nested helper session, as recorded in the JSONL session_meta event.
    changed = True
    while changed:
        changed = False
        for _, sid, parent in metadata:
            if parent in target_ids and sid and sid not in target_ids:
                target_ids.add(sid)
                changed = True
    result = Totals()
    for path, sid, parent in metadata:
        if sid in target_ids:
            _, _, t = _read_log(path)
            result.input += t.input
            result.output += t.output
            result.cached += t.cached
            result.cache_write += t.cache_write
            result.last_update = max(result.last_update, t.last_update)
            result.logs += 1
    return result


class RetainedHudCanvas:
    """Reuse Canvas items across morph frames to avoid full-scene churn."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.items = {}
        self.counts = {}
        self.used = set()
        self.changed = False

    def begin(self):
        self.counts.clear()
        self.used.clear()
        self.changed = False

    def end(self):
        for key in self.items.keys() - self.used:
            item, _, _ = self.items.pop(key)
            self.canvas.delete(item)
            self.changed = True

    def _item(self, kind, coords, options):
        index = self.counts.get(kind, 0)
        self.counts[kind] = index + 1
        key = kind, index
        self.used.add(key)
        coords = tuple(coords)
        if key not in self.items:
            item = getattr(self.canvas, f"create_{kind}")(*coords, **options)
            self.items[key] = item, coords, dict(options)
            self.changed = True
            return item
        item, previous_coords, previous_options = self.items[key]
        if coords != previous_coords:
            self.canvas.coords(item, *coords)
            self.changed = True
        changes = {name: value for name, value in options.items()
                   if previous_options.get(name) != value}
        for name in previous_options.keys() - options.keys():
            changes[name] = ""
        if changes:
            self.canvas.itemconfigure(item, **changes)
            self.changed = True
        self.items[key] = item, coords, dict(options)
        return item

    def create_polygon(self, *coords, **options):
        return self._item("polygon", coords, options)

    def create_oval(self, *coords, **options):
        return self._item("oval", coords, options)

    def create_text(self, *coords, **options):
        return self._item("text", coords, options)

    def create_line(self, *coords, **options):
        return self._item("line", coords, options)

class TokenStrip:
    def __init__(self, visual_only=False):
        self.visual_only = visual_only
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", False)
        self.root.configure(bg="#111318")
        self.root.withdraw()
        self.hwnd = None
        self.smooth = None
        self.target_hwnd: int | None = None
        self.thread_id: str | None = None
        self.pinned_thread: str | None = None
        self._pinned_title = ""
        self._pinned_hwnd = None
        self.catalog: list[tuple[str, str]] = []
        self.totals = Totals()
        self.last_active_codex: int | None = None
        self.drag = None
        self.vertical = False
        self.edge = "top"
        self._dock_along = .5
        self.polling = False
        self._worker_busy = False
        self._user_hidden = False
        self._exact_metric_keys = {"input": False, "cached": False, "output": False, "total": False}
        self._exact_offsets = {"input": 0, "cached": 0, "output": 0, "total": 0}
        self._selected_exact_key = None
        self._exact_values: list[int] = []
        self.details_pinned = False
        self._hide_after_id = None
        self._enter_after_id = None
        self._hover_watch_id = None
        self._morph_after_id = None
        self._morph_state = "collapsed"
        self._morph_generation = 0
        self._geometry_width = 320
        self._geometry_height = 42
        self._geometry_x = 0
        self._geometry_y = 0
        self._geometry_applied = None
        self._capsule_radius = 14.0
        self._morph_velocity = 0.0
        self._morph_frame_interval = 1000 / 170
        self._morph_visual_tick = 0
        self._morph_using_fallback = False
        self._morph_overlay_restore = False
        self._morph_transition_frames = None
        self._morph_transition_building = False
        self._morph_native_fixed = False
        self._dwm_rounding = False
        self._timer_resolution_active = False
        self._build_ui()
        self._geometry_controller(size=self._collapsed_size(), capture=False)
        self.motion_allowed = client_area_animations_enabled()
        if not self.visual_only:
            self.root.after(500, self._init_native)
            self.root.after(500, self._tick)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def _build_ui(self):
        self.palette = {
            "window": "#11151d", "surface": "#1a202b", "border": "#2d3542",
            "primary": "#f5f7fb", "secondary": "#9aa8bc", "accent": "#75d9bf",
            "muted": "#8b98aa", "divider": "#3a4555", "detail": "#171c25",
        }
        p = self.palette
        self.root.configure(bg=p["surface"])
        self.canvas = tk.Canvas(self.root, bg=p["surface"], bd=0, highlightthickness=0,
                                takefocus=True, cursor="arrow")
        self.canvas.pack(fill="both", expand=True)
        self._hud_items = RetainedHudCanvas(self.canvas)
        self._canvas_surface = p["surface"]
        self.font_caption = tkfont.Font(root=self.root, family="Segoe UI", size=9)
        self.font_detail_title = tkfont.Font(root=self.root, family="Segoe UI", size=10, weight="bold")
        self.font_grid_value = tkfont.Font(root=self.root, family="Consolas", size=12, weight="bold")
        self.font_morph_total = tkfont.Font(root=self.root, family="Consolas", size=15, weight="bold")
        self.font_morph_cache = tkfont.Font(root=self.root, family="Consolas", size=12, weight="bold")
        self._hit_text = "—"
        self._detail_metrics = [(label, "—", key) for label, key in
                                (("输入", "input"), ("缓存", "cached"),
                                 ("输出", "output"), ("总计", "total"))]
        self._detail_timestamp = ""
        self._detail_hint = "右键手选聊天"
        self._morph_progress = 0.0
        self._canvas_action = None
        self.canvas.bind("<Configure>", self._draw_hud)
        self.canvas.bind("<Enter>", self._show_detail)
        self.canvas.bind("<Leave>", self._schedule_hide_detail)
        self.canvas.bind("<ButtonPress-1>", self._canvas_press)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._canvas_release)
        self.canvas.bind("<Button-3>", self._menu)
        self.canvas.bind("<Return>", lambda _e: self._toggle_detail())
        self.canvas.bind("<space>", lambda _e: self._toggle_detail())
        self.canvas.bind("<Control-c>", lambda _e: self._copy_selected_exact())
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label="手动选择聊天…", command=self._choose_thread)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=self.quit)

    def _canvas_press(self, event):
        if event.x < 0 or event.y < 0 or event.x >= self._geometry_width or event.y >= self._geometry_height:
            return "break"
        self.canvas.focus_set()
        self._canvas_action = None
        progress = self._morph_progress
        if progress > .35:
            tags = set(self.canvas.gettags("current"))
            if "copy-all" in tags:
                self._canvas_action = "copy-all"
            elif "close" in tags:
                self._canvas_action = "close"
            else:
                for key in ("input", "cached", "output", "total"):
                    if f"scroll-left-{key}" in tags:
                        self._canvas_action = ("scroll", key, -1)
                        break
                    if f"scroll-right-{key}" in tags:
                        self._canvas_action = ("scroll", key, 1)
                        break
                    if f"metric-{key}" in tags:
                        self._canvas_action = ("toggle-metric", key)
                        break
                if self._canvas_action is None and event.y >= 38:
                    self._canvas_action = "detail"
        self._drag_start(event)
        return "break"

    def _canvas_release(self, event):
        action, self._canvas_action = self._canvas_action, None
        if self.drag and not self._drag_moved:
            sx, sy, _, _ = self.drag
            if abs(event.x_root-sx) + abs(event.y_root-sy) > 5:
                self._drag_move(event)
        if self._drag_moved:
            self._drag_end(event)
            return "break"
        if action is not None:
            self.drag = None
        if action == "copy-all":
            self._copy_exact_metrics()
        elif action == "close":
            self._close_detail()
        elif isinstance(action, tuple) and action[0] == "scroll":
            self._scroll_exact(action[1], action[2])
        elif isinstance(action, tuple) and action[0] == "toggle-metric":
            self._toggle_metric_exact(action[1])
        elif action == "detail":
            return "break"
        else:
            self._drag_end(event)
        return "break"

    def _blend(self, first, second, fraction):
        fraction = max(0.0, min(1.0, fraction))
        a = tuple(int(first[i:i+2], 16) for i in (1, 3, 5))
        b = tuple(int(second[i:i+2], 16) for i in (1, 3, 5))
        return "#" + "".join(f"{round(x+(y-x)*fraction):02x}" for x, y in zip(a, b))

    def _fit_canvas_text(self, text, font, max_width):
        if font.measure(text) <= max_width:
            return text
        mark = "…"
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if font.measure(text[:mid] + mark) <= max_width:
                lo = mid
            else:
                hi = mid - 1
        return text[:lo] + mark

    def _fit_token_count(self, value, font, max_width):
        text = format_token_count(value)
        if font.measure(text) <= max_width:
            return text
        value = max(0, int(value))
        if value >= 1_000_000_000:
            whole = value // 1_000_000_000
            return format_scientific_tokens(whole) + "B"
        if value >= 1_000_000:
            whole = value // 1_000_000
            return format_scientific_tokens(whole) + "M"
        if value >= 10_000:
            whole = value // 10_000
            return format_scientific_tokens(whole) + "W"
        return format_integer_exact(value)

    def _draw_hud(self, _event=None):
        if not hasattr(self, "canvas"):
            return
        c = self._hud_items
        c.begin()
        width, height = self._geometry_width, self._geometry_height
        progress = self._morph_progress
        surface = self.palette["surface"]
        border = self.palette["border"]
        if surface != self._canvas_surface:
            self.canvas.configure(bg=surface)
            self._canvas_surface = surface
            c.changed = True
        points = rounded_rect_points(1, 1, width-1, height-1, self._capsule_radius)
        c.create_polygon(points, smooth=True, splinesteps=16, fill=surface, outline=border,
                         width=1, tags=("surface",))
        self._draw_primary(c, width, progress)
        if progress >= .42:
            self._draw_details(c, width, height, progress, surface)
        c.end()
        return c.changed

    def _refresh_content(self):
        self._draw_hud()
        self.root.update_idletasks()
        self._sync_smooth_overlay(capture=True, radius=self._capsule_radius)

    @staticmethod
    def _lerp(start, end, fraction):
        return start + (end - start) * fraction

    @staticmethod
    def _phase(progress, start, end):
        return max(0.0, min(1.0, (progress - start) / (end - start)))

    def _draw_primary(self, canvas, width, progress):
        move = self._phase(progress, .38, .96)
        total_size = round(self._lerp(15, 20, move))
        cache_size = round(self._lerp(12, 20, move))
        if self.font_morph_total.cget("size") != total_size:
            self.font_morph_total.configure(size=total_size)
        if self.font_morph_cache.cget("size") != cache_size:
            self.font_morph_cache.configure(size=cache_size)
        dot_x = self._lerp(16, 20, move)
        canvas.create_oval(dot_x-3, 17, dot_x+3, 23,
                           fill=self.palette["accent"] if self.thread_id and self.totals.last_update else self.palette["muted"],
                           outline="")
        value_y = self._lerp(21, 67, move)
        label_y = self._lerp(21, 89, move)
        total = self.totals.input + self.totals.output
        if not self.thread_id or not self.totals.last_update:
            total_text = "—"
        elif progress >= .94 and self._exact_metric_keys["total"]:
            total_text = self._fit_canvas_text(format_integer_exact(total).replace(",", ""),
                                               self.font_morph_total, width/2-34)
        else:
            total_text = self._fit_token_count(total, self.font_morph_total,
                                               102 if move < .5 else width/2-34)
        canvas.create_text(self._lerp(27, 18, move), value_y, text=total_text,
                           fill=self.palette["primary"], font=self.font_morph_total,
                           anchor="w", tags=("metric-total",) if progress >= .94 else ("metric",))
        canvas.create_text(self._lerp(width-76, width-18, move), value_y, text=self._hit_text,
                           fill=self.palette["accent"], font=self.font_morph_cache, anchor="e")
        label_color = self._blend(self.palette["muted"], self.palette["secondary"], move)
        canvas.create_text(self._lerp(128, 18, move), label_y, text="Tokens",
                           fill=label_color, font=self.font_caption, anchor="w")
        canvas.create_text(self._lerp(width-16, width-18, move), label_y,
                           text="Cache Hit",
                           fill=label_color, font=self.font_caption, anchor="e")

    def _draw_details(self, canvas, width, height, progress, surface):
        expanded_width, expanded_height = self._expanded_size()
        status = "实时" if self.thread_id and self.totals.last_update else "等待" if self.thread_id else "未识别"
        canvas.create_text(32, 20, text="Codex 用量",
                           fill=self.palette["primary"],
                           font=self.font_detail_title, anchor="w")
        if progress >= .75:
            canvas.create_text(expanded_width-18, 20, text=status,
                               fill=self.palette["accent"] if status == "实时" else self.palette["muted"],
                               font=self.font_caption, anchor="e")
        if progress < .68:
            return
        if progress >= .82:
            canvas.create_line(18, 105, expanded_width-18, 105,
                               fill=self.palette["divider"])
        columns = (18, expanded_width/2+8)
        cell_w = expanded_width/2-32
        positions = ((columns[0], 118), (columns[1], 118),
                     (columns[0], 159), (columns[1], 159))
        shift = 4 if progress < .76 else 2 if progress < .84 else 0
        for index, (label, value, key) in enumerate(self._detail_metrics):
            x, y = positions[index]
            canvas.create_text(x, y+shift, text=label,
                               fill=self.palette["secondary"],
                               font=self.font_caption, anchor="w")
            value_color = self.palette["primary"]
            exact = self._exact_metric_keys[key]
            if exact:
                raw = value
                offset = min(self._exact_offsets[key], max(0, len(raw)-1))
                viewport = max(40, cell_w-24)
                lo, hi = 0, len(raw)-offset
                while lo < hi:
                    mid = (lo+hi+1)//2
                    if self.font_grid_value.measure(raw[offset:offset+mid]) <= viewport:
                        lo = mid
                    else:
                        hi = mid-1
                count = max(1, lo)
                shown = raw[offset:offset+count]
                if offset:
                    canvas.create_text(x, y+18+shift, text="‹", fill=self.palette["accent"],
                                       font=self.font_grid_value, anchor="w",
                                       tags=(f"scroll-left-{key}",))
                canvas.create_text(x + (12 if offset else 0), y+18+shift, text=shown,
                                   fill=value_color, font=self.font_grid_value, anchor="w",
                                   tags=(f"metric-{key}",))
                if offset+count < len(raw):
                    canvas.create_text(x+cell_w-7, y+18+shift, text="›", fill=self.palette["accent"],
                                       font=self.font_grid_value, anchor="e",
                                       tags=(f"scroll-right-{key}",))
            else:
                metric_index = ("input", "cached", "output", "total").index(key)
                token_value = self._exact_values[metric_index] if metric_index < len(self._exact_values) else 0
                shown = self._fit_token_count(token_value, self.font_grid_value, cell_w) if self._exact_values else "—"
                canvas.create_text(x, y+18+shift, text=shown, fill=value_color,
                                   font=self.font_grid_value, anchor="w", tags=(f"metric-{key}",))
        if progress >= .96:
            canvas.create_text(18, expanded_height-13, text=self._detail_timestamp or self._detail_hint,
                               fill=self.palette["muted"],
                               font=self.font_caption, anchor="w")
            if self._exact_values:
                canvas.create_text(expanded_width-18, expanded_height-13, text="复制",
                                   fill=self.palette["secondary"],
                                   font=self.font_caption, anchor="e", tags=("copy-all",))

    def _init_native(self):
        try:
            widget_hwnd = int(self.root.winfo_id())
            self.hwnd = int(u32.GetAncestor(widget_hwnd, GA_ROOT) or widget_hwnd)
            disable_drop_shadow(self.hwnd)
            style = _get_window_long(self.hwnd, GWL_EXSTYLE)
            _set_window_long(self.hwnd, GWL_EXSTYLE, style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
            # A named mutex makes the portable exe single-instance.
            self._mutex = kernel32.CreateMutexW(None, True, "Local\\CodexTokenStrip.Singleton")
            if kernel32.GetLastError() == 183:
                self.root.destroy()
                return
            self._start_tray()
            # The layered alpha edge supplies the visual contour; a DWM
            # drop shadow would read as a dark fringe around the HUD.
            no_nc = ctypes.c_int(DWMNCRP_DISABLED)
            dwmapi.DwmSetWindowAttribute(self.hwnd, DWMWA_NCRENDERING_POLICY,
                                         ctypes.byref(no_nc), ctypes.sizeof(no_nc))
            self.smooth = SmoothCapsule(self.hwnd,
                                        fill=(26, 32, 43), border=(45, 53, 66),
                                        input_surface=False)
            self.smooth.enable_input_surface()
            # The Tk window is an invisible rectangular input surface. Its
            # native corner clip stays disabled; SmoothCapsule owns the
            # visible per-pixel rounded edge.
            corner_preference = ctypes.c_int(1)  # DWMWCP_DONOTROUND
            self._dwm_rounding = (dwmapi.DwmSetWindowAttribute(
                self.hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(corner_preference),
                ctypes.sizeof(corner_preference)) == 0)
        except Exception:
            pass

    def _tick(self):
        if not self._worker_busy:
            self._worker_busy = True
            threading.Thread(target=self._background_poll, daemon=True).start()
        self.root.after(500, self._tick)

    def _background_poll(self):
        try:
            catalog = get_catalog()
            windows = enum_windows()
            fg = int(u32.GetForegroundWindow() or 0)
            previous = self.last_active_codex
            hwnd = fg if fg in windows else previous if previous in windows else next(
                (h for h in windows if not is_minimized_or_cloaked(h)), None)
            title = uia_page_title(hwnd, catalog) if hwnd else ""
            auto = discover_thread_for_title(title, catalog)
            pinned = self.pinned_thread
            if pinned and (self._pinned_hwnd != hwnd or self._pinned_title != title):
                pinned = None
            thread_id = pinned or auto
            totals = aggregate(thread_id) if thread_id else Totals()
            self.root.after(0, lambda: self._accept_poll(catalog, hwnd, title, thread_id, totals))
        except Exception:
            self.root.after(0, lambda: self._accept_poll([], None, "", None, Totals()))
        finally:
            self.root.after(0, lambda: setattr(self, "_worker_busy", False))

    def _accept_poll(self, catalog, hwnd, title, thread_id, totals):
        self.catalog = catalog
        previous_thread = self.thread_id
        previous_hwnd = self.target_hwnd
        if hwnd != self.target_hwnd:
            self.pinned_thread = None
        self.target_hwnd = hwnd
        self.last_active_codex = hwnd
        if self.pinned_thread and (self._pinned_hwnd != hwnd or self._pinned_title != title):
            self.pinned_thread = None
        self.thread_id = self.pinned_thread or thread_id
        if self.thread_id != previous_thread or hwnd != previous_hwnd:
            self.details_pinned = False
            self._cancel_morph_timers()
            self._morph_using_fallback = False
            self._morph_transition_frames = None
            self._morph_state = "collapsed"
            self._morph_progress = 0.0
            self._geometry_controller(size=self._collapsed_size(), capture=False)
            self._exact_metric_keys = {key: False for key in self._exact_metric_keys}
            self._exact_offsets = {key: 0 for key in self._exact_offsets}
        self.totals = totals if self.thread_id == thread_id else Totals()
        if hwnd and not is_minimized_or_cloaked(hwnd):
            self._render() if self.thread_id else self._render_unknown()
            showing = not self._user_hidden and not self.root.winfo_viewable()
            if showing:
                self._show_hud()
            self._follow_window(capture=showing)
        elif self.root.winfo_viewable():
            self.root.withdraw()
            if self.smooth: self.smooth.hide()
            self._cancel_morph_timers()
            self._morph_using_fallback = False
            self._morph_transition_frames = None
            self._morph_state = "collapsed"
            self._morph_progress = 0.0
            self._geometry_controller(size=self._collapsed_size(), capture=False)

    def _follow_window(self, capture=False):
        if not self.target_hwnd or self.drag:
            return
        cfg = load_config()
        self.edge = cfg.get("edge", "top")
        along = max(0.02, min(.98, cfg.get("along", .5)))
        self._dock_along = along
        position = self._dock_candidate(self.edge, along)
        if position is None:
            self.edge = "safe"
            position = self._dock_candidate("safe", along)
        # Following Codex owns only x/y. Morph owns the current width/height;
        # forcing collapsed size here would erase the expanded detail view on
        # the next polling tick.
        self._geometry_controller(position=position, capture=capture)

    def _safe_titlebar_size(self):
        """Return the full Codex titlebar footprint used by safe docking."""
        if not self.target_hwnd:
            return self._collapsed_size()
        left, top, right, _ = rect(self.target_hwnd)
        dpi = get_dpi(self.target_hwnd) / 96.0
        fallback_height = max(42, round(48 * dpi))
        titlebar_height = fallback_height
        try:
            client = wintypes.RECT()
            point = wintypes.POINT(0, 0)
            if (u32.GetClientRect(self.target_hwnd, ctypes.byref(client))
                    and u32.ClientToScreen(self.target_hwnd, ctypes.byref(point))):
                measured = int(point.y) - int(top)
                # Codex uses a custom client-side titlebar. When the client
                # origin is flush with the frame, use the platform-sized
                # titlebar fallback instead of collapsing to zero height.
                if round(36 * dpi) <= measured <= round(80 * dpi):
                    titlebar_height = measured
        except Exception:
            pass
        return max(280, right - left), titlebar_height

    def _dock_candidate(self, edge, along):
        left, top, right, bottom = rect(self.target_hwnd)
        ml, mt, mr, mb = monitor_rect(self.target_hwnd)
        dpi = get_dpi(self.target_hwnd) / 96.0
        width, height = self._collapsed_size()
        expanded_width, expanded_height = self._expanded_size()
        max_x, max_y = mr - expanded_width, mb - expanded_height
        if edge == "left":
            x = left - width - int(10*dpi)
            y = top + int(max(0, bottom-top-height) * along)
        elif edge == "right":
            x = right + int(10*dpi)
            y = top + int(max(0, bottom-top-height) * along)
        elif edge in ("top", "bottom"):
            x = left + int(max(0, right-left-width) * along)
            y = top-height-int(10*dpi) if edge == "top" else bottom+int(10*dpi)
        elif edge == "safe":
            # Keep the normal capsule size. Move it to the top edge of Codex
            # so the titlebar is covered without changing the HUD width.
            x = left + int(max(0, right-left-width) * along)
            y = top
            return max(ml, min(mr-width, x)), max(mt, min(mb-height, y))
        else:
            return None
        if x < ml or x > max_x or y < mt or y > max_y:
            return None
        return x, y

    def _collapsed_size(self):
        dpi = get_dpi(self.target_hwnd) / 96.0 if self.target_hwnd else 1.0
        return (max(280, round(320*dpi)), max(42, round(42*dpi)))

    def _collapsed_radius(self):
        """Use a restrained rounded-rectangle corner instead of a full pill."""
        dpi = get_dpi(self.target_hwnd) / 96.0 if self.target_hwnd else 1.0
        return max(8, round(16*dpi))

    def _expanded_size(self):
        dpi = get_dpi(self.target_hwnd) / 96.0 if self.target_hwnd else 1.0
        w, h = round(380*dpi), round(210*dpi)
        if self.target_hwnd:
            ml, mt, mr, mb = monitor_rect(self.target_hwnd)
        else:
            ml, mt, mr, mb = 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        return min(w, max(280, mr-ml-16)), min(h, max(150, mb-mt-16))

    def _expanded_radius(self):
        dpi = get_dpi(self.target_hwnd) / 96.0 if self.target_hwnd else 1.0
        return max(12, round(24*dpi))

    def _geometry_controller(self, position=None, size=None, radius=None, capture=False):
        """Sole writer of HUD geometry; callers provide position or size intent."""
        x, y = position if position is not None else (self._geometry_x, self._geometry_y)
        width, height = size if size is not None else (self._geometry_width, self._geometry_height)
        width, height = max(2, int(width)), max(2, int(height))
        if self.target_hwnd:
            ml, mt, mr, mb = monitor_rect(self.target_hwnd)
        else:
            ml, mt, mr, mb = 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        width = min(width, max(2, mr-ml-8))
        height = min(height, max(2, mb-mt-8))
        x = max(ml, min(mr-width, int(x)))
        y = max(mt, min(mb-height, int(y)))
        if radius is None:
            radius = self._lerp(self._collapsed_radius(),
                                self._expanded_radius(), self._morph_progress)
        radius = max(1.0, min(float(radius), width / 2, height / 2))
        old_radius = self._capsule_radius
        self._geometry_x, self._geometry_y = x, y
        self._geometry_width, self._geometry_height = width, height
        geometry = (x, y, width, height)
        changed = geometry != self._geometry_applied
        size_changed = self._geometry_applied is None or geometry[2:] != self._geometry_applied[2:]
        redraw = capture or size_changed or abs(radius - old_radius) >= 1 / 8
        self._capsule_radius = radius
        if size_changed or abs(radius - old_radius) >= 1 / 8:
            self._apply_capsule_region(width, height, radius)
        if changed and not (self._morph_native_fixed and
                            self._morph_state in ("expanding", "collapsing")):
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            self._geometry_applied = geometry
        paint_changed = self._draw_hud() if redraw else False
        if changed or paint_changed:
            # Canvas item updates are synchronous enough for the normal
            # geometry path. During Morph, forcing a full Tk idle flush on
            # every frame costs 5-8ms and becomes the dominant frame-time
            # source; the final frame still flushes before the next idle poll.
            if self._morph_state not in ("expanding", "collapsing"):
                self.root.update_idletasks()
        if self.hwnd:
            self._place_z_order()
            self._sync_smooth_overlay(capture=redraw, radius=radius)

    def _place_z_order(self):
        if not self.hwnd or not self.target_hwnd:
            return
        # Owner windows stay above their owner without entering the global topmost band.
        if getattr(self, "_owner_hwnd", None) != self.target_hwnd:
            _set_window_long(self.hwnd, GWLP_HWNDPARENT, self.target_hwnd)
            self._owner_hwnd = self.target_hwnd
            previous = u32.GetWindow(self.target_hwnd, GW_HWNDPREV)
            flags = SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER
            if previous == self.hwnd:
                flags |= SWP_NOZORDER
            u32.SetWindowPos(self.hwnd, previous, 0, 0, 0, 0, flags)

    def _show_hud(self):
        if self.hwnd:
            # Map the native window while preserving focus and both z-orders.
            self._place_z_order()
            u32.SetWindowPos(self.hwnd, 0, 0, 0, 0, 0,
                             SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE |
                             SWP_NOZORDER | SWP_NOOWNERZORDER | SWP_SHOWWINDOW)
        else:
            self.root.deiconify()

    def _sync_smooth_overlay(self, capture=False, radius=None):
        if not self.smooth or not self.root.winfo_viewable():
            return
        if self._morph_transition_building:
            return
        if self._morph_using_fallback:
            return
        if self.drag and self._drag_moved:
            capture = False
        try:
            if self._morph_native_fixed and self._morph_state in ("expanding", "collapsing"):
                left, top = self._geometry_x, self._geometry_y
                right, bottom = left + self._geometry_width, top + self._geometry_height
            else:
                left, top, right, bottom = rect(self.hwnd)
            if self._morph_transition_frames:
                start_image, end_image = self._morph_transition_frames
                self.smooth.present_transition(left, top, right-left, bottom-top,
                                               start_image, end_image, self._morph_progress)
                return
            if capture:
                progress = self._morph_progress
                background = self._blend(self.palette["surface"], self.palette["detail"], progress * .7)
                border = self._blend(self.palette["border"], "#364252", progress)
                preserve_input = self._morph_overlay_restore
                # Every presented frame is captured from the current Canvas.
                # Re-scaling the previous frame saves work but makes text
                # temporarily soft during the morph.
                self.smooth.update(left, top, right-left, bottom-top, radius=radius,
                                   background=background, border=border,
                                   preserve_input=preserve_input)
                if preserve_input:
                    self.smooth.restore_input_opacity()
            else:
                self.smooth.move(left, top, right-left, bottom-top)
        except Exception:
            # Keep the Tk surface as the 1/255-alpha input layer if a capture
            # fails. Leaving the last good overlay frame in place is preferable
            # to restoring the opaque Tk rectangle for one frame.
            try:
                self.smooth.enable_input_surface()
            except Exception:
                pass

    def _prepare_morph_transition(self, target, target_radius, target_progress):
        """Capture endpoint frames while the transparent input layer hides setup."""
        if not self.smooth or not self.smooth.surface_enabled or not self.root.winfo_viewable():
            return False
        current_size = (self._geometry_width, self._geometry_height)
        current_radius = self._capsule_radius
        current_progress = self._morph_progress
        current_state = self._morph_state
        self._morph_transition_building = True
        try:
            start_image = self.smooth.capture_frame(*current_size, current_radius)
            self._morph_progress = target_progress
            self._geometry_controller(size=target, radius=target_radius, capture=False)
            end_image = self.smooth.capture_frame(*target, target_radius)
            self._morph_progress = current_progress
            self._morph_state = current_state
            self._geometry_controller(size=current_size, radius=current_radius, capture=False)
            self._morph_transition_frames = (start_image, end_image)
            return True
        except Exception:
            self._morph_transition_frames = None
            return False
        finally:
            self._morph_transition_building = False

    def _apply_capsule_region(self, width, height, radius=None):
        # Keep the Tk input surface rectangular. A binary HRGN would create a
        # stepped edge and can expose a native corner during geometry changes.
        # SmoothCapsule is the only visual clip.
        return

    def _render(self):
        valid = bool(self.thread_id and self.totals.last_update)
        self._hit_text = format_hit_rate(self.totals.cached, self.totals.input) if valid else "—"
        self._update_detail_text()
        self._refresh_content()

    def _render_unknown(self):
        self.totals = Totals()
        self._render()

    def _update_detail_text(self):
        if not self.thread_id:
            self._exact_values = []
            timestamp = ""
            self._detail_metrics = [("输入", "—", "input"), ("缓存", "—", "cached"),
                                    ("输出", "—", "output"), ("总计", "—", "total")]
            self._detail_hint = "右键选择聊天"
        elif not self.totals.last_update:
            self._exact_values = []
            timestamp = ""
            self._detail_metrics = [("输入", "—", "input"), ("缓存", "—", "cached"),
                                    ("输出", "—", "output"), ("总计", "—", "total")]
            self._detail_hint = "等待用量更新"
        else:
            age = max(0, int(time.time() - self.totals.last_update))
            timestamp = f"{age} 秒前更新" if age < 60 else f"{age//60} 分钟前更新" if age < 3600 else "更新于 " + time.strftime("%H:%M", time.localtime(self.totals.last_update))
            total = self.totals.input + self.totals.output
            self._exact_values = [self.totals.input, self.totals.cached, self.totals.output, total]
            source = {"input": self.totals.input, "cached": self.totals.cached,
                      "output": self.totals.output, "total": total}
            self._detail_metrics = [(label, format_integer_exact(source[key]).replace(",", "") if self._exact_metric_keys[key]
                                     else format_token_count(source[key]), key)
                                    for label, key in (("输入", "input"), ("缓存", "cached"),
                                                       ("输出", "output"), ("总计", "total"))]
            self._detail_hint = "单击数值切换精确值"
        self._detail_timestamp = timestamp

    def _toggle_metric_exact(self, key):
        if key not in self._exact_metric_keys:
            return
        self._exact_metric_keys[key] = not self._exact_metric_keys[key]
        self._selected_exact_key = key if self._exact_metric_keys[key] else None
        self._exact_offsets[key] = 0
        self._update_detail_text()
        self._refresh_content()

    def _scroll_exact(self, key, direction):
        if not self._exact_metric_keys.get(key):
            return
        value = self._exact_values[("input", "cached", "output", "total").index(key)]
        raw = format_integer_exact(value).replace(",", "")
        self._exact_offsets[key] = max(0, min(len(raw)-1,
            self._exact_offsets[key] + direction * self._exact_page_chars(key)))
        self._refresh_content()

    def _exact_page_chars(self, key):
        width = self._geometry_width / 2 - 56
        return max(4, int(width / max(1, self.font_grid_value.measure("0"))))

    def _copy_exact_metrics(self):
        if not self._exact_values:
            return
        text = "\n".join(format_integer_exact(value).replace(",", "") for value in self._exact_values)
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._detail_hint = "已复制全部精确值"
            self._refresh_content()
        except tk.TclError:
            pass

    def _copy_selected_exact(self):
        key = self._selected_exact_key
        if not key:
            self._copy_exact_metrics()
            return "break"
        index = ("input", "cached", "output", "total").index(key)
        self._copy_exact_detail_value(index)
        return "break"

    def _copy_exact_detail_value(self, index):
        if index >= len(self._exact_values):
            return
        exact = format_integer_exact(self._exact_values[index]).replace(",", "")
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(exact)
            self.root.update_idletasks()
            self._selected_exact_key = ("input", "cached", "output", "total")[index]
            self._detail_hint = f"已复制{('输入', '缓存', '输出', '总计')[index]}精确值"
            self._refresh_content()
        except tk.TclError:
            pass

    def _schedule_hide_detail(self, _=None):
        if not self.details_pinned and not self._hide_after_id:
            if self._enter_after_id:
                try: self.root.after_cancel(self._enter_after_id)
                except tk.TclError: pass
                self._enter_after_id = None
            self._hide_after_id = self.root.after(200, self._hide_detail)

    def _show_detail(self, _=None):
        if self._hide_after_id:
            try: self.root.after_cancel(self._hide_after_id)
            except tk.TclError: pass
            self._hide_after_id = None
        if self._morph_state == "collapsing":
            self._start_morph(True)
        elif self._morph_state == "collapsed" and not self._enter_after_id:
            self._enter_after_id = self.root.after(90, self._begin_expand)

    def _cancel_morph_timers(self):
        for attr in ("_hide_after_id", "_enter_after_id", "_hover_watch_id", "_morph_after_id"):
            callback_id = getattr(self, attr, None)
            if callback_id:
                try: self.root.after_cancel(callback_id)
                except tk.TclError: pass
                setattr(self, attr, None)
        self._morph_generation += 1
        self._end_precise_timer()
        self._morph_native_fixed = False

    def _begin_precise_timer(self):
        if not self._timer_resolution_active and winmm.timeBeginPeriod(1) == 0:
            self._timer_resolution_active = True

    def _end_precise_timer(self):
        if self._timer_resolution_active:
            winmm.timeEndPeriod(1)
            self._timer_resolution_active = False

    def _begin_expand(self):
        self._enter_after_id = None
        if self._pointer_inside_hud() and self._morph_state not in ("expanded", "expanding"):
            self._start_morph(True)

    def _hide_detail(self, _=None):
        self._hide_after_id = None
        if not self.details_pinned and not self._pointer_inside_hud():
            self._start_morph(False)

    def _pointer_inside_hud(self):
        try:
            px, py = self.root.winfo_pointerxy()
            # During Morph the native Tk window is temporarily the endpoint
            # envelope. Use the logical visible bounds so the extra invisible
            # input area cannot keep the HUD expanded.
            left, top = self._geometry_x, self._geometry_y
            return (left <= px < left + self._geometry_width and
                    top <= py < top + self._geometry_height)
        except tk.TclError:
            return False

    def _watch_pointer(self):
        self._hover_watch_id = None
        if not self.root.winfo_viewable() or self._morph_state == "collapsed":
            return
        if self._pointer_inside_hud():
            if self._hide_after_id:
                self.root.after_cancel(self._hide_after_id)
                self._hide_after_id = None
            if self._morph_state == "collapsing":
                self._start_morph(True)
        elif not self.details_pinned and self._morph_state in ("expanding", "expanded"):
            self._schedule_hide_detail()
        self._hover_watch_id = self.root.after(40, self._watch_pointer)

    def _start_morph(self, expand):
        if expand and self._morph_state == "expanded":
            return
        if not expand and self._morph_state == "collapsed":
            return
        if self._morph_after_id:
            try: self.root.after_cancel(self._morph_after_id)
            except tk.TclError: pass
            self._morph_after_id = None
        self._morph_generation += 1
        generation = self._morph_generation
        if expand:
            self._update_detail_text()
            self._morph_state = "expanding"
            target = self._expanded_size()
            duration = 240
        else:
            self._morph_state = "collapsing"
            target = self._collapsed_size()
            duration = 200
        if self._hover_watch_id is None:
            self._hover_watch_id = self.root.after(40, self._watch_pointer)
        # Keep the Tk window at alpha=1 (transparent input) during the entire
        # morph. The current Canvas layout is captured at each geometry frame,
        # so text and dividers follow their interpolated positions instead of
        # being non-uniformly scaled as one large endpoint screenshot.
        self._morph_using_fallback = False
        self._morph_transition_frames = None
        self._morph_visual_tick = 0
        start = (self._geometry_width, self._geometry_height)
        if self.smooth and self.smooth.surface_enabled and self.root.winfo_viewable():
            self.smooth.enable_input_surface()
            # Text is still captured from the live Canvas at full resolution;
            # only the temporary edge mask uses a cheaper supersample.
            self.smooth.set_mask_scale(1)
            # Reserve the larger endpoint once. Without this, the DIB section
            # is recreated on every growing frame, which stalls the Tk thread.
            try:
                self.smooth._ensure_bitmap(max(start[0], target[0]),
                                           max(start[1], target[1]))
            except Exception:
                pass
        # Keep the Tk input/layout window at one native size for the duration
        # of the morph. The visible overlay and Canvas still use the current
        # logical geometry, so text is rendered at its exact current size.
        self._morph_native_fixed = True
        native_width = max(start[0], target[0])
        native_height = max(start[1], target[1])
        self.root.geometry(f"{native_width}x{native_height}+{self._geometry_x}+{self._geometry_y}")
        self.root.update_idletasks()
        progress_start = self._morph_progress
        progress_end = 1.0 if expand else 0.0
        started = time.perf_counter()
        # Tk callbacks and GDI composition are not deterministic enough for a
        # 170Hz deadline. A stable 120Hz cadence presents more consistent
        # motion and avoids timer backlog on high-refresh displays.
        self._morph_frame_interval = 1000 / 120
        if not self.motion_allowed:
            self._morph_progress = progress_end
            self._morph_velocity = 0.0
            self._geometry_controller(size=target,
                                      radius=self._expanded_radius() if expand else self._collapsed_radius(),
                                      capture=True)
            self._finish_morph(expand)
            return

        self._begin_precise_timer()
        next_frame = started
        def frame():
            nonlocal next_frame
            if generation != self._morph_generation:
                return
            elapsed = time.perf_counter() - started
            t = min(1.0, elapsed / (duration / 1000.0))
            # Deterministic, non-bouncy easing keeps geometry updates smooth
            # and guarantees a bounded finish even when Tk timer callbacks
            # arrive a few milliseconds late.
            eased_time = 1.0 - (1.0 - t) ** 3
            self._morph_progress = progress_start + (
                progress_end - progress_start) * eased_time
            self._morph_velocity = 0.0
            eased = self._morph_progress if expand else 1.0 - self._morph_progress
            width = round(start[0] + (target[0] - start[0]) * eased)
            height = round(start[1] + (target[1] - start[1]) * eased)
            radius = self._collapsed_radius() + (
                self._expanded_radius() - self._collapsed_radius()) * self._morph_progress
            self._geometry_controller(size=(width, height), radius=radius, capture=True)
            if t >= 1.0:
                self._finish_morph(expand)
            else:
                next_frame += self._morph_frame_interval / 1000
                now = time.perf_counter()
                if next_frame <= now:
                    next_frame = now
                delay = max(1, int((next_frame - now) * 1000))
                self._morph_after_id = self.root.after(delay, frame)
        frame()

    def _finish_morph(self, expanded):
        self._morph_after_id = None
        self._end_precise_timer()
        self._morph_state = "expanded" if expanded else "collapsed"
        self._morph_progress = 1.0 if expanded else 0.0
        self._morph_using_fallback = False
        self._morph_overlay_restore = False
        self._morph_native_fixed = False
        try:
            self._geometry_controller(size=self._expanded_size() if expanded else self._collapsed_size(),
                                      radius=self._expanded_radius() if expanded else self._collapsed_radius(),
                                      capture=True)
        finally:
            # Keep the input surface transparent after the final captured
            # frame; subsequent token refreshes can update the same overlay.
            self._morph_transition_frames = None
            if self.smooth and self.smooth.surface_enabled:
                self.smooth.set_mask_scale(self.smooth.MASK_SCALE)
                self._geometry_controller(capture=True)
                self.smooth.enable_input_surface()

    def _close_detail(self):
        self.details_pinned = False
        if self._hide_after_id:
            try: self.root.after_cancel(self._hide_after_id)
            except tk.TclError: pass
            self._hide_after_id = None
        self._start_morph(False)

    def _toggle_detail(self):
        if self._enter_after_id:
            try: self.root.after_cancel(self._enter_after_id)
            except tk.TclError: pass
            self._enter_after_id = None
        if self.details_pinned:
            self._close_detail()
        else:
            self.details_pinned = True
            self._start_morph(True)

    def _drag_start(self, e):
        self.drag = (e.x_root, e.y_root, self.root.winfo_x(), self.root.winfo_y())
        self._drag_moved = False
        self._drag_resume_expanded = None

    def _drag_move(self, e):
        if self.drag:
            sx, sy, x, y = self.drag
            dx, dy = e.x_root - sx, e.y_root - sy
            if abs(dx) + abs(dy) > 5:
                if not getattr(self, "_drag_moved", False):
                    self._cancel_morph_timers()
                    if self._morph_state in ("expanding", "collapsing"):
                        self._drag_resume_expanded = self._morph_progress >= .5
                        self._morph_state = "dragging"
                self._drag_moved = True
                self._geometry_controller(position=(x+dx, y+dy), capture=False)

    def _drag_end(self, e):
        if not self.drag:
            return
        sx, sy, _, _ = self.drag
        moved = getattr(self, "_drag_moved", False) or (e is not None and abs(e.x_root-sx)+abs(e.y_root-sy)>5)
        self.drag = None
        self._drag_moved = False
        if not moved:
            self._toggle_detail()
            return
        if not self.target_hwnd:
            if self._drag_resume_expanded is not None:
                self._start_morph(self._drag_resume_expanded)
            return
        x, y = self._geometry_x, self._geometry_y
        left, top, right, bottom = rect(self.target_hwnd)
        dock_width, dock_height = self._collapsed_size()
        candidates = []
        for edge in ("left", "right", "top", "bottom", "safe"):
            if edge in ("left", "right"):
                along = max(.02, min(.98, (y-top)/max(1, bottom-top-dock_height)))
            else:
                along = max(.02, min(.98, (x-left)/max(1, right-left-dock_width)))
            position = self._dock_candidate(edge, along)
            if position is not None:
                distance = (x-position[0])**2 + (y-position[1])**2
                candidates.append((distance, edge, along, position))
        safe_candidate = self._dock_candidate("safe", .5)
        safe_width, safe_height = self._collapsed_size()
        overlaps_titlebar = (
            safe_candidate is not None
            and max(x, left) < min(x + self._geometry_width, right)
            and max(y, top) < min(y + self._geometry_height, top + safe_height)
        )
        if overlaps_titlebar:
            self.edge, along, position = "safe", .5, safe_candidate
        else:
            _, self.edge, along, position = min(candidates)
        self._dock_along = along
        self._geometry_controller(position=position, size=self._collapsed_size(), capture=True)
        save_config({"edge": self.edge, "along": along})
        if self._drag_resume_expanded is not None:
            self._start_morph(self._drag_resume_expanded)

    def _menu(self, e):
        try: self.menu.tk_popup(e.x_root, e.y_root)
        finally: self.menu.grab_release()

    def _choose_thread(self):
        items = self.catalog
        win = tk.Toplevel(self.root)
        win.title("选择当前聊天")
        win.configure(bg="#191c23")
        win.geometry("480x300")
        tk.Label(win, text="选择与当前 Codex 窗口对应的聊天", bg="#191c23", fg="white").pack(padx=12,pady=10)
        status = tk.Label(win, text="", bg="#191c23", fg="#ffb86b", wraplength=440, justify="left")
        status.pack(padx=16, pady=(0, 4), anchor="w")
        box = None
        if items:
            names = [f"{title}  ·  {tid[:8]}  ·  {time.strftime('%Y-%m-%d', time.localtime(updated)) if updated else '日期未知'}"
                     for tid, title, updated in items]
            box = ttk.Combobox(win, values=names, state="readonly", width=60)
            box.pack(padx=12,pady=8)
            box.current(0)
        else:
            tk.Label(win, text="本地会话目录不可用或没有可选聊天。请检查 Codex 本地索引后重试。",
                     bg="#191c23", fg="#e6e9ef", wraplength=440).pack(padx=16,pady=18)
        def choose():
            i = box.current() if box else -1
            if i >= 0 and self.target_hwnd:
                page_id = uia_page_title(self.target_hwnd, self.catalog)
                if page_id:
                    self.pinned_thread = items[i][0]
                    self.thread_id = self.pinned_thread
                    self._pinned_title = page_id
                    self._pinned_hwnd = self.target_hwnd
                    self.totals = Totals()
                    self._close_detail()
                else:
                    status.configure(text="无法读取当前窗口的聊天页面标题。请先打开目标聊天，稍后再试。")
                    return
            win.destroy()
        ttk.Button(win, text="选择" if items else "关闭", command=choose if items else win.destroy).pack(pady=10)

    def quit(self):
        self._cancel_morph_timers()
        save_config(load_config())
        try:
            if getattr(self, "_tray", None): self._tray.stop()
            if getattr(self, "_mutex", None): kernel32.CloseHandle(self._mutex)
        except Exception:
            pass
        if self.smooth:
            self.smooth.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

    def _start_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
            im = Image.new("RGBA", (64,64), (25,28,35,255))
            draw = ImageDraw.Draw(im)
            draw.rounded_rectangle((5,12,59,52), radius=18, fill=(79,132,255,255))
            draw.text((13,23), "T", fill="white")
            menu = pystray.Menu(
                pystray.MenuItem("显示/隐藏", lambda: self.root.after(0, self._toggle_visible)),
                pystray.MenuItem("手动选择聊天…", lambda: self.root.after(0, self._choose_thread)),
                pystray.MenuItem("退出", lambda: self.root.after(0, self.quit)),
            )
            self._tray = pystray.Icon("codex-token-strip", im, "Codex Token Strip", menu)
            self._tray.run_detached()
        except Exception:
            pass

    def _toggle_visible(self):
        if self.root.winfo_viewable():
            self._user_hidden = True
            self._cancel_morph_timers()
            self._morph_using_fallback = False
            self.details_pinned = False
            self._morph_state = "collapsed"
            self._morph_progress = 0.0
            self.root.withdraw()
            if self.smooth: self.smooth.hide()
            self._geometry_controller(size=self._collapsed_size(), capture=False)
        elif self.target_hwnd and not is_minimized_or_cloaked(self.target_hwnd):
            self._user_hidden = False
            self._show_hud()
            self.root.update_idletasks()
            self._follow_window(capture=True)


def config_path() -> Path:
    return codex_dir() / "token-strip.json"


def load_config():
    try:
        return json.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"edge": "top", "along": .5}


def save_config(value):
    try:
        config_path().write_text(json.dumps(value), encoding="utf-8")
    except OSError:
        pass


if __name__ == "__main__":
    if os.name != "nt":
        raise SystemExit("Windows only")
    try:
        u32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        u32.SetProcessDpiAwarenessContext.restype = BOOL
        u32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
    except Exception:
        pass
    TokenStrip().run()

import ctypes
from ctypes import wintypes
from pathlib import Path
import sys

u32 = ctypes.WinDLL("user32", use_last_error=True)
gdi = ctypes.WinDLL("gdi32", use_last_error=True)
HWND = wintypes.HWND
BOOL = wintypes.BOOL
u32.EnumWindows.argtypes = [ctypes.c_void_p, wintypes.LPARAM]
u32.EnumWindows.restype = BOOL
u32.GetWindowThreadProcessId.argtypes = [HWND, ctypes.POINTER(wintypes.DWORD)]
u32.GetWindowThreadProcessId.restype = wintypes.DWORD
u32.GetWindowRect.argtypes = [HWND, ctypes.POINTER(wintypes.RECT)]
u32.GetWindowRect.restype = BOOL
u32.IsWindowVisible.argtypes = [HWND]
u32.IsWindowVisible.restype = BOOL
u32.GetWindow.argtypes = [HWND, wintypes.UINT]
u32.GetWindow.restype = HWND
u32.GetWindowLongPtrW.argtypes = [HWND, ctypes.c_int]
u32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
u32.GetWindowRgn.argtypes = [HWND, wintypes.HANDLE]
u32.GetWindowRgn.restype = ctypes.c_int
gdi.CreateRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
gdi.CreateRectRgn.restype = wintypes.HANDLE
gdi.DeleteObject.argtypes = [wintypes.HANDLE]

pids = {int(value) for value in sys.argv[1:]}
matches = []
callback_type = ctypes.WINFUNCTYPE(BOOL, HWND, wintypes.LPARAM)


@callback_type
def visit(hwnd, _):
    pid = wintypes.DWORD()
    u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value in pids and u32.IsWindowVisible(hwnd):
        rect = wintypes.RECT()
        u32.GetWindowRect(hwnd, ctypes.byref(rect))
        matches.append((int(hwnd), pid.value, rect.left, rect.top, rect.right, rect.bottom))
    return True


u32.EnumWindows(visit, 0)
assert matches, f"no visible app window for test pids {pids}"
hwnd, pid, left, top, right, bottom = matches[0]
region = gdi.CreateRectRgn(0, 0, 1, 1)
region_type = u32.GetWindowRgn(hwnd, region)
gdi.DeleteObject(region)
exstyle = u32.GetWindowLongPtrW(hwnd, -20)
owner = int(u32.GetWindow(hwnd, 4) or 0)
owner_pid = wintypes.DWORD()
if owner:
    u32.GetWindowThreadProcessId(owner, ctypes.byref(owner_pid))
print(f"hwnd={hwnd} pid={pid} visible=1 rect={left},{top},{right},{bottom} region_type={region_type} topmost={bool(exstyle & 8)} owner={owner} owner_pid={owner_pid.value}")
assert region_type in (2, 3), f"expected a non-rectangular rounded window region, got {region_type}"
assert not (exstyle & 8), "capsule unexpectedly entered global topmost band"
assert right > left and bottom > top

# Capture only the overlay rectangle, never the Codex chat window.
try:
    from PIL import ImageGrab
    shot = ImageGrab.grab(bbox=(left, top, right, bottom))
    output = Path(__file__).with_name("ui-review") / "exe-window.png"
    shot.save(output)
    print(f"screen_capture={output}")
except Exception as exc:
    print(f"screen_capture_unavailable={type(exc).__name__}")

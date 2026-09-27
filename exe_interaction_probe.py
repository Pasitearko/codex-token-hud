import ctypes
import time
from ctypes import wintypes
from pathlib import Path
import sys
from PIL import ImageGrab

u32 = ctypes.WinDLL("user32", use_last_error=True)
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
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.SetCursorPos.restype = BOOL
u32.mouse_event.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
u32.mouse_event.restype = None

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
pid_set = {int(v) for v in sys.argv[1:]}


def windows():
    result = []
    cb = ctypes.WINFUNCTYPE(BOOL, HWND, wintypes.LPARAM)

    @cb
    def visit(hwnd, _):
        if u32.IsWindowVisible(hwnd):
            pid = wintypes.DWORD()
            u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value in pid_set:
                r = wintypes.RECT()
                u32.GetWindowRect(hwnd, ctypes.byref(r))
                result.append((int(hwnd), r.left, r.top, r.right, r.bottom))
        return True

    u32.EnumWindows(visit, 0)
    return result


def click(x, y):
    assert u32.SetCursorPos(x, y)
    time.sleep(.1)
    u32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(.08)
    u32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


current = windows()
main = next((w for w in current if w[4]-w[2] < w[3]-w[1]), None)
assert main, f"capsule window missing: {current}"
mx, my = (main[1]+main[3])//2, (main[2]+main[4])//2
# Hover opens, leaving the capsule closes the unpinned details.
u32.SetCursorPos(8, 8)
time.sleep(.3)
u32.SetCursorPos(mx, my)
time.sleep(.35)
hover_windows = windows()
assert len(hover_windows) >= 2, f"hover did not show details: {hover_windows}"
tip = next(w for w in hover_windows if w[0] != main[0])
r = (tip[1], tip[2], tip[3], tip[4])
ImageGrab.grab(bbox=r).save(Path(__file__).with_name("docs") / "ui-exe-detail-smoke.png")
u32.SetCursorPos(8, 8)
time.sleep(.35)
assert len(windows()) == 1, f"hover details did not close: {windows()}"

# A real button click opens pinned details and a second click closes them.
click(mx, my)
time.sleep(.3)
assert len(windows()) >= 2, f"click did not open details: {windows()}"
click(mx, my)
time.sleep(.3)
assert len(windows()) == 1, f"click did not close pinned details: {windows()}"
print("real exe hover/click detail interaction passed")

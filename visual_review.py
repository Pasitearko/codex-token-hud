import time
import json
import tempfile
from types import SimpleNamespace
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageGrab
import token_strip as ts
from token_strip import TokenStrip, Totals
assert ts.format_millions(0) == "0M"
assert ts.format_millions(1) == "0.000001M"
assert ts.format_millions(999_999).startswith("0.") and ts.format_millions(999_999) != "1M"
assert ts.format_millions(1_000_000) == "1M"
assert ts.format_millions(85_690_000) == "85.69M"

OUT = Path(__file__).with_name("ui-review")
OUT.mkdir(exist_ok=True)
app = TokenStrip(visual_only=True)
app.motion_allowed = False
app.root.geometry("320x80+120+120")
app.root.attributes("-topmost", True)
app.root.deiconify()
app.root.update()
cases = [
    ("zero", Totals(0, 0, 0, 0, time.time(), 1), False),
    ("9999", Totals(9999, 0, 9999, 0, time.time(), 1), False),
    ("10000", Totals(10000, 0, 7500, 0, time.time(), 1), False),
    ("millions", Totals(1_800_000, 250_000, 1_500_000, 0, time.time(), 1), False),
    ("hundred-million", Totals(100_000_000, 0, 90_000_000, 0, time.time(), 1), False),
    ("wide-scientific", Totals(10**10_000, 0, 10**10_000, 0, time.time(), 1), False),
    ("normal-8569wan", Totals(85_690_000, 0, 80_000_000, 0, time.time(), 1), False),
    ("huge", Totals(10**120, 10**119, 10**120, 0, time.time(), 1), False),
    ("unknown", Totals(), False),
    ("side", Totals(1_800_000, 250_000, 1_500_000, 0, time.time(), 1), True),
]
shots = []
for name, totals, side in cases:
    app.thread_id = None if name == "unknown" else "synthetic-preview"
    app.totals = totals
    app.vertical = side
    if not side:
        app._horizontal_base_column = 88
    app._set_layout(side)
    app._render_unknown() if name == "unknown" else app._render()
    app.root.update_idletasks()
    w = max(app.frame.winfo_reqwidth(), 228 if not side else 136)
    h = max(app.frame.winfo_reqheight(), 60 if not side else 164)
    app.root.geometry(f"{w}x{h}+120+120")
    app.root.update()
    time.sleep(.08)
    shot = ImageGrab.grab(bbox=(app.root.winfo_rootx(), app.root.winfo_rooty(), app.root.winfo_rootx()+app.root.winfo_width(), app.root.winfo_rooty()+app.root.winfo_height()))
    # The production window uses this same Win32 rounded rectangle region. Apply
    # the shape to the captured pixels instead of mutating the desktop test HWND;
    # this keeps screenshots clean even when other windows overlap the transparent corners.
    rounded = Image.new("L", shot.size, 0)
    ImageDraw.Draw(rounded).rounded_rectangle((0, 0, shot.width-1, shot.height-1),
                                               radius=min(shot.size)//2, fill=255)
    shot = shot.convert("RGBA")
    shot.putalpha(rounded)
    shot.save(OUT / f"{name}.png")
    docs_name = {
        "normal-8569wan": "ui-horizontal-normal.png",
        "wide-scientific": "ui-long-label-adaptive.png",
        "hundred-million": "ui-horizontal-large.png",
        "side": "ui-side.png",
        "unknown": "ui-unknown.png",
    }.get(name)
    if docs_name:
        shot.save(Path(__file__).with_name("docs") / docs_name)
    value = app.v_token_value if side else app.h_token_value
    value.update_idletasks()
    measured = (app.font_side_primary if side else app.font_primary).measure(value.cget("text"))
    assert measured <= value.winfo_width() + 2, (name, measured, value.winfo_width(), value.cget("text"))
    if name == "normal-8569wan":
        divider = app.separator.winfo_rootx() + app.separator.winfo_width() / 2
        center = app.root.winfo_rootx() + app.root.winfo_width() / 2
        assert app.h_token_group.winfo_width() == app.h_cache_group.winfo_width()
        assert abs(divider - center) <= 1, f"regular value divider is off center: {divider} vs {center}"
    if name == "wide-scientific":
        divider = app.separator.winfo_rootx() + app.separator.winfo_width() / 2
        center = app.root.winfo_rootx() + app.root.winfo_width() / 2
        assert value.cget("text") == "1e10000"
        assert app.font_primary.measure(value.cget("text")) + 8 > app._horizontal_base_column
        assert app.h_token_group.winfo_width() > app.h_cache_group.winfo_width()
        assert divider > center, f"overflow did not move divider right: {divider} vs {center}"
        assert app.font_secondary.measure(app.h_cache_value.cget("text")) <= app.h_cache_value.winfo_width() + 2
    shots.append((name, shot.copy()))

# Capture the measured overflow case after a real 10^10,000 token total is laid out.
app.thread_id = "synthetic-preview"
app.vertical = False
app._horizontal_base_column = 88
app._set_layout(False)
app.totals = Totals(10**10_000, 0, 10**10_000, 0, time.time(), 1)
app._render()
app.root.update_idletasks()
app.root.geometry(f"{max(app.frame.winfo_reqwidth(), 228)}x60+120+120")
app.root.update()
adaptive = ImageGrab.grab(bbox=(app.root.winfo_rootx(), app.root.winfo_rooty(),
                                app.root.winfo_rootx()+app.root.winfo_width(), app.root.winfo_rooty()+app.root.winfo_height()))
adaptive.save(Path(__file__).with_name("docs") / "ui-long-label-adaptive.png")

# First-poll handoff and user-controlled visibility must not reuse stale values.
prior_follow = app._follow_window
prior_cloaked_check = ts.is_minimized_or_cloaked
app._follow_window = lambda: None
ts.is_minimized_or_cloaked = lambda _hwnd: False
app.target_hwnd = None
app._accept_poll([], 111, "Synthetic chat", "synthetic-preview", Totals(10, 2, 8, 0, time.time(), 1))
assert app.thread_id == "synthetic-preview" and app.root.winfo_viewable()
app._user_hidden = True
app.root.withdraw()
app._accept_poll([], 111, "Synthetic chat", "synthetic-preview", Totals(11, 2, 8, 0, time.time(), 1))
assert not app.root.winfo_viewable(), "poll must respect tray-hidden state"
app._toggle_visible()
assert app.root.winfo_viewable() and not app._user_hidden
app.target_hwnd = None
app._show_detail()
assert app.tip.winfo_viewable()
app.target_hwnd = 111
app._toggle_visible()
assert not app.root.winfo_viewable() and not app.tip.winfo_viewable(), "tray hide left the tooltip visible"
app._toggle_visible()
assert app.root.winfo_viewable() and not app._user_hidden
ts.is_minimized_or_cloaked = lambda _hwnd: True
app._accept_poll([], 111, "Synthetic chat", "synthetic-preview", Totals(11, 2, 8, 0, time.time(), 1))
assert not app.root.winfo_viewable() and not app.tip.winfo_viewable(), "cloaked target must hide both windows"
ts.is_minimized_or_cloaked = prior_cloaked_check
app._follow_window = prior_follow
app.target_hwnd = None
app._user_hidden = False
app.root.deiconify()
app.root.update()

# One tick schedules one successor; it must not create duplicate polling timers.
old_after, app._worker_busy = app.root.after, True
scheduled = []
app.root.after = lambda ms, callback: scheduled.append((ms, callback))
app._tick()
assert len(scheduled) == 1 and scheduled[0][0] == 500
app.root.after, app._worker_busy = old_after, False

app.thread_id = "synthetic-preview"
app.totals = Totals(800, 20, 800, 0, time.time(), 1)
app._set_layout(False)
app._render()
app.root.geometry(f"{max(app.frame.winfo_reqwidth(), 228)}x{max(app.frame.winfo_reqheight(),60)}+120+120")
app.root.update()
app.h_token_value.event_generate("<Enter>")
app.root.update()
assert app.tip.winfo_viewable(), "hover did not open details"
app.h_token_value.event_generate("<Leave>")
time.sleep(.2)
app.root.update()
assert not app.tip.winfo_viewable(), "hover dismissal did not close unpinned details"
app.h_token_value.event_generate("<ButtonPress-1>", x=5, y=5)
app.h_token_value.event_generate("<ButtonRelease-1>", x=5, y=5)
app.root.update()
assert app.details_pinned and app.tip.winfo_viewable(), "click did not open details"
assert app.detail_values[0].cget("text") == "0.0008M"
assert app.detail_values[1].cget("text") == "0.00002M"
assert app.detail_values[2].cget("text") == "0.0008M"
assert app.detail_values[4].cget("text") == "100.00%"
assert not app.detail_scroll.winfo_manager(), "ordinary details should not show a scrollbar"
app.detail_precision.invoke()
app.tip.update()
assert app.detail_values[0].cget("text") == "800"
assert "点击数值复制" in app.detail_time.cget("text")
app.detail_values[0].event_generate("<Button-1>")
app.root.update()
assert app.root.clipboard_get() == "800", "exact-value click did not copy the full integer"
app.detail_precision.invoke()
app.tip.update()
assert app.detail_values[0].cget("text") == "0.0008M"
app.detail_close.focus_set()
app.tip.update()
time.sleep(.1)
detail = ImageGrab.grab(bbox=(app.tip.winfo_rootx(), app.tip.winfo_rooty(), app.tip.winfo_rootx()+app.tip.winfo_width(), app.tip.winfo_rooty()+app.tip.winfo_height()))
detail.save(OUT / "detail.png")
shots.append(("100% detail", detail.copy()))

app._close_detail()
app.totals = Totals(10**1200, 10**1200, 0, 0, time.time(), 1)
app._update_detail_text()
app._position_detail()
app.tip.deiconify()
app.root.update()
assert not app.detail_scroll.winfo_manager(), "M mode should remain compact for huge integers"
app.detail_precision.invoke()
app.root.update()
assert app.detail_values[0].cget("text").endswith("000"), "exact large integer lost digits"
assert app.detail_scroll.winfo_manager(), "very large values should scroll only when necessary"
huge_detail = ImageGrab.grab(bbox=(app.tip.winfo_rootx(), app.tip.winfo_rooty(), app.tip.winfo_rootx()+app.tip.winfo_width(), app.tip.winfo_rooty()+app.tip.winfo_height()))
huge_detail.save(OUT / "huge-detail.png")

# Docking follow geometry uses the same screen coordinates at 96/144 DPI and on
# monitors with negative origins. The safe titlebar slot is also exercised.
prior_get_dpi, prior_rect, prior_monitor, prior_config = ts.get_dpi, ts.rect, ts.monitor_rect, ts.load_config
app.target_hwnd = 123
app._place_z_order = lambda: None
ts.rect = lambda _h: (200, 160, 1400, 1000)
ts.monitor_rect = lambda _h: (0, 0, 1920, 1080)
ts.get_dpi = lambda _h: 96
ts.load_config = lambda: {"edge": "safe", "along": .5}
app._follow_window()
assert app.root.winfo_y() == 172 and 0 <= app.root.winfo_x() < 1920
safe_follow_x = app.root.winfo_x()
ts.rect = lambda _h: (280, 160, 1480, 1000)
app._follow_window()
assert app.root.winfo_x() == safe_follow_x + 80, "capsule did not follow Codex window movement"
ts.rect = lambda _h: (-1750, 140, -550, 940)
ts.monitor_rect = lambda _h: (-1920, 0, 0, 1080)
ts.get_dpi = lambda _h: 144
ts.load_config = lambda: {"edge": "right", "along": .5}
app._follow_window()
assert app.root.winfo_x() + app.root.winfo_width() <= 0
assert app.root.winfo_y() >= 0 and app.root.winfo_y() + app.root.winfo_height() <= 1080
ts.get_dpi, ts.rect, ts.monitor_rect, ts.load_config = prior_get_dpi, prior_rect, prior_monitor, prior_config
app.target_hwnd = None
app._place_z_order = TokenStrip._place_z_order.__get__(app, TokenStrip)

# Drag release chooses the nearest safe titlebar area or outer edge and persists it.
prior_rect, prior_monitor, prior_save = ts.rect, ts.monitor_rect, ts.save_config
saved = []
ts.rect = lambda _h: (200, 160, 1400, 1000)
ts.monitor_rect = lambda _h: (0, 0, 1920, 1080)
ts.save_config = lambda value: saved.append(value)
app.target_hwnd = 123
app.vertical = False
app.root.geometry("228x60+500+172")
app.root.update()
app.drag = (0, 0, 500, 172)
app._drag_moved = True
app._drag_end(SimpleNamespace(x_root=600, y_root=200))
assert app.edge == "safe" and app.root.winfo_y() == 172 and saved[-1]["edge"] == "safe"
app.root.geometry("228x60+600+90")
app.root.update()
app.drag = (0, 0, 600, 90)
app._drag_moved = True
app._drag_end(SimpleNamespace(x_root=700, y_root=110))
assert app.edge == "top" and app.root.winfo_y() == 90 and saved[-1]["edge"] == "top"
ts.rect, ts.monitor_rect, ts.save_config = prior_rect, prior_monitor, prior_save
app.target_hwnd = None

# Initial binding inserts the HUD just above Codex, below unrelated windows.
prior_set_long, prior_set_pos = ts._set_window_long, ts.u32.SetWindowPos
prior_get_window = ts.u32.GetWindow
z_calls = []
ts._set_window_long = lambda *args: z_calls.append(("owner", args)) or 0
ts.u32.SetWindowPos = lambda *args: z_calls.append(("position", args)) or 1
ts.u32.GetWindow = lambda *args: 789
app.hwnd, app.target_hwnd = 456, 123
app._owner_hwnd = None
app._place_z_order()
assert z_calls[0][1][0:2] == (456, ts.GWLP_HWNDPARENT)
assert z_calls[1][1][1] == 789
assert z_calls[1][1][-1] & ts.SWP_NOACTIVATE
assert z_calls[1][1][-1] & ts.SWP_NOOWNERZORDER
z_calls.clear()
app._place_z_order()
assert not z_calls, "routine polls must not keep raising the strip over other windows"
ts._set_window_long, ts.u32.SetWindowPos = prior_set_long, prior_set_pos
ts.u32.GetWindow = prior_get_window
app.hwnd, app.target_hwnd = None, None
app._owner_hwnd = None

# Synthetic parent/child/grandchild logs verify recursive aggregation and that
# cumulative snapshots in a session are reduced to their latest maxima.
with tempfile.TemporaryDirectory() as temp:
    temp_root = Path(temp)
    prior_codex_dir = ts.codex_dir
    ts.codex_dir = lambda: temp_root
    logs = temp_root / "sessions" / "2026" / "09"
    logs.mkdir(parents=True)
    def write_session(name, sid, parent, snapshots):
        path = logs / f"{name}.jsonl"
        entries = [{"type": "session_meta", "payload": {"id": sid, "parent_thread_id": parent}}]
        entries.extend({"type": "event_msg", "payload": {"type": "token_count", "info": {"total_token_usage": row}}} for row in snapshots)
        path.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
    write_session("root", "p", None, [{"input_tokens": 100, "output_tokens": 10, "cached_input_tokens": 80}, {"input_tokens": 120, "output_tokens": 15, "cached_input_tokens": 90}])
    write_session("child", "c", "p", [{"input_tokens": 30, "output_tokens": 5, "cached_input_tokens": 20}])
    write_session("grandchild", "g", "c", [{"input_tokens": 2, "output_tokens": 1, "cached_input_tokens": 1}])
    total = ts.aggregate("p")
    assert (total.input, total.output, total.cached, total.logs) == (152, 21, 111, 3), total
    ts.codex_dir = prior_codex_dir

cell_w, cell_h = 370, 220
sheet = Image.new("RGB", (cell_w * 2, cell_h * 5), "#0b0d11")
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype("segoeui.ttf", 14)
for index, (name, shot) in enumerate(shots):
    x, y = (index % 2) * cell_w, (index // 2) * cell_h
    draw.text((x+8, y+6), name, font=font, fill="#e5e9f0")
    shot.thumbnail((cell_w-18, cell_h-40))
    sheet.paste(shot, (x+8, y+30))
sheet.save(OUT / "contact-sheet.png")
app.quit()
print(OUT / "contact-sheet.png")

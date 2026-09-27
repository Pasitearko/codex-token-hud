"""Deterministic visual edge loop for the capsule's current Win32 region path."""
from pathlib import Path
from PIL import Image, ImageGrab
import tkinter as tk

from token_strip import TokenStrip

app = TokenStrip(visual_only=True)
app.motion_allowed = False
app.root.withdraw()
backdrop = tk.Toplevel(app.root)
backdrop.overrideredirect(True)
backdrop.attributes("-topmost", True)
backdrop.configure(bg="#f4f5f8")
backdrop.geometry("500x300+180+180")
app.root.configure(bg="#11151d")
app.root.geometry("228x60+300+300")
app.root.attributes("-topmost", True)
app.root.deiconify()
app.root.update()
app.hwnd = int(__import__("token_strip").u32.GetAncestor(app.root.winfo_id(), 2) or app.root.winfo_id())
app.root.lift()
app.root.update()
app._apply_capsule_region(app.root.winfo_width(), app.root.winfo_height())
app.root.update()
shot = ImageGrab.grab(bbox=(app.root.winfo_rootx(), app.root.winfo_rooty(),
                            app.root.winfo_rootx()+app.root.winfo_width(),
                            app.root.winfo_rooty()+app.root.winfo_height())).convert("RGB")
out = Path(__file__).with_name("ui-review") / "edge-baseline-region.png"
shot.save(out)

# Search the capsule's top-left corner for partially blended pixels. With a
# smooth edge over this pale background, pixels exist between the surface and
# backdrop colors; a binary SetWindowRgn boundary yields only solid or outside.
mixed = [(x, y, shot.getpixel((x, y)))
         for y in range(0, min(30, shot.height))
         for x in range(0, min(30, shot.width))
         if all(90 < channel < 230 for channel in shot.getpixel((x, y)))]
print(f"path=SetWindowRgn size={shot.width}x{shot.height} background=#f4f5f8 antialiased_corner_pixels={len(mixed)} screenshot={out}")
backdrop.destroy()
app.quit()
assert mixed, "jagged capsule boundary reproduced: no partial-coverage edge pixels"

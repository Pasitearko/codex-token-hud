# Codex Token HUD

**[简体中文](README.zh-CN.md)** · Windows · Python/Tkinter · MIT

An unofficial floating HUD for the Codex desktop app on Windows. It follows the Codex window and shows token usage and cache hit rate for the current local chat. Hover to expand the same HUD into a compact usage breakdown.

| Collapsed | Expanded |
| --- | --- |
| ![Collapsed HUD](docs/hud-collapsed.png) | ![Expanded HUD](docs/hud-expanded.png) |

*Screenshots use synthetic numbers.*

## Features

- **One continuous HUD:** a compact single-line view morphs into an expanded two-column view. Hover begins expansion after about 90 ms; leaving begins collapse after about 200 ms. Click to pin or unpin the expanded view.
- **Current-chat metrics:** total tokens, input, output, cached input, cache hit rate, and relative update time. Click an expanded token number to switch that metric between abbreviated and exact integer display; the collapsed HUD always stays abbreviated. The **Copy** control copies all four exact token counts.
- **Readable units:** counts below 10,000 show their full number. At 10,000, one million, and one billion the HUD switches to W (ten thousand), M (million), and B (billion), with at most one decimal.
- **Window-aware docking:** drag and release to dock beside a Codex edge or its safe titlebar area. The HUD follows Codex, hides when its window is minimized or closed, and stays below unrelated foreground windows.
- **Local-only data:** reads Codex's local token-count snapshots and catalog. It does not send chat content or usage data to a server.

## Requirements

- Windows and the Codex desktop app.
- For source use: Python 3.12 or newer, Pillow, pystray, and comtypes.
- Access to the current user's local Codex data directory.

This is a community project, not an official OpenAI product. It depends on the current Codex desktop window and local log formats; a future Codex update may require a compatibility change.

## Run from source

In PowerShell:

```powershell
git clone https://github.com/Pasitearko/codex-token-hud.git
cd codex-token-hud
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install pillow pystray comtypes
.\.venv\Scripts\python.exe token_strip.py
```

Open a local Codex chat. The HUD appears near the Codex window. If automatic chat matching is unavailable, right-click the HUD or use the tray menu to select the chat. To quit fully, choose **Exit** from the tray menu.

## Build a portable executable

With the virtual environment active, run `powershell -ExecutionPolicy Bypass -File .\build.ps1`. The output is `dist\CodexTokenStrip.exe`. The script installs its packaging dependencies and uses PyInstaller. The `dist/` directory is intentionally excluded from source control; build it from the checked-out source.

## Data and privacy

The app opens `~/.codex/sqlite/codex-dev.db` in read-only mode and reads token-count events from `~/.codex/sessions/**/*.jsonl`. It matches the visible Codex page title to a local chat; if that match is ambiguous, it shows an unknown state and offers manual selection. Child sessions are included, and cumulative snapshots are deduplicated per session.

**Total tokens** = input + output. **Cache hit rate** = cached input ÷ input. Values update after Codex writes a snapshot; tokens still being generated are not estimated. The only setting written by this app is its dock position in `~/.codex/token-strip.json`. It does not store message text.

When reporting a bug, do not attach real session logs, database files, chat text, or credentials. Use synthetic or redacted screenshots.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). UI probes in this repository require an unlocked, interactive Windows desktop; they are not headless CI tests. You can check Python syntax with:

```powershell
python -m py_compile token_strip.py smooth_capsule.py
```

## License

Released under the [MIT License](LICENSE).

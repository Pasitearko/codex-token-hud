$ErrorActionPreference = 'Stop'
python -m pip install --disable-pip-version-check comtypes pystray pillow pyinstaller
python -m PyInstaller --clean --noconfirm --onefile --windowed --name CodexTokenStrip `
  --collect-submodules comtypes `
  --collect-data pystray `
  token_strip.py
Write-Host "Portable executable: $((Resolve-Path 'dist/CodexTokenStrip.exe').Path)"

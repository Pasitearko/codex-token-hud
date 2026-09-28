$ErrorActionPreference = 'Stop'
python -m pip install --disable-pip-version-check comtypes pystray pillow pyinstaller
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m PyInstaller --clean --noconfirm --onefile --windowed --name CodexTokenStrip `
  --collect-submodules comtypes `
  --collect-data pystray `
  --add-data 'assets/app-icon.png;assets' `
  --icon assets/app-icon.ico `
  --distpath dist/icon-check `
  --workpath build/icon-check `
  token_strip.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Portable executable: $((Resolve-Path 'dist/icon-check/CodexTokenStrip.exe').Path)"

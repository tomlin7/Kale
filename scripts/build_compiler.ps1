# Build script for standalone native Kale compiler binary
# Usage: ./scripts/build_compiler.ps1

Write-Host "Building standalone Kale compiler binary..." -ForegroundColor Cyan

uv run pyinstaller `
    --noconfirm `
    --onedir `
    --name kale `
    --collect-all llvmlite `
    --collect-all colorama `
    --collect-all kale `
    --paths src `
    src/kale/__main__.py

if ($LASTEXITCODE -eq 0) {
    New-Item -ItemType Directory -Force -Path bin | Out-Null
    Copy-Item -Recurse -Force dist/kale/* bin/
    Remove-Item -Recurse -Force build, dist, kale.spec -ErrorAction SilentlyContinue
    Write-Host "Successfully compiled native binary: bin/kale.exe" -ForegroundColor Green
} else {
    Write-Host "Failed to build compiler binary!" -ForegroundColor Red
    exit 1
}

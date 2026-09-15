param(
    [string]$Image = "",
    [string]$Display = "gtk"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if ([string]::IsNullOrWhiteSpace($Image)) {
    $Image = Join-Path $root "bin\kale-os.img"
}
$Image = [System.IO.Path]::GetFullPath($Image)

if (-not (Test-Path -LiteralPath $Image)) {
    & (Join-Path $PSScriptRoot "build.ps1")
}

$qemu = $null
$candidates = @(
    (Get-Command qemu-system-x86_64.exe -ErrorAction SilentlyContinue).Source,
    "$env:USERPROFILE\scoop\apps\qemu\current\qemu-system-x86_64.exe",
    "$env:USERPROFILE\scoop\shims\qemu-system-x86_64.exe"
)
foreach ($candidate in $candidates) {
    if (-not [string]::IsNullOrWhiteSpace($candidate) -and (Test-Path -LiteralPath $candidate)) {
        $qemu = $candidate
        break
    }
}
if ($null -eq $qemu) {
    throw "qemu-system-x86_64.exe was not found on PATH or in the Scoop installation."
}

Write-Output "Launching QEMU: $qemu"
Write-Output "Boot image: $Image"
& $qemu `
    "-drive" "format=raw,file=$Image" `
    "-m" "128M" `
    "-no-reboot" `
    "-serial" "none" `
    "-display" $Display

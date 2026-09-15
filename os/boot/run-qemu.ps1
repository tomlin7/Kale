param(
    [string]$Image = "",
    [string]$Display = "gtk",
    [string]$SerialLog = "",
    [string]$DataImage = ""
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
if ([string]::IsNullOrWhiteSpace($DataImage)) {
    $DataImage = Join-Path (Split-Path -Parent $Image) "kale-os-data.img"
}
$DataImage = [System.IO.Path]::GetFullPath($DataImage)

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
$serialMode = "none"
if (-not [string]::IsNullOrWhiteSpace($SerialLog)) {
    $SerialLog = [System.IO.Path]::GetFullPath($SerialLog)
    $serialMode = "file:$SerialLog"
    Write-Output "Serial log: $SerialLog"
}
& $qemu `
    "-drive" "format=raw,file=$Image" `
    "-drive" "format=raw,file=$DataImage,if=ide,index=1" `
    "-m" "128M" `
    "-no-reboot" `
    "-serial" $serialMode `
    "-display" $Display

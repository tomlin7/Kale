param(
    [string]$OutputDirectory = "bin"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if ([System.IO.Path]::IsPathRooted($OutputDirectory)) {
    $output = $OutputDirectory
} else {
    $output = Join-Path $root $OutputDirectory
}
New-Item -ItemType Directory -Force -Path $output | Out-Null

$boot = Join-Path $output "kale-os-boot.bin"
$stage2 = Join-Path $output "kale-os-stage2.bin"
nasm -f bin (Join-Path $PSScriptRoot "boot.asm") -o $boot
nasm -f bin (Join-Path $PSScriptRoot "stage2.asm") -o $stage2

$size = (Get-Item $boot).Length
if ($size -ne 512) {
    throw "The BIOS boot sector must be exactly 512 bytes; got $size bytes."
}
$stage2Size = (Get-Item $stage2).Length
if ($stage2Size -ne 4096) {
    throw "The second stage must be exactly 4096 bytes; got $stage2Size bytes."
}
$stage2Bytes = [System.IO.File]::ReadAllBytes($stage2)
$checksum = [uint64]0
foreach ($byte in $stage2Bytes) {
    $checksum = ($checksum + $byte) -band 0xFFFFFFFF
}
$manifest = [ordered]@{
    format = 1
    stage2_bytes = $stage2Size
    stage2_sectors = [int]($stage2Size / 512)
    stage2_checksum = [uint64]$checksum
}
$manifestPath = Join-Path $output "kale-os-stage2.json"
$manifest | ConvertTo-Json | Set-Content -LiteralPath $manifestPath -Encoding ascii

$image = Join-Path $output "kale-os.img"
$stream = [System.IO.File]::Create($image)
try {
    $sector = [System.IO.File]::ReadAllBytes($boot)
    $stream.Write($sector, 0, $sector.Length)
    $payload = [System.IO.File]::ReadAllBytes($stage2)
    $stream.Write($payload, 0, $payload.Length)
    $stream.SetLength(1474560)
}
finally {
    $stream.Dispose()
}

Write-Output "Built $image (1.44 MiB)"
Write-Output "Stage2 checksum: $checksum"

$dataImage = Join-Path $output "kale-os-data.img"
& (Join-Path $root "os\fs\make-fat12.ps1") -OutputPath $dataImage

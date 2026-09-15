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
if ($stage2Size -ne 2048) {
    throw "The second stage must be exactly 2048 bytes; got $stage2Size bytes."
}

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

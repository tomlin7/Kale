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
nasm -f bin (Join-Path $PSScriptRoot "boot.asm") -o $boot

$size = (Get-Item $boot).Length
if ($size -ne 512) {
    throw "The BIOS boot sector must be exactly 512 bytes; got $size bytes."
}

$image = Join-Path $output "kale-os.img"
$stream = [System.IO.File]::Create($image)
try {
    $sector = [System.IO.File]::ReadAllBytes($boot)
    $stream.Write($sector, 0, $sector.Length)
    $stream.SetLength(1474560)
}
finally {
    $stream.Dispose()
}

Write-Output "Built $image (1.44 MiB)"

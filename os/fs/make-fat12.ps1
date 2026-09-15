param(
    [string]$OutputPath = "bin\kale-os-data.img"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not [System.IO.Path]::IsPathRooted($OutputPath)) {
    $OutputPath = Join-Path $root $OutputPath
}
$parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Force -Path $parent | Out-Null

$image = [byte[]]::new(1474560)
function Put-U16([int]$offset, [int]$value) {
    $image[$offset] = [byte]($value -band 0xFF)
    $image[$offset + 1] = [byte](($value -shr 8) -band 0xFF)
}
function Put-U32([int]$offset, [int]$value) {
    Put-U16 $offset ($value -band 0xFFFF)
    Put-U16 ($offset + 2) (($value -shr 16) -band 0xFFFF)
}

# FAT12 BPB for a standard 1.44 MiB floppy layout.
$image[0] = 0xEB; $image[1] = 0x3C; $image[2] = 0x90
[Text.Encoding]::ASCII.GetBytes("KALEOS  ") | ForEach-Object -Begin {$i=3} -Process {$image[$i++] = $_}
Put-U16 11 512
$image[13] = 1
Put-U16 14 1
$image[16] = 2
Put-U16 17 224
Put-U16 19 2880
$image[21] = 0xF0
Put-U16 22 9
Put-U16 24 18
Put-U16 26 2
Put-U32 28 0
$image[510] = 0x55; $image[511] = 0xAA

# FAT copies at sectors 1 and 10: media descriptor, reserved clusters, file cluster 2 EOC.
foreach ($fatSector in @(1, 10)) {
    $base = $fatSector * 512
    $image[$base] = 0xF0; $image[$base + 1] = 0xFF; $image[$base + 2] = 0xFF
    $image[$base + 3] = 0xFF; $image[$base + 4] = 0x0F
}

$message = [Text.Encoding]::ASCII.GetBytes("Kale OS FAT12 filesystem online`r`n")
$root = 19 * 512
[Text.Encoding]::ASCII.GetBytes("KALEOS  TXT") | ForEach-Object -Begin {$i=$root} -Process {$image[$i++] = $_}
$image[$root + 11] = 0x20
Put-U16 ($root + 26) 2
Put-U32 ($root + 28) $message.Length
$data = 33 * 512
[Array]::Copy($message, 0, $image, $data, $message.Length)

[System.IO.File]::WriteAllBytes($OutputPath, $image)
Write-Output "Built FAT12 data disk $OutputPath (1.44 MiB)"

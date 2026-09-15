import os
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_os_boot_script_builds_a_bios_disk_image(tmp_path):
    output = tmp_path / "os-bin"
    script = ROOT / "os" / "boot" / "build.ps1"
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(script), "-OutputDirectory", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    image = output / "kale-os.img"
    data_image = output / "kale-os-data.img"
    stage2 = output / "kale-os-stage2.bin"
    manifest = output / "kale-os-stage2.json"
    assert image.exists()
    assert data_image.exists()
    assert data_image.stat().st_size == 1474560
    data = data_image.read_bytes()
    assert data[510:512] == b"\x55\xaa"
    assert b"KALEOS  TXT" in data[19 * 512:33 * 512]
    cluster2 = data[33 * 512:34 * 512]
    assert b"Kale OS FAT12 filesystem online" in cluster2
    assert stage2.exists()
    metadata = json.loads(manifest.read_text())
    assert metadata["stage2_bytes"] == 4096
    assert metadata["stage2_sectors"] == 8
    assert metadata["stage2_checksum"] == sum(stage2.read_bytes()) & 0xFFFFFFFF
    assert stage2.stat().st_size == 4096
    assert b"STAGE2 LOADED" in stage2.read_bytes()
    stage2_source = (ROOT / "os" / "boot" / "stage2.asm").read_text()
    assert "pic_init:" in stage2_source
    assert "kbd_isr:" in stage2_source
    assert "kbd_queue:" in stage2_source
    assert "kbd_head" in stage2_source
    image_data = image.read_bytes()
    assert image_data[512:512 + 4096] == stage2.read_bytes()
    assert image.stat().st_size == 1474560


def test_os_boot_sector_has_bios_signature():
    boot = ROOT / "bin" / "os-boot.bin"
    if not boot.exists():
        pytest_skip = os.environ.get("KALE_SKIP_BOOT_ARTIFACT")
        if pytest_skip:
            return
        subprocess.run(
            ["nasm", "-f", "bin", str(ROOT / "os" / "boot" / "boot.asm"), "-o", str(boot)],
            cwd=ROOT,
            check=True,
        )
    data = boot.read_bytes()
    assert len(data) == 512
    assert data[510:512] == b"\x55\xaa"


def test_os_qemu_reaches_stage2_serial_banner(tmp_path):
    output = tmp_path / "os-bin"
    script = ROOT / "os" / "boot" / "build.ps1"
    subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(script), "-OutputDirectory", str(output)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    image = output / "kale-os.img"
    qemu = os.environ.get("KALE_QEMU", "qemu-system-x86_64")
    process = subprocess.Popen(
        [
            qemu,
            "-drive",
            f"format=raw,file={image}",
            "-display",
            "none",
            "-serial",
            "stdio",
            "-no-reboot",
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, _ = process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, _ = process.communicate()
    assert b"KALE OS stage2: serial, IDT, PIC, keyboard queue online" in stdout

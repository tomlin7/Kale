import os
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
    stage2 = output / "kale-os-stage2.bin"
    assert image.exists()
    assert stage2.exists()
    assert stage2.stat().st_size == 2048
    assert b"STAGE2 LOADED" in stage2.read_bytes()
    stage2_source = (ROOT / "os" / "boot" / "stage2.asm").read_text()
    assert "pic_init:" in stage2_source
    assert "kbd_isr:" in stage2_source
    assert "kbd_queue:" in stage2_source
    assert "kbd_head" in stage2_source
    image_data = image.read_bytes()
    assert image_data[512:512 + 2048] == stage2.read_bytes()
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

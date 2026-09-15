from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_qemu_runner_resolves_an_executable_and_uses_absolute_image():
    source = (ROOT / "os" / "boot" / "run-qemu.ps1").read_text()
    assert "qemu-system-x86_64.exe" in source
    assert "GetFullPath" in source
    assert '"-drive" "format=raw,file=$Image"' in source
    assert "-display" in source
    assert "SerialLog" in source
    assert "file:$SerialLog" in source
    assert "DataImage" in source
    assert "if=ide,index=1" in source

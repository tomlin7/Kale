from pathlib import Path


ROOT = Path(__file__).parents[1]


def read(path):
    return (ROOT / path).read_text()


def test_os_plan_defines_the_ten_foundation_features():
    plan = read("os/PLAN.md")
    required = [
        "E820 memory-map discovery",
        "PIT channel-0 timer",
        "RTC CMOS date/time",
        "ATA PIO",
        "FAT12 parser",
        "VFS mount/open/read",
        "Interactive kernel console",
        "Kernel assertions",
    ]
    for feature in required:
        assert feature in plan


def test_boot_and_time_services_have_deterministic_entry_points():
    assert "boot_info_valid" in read("os/kernel/boot_info.kl")
    assert "stage2_checksum" in read("os/kernel/boot_info.kl")
    assert "e820_is_usable" in read("os/kernel/e820.kl")
    assert "exception_name" in read("os/kernel/exceptions.kl")
    assert "panic_begin" in read("os/kernel/panic.kl")
    assert "pit_init" in read("os/kernel/pit.kl")
    assert "pit_tick" in read("os/kernel/pit.kl")
    assert "rtc_bcd_to_binary" in read("os/kernel/rtc.kl")


def test_storage_stack_has_mount_read_write_and_vfs_semantics():
    fat = read("os/fs/fat12.kl")
    vfs = read("os/fs/vfs.kl")
    assert "fat12_mount" in fat
    assert "fat12_read_file" in fat
    assert "fat12_write_file" in fat
    assert "fat12_next_cluster" in fat
    assert "vfs_mount" in vfs
    assert "vfs_read" in vfs
    assert "vfs_seek" in vfs
    assert "vfs_close" in vfs
    assert "make-fat12.ps1" in read("os/boot/build.ps1")


def test_device_layer_has_block_ata_and_serial_ring_contracts():
    assert "struct BlockDevice" in read("os/fs/block.kl")
    assert "block_device_valid" in read("os/fs/block.kl")
    assert "ata_identify_result" in read("os/drivers/ata.kl")
    serial = read("os/drivers/serial_rx.kl")
    assert "serial_rx_push" in serial
    assert "serial_rx_pop" in serial
    assert "pci_device_valid" in read("os/drivers/pci.kl")


def test_kernel_scaling_services_have_heap_scheduler_and_loopback():
    assert "early_heap_alloc" in read("os/kernel/heap.kl")
    assert "scheduler_add" in read("os/kernel/scheduler.kl")
    assert "scheduler_next" in read("os/kernel/scheduler.kl")
    assert "loopback_send" in read("os/net/loopback.kl")
    assert "loopback_receive" in read("os/net/loopback.kl")
    assert "initramfs_mount" in read("os/fs/initramfs.kl")
    assert "initramfs_read" in read("os/fs/initramfs.kl")
    assert "kernel_assert" in read("os/kernel/assert.kl")
    assert "syscall_dispatch" in read("os/kernel/syscall.kl")
    assert "udp_checksum" in read("os/net/udp.kl")
    assert "checksum_bytes" in read("os/kernel/checksum.kl")

"""
Kale OS Build & Launch Tool
Assembles the 16-bit MBR bootstrap and 64-bit microkernel,
creates bootable disk image (bin/kale_os.img & bin/boot.bin),
and provides optional QEMU execution.
"""

import os
import sys
import subprocess
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OS_DIR = os.path.join(BASE_DIR, "os")
BIN_DIR = os.path.join(BASE_DIR, "bin")

BOOT_SRC = os.path.join(OS_DIR, "boot", "boot.asm")
KERNEL_SRC = os.path.join(OS_DIR, "kernel", "kernel.asm")

BOOT_BIN = os.path.join(BIN_DIR, "boot_sector.bin")
KERNEL_BIN = os.path.join(BIN_DIR, "kernel.bin")
COMBINED_BIN = os.path.join(BIN_DIR, "boot.bin")
IMG_BIN = os.path.join(BIN_DIR, "kale_os.img")


def assemble(src_file, out_file):
    print(f"[*] Assembling {os.path.relpath(src_file, BASE_DIR)} -> {os.path.relpath(out_file, BASE_DIR)}")
    cmd = ["nasm", "-f", "bin", src_file, "-o", out_file]
    res = subprocess.run(cmd)
    if res.returncode != 0:
        print(f"[!] Assembly failed for {src_file}")
        sys.exit(1)


def build_image():
    os.makedirs(BIN_DIR, exist_ok=True)

    # 1. Assemble MBR bootloader
    assemble(BOOT_SRC, BOOT_BIN)
    boot_size = os.path.getsize(BOOT_BIN)
    if boot_size != 512:
        print(f"[!] Error: Boot sector must be exactly 512 bytes, got {boot_size}")
        sys.exit(1)
    print(f"[+] Bootloader MBR: {boot_size} bytes (OK)")

    # 2. Assemble 64-bit kernel
    assemble(KERNEL_SRC, KERNEL_BIN)
    kernel_size = os.path.getsize(KERNEL_BIN)
    print(f"[+] 64-bit Kernel: {kernel_size} bytes")

    # 3. Read both parts
    with open(BOOT_BIN, "rb") as f:
        boot_bytes = f.read()

    with open(KERNEL_BIN, "rb") as f:
        kernel_bytes = f.read()

    # 4. Pad kernel to 32 sectors (16,384 bytes)
    target_sectors = 32
    target_kernel_size = target_sectors * 512
    if len(kernel_bytes) > target_kernel_size:
        print(f"[!] Error: Kernel size {len(kernel_bytes)} exceeds {target_kernel_size} bytes")
        sys.exit(1)

    kernel_padded = kernel_bytes.ljust(target_kernel_size, b"\x00")

    # 5. Write combined image
    disk_data = boot_bytes + kernel_padded
    with open(COMBINED_BIN, "wb") as f:
        f.write(disk_data)
    with open(IMG_BIN, "wb") as f:
        f.write(disk_data)

    print(f"[+] Generated boot image: {len(disk_data)} bytes ({len(disk_data)//512} sectors)")
    print(f"    - {os.path.relpath(COMBINED_BIN, BASE_DIR)}")
    print(f"    - {os.path.relpath(IMG_BIN, BASE_DIR)}")


def run_qemu(headless=False):
    qemu_cmd = [
        "qemu-system-x86_64",
        "-drive", f"format=raw,file={COMBINED_BIN}",
        "-serial", "stdio"
    ]
    if headless:
        qemu_cmd.extend(["-display", "none"])
    print(f"[*] Launching QEMU: {' '.join(qemu_cmd)}")
    subprocess.run(qemu_cmd)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kale OS Build and Run tool")
    parser.add_argument("--run", action="store_true", help="Launch QEMU after build")
    parser.add_argument("--headless", action="store_true", help="Run QEMU headlessly with serial stdio")
    args = parser.parse_args()

    build_image()
    if args.run:
        run_qemu(headless=args.headless)

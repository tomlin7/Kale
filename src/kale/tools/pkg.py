"""Package archiver and cryptographic manifest generator for the Kale Package Registry."""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
from pathlib import Path


def create_package(package_dir: str, out_file: str | None = None) -> int:
    pkg_path = Path(package_dir)
    if not pkg_path.exists() or not pkg_path.is_dir():
        print(f"Error: Directory '{package_dir}' does not exist.", file=sys.stderr)
        return 1

    manifest_file = pkg_path / "kale.toml"
    name = pkg_path.name
    version = "0.1.0"

    archive_name = out_file or f"{name}-{version}.kpkg"
    out_path = Path(archive_name)

    print(f"\033[1;34m[kale package]\033[0m Building distribution archive '{archive_name}' from '{package_dir}'...")

    files_to_pack = []
    hasher = hashlib.sha256()

    for item in pkg_path.rglob("*"):
        if item.is_file() and not item.name.endswith((".kpkg", ".tmp", ".exe", ".pdb")):
            files_to_pack.append(item)
            hasher.update(item.read_bytes())

    checksum = hasher.hexdigest()

    # Create metadata manifest
    meta = {
        "name": name,
        "version": version,
        "format": "kpkg-v1",
        "file_count": len(files_to_pack),
        "sha256": checksum,
    }

    with tarfile.open(out_path, "w:gz") as tar:
        for f in files_to_pack:
            arcname = f.relative_to(pkg_path)
            tar.add(f, arcname=str(arcname))

        # Add manifest
        manifest_bytes = json.dumps(meta, indent=2).encode("utf-8")
        import io
        ti = tarfile.TarInfo(name=".kpkg-manifest.json")
        ti.size = len(manifest_bytes)
        tar.addfile(ti, io.BytesIO(manifest_bytes))

    print(f"\033[1;32m[kale package]\033[0m Created '{archive_name}' ({out_path.stat().st_size} bytes)")
    print(f"  SHA-256 Checksum: {checksum}")
    print(f"  Files packed:     {len(files_to_pack)}")
    return 0


def verify_package(archive_path: str) -> int:
    p = Path(archive_path)
    if not p.exists():
        print(f"Error: Archive '{archive_path}' not found.", file=sys.stderr)
        return 1

    try:
        with tarfile.open(p, "r:gz") as tar:
            manifest_member = tar.getmember(".kpkg-manifest.json")
            f = tar.extractfile(manifest_member)
            if f:
                meta = json.loads(f.read().decode("utf-8"))
                print(f"\033[1;32m[kale package]\033[0m Archive '{p.name}' is valid.")
                print(f"  Package: {meta.get('name')} v{meta.get('version')}")
                print(f"  Format:  {meta.get('format')}")
                print(f"  SHA-256: {meta.get('sha256')}")
                return 0
    except Exception as e:
        print(f"Error verifying archive: {e}", file=sys.stderr)
        return 1
    return 0

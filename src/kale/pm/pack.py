"""Packaging tool for creating reproducible `.kale-pkg` (tar.gz) archives."""

import os
import gzip
import tarfile
import hashlib
import fnmatch
from typing import List, Tuple, Optional
from .manifest import Manifest

EXCLUDE_PATTERNS = [
    ".git*",
    "bin",
    "bin/*",
    "dist",
    "dist/*",
    "build",
    "build/*",
    ".kale*",
    ".pytest_cache*",
    ".venv*",
    "__pycache__*",
    "*.pyc",
    "*.tmp.*",
    "*.ll",
    "*.o",
    "*.exe",
    "*.kale-pkg",
    "*.sha256",
]

REPRODUCIBLE_MTIME = 1700000000  # Fixed epoch timestamp for reproducible archives


def _is_excluded(rel_path: str) -> bool:
    norm = rel_path.replace("\\", "/")
    parts = norm.split("/")
    for part in parts:
        if part in {".git", ".kale", "bin", "dist", "build", "__pycache__", ".pytest_cache", ".venv"}:
            return True
    for pat in EXCLUDE_PATTERNS:
        if fnmatch.fnmatch(norm, pat) or fnmatch.fnmatch(os.path.basename(norm), pat):
            return True
    return False


def pack_project(
    project_dir: str = ".",
    output_dir: Optional[str] = None,
) -> Tuple[str, str]:
    """Packs a Kale project into a reproducible `.kale-pkg` archive with SHA-256 checksum."""
    proj_dir = os.path.abspath(project_dir)
    manifest_file = os.path.join(proj_dir, "kale.toml")
    if not os.path.isfile(manifest_file):
        raise FileNotFoundError(f"No kale.toml found in '{proj_dir}'. Cannot pack.")

    manifest = Manifest.load(manifest_file)
    if not manifest.name or not manifest.version:
        raise ValueError("Package manifest must specify 'name' and 'version'.")

    out_dir = os.path.abspath(output_dir or os.path.join(proj_dir, "dist"))
    os.makedirs(out_dir, exist_ok=True)

    archive_name = f"{manifest.name}-{manifest.version}.kale-pkg"
    archive_path = os.path.join(out_dir, archive_name)

    # Collect files to pack
    files_to_pack: List[str] = []

    # Essential files
    for root, dirs, files in os.walk(proj_dir):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if not _is_excluded(os.path.relpath(os.path.join(root, d), proj_dir))]

        for file in files:
            full_path = os.path.join(root, file)
            rel = os.path.relpath(full_path, proj_dir)
            if not _is_excluded(rel):
                files_to_pack.append(rel)

    # Sort files deterministically
    files_to_pack.sort()

    # Build reproducible tar.gz with fixed gzip mtime and pax headers
    with open(archive_path, "wb") as f_out:
        with gzip.GzipFile(filename="", mode="wb", fileobj=f_out, mtime=REPRODUCIBLE_MTIME) as gz_out:
            with tarfile.open(mode="w", fileobj=gz_out, format=tarfile.PAX_FORMAT) as tar:
                for rel in files_to_pack:
                    abs_p = os.path.join(proj_dir, rel)
                    arcname = rel.replace("\\", "/")
                    tarinfo = tar.gettarinfo(abs_p, arcname=arcname)
                    tarinfo.uid = 0
                    tarinfo.gid = 0
                    tarinfo.uname = ""
                    tarinfo.gname = ""
                    tarinfo.mtime = REPRODUCIBLE_MTIME
                    if tarinfo.isreg():
                        tarinfo.mode = 0o644
                        with open(abs_p, "rb") as f:
                            tar.addfile(tarinfo, f)
                    else:
                        tar.addfile(tarinfo)

    # Compute SHA-256
    hasher = hashlib.sha256()
    with open(archive_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    checksum = hasher.hexdigest()

    checksum_file = f"{archive_path}.sha256"
    with open(checksum_file, "w", encoding="utf-8") as f:
        f.write(f"{checksum} *{archive_name}\n")

    return archive_path, checksum

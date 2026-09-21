"""
src/kale/tools/bundle.py
Single-bundle distribution packager for Kale applications and assets.
"""

import sys
import os
import shutil
import zipfile
from typing import List, Optional


def bundle_application(
    executable_path: str,
    output_dir: str = "dist",
    create_zip: bool = False,
    extra_assets: Optional[List[str]] = None
) -> int:
    if not os.path.isfile(executable_path):
        print(f"Error: Target executable '{executable_path}' not found.", file=sys.stderr)
        return 1

    app_name = os.path.splitext(os.path.basename(executable_path))[0]
    bundle_name = f"{app_name}-bundle"
    target_bundle_dir = os.path.join(output_dir, bundle_name)

    os.makedirs(target_bundle_dir, exist_ok=True)
    print(f"Creating Kale App Bundle: '{bundle_name}' in '{target_bundle_dir}'...")

    # 1. Copy main executable
    dest_exe = os.path.join(target_bundle_dir, os.path.basename(executable_path))
    shutil.copy2(executable_path, dest_exe)
    print(f"  -> Copied binary: {os.path.basename(executable_path)}")

    # 2. Discover and copy runtime DLLs if present
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    candidate_dlls = [
        os.path.join(repo_root, "sqlite3.dll"),
        os.path.join(repo_root, "bin", "sqlite3.dll"),
        os.path.join(repo_root, "libs", "sql", "bin", "sqlite3.dll"),
    ]
    for dll_p in candidate_dlls:
        if os.path.isfile(dll_p):
            dest_dll = os.path.join(target_bundle_dir, os.path.basename(dll_p))
            if not os.path.exists(dest_dll):
                shutil.copy2(dll_p, dest_dll)
                print(f"  -> Included runtime library: {os.path.basename(dll_p)}")

    # 3. Copy extra assets or default fonts
    if extra_assets:
        for asset in extra_assets:
            if os.path.exists(asset):
                dest_asset = os.path.join(target_bundle_dir, os.path.basename(asset))
                if os.path.isdir(asset):
                    shutil.copytree(asset, dest_asset, dirs_exist_ok=True)
                else:
                    shutil.copy2(asset, dest_asset)
                print(f"  -> Included asset: {asset}")

    # 4. Generate Launcher script for Windows / Unix
    launcher_bat = os.path.join(target_bundle_dir, f"run_{app_name}.cmd")
    with open(launcher_bat, "w", encoding="utf-8") as f:
        f.write(f"@echo off\ncd /d \"%~dp0\"\nstart \"\" \"{os.path.basename(executable_path)}\" %*\n")
    print(f"  -> Created launcher: {os.path.basename(launcher_bat)}")

    # 5. Optionally create zip
    if create_zip:
        zip_path = os.path.join(output_dir, f"{bundle_name}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(target_bundle_dir):
                for file in files:
                    full_p = os.path.join(root, file)
                    rel_p = os.path.relpath(full_p, target_bundle_dir)
                    zf.write(full_p, arcname=rel_p)
        print(f"  -> Compressed archive created: {zip_path}")

    print(f"Bundle completed successfully! Target: {target_bundle_dir}")
    return 0


def run_bundle(args) -> int:
    exe = getattr(args, "target", None)
    if not exe:
        print("Usage: kale bundle <executable_path> [--out <dir>] [--zip]", file=sys.stderr)
        return 1
    out_dir = getattr(args, "out", "dist") or "dist"
    make_zip = getattr(args, "zip", False)
    assets = getattr(args, "assets", []) or []
    return bundle_application(executable_path=exe, output_dir=out_dir, create_zip=make_zip, extra_assets=assets)

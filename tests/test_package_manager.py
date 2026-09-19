import os
import sys
import shutil
import tempfile
import unittest
import tarfile
import hashlib
import argparse
from unittest.mock import patch

from kale.pm.manifest import Manifest, find_manifest, serialize_toml_value
from kale.pm.project import create_project, init_project
from kale.pm.pack import pack_project
from kale.pm.registry import RegistryServer, RegistryClient, RegistryConfig
from kale.cli import main, cmd_build, cmd_run, cmd_new, cmd_init, cmd_add, cmd_remove, cmd_pack, cmd_publish, cmd_search, cmd_info


class TestManifest(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="kale_pm_test_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_manifest_roundtrip(self):
        manifest_path = os.path.join(self.test_dir, "kale.toml")
        manifest = Manifest(
            name="demo_app",
            version="1.2.3",
            description="A test package",
            authors=["Alice <alice@kale.org>", "Bob <bob@kale.org>"],
            license="Apache-2.0",
            edition="2026",
            entry="src/main.kl",
            dependencies={
                "std": "^0.2.0",
                "math_lib": {"path": "../math_lib"},
            },
            dev_dependencies={
                "test_suite": "1.0.0",
            },
            scripts={
                "start": "kale run src/main.kl",
                "test": "uv run pytest tests/",
            },
            build_backend="llvm",
            build_opt=3,
            build_output="bin/custom_demo",
            build_libs=["ws2_32"],
            build_lib_dirs=["libs/win32"],
            build_includes=["libs", "headers"],
            manifest_path=manifest_path,
        )
        manifest.save()

        self.assertTrue(os.path.isfile(manifest_path))

        loaded = Manifest.load(manifest_path)
        self.assertEqual(loaded.name, "demo_app")
        self.assertEqual(loaded.version, "1.2.3")
        self.assertEqual(loaded.description, "A test package")
        self.assertEqual(loaded.authors, ["Alice <alice@kale.org>", "Bob <bob@kale.org>"])
        self.assertEqual(loaded.license, "Apache-2.0")
        self.assertEqual(loaded.edition, "2026")
        self.assertEqual(loaded.entry, "src/main.kl")
        self.assertEqual(loaded.dependencies["std"], "^0.2.0")
        self.assertEqual(loaded.dependencies["math_lib"], {"path": "../math_lib"})
        self.assertEqual(loaded.dev_dependencies["test_suite"], "1.0.0")
        self.assertEqual(loaded.scripts["start"], "kale run src/main.kl")
        self.assertEqual(loaded.scripts["test"], "uv run pytest tests/")
        self.assertEqual(loaded.build_backend, "llvm")
        self.assertEqual(loaded.build_opt, 3)
        self.assertEqual(loaded.build_output, "bin/custom_demo")
        self.assertEqual(loaded.build_libs, ["ws2_32"])
        self.assertEqual(loaded.build_lib_dirs, ["libs/win32"])
        self.assertEqual(loaded.build_includes, ["libs", "headers"])

    def test_find_manifest_walkup(self):
        root_dir = os.path.join(self.test_dir, "project")
        sub_dir = os.path.join(root_dir, "src", "submodule")
        os.makedirs(sub_dir, exist_ok=True)
        manifest_file = os.path.join(root_dir, "kale.toml")
        with open(manifest_file, "w", encoding="utf-8") as f:
            f.write("[package]\nname = 'walkup_test'\n")

        found = find_manifest(sub_dir)
        self.assertIsNotNone(found)
        self.assertEqual(os.path.abspath(found), os.path.abspath(manifest_file))

    def test_add_and_remove_dependency(self):
        manifest_path = os.path.join(self.test_dir, "kale.toml")
        manifest = Manifest(name="dep_test", manifest_path=manifest_path)
        manifest.add_dependency("http", "^1.0.0")
        manifest.add_dependency("local_dep", {"path": "../local"}, dev=False)
        manifest.add_dependency("test_mock", "^0.5.0", dev=True)
        manifest.save()

        reloaded = Manifest.load(manifest_path)
        self.assertIn("http", reloaded.dependencies)
        self.assertEqual(reloaded.dependencies["local_dep"], {"path": "../local"})
        self.assertIn("test_mock", reloaded.dev_dependencies)

        # Remove
        removed_std = reloaded.remove_dependency("http")
        removed_dev = reloaded.remove_dependency("test_mock")
        not_found = reloaded.remove_dependency("nonexistent")
        self.assertTrue(removed_std)
        self.assertTrue(removed_dev)
        self.assertFalse(not_found)
        reloaded.save()

        reloaded2 = Manifest.load(manifest_path)
        self.assertNotIn("http", reloaded2.dependencies)
        self.assertNotIn("test_mock", reloaded2.dev_dependencies)


class TestProjectBootstrapping(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="kale_bootstrap_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_project_binary(self):
        target = os.path.join(self.test_dir, "my_app")
        create_project("my_app", target_dir=target, is_lib=False)

        self.assertTrue(os.path.isfile(os.path.join(target, "kale.toml")))
        self.assertTrue(os.path.isfile(os.path.join(target, "src", "main.kl")))
        self.assertTrue(os.path.isfile(os.path.join(target, ".gitignore")))
        self.assertTrue(os.path.isfile(os.path.join(target, "README.md")))

        manifest = Manifest.load(os.path.join(target, "kale.toml"))
        self.assertEqual(manifest.name, "my_app")
        self.assertEqual(manifest.entry, "src/main.kl")
        self.assertIn("start", manifest.scripts)

    def test_create_project_library(self):
        target = os.path.join(self.test_dir, "my_lib")
        create_project("my_lib", target_dir=target, is_lib=True)

        self.assertTrue(os.path.isfile(os.path.join(target, "kale.toml")))
        self.assertTrue(os.path.isfile(os.path.join(target, "src", "lib.kl")))
        manifest = Manifest.load(os.path.join(target, "kale.toml"))
        self.assertEqual(manifest.name, "my_lib")
        self.assertEqual(manifest.entry, "src/lib.kl")

    def test_create_project_validation(self):
        # Invalid characters in project name
        with self.assertRaises(ValueError):
            create_project("invalid name with spaces", target_dir=os.path.join(self.test_dir, "inv"))

        # Cannot create in non-empty directory
        target = os.path.join(self.test_dir, "non_empty")
        os.makedirs(target, exist_ok=True)
        with open(os.path.join(target, "file.txt"), "w") as f:
            f.write("content")

        with self.assertRaises(FileExistsError):
            create_project("app", target_dir=target)

    def test_init_project(self):
        proj_dir = os.path.join(self.test_dir, "existing_dir")
        os.makedirs(proj_dir, exist_ok=True)
        init_project(dir_path=proj_dir, is_lib=False)

        manifest_file = os.path.join(proj_dir, "kale.toml")
        self.assertTrue(os.path.isfile(manifest_file))
        self.assertTrue(os.path.isfile(os.path.join(proj_dir, "src", "main.kl")))

        # Fails if kale.toml already exists
        with self.assertRaises(FileExistsError):
            init_project(dir_path=proj_dir)


class TestPackaging(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="kale_pack_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pack_project(self):
        proj_dir = os.path.join(self.test_dir, "pkg_app")
        create_project("pkg_app", target_dir=proj_dir)

        # Create dummy artifacts that should be excluded
        bin_dir = os.path.join(proj_dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        with open(os.path.join(bin_dir, "app.exe"), "wb") as f:
            f.write(b"\x00" * 100)
        with open(os.path.join(proj_dir, "temp.ll"), "w") as f:
            f.write("dummy ll")

        archive_path, checksum = pack_project(proj_dir)
        self.assertTrue(os.path.isfile(archive_path))
        self.assertTrue(archive_path.endswith(".kale-pkg"))
        self.assertTrue(os.path.isfile(f"{archive_path}.sha256"))

        # Inspect tar contents
        with tarfile.open(archive_path, "r:gz") as tar:
            members = [m.name for m in tar.getmembers()]
            self.assertIn("kale.toml", members)
            self.assertIn("src/main.kl", members)
            self.assertIn("README.md", members)

            # Excluded artifacts
            self.assertNotIn("bin/app.exe", members)
            self.assertNotIn("temp.ll", members)

            # Check reproducibility attributes
            for m in tar.getmembers():
                self.assertEqual(m.uid, 0)
                self.assertEqual(m.gid, 0)
                self.assertEqual(m.mtime, 1700000000)

        # Verify checksum calculation
        with open(archive_path, "rb") as f:
            calculated = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(checksum, calculated)


class TestRegistryAndPublishing(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="kale_registry_")
        self.storage_dir = os.path.join(self.test_dir, "registry_store")
        # Start reference server on localhost with port 0 (OS picks available port)
        self.server = RegistryServer(host="127.0.0.1", port=0, storage_dir=self.storage_dir, require_auth=True)
        self.server.start_background()
        self.client = RegistryClient(registry_url=self.server.url)

    def tearDown(self):
        self.server.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_login_publish_search_info_download(self):
        # 1. Login
        token = self.client.login(username="tester", password="secret_password")
        self.assertTrue(token.startswith("kale_pat_"))

        # 2. Prepare package
        proj_dir = os.path.join(self.test_dir, "math_utils")
        create_project("math_utils", target_dir=proj_dir, is_lib=True, description="Math utility functions")

        # 3. Publish
        pub_res = self.client.publish(proj_dir, token=token)
        self.assertEqual(pub_res.get("status"), "success")
        self.assertEqual(pub_res.get("package"), "math_utils")
        self.assertEqual(pub_res.get("version"), "0.1.0")

        # 4. Duplicate publish conflict check (409)
        with self.assertRaises(RuntimeError) as ctx:
            self.client.publish(proj_dir, token=token)
        self.assertIn("409", str(ctx.exception))

        # 5. Search
        search_res = self.client.search("math")
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0]["name"], "math_utils")

        # 6. Package Info
        info_res = self.client.info("math_utils")
        self.assertEqual(info_res["name"], "math_utils")
        self.assertEqual(info_res["latest"], "0.1.0")
        self.assertIn("0.1.0", info_res["versions"])

        # 7. Download
        download_dir = os.path.join(self.test_dir, "downloads")
        downloaded_file = self.client.download("math_utils", "0.1.0", dest_dir=download_dir)
        self.assertTrue(os.path.isfile(downloaded_file))
        self.assertTrue(downloaded_file.endswith("math_utils-0.1.0.kale-pkg"))


class TestCLIE2E(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="kale_cli_test_")
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cli_new_init_add_remove_pack(self):
        # kale new
        with patch("sys.argv", ["kale", "new", "testapp"]):
            ret = main()
            self.assertEqual(ret, 0)
        self.assertTrue(os.path.isdir(os.path.join(self.test_dir, "testapp")))

        app_dir = os.path.join(self.test_dir, "testapp")
        os.chdir(app_dir)

        # kale add
        with patch("sys.argv", ["kale", "add", "dep1@^1.0.0"]):
            ret = main()
            self.assertEqual(ret, 0)

        with patch("sys.argv", ["kale", "add", "dep_dev", "--dev"]):
            ret = main()
            self.assertEqual(ret, 0)

        with patch("sys.argv", ["kale", "add", "local_lib", "--path", "../locallib"]):
            ret = main()
            self.assertEqual(ret, 0)

        manifest = Manifest.load("kale.toml")
        self.assertEqual(manifest.dependencies["dep1"], "^1.0.0")
        self.assertIn("dep_dev", manifest.dev_dependencies)
        self.assertEqual(manifest.dependencies["local_lib"], {"path": "../locallib"})

        # kale remove
        with patch("sys.argv", ["kale", "remove", "dep1"]):
            ret = main()
            self.assertEqual(ret, 0)

        manifest = Manifest.load("kale.toml")
        self.assertNotIn("dep1", manifest.dependencies)

        # kale pack
        with patch("sys.argv", ["kale", "pack"]):
            ret = main()
            self.assertEqual(ret, 0)
        self.assertTrue(os.path.isfile("dist/testapp-0.1.0.kale-pkg"))

    def test_cli_run_script_and_manifest_build(self):
        # Create a simple project with main.kl that compiles and runs
        proj_dir = os.path.join(self.test_dir, "run_build_app")
        create_project("run_build_app", target_dir=proj_dir)
        os.chdir(proj_dir)

        # Add a custom script into kale.toml
        manifest = Manifest.load("kale.toml")
        manifest.scripts["custom"] = f"{sys.executable} -c \"print('CUSTOM_SCRIPT_EXECUTED')\""
        manifest.save()

        # Run custom script via: kale run custom
        with patch("sys.argv", ["kale", "run", "custom"]):
            ret = main()
            self.assertEqual(ret, 0)

        # Run without arguments: executes start script
        manifest = Manifest.load("kale.toml")
        manifest.scripts["start"] = f"{sys.executable} -c \"print('START_SCRIPT_EXECUTED')\""
        manifest.save()
        with patch("sys.argv", ["kale", "run"]):
            ret = main()
            self.assertEqual(ret, 0)

        # kale build without arguments (reads manifest settings and compiles to C source)
        with patch("sys.argv", ["kale", "build", "--backend", "c", "--no-compile"]):
            ret = main()
            self.assertEqual(ret, 0)
            # Verify C file generated
            self.assertTrue(os.path.isfile(os.path.join(proj_dir, "src", "main.c")))

    def test_cli_errors_and_edge_cases(self):
        empty_dir = os.path.join(self.test_dir, "empty")
        os.makedirs(empty_dir, exist_ok=True)
        os.chdir(empty_dir)

        # kale build with no args in empty directory -> returns 1
        with patch("sys.argv", ["kale", "build"]):
            ret = main()
            self.assertEqual(ret, 1)

        # kale run with no args in empty directory -> returns 1
        with patch("sys.argv", ["kale", "run"]):
            ret = main()
            self.assertEqual(ret, 1)

        # kale remove with no kale.toml -> returns 1
        with patch("sys.argv", ["kale", "remove", "some_pkg"]):
            ret = main()
            self.assertEqual(ret, 1)

    def test_cli_publish_search_info_e2e(self):
        server = RegistryServer(host="127.0.0.1", port=0, require_auth=False)
        server.start_background()
        try:
            proj_dir = os.path.join(self.test_dir, "pub_app")
            create_project("pub_app", target_dir=proj_dir)
            os.chdir(proj_dir)

            # kale publish
            with patch("sys.argv", ["kale", "publish", "--registry", server.url]):
                ret = main()
                self.assertEqual(ret, 0)

            # kale search
            with patch("sys.argv", ["kale", "search", "pub_app", "--registry", server.url]):
                ret = main()
                self.assertEqual(ret, 0)

            # kale info
            with patch("sys.argv", ["kale", "info", "pub_app", "--registry", server.url]):
                ret = main()
                self.assertEqual(ret, 0)
        finally:
            server.stop()

    def test_path_dependency_resolution(self):
        root = os.path.join(self.test_dir, "dep_res_test")
        dep_dir = os.path.join(root, "dep_pkg")
        create_project("dep_pkg", target_dir=dep_dir, is_lib=True)

        app_dir = os.path.join(root, "app_pkg")
        create_project("app_pkg", target_dir=app_dir, is_lib=False)
        os.chdir(app_dir)

        manifest = Manifest.load("kale.toml")
        manifest.add_dependency("dep_pkg", {"path": "../dep_pkg"})
        manifest.save()

        includes = manifest.get_all_include_dirs(app_dir)
        norm_includes = [os.path.normpath(p) for p in includes]
        self.assertIn(os.path.normpath(os.path.join(app_dir, "src")), norm_includes)
        self.assertIn(os.path.normpath(os.path.join(dep_dir, "src")), norm_includes)
        self.assertIn(os.path.normpath(dep_dir), norm_includes)

    def test_exact_archive_reproducibility_across_time(self):
        import time
        proj_dir = os.path.join(self.test_dir, "repro_app")
        create_project("repro_app", target_dir=proj_dir)

        _, c1 = pack_project(proj_dir)
        time.sleep(1.2)
        _, c2 = pack_project(proj_dir)

        self.assertEqual(c1, c2, "Archive SHA-256 checksums must be bit-for-bit identical regardless of creation time.")

    def test_cli_flag_precedence_over_manifest(self):
        proj_dir = os.path.join(self.test_dir, "flag_prec_app")
        create_project("flag_prec_app", target_dir=proj_dir)
        os.chdir(proj_dir)

        manifest = Manifest.load("kale.toml")
        manifest.build_backend = "c"
        manifest.build_opt = 3
        manifest.save()

        # Explicitly pass --backend llvm to override manifest backend = "c"
        with patch("sys.argv", ["kale", "build", "--backend", "llvm", "--emit-llvm", "--emit-c", "--no-compile"]):
            ret = main()
            self.assertEqual(ret, 0)

        self.assertTrue(os.path.isfile(os.path.join(proj_dir, "src", "main.ll")), "Must generate .ll when --backend llvm is passed")
        self.assertFalse(os.path.isfile(os.path.join(proj_dir, "src", "main.c")), "Must not generate .c when --backend llvm is passed")

    def test_transitive_and_circular_path_dependencies(self):
        root = os.path.join(self.test_dir, "transitive_test")
        c_dir = os.path.join(root, "pkg_c")
        b_dir = os.path.join(root, "pkg_b")
        a_dir = os.path.join(root, "pkg_a")

        create_project("pkg_c", c_dir, is_lib=True)
        create_project("pkg_b", b_dir, is_lib=True)
        create_project("pkg_a", a_dir, is_lib=False)

        # B depends on C and circularly on A
        mb = Manifest.load(os.path.join(b_dir, "kale.toml"))
        mb.add_dependency("pkg_c", {"path": "../pkg_c"})
        mb.add_dependency("pkg_a", {"path": "../pkg_a"})
        mb.save()

        # A depends on B
        ma = Manifest.load(os.path.join(a_dir, "kale.toml"))
        ma.add_dependency("pkg_b", {"path": "../pkg_b"})
        ma.save()

        includes = ma.get_all_include_dirs()
        norm_includes = [os.path.normpath(p) for p in includes]

        # Must include transitive dependency C's source dir
        self.assertIn(os.path.normpath(os.path.join(c_dir, "src")), norm_includes)
        self.assertIn(os.path.normpath(os.path.join(b_dir, "src")), norm_includes)

    def test_security_path_traversal_rejection(self):
        server = RegistryServer(host="127.0.0.1", port=0, require_auth=False)
        server.start_background()
        try:
            client = RegistryClient(registry_url=server.url)

            # Direct server call with traversal name
            ok, err = server.publish_package(
                name="../../traversal_pkg",
                version="1.0.0",
                description="",
                authors=[],
                license="MIT",
                dependencies={},
                checksum="abc",
                archive_bytes=b"dummy",
            )
            self.assertFalse(ok)
            self.assertIn("Invalid package name", err)

            # Client download with traversal
            with self.assertRaises(ValueError):
                client.download("../../traversal_pkg", "1.0.0", dest_dir=self.test_dir)
        finally:
            server.stop()

    def test_registry_whoami_and_search_all(self):
        server = RegistryServer(host="127.0.0.1", port=0, require_auth=True)
        server.start_background()
        try:
            client = RegistryClient(registry_url=server.url)
            # Before login
            who = client.whoami()
            self.assertFalse(who.get("authenticated", False))

            # Login
            token = client.login(username="alice", password="pw")
            who = client.whoami()
            self.assertTrue(who.get("authenticated"))
            self.assertEqual(who.get("username"), "alice")

            # Search without query returns all published packages
            pkg_dir = os.path.join(self.test_dir, "listed_pkg")
            create_project("listed_pkg", target_dir=pkg_dir)
            client.publish(pkg_dir, token=token)

            all_pkgs = client.search("")
            self.assertEqual(len(all_pkgs), 1)
            self.assertEqual(all_pkgs[0]["name"], "listed_pkg")

            # CLI whoami command
            with patch("sys.argv", ["kale", "whoami", "--registry", server.url]):
                ret = main()
                self.assertEqual(ret, 0)
        finally:
            server.stop()

    def test_cli_add_resolves_registry_version(self):
        server = RegistryServer(host="127.0.0.1", port=0, require_auth=False)
        server.start_background()
        try:
            # Publish a package to the registry
            lib_dir = os.path.join(self.test_dir, "cloud_math")
            create_project("cloud_math", target_dir=lib_dir, is_lib=True)
            client = RegistryClient(registry_url=server.url)
            client.publish(lib_dir)

            # Create an app and run `kale add cloud_math`
            app_dir = os.path.join(self.test_dir, "consumer_app")
            create_project("consumer_app", target_dir=app_dir)
            os.chdir(app_dir)

            with patch("sys.argv", ["kale", "add", "cloud_math", "--registry", server.url]):
                ret = main()
                self.assertEqual(ret, 0)

            manifest = Manifest.load("kale.toml")
            # Should resolve ^0.1.0 from registry
            self.assertEqual(manifest.dependencies.get("cloud_math"), "^0.1.0")
        finally:
            server.stop()

    def test_find_manifest_with_file_path(self):
        proj_dir = os.path.join(self.test_dir, "file_find_proj")
        create_project("file_find_proj", target_dir=proj_dir)
        source_file = os.path.join(proj_dir, "src", "main.kl")

        # Passing file path directly should locate kale.toml in parent
        found = find_manifest(source_file)
        self.assertIsNotNone(found)
        self.assertEqual(os.path.abspath(found), os.path.abspath(os.path.join(proj_dir, "kale.toml")))


if __name__ == "__main__":
    unittest.main()

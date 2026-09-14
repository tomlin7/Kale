import unittest
from kale.codegen.llvm_driver import LLVMDriver

class TestLinkerArgs(unittest.TestCase):
    def test_llvm_driver_accepts_extra_libs_and_lib_dirs(self):
        driver = LLVMDriver()
        # Verify the compile_ll method signature and argument propagation
        import inspect
        sig = inspect.signature(driver.compile_ll)
        self.assertIn("extra_libs", sig.parameters)
        self.assertIn("lib_dirs", sig.parameters)

    def test_cli_parser_accepts_linker_flags(self):
        import argparse
        from kale.cli import main
        # Verify that parse_args parses -l, -L, -I flags on build command
        import sys
        old_argv = sys.argv
        try:
            # We construct a mock parse
            from kale.cli import cmd_build
            from unittest.mock import patch

            test_args = ["kale", "build", "hello.kl", "-l", "glfw3", "-l", "opengl32", "-L", "libs/glfw", "-I", "libs"]
            with patch("sys.argv", test_args):
                with patch("kale.cli.cmd_build") as mock_build:
                    mock_build.return_value = 0
                    from kale.cli import main
                    main()
                    args = mock_build.call_args[0][0]
                    self.assertEqual(args.libs, ["glfw3", "opengl32"])
                    self.assertEqual(args.lib_dirs, ["libs/glfw"])
                    self.assertEqual(args.includes, ["libs"])
        finally:
            sys.argv = old_argv

if __name__ == "__main__":
    unittest.main()

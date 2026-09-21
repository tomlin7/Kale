"""
src/kale/tools/repl.py
Interactive REPL (Read-Eval-Print Loop) for Kale.
Evaluates expressions, declarations, and statements on the fly via the LLVM JIT.
"""

import sys
import os
from typing import List

from ..diagnostics.source_text import SourceText
from ..diagnostics.diagnostic_bag import DiagnosticBag
from ..parser.parser import Parser
from ..binding.binder import Binder
from ..binding.module_loader import ModuleLoader
from ..codegen.llvm_emitter import LLVMEmitter
from ..codegen.llvm_jit import LLVMJIT


BANNER = r"""
  _  __     _      
 | |/ /__ _| | ___ 
 | ' </ _` | |/ -_)
 |_|\_\__,_|_|\___|  Interactive REPL v0.1.0
Type :help for commands, :quit or Ctrl+D to exit.
"""

HELP_TEXT = """
REPL Commands:
  :help          Show this help message
  :quit / :exit  Exit the REPL
  :clear         Clear session history
  :ir            Toggle dumping emitted LLVM IR
"""

class KaleRepl:
    def __init__(self, opt_level: int = 0):
        self.opt_level = opt_level
        self.show_ir = False
        self.history: List[str] = []
        self.accumulated_decls: List[str] = []

    def start(self):
        print(BANNER)
        buffer: List[str] = []

        while True:
            try:
                prompt = "kale> " if not buffer else " ...> "
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            stripped = line.strip()

            # Command handling
            if not buffer and stripped.startswith(":"):
                cmd = stripped.lower()
                if cmd in (":quit", ":exit", ":q"):
                    print("Goodbye!")
                    break
                elif cmd in (":help", ":h", ":?"):
                    print(HELP_TEXT)
                    continue
                elif cmd in (":clear", ":cls"):
                    self.history.clear()
                    self.accumulated_decls.clear()
                    print("Session cleared.")
                    continue
                elif cmd == ":ir":
                    self.show_ir = not self.show_ir
                    print(f"Dump LLVM IR: {'ON' if self.show_ir else 'OFF'}")
                    continue
                else:
                    print(f"Unknown command: {stripped}. Type :help for commands.")
                    continue

            # Multi-line buffering: check if line ends with '\' or open braces
            buffer.append(line)
            combined = "\n".join(buffer)

            # Simple brace count
            opens = combined.count("{")
            closes = combined.count("}")
            if opens > closes or line.rstrip().endswith("\\"):
                continue

            # Complete input received
            source_input = combined
            buffer.clear()

            if not source_input.strip():
                continue

            self._eval(source_input)

    def _wrap_code(self, code: str) -> str:
        # Check if code is already a full function/compilation unit
        trimmed = code.strip()
        if trimmed.startswith("fn ") or trimmed.startswith("struct ") or trimmed.startswith("extern "):
            return code

        # Wrap in a runnable main function
        wrapped_lines = []
        wrapped_lines.append('extern int printf(string fmt, ...);')
        for d in self.accumulated_decls:
            wrapped_lines.append(d)

        wrapped_lines.append('fn int main() {')
        # If it's a simple expression like `1 + 2`, add print
        if not trimmed.endswith(";") and not trimmed.endswith("}"):
            wrapped_lines.append(f'    print({trimmed});')
        else:
            wrapped_lines.append(f'    {trimmed}')
        wrapped_lines.append('    return 0;')
        wrapped_lines.append('}')
        return "\n".join(wrapped_lines)

    def _eval(self, code: str):
        full_code = self._wrap_code(code)

        source_text = SourceText(full_code, file_name="<repl>")
        diagnostics = DiagnosticBag()

        try:
            parser = Parser(source_text, diagnostics)
            unit = parser.parse_compilation_unit()

            # If top-level declaration (fn, struct), store in accumulated declarations
            stripped = code.strip()
            if stripped.startswith("fn ") or stripped.startswith("struct ") or stripped.startswith("extern "):
                if not diagnostics.has_errors:
                    self.accumulated_decls.append(code)
                    print("Defined.")
                    return

            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            search_paths = [os.path.abspath("."), os.path.join(repo_root, "packages", "std"), os.path.join(repo_root, "libs")]
            loader = ModuleLoader(diagnostics, search_paths=search_paths)
            binder = Binder(diagnostics, module_loader=loader, current_file="<repl>")
            program = binder.bind_program(unit)

            if diagnostics.has_errors:
                for diag in diagnostics:
                    print(source_text.format_diagnostic(diag), file=sys.stderr)
                return

            emitter = LLVMEmitter()
            mod = emitter.emit_module(program)
            ir_str = str(mod)

            if self.show_ir:
                print("\n── Emitted LLVM IR ──")
                print(ir_str)
                print("─────────────────────\n")

            jit = LLVMJIT(opt_level=self.opt_level)
            exit_code = jit.run_ir(ir_str)
            if exit_code != 0:
                print(f"[Exit code: {exit_code}]")

        except Exception as e:
            print(f"Evaluation error: {e}", file=sys.stderr)


def run_repl(opt_level: int = 0) -> int:
    repl = KaleRepl(opt_level=opt_level)
    repl.start()
    return 0

"""
src/kale/tools/fuzz.py
Mutation-based fuzzer for Kale compiler frontend (Lexer, Parser, Binder).
"""

import sys
import os
import random
import time
from typing import List, Optional

from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader

BASE_CORPUS = [
    'fn int main() { return 42; }',
    'struct Point { int x; int y; } fn void test() { Point p; p.x = 10; }',
    'fn int add(int a, int b) { if (a > 0) { return a + b; } else { return b; } }',
    'import "libs/render/math.kl" as rmath; fn void draw() { rmath.Color c; }',
    'fn void loop() { int i = 0; while (i < 100) { i = i + 1; if (i == 50) { break; } } }',
    'struct Node { Node* next; int val; } fn void foo() { Node* n = alloc(Node, 1); free(n); }',
    'enum State { Idle, Running, Stopped } fn int check(State s) { return 0; }',
]

MUTATION_OPS = [
    "delete_char",
    "insert_random",
    "swap_chars",
    "duplicate_line",
    "insert_keyword",
    "flip_bit",
    "truncate",
]

KEYWORDS = [
    "fn", "int", "float", "bool", "string", "void", "char", "struct", "enum",
    "if", "else", "while", "for", "return", "break", "continue", "import",
    "as", "alloc", "free", "true", "false", "null", "{", "}", "(", ")", ";", "=", "->", "."
]


def mutate(text: str) -> str:
    if not text:
        return random.choice(KEYWORDS)

    op = random.choice(MUTATION_OPS)
    chars = list(text)

    if op == "delete_char" and len(chars) > 1:
        idx = random.randint(0, len(chars) - 1)
        del chars[idx]
    elif op == "insert_random":
        idx = random.randint(0, len(chars))
        char = chr(random.randint(32, 126)) if random.random() > 0.3 else chr(random.randint(0, 255))
        chars.insert(idx, char)
    elif op == "swap_chars" and len(chars) > 1:
        idx = random.randint(0, len(chars) - 2)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
    elif op == "duplicate_line":
        lines = text.splitlines()
        if lines:
            line_idx = random.randint(0, len(lines) - 1)
            lines.insert(line_idx, lines[line_idx])
            return "\n".join(lines)
    elif op == "insert_keyword":
        idx = random.randint(0, len(chars))
        kw = " " + random.choice(KEYWORDS) + " "
        chars.insert(idx, kw)
    elif op == "flip_bit" and len(chars) > 0:
        idx = random.randint(0, len(chars) - 1)
        chars[idx] = chr(ord(chars[idx]) ^ (1 << random.randint(0, 7)))
    elif op == "truncate" and len(chars) > 4:
        trunc_len = random.randint(1, len(chars) - 1)
        chars = chars[:trunc_len]

    return "".join(chars)


def fuzz_compiler(iterations: int = 1000, out_dir: str = "tests/fuzz_corpus") -> int:
    os.makedirs(out_dir, exist_ok=True)
    crashes = 0
    start_time = time.time()

    current_corpus = list(BASE_CORPUS)
    print(f"Starting Kale compiler fuzzer: {iterations} iterations...")
    print(f"Initial seed corpus: {len(current_corpus)} templates.")

    for it in range(1, iterations + 1):
        seed = random.choice(current_corpus)
        mutated = mutate(seed)

        # Periodically add mutated valid-length text to corpus pool
        if len(current_corpus) < 200 and random.random() < 0.05:
            current_corpus.append(mutated)

        try:
            st = SourceText(mutated)
            diag = DiagnosticBag()
            loader = ModuleLoader([os.path.abspath(".")], diag)
            parser = Parser(st, diag)
            unit = parser.parse_compilation_unit()

            if not diag.has_errors:
                binder = Binder(diag, module_loader=loader)
                binder.bind_program(unit)

        except Exception as e:
            # An unhandled exception in parser/binder is a fuzzer finding!
            crashes += 1
            crash_file = os.path.join(out_dir, f"crash_{crashes}_{int(time.time())}.kl")
            with open(crash_file, "w", encoding="utf-8") as f:
                f.write(f"// Crash exception: {e}\n{mutated}")
            print(f"\n[CRASH FOUND #{crashes}] Saved repro to {crash_file} (Error: {e})")

        if it % 200 == 0 or it == iterations:
            elapsed = max(time.time() - start_time, 0.001)
            execs_per_sec = it / elapsed
            print(f"[{it}/{iterations}] {execs_per_sec:.1f} exec/s | Crashes: {crashes}")

    elapsed = time.time() - start_time
    print("-" * 60)
    print(f"Fuzzing completed in {elapsed:.2f}s. Total crashes: {crashes}")
    return 1 if crashes > 0 else 0


def run_fuzz(args) -> int:
    iterations = getattr(args, "iterations", 1000) or 1000
    out_dir = getattr(args, "out", "tests/fuzz_corpus") or "tests/fuzz_corpus"
    return fuzz_compiler(iterations=iterations, out_dir=out_dir)

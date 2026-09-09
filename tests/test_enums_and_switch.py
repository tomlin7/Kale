import pytest
from kale.syntax.lexer import Lexer
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT
from kale.codegen.c_emitter import CEmitter
from kale.ast.nodes import (
    EnumDeclarationStatement,
    SwitchStatement,
)
from kale.binding.bound_nodes import (
    BoundSwitchStatement,
)
from kale.binding.types import EnumTypeSymbol

def test_parse_enum_declaration():
    src = """
    enum Status {
        Idle,
        Running = 10,
        Finished,
        Failed = 500
    }
    """
    diagnostics = DiagnosticBag()
    parser = Parser(SourceText(src), diagnostics)
    unit = parser.parse_compilation_unit()
    assert not diagnostics.has_errors
    assert len(unit.statements) == 1
    stmt = unit.statements[0]
    assert isinstance(stmt, EnumDeclarationStatement)
    assert stmt.identifier_token.text == "Status"
    assert len(stmt.members) == 4
    assert stmt.members[0].identifier_token.text == "Idle"
    assert stmt.members[1].identifier_token.text == "Running"
    assert stmt.members[2].identifier_token.text == "Finished"
    assert stmt.members[3].identifier_token.text == "Failed"

def test_bind_enum_declaration():
    src = """
    enum Color {
        Red,
        Green = 5,
        Blue
    }
    Color c = Color.Green;
    print(c);
    """
    diagnostics = DiagnosticBag()
    parser = Parser(SourceText(src), diagnostics)
    unit = parser.parse_compilation_unit()
    binder = Binder(diagnostics)
    program = binder.bind_program(unit)
    assert not diagnostics.has_errors
    assert len(program.enums) == 1
    enum_sym = program.enums[0].enum_type
    assert isinstance(enum_sym, EnumTypeSymbol)
    assert enum_sym.get_member_value("Red") == 0
    assert enum_sym.get_member_value("Green") == 5
    assert enum_sym.get_member_value("Blue") == 6

def test_parse_and_bind_switch():
    src = """
    int x = 2;
    switch (x) {
        case 1:
            print(10);
            break;
        case 2:
            print(20);
            break;
        default:
            print(99);
    }
    """
    diagnostics = DiagnosticBag()
    parser = Parser(SourceText(src), diagnostics)
    unit = parser.parse_compilation_unit()
    assert not diagnostics.has_errors
    stmt = unit.statements[1]
    assert isinstance(stmt, SwitchStatement)
    assert len(stmt.cases) == 2
    assert stmt.default_clause is not None

    binder = Binder(diagnostics)
    program = binder.bind_program(unit)
    assert not diagnostics.has_errors
    bound_switch = program.statements[1]
    assert isinstance(bound_switch, BoundSwitchStatement)
    assert len(bound_switch.cases) == 2
    assert bound_switch.default_body is not None

def test_jit_switch_statement():
    src = """
    int evaluate(int val) {
        int result = 0;
        switch (val) {
            case 10:
                result = 100;
                break;
            case 20:
                result = 200;
                break;
            default:
                result = 300;
        }
        return result;
    }

    int a = evaluate(10);
    int b = evaluate(20);
    int c = evaluate(99);
    return a + b + c;
    """
    diagnostics = DiagnosticBag()
    parser = Parser(SourceText(src), diagnostics)
    unit = parser.parse_compilation_unit()
    binder = Binder(diagnostics)
    program = binder.bind_program(unit)
    assert not diagnostics.has_errors

    emitter = LLVMEmitter()
    llvm_mod = emitter.emit_module(program)
    jit = LLVMJIT()
    ret = jit.run_ir(str(llvm_mod))
    assert ret == 600

def test_jit_enum_with_switch():
    src = """
    enum Mode {
        Fast,
        Medium = 5,
        Slow
    }

    int handle_mode(Mode m) {
        int code = 0;
        switch (m) {
            case Mode.Fast:
                code = 10;
                break;
            case Mode.Medium:
                code = 20;
                break;
            case Mode.Slow:
                code = 30;
                break;
            default:
                code = 99;
        }
        return code;
    }

    int r1 = handle_mode(Mode.Fast);
    int r2 = handle_mode(Mode.Medium);
    int r3 = handle_mode(Mode.Slow);
    return r1 + r2 + r3;
    """
    diagnostics = DiagnosticBag()
    parser = Parser(SourceText(src), diagnostics)
    unit = parser.parse_compilation_unit()
    binder = Binder(diagnostics)
    program = binder.bind_program(unit)
    assert not diagnostics.has_errors

    emitter = LLVMEmitter()
    llvm_mod = emitter.emit_module(program)
    jit = LLVMJIT()
    ret = jit.run_ir(str(llvm_mod))
    assert ret == 60

def test_c_emitter_enums_and_switch():
    src = """
    enum Level { Low, Med, High = 10 };
    Level l = Level.Med;
    switch (l) {
        case Level.Low:
            print(1);
            break;
        case Level.Med:
            print(2);
            break;
        default:
            print(3);
    }
    """
    diagnostics = DiagnosticBag()
    parser = Parser(SourceText(src), diagnostics)
    unit = parser.parse_compilation_unit()
    binder = Binder(diagnostics)
    program = binder.bind_program(unit)
    assert not diagnostics.has_errors

    c_emitter = CEmitter()
    c_code = c_emitter.emit(program)
    assert "typedef enum {" in c_code
    assert "Level_Low = 0" in c_code
    assert "Level_Med = 1" in c_code
    assert "Level_High = 10" in c_code
    assert "} Level;" in c_code
    assert "switch (l) {" in c_code
    assert "case 1:" in c_code
    assert "break;" in c_code

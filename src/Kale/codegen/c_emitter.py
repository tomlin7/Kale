import io
from ..binding.bound_nodes import (
    BoundProgram,
    BoundStatement,
    BoundBlockStatement,
    BoundVariableDeclaration,
    BoundIfStatement,
    BoundWhileStatement,
    BoundForStatement,
    BoundPrintStatement,
    BoundReturnStatement,
    BoundBreakStatement,
    BoundContinueStatement,
    BoundExpressionStatement,
    BoundExpression,
    BoundLiteralExpression,
    BoundVariableExpression,
    BoundAssignmentExpression,
    BoundUnaryExpression,
    BoundBinaryExpression,
)
from ..binding.types import (
    TypeInt,
    TypeFloat,
    TypeDouble,
    TypeBool,
    TypeString,
    TypeChar,
    TypeSymbol,
)

class CEmitter:
    """Generates standard C99 source code from a BoundProgram."""
    def __init__(self):
        self._indent_level = 0
        self._out = io.StringIO()

    def _indent(self) -> str:
        return "    " * self._indent_level

    def _write_line(self, line: str = ""):
        if line:
            self._out.write(self._indent() + line + "\n")
        else:
            self._out.write("\n")

    def _map_type(self, t: TypeSymbol) -> str:
        if t == TypeInt:
            return "long long"
        if t in (TypeFloat, TypeDouble):
            return "double"
        if t == TypeBool:
            return "bool"
        if t == TypeString:
            return "const char*"
        if t == TypeChar:
            return "char"
        return "void"

    def emit(self, program: BoundProgram) -> str:
        self._out = io.StringIO()
        self._indent_level = 0

        # Runtime headers
        self._write_line("#include <stdio.h>")
        self._write_line("#include <stdbool.h>")
        self._write_line("#include <stdlib.h>")
        self._write_line("#include <string.h>")
        self._write_line("#include <math.h>")
        self._write_line()

        # Helper runtime functions
        self._write_line("// --- Kale Runtime ---")
        self._write_line("static inline void _kale_print_int(long long x) { printf(\"%lld\", x); }")
        self._write_line("static inline void _kale_print_double(double x) { printf(\"%g\", x); }")
        self._write_line("static inline void _kale_print_bool(bool x) { printf(\"%s\", x ? \"true\" : \"false\"); }")
        self._write_line("static inline void _kale_print_str(const char* x) { printf(\"%s\", x); }")
        self._write_line("static inline void _kale_println(void) { printf(\"\\n\"); }")
        self._write_line()

        # Main function
        self._write_line("int main(int argc, char** argv) {")
        self._indent_level += 1

        for statement in program.statements:
            self._emit_statement(statement)

        self._write_line("return 0;")
        self._indent_level -= 1
        self._write_line("}")

        return self._out.getvalue()

    def _emit_statement(self, statement: BoundStatement):
        if isinstance(statement, BoundBlockStatement):
            self._write_line("{")
            self._indent_level += 1
            for s in statement.statements:
                self._emit_statement(s)
            self._indent_level -= 1
            self._write_line("}")
        elif isinstance(statement, BoundVariableDeclaration):
            c_type = self._map_type(statement.variable.type)
            name = statement.variable.name
            if statement.initializer is not None:
                init_str = self._emit_expression(statement.initializer)
                self._write_line(f"{c_type} {name} = {init_str};")
            else:
                self._write_line(f"{c_type} {name};")
        elif isinstance(statement, BoundIfStatement):
            cond_str = self._emit_expression(statement.condition)
            self._write_line(f"if ({cond_str}) {{")
            self._indent_level += 1
            self._emit_statement(statement.then_statement)
            self._indent_level -= 1
            if statement.else_statement is not None:
                self._write_line("} else {")
                self._indent_level += 1
                self._emit_statement(statement.else_statement)
                self._indent_level -= 1
            self._write_line("}")
        elif isinstance(statement, BoundWhileStatement):
            cond_str = self._emit_expression(statement.condition)
            self._write_line(f"while ({cond_str}) {{")
            self._indent_level += 1
            self._emit_statement(statement.body)
            self._indent_level -= 1
            self._write_line("}")
        elif isinstance(statement, BoundForStatement):
            # For header
            init_code = ""
            if statement.initializer:
                # Format inline init without newline
                old_out = self._out
                self._out = io.StringIO()
                self._emit_statement(statement.initializer)
                init_code = self._out.getvalue().strip()
                self._out = old_out

            cond_code = self._emit_expression(statement.condition) if statement.condition else ""
            inc_code = self._emit_expression(statement.increment) if statement.increment else ""

            # Ensure init_code doesn't duplicate semicolon
            if init_code.endswith(";"):
                init_code = init_code[:-1]

            self._write_line(f"for ({init_code}; {cond_code}; {inc_code}) {{")
            self._indent_level += 1
            self._emit_statement(statement.body)
            self._indent_level -= 1
            self._write_line("}")
        elif isinstance(statement, BoundPrintStatement):
            for i, arg in enumerate(statement.arguments):
                arg_expr = self._emit_expression(arg)
                if arg.type == TypeInt:
                    self._write_line(f"_kale_print_int({arg_expr});")
                elif arg.type in (TypeFloat, TypeDouble):
                    self._write_line(f"_kale_print_double({arg_expr});")
                elif arg.type == TypeBool:
                    self._write_line(f"_kale_print_bool({arg_expr});")
                elif arg.type == TypeString:
                    self._write_line(f"_kale_print_str({arg_expr});")
                else:
                    self._write_line(f"_kale_print_str(\"{arg_expr}\");")
                if i < len(statement.arguments) - 1:
                    self._write_line("_kale_print_str(\" \");")
            self._write_line("_kale_println();")
        elif isinstance(statement, BoundReturnStatement):
            if statement.expression:
                self._write_line(f"return {self._emit_expression(statement.expression)};")
            else:
                self._write_line("return;")
        elif isinstance(statement, BoundBreakStatement):
            self._write_line("break;")
        elif isinstance(statement, BoundContinueStatement):
            self._write_line("continue;")
        elif isinstance(statement, BoundExpressionStatement):
            self._write_line(f"{self._emit_expression(statement.expression)};")

    def _emit_expression(self, expr: BoundExpression) -> str:
        if isinstance(expr, BoundLiteralExpression):
            if expr.value is None:
                return "NULL"
            if isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            if isinstance(expr.value, str):
                escaped = expr.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
                return f'"{escaped}"'
            return str(expr.value)
        if isinstance(expr, BoundVariableExpression):
            return expr.variable.name
        if isinstance(expr, BoundAssignmentExpression):
            right_str = self._emit_expression(expr.expression)
            return f"{expr.variable.name} {expr.operator_kind} {right_str}"
        if isinstance(expr, BoundUnaryExpression):
            op_str = expr.operator.operator_kind
            operand_str = self._emit_expression(expr.operand)
            if expr.is_postfix:
                return f"({operand_str}{op_str})"
            return f"({op_str}{operand_str})"
        if isinstance(expr, BoundBinaryExpression):
            left_str = self._emit_expression(expr.left)
            right_str = self._emit_expression(expr.right)
            op = expr.operator.operator_kind
            if op == "**":
                return f"pow((double)({left_str}), (double)({right_str}))"
            return f"({left_str} {op} {right_str})"
        return ""

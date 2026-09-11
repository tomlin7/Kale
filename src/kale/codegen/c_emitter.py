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
    BoundCallExpression,
    BoundAssignmentExpression,
    BoundUnaryExpression,
    BoundBinaryExpression,
    BoundArrayLiteralExpression,
    BoundIndexExpression,
    BoundIndexAssignmentExpression,
    BoundMemberAccessExpression,
    BoundMemberAssignmentExpression,
    BoundAddressOfExpression,
    BoundDereferenceExpression,
    BoundDereferenceAssignmentExpression,
    BoundAllocExpression,
    BoundCastExpression,
    BoundFreeStatement,
    BoundStructDeclaration,
    BoundEnumDeclaration,
    BoundSwitchStatement,
)
from ..binding.types import (
    TypeInt,
    TypeFloat,
    TypeDouble,
    TypeBool,
    TypeString,
    TypeChar,
    TypeSymbol,
    ArrayTypeSymbol,
    PointerTypeSymbol,
    StructTypeSymbol,
    EnumTypeSymbol,
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
        if isinstance(t, PointerTypeSymbol):
            return f"{self._map_type(t.base_type)}*"
        if isinstance(t, StructTypeSymbol):
            return f"struct {t.name}"
        if isinstance(t, EnumTypeSymbol):
            return t.name
        if isinstance(t, ArrayTypeSymbol):
            return f"{self._map_type(t.element_type)}*"
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

        # Enum definitions
        if program.enums:
            self._write_line("// --- User Enums ---")
            for en in program.enums:
                self._write_line(f"typedef enum {{")
                self._indent_level += 1
                for idx, (mname, mval) in enumerate(en.enum_type.members):
                    comma = "," if idx < len(en.enum_type.members) - 1 else ""
                    self._write_line(f"{en.enum_type.name}_{mname} = {mval}{comma}")
                self._indent_level -= 1
                self._write_line(f"}} {en.enum_type.name};")
                self._write_line()

        # Struct definitions
        if program.structs:
            self._write_line("// --- User Structs ---")
            for st in program.structs:
                self._write_line(f"struct {st.struct_type.name} {{")
                self._indent_level += 1
                for fname, ftype in st.struct_type.fields:
                    self._write_line(f"{self._map_type(ftype)} {fname};")
                self._indent_level -= 1
                self._write_line("};")
                self._write_line()

        # Forward declarations of user and extern functions
        if program.functions:
            self._write_line("// --- Function Prototypes ---")
            for fn in program.functions:
                fn_name = fn.symbol.mangled_name or fn.symbol.name
                ret_t = self._map_type(fn.symbol.return_type)
                param_parts = [f"{self._map_type(p.type)} {p.name}" for p in fn.symbol.parameters]
                if getattr(fn.symbol, "is_var_args", False):
                    param_parts.append("...")
                params_str = ", ".join(param_parts) or "void"
                prefix = "extern " if fn.symbol.is_extern else ""
                self._write_line(f"{prefix}{ret_t} {fn_name}({params_str});")
            self._write_line()

            # User function definitions
            self._write_line("// --- User Functions ---")
            for fn in program.functions:
                if fn.symbol.is_extern or fn.body is None:
                    continue
                fn_name = fn.symbol.mangled_name or fn.symbol.name
                ret_t = self._map_type(fn.symbol.return_type)
                param_parts = [f"{self._map_type(p.type)} {p.name}" for p in fn.symbol.parameters]
                params_str = ", ".join(param_parts) or "void"
                self._write_line(f"{ret_t} {fn_name}({params_str}) {{")
                self._indent_level += 1
                for s in fn.body.statements:
                    self._emit_statement(s)
                self._indent_level -= 1
                self._write_line("}")
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
        elif isinstance(statement, BoundSwitchStatement):
            cond_str = self._emit_expression(statement.condition)
            self._write_line(f"switch ({cond_str}) {{")
            self._indent_level += 1
            for case in statement.cases:
                for v in case.case_values:
                    self._write_line(f"case {self._emit_expression(v)}:")
                self._indent_level += 1
                for s in case.body:
                    self._emit_statement(s)
                self._indent_level -= 1
            if statement.default_body is not None:
                self._write_line("default:")
                self._indent_level += 1
                for s in statement.default_body:
                    self._emit_statement(s)
                self._indent_level -= 1
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
                if arg.type == TypeInt or isinstance(arg.type, EnumTypeSymbol):
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
        elif isinstance(statement, BoundFreeStatement):
            self._write_line(f"free((void*)({self._emit_expression(statement.expression)}));")
        elif isinstance(statement, BoundExpressionStatement):
            self._write_line(f"{self._emit_expression(statement.expression)};")

    def _emit_expression(self, expr: BoundExpression) -> str:
        if isinstance(expr, BoundLiteralExpression):
            if expr.value is None:
                return "NULL"
            if expr.type == TypeChar:
                char_int = expr.value if isinstance(expr.value, int) else (ord(expr.value[0]) if expr.value else 0)
                return str(char_int)
            if isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            if isinstance(expr.value, str):
                escaped = expr.value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")
                return f'"{escaped}"'
            return str(expr.value)
        if isinstance(expr, BoundVariableExpression):
            return expr.variable.name
        if isinstance(expr, BoundCallExpression):
            fn_name = expr.function.mangled_name or expr.function.name
            args_str = ", ".join(self._emit_expression(a) for a in expr.arguments)
            return f"{fn_name}({args_str})"
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
        if isinstance(expr, BoundArrayLiteralExpression):
            elems = ", ".join(self._emit_expression(e) for e in expr.elements)
            elem_t = self._map_type(expr.array_type.element_type) if isinstance(expr.array_type, ArrayTypeSymbol) else "long long"
            return f"(({elem_t}[]){{{elems}}})"
        if isinstance(expr, BoundIndexExpression):
            t_str = self._emit_expression(expr.target)
            idx_str = self._emit_expression(expr.index)
            return f"{t_str}[{idx_str}]"
        if isinstance(expr, BoundIndexAssignmentExpression):
            t_str = self._emit_expression(expr.target)
            idx_str = self._emit_expression(expr.index)
            val_str = self._emit_expression(expr.value)
            return f"{t_str}[{idx_str}] {expr.operator_kind} {val_str}"
        if isinstance(expr, BoundMemberAccessExpression):
            t_str = self._emit_expression(expr.target)
            return f"{t_str}.{expr.member_name}"
        if isinstance(expr, BoundMemberAssignmentExpression):
            t_str = self._emit_expression(expr.target)
            val_str = self._emit_expression(expr.value)
            return f"{t_str}.{expr.member_name} {expr.operator_kind} {val_str}"
        if isinstance(expr, BoundAddressOfExpression):
            op_str = self._emit_expression(expr.operand)
            return f"(&({op_str}))"
        if isinstance(expr, BoundDereferenceExpression):
            op_str = self._emit_expression(expr.operand)
            return f"(*({op_str}))"
        if isinstance(expr, BoundDereferenceAssignmentExpression):
            target_str = self._emit_expression(expr.operand)
            val_str = self._emit_expression(expr.value)
            return f"(*({target_str})) {expr.operator_kind} {val_str}"
        if isinstance(expr, BoundAllocExpression):
            c_type = self._map_type(expr.allocated_type)
            if expr.count is not None:
                count_str = self._emit_expression(expr.count)
                return f"(({c_type}*)malloc(sizeof({c_type}) * ({count_str})))"
            return f"(({c_type}*)malloc(sizeof({c_type})))"
        if isinstance(expr, BoundCastExpression):
            c_type = self._map_type(expr.target_type)
            inner_str = self._emit_expression(expr.expression)
            return f"(({c_type})({inner_str}))"
        return ""

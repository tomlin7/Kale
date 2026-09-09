import llvmlite.ir as ir
import llvmlite.binding as llvm

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
)
from .llvm_types import to_llvm_type

class LLVMEmitter:
    """Compiles a typed BoundProgram into an LLVM IR Module."""
    def __init__(self, module_name: str = "kale_module"):
        self.module = ir.Module(name=module_name)
        try:
            self.module.triple = llvm.get_default_triple()
        except Exception:
            self.module.triple = "x86_64-pc-windows-msvc"

        self._builder: ir.IRBuilder | None = None
        self._main_func: ir.Function | None = None
        self._entry_block: ir.Block | None = None

        # Scopes: list of variable maps mapping name -> alloca_instruction
        self._scopes: list[dict[str, ir.AllocaInstr]] = [{}]
        self._break_blocks: list[ir.Block] = []
        self._continue_blocks: list[ir.Block] = []
        self._string_constants: dict[str, ir.Value] = {}

        # Declare external runtime functions
        self._printf = self._declare_printf()
        self._pow = self._declare_pow()

    def _declare_printf(self) -> ir.Function:
        func_type = ir.FunctionType(ir.IntType(32), [ir.PointerType()], var_arg=True)
        return ir.Function(self.module, func_type, name="printf")

    def _declare_pow(self) -> ir.Function:
        func_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType(), ir.DoubleType()])
        return ir.Function(self.module, func_type, name="pow")

    def _get_string_constant(self, text: str) -> ir.Value:
        """Creates or reuses a global string constant and returns an i8* pointer to it."""
        if text in self._string_constants:
            return self._string_constants[text]

        raw_bytes = bytearray(text.encode("utf-8") + b"\0")
        c_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(raw_bytes)), raw_bytes)
        global_name = f".str_{len(self._string_constants)}"
        global_var = ir.GlobalVariable(self.module, c_str.type, name=global_name)
        global_var.linkage = "internal"
        global_var.global_constant = True
        global_var.initializer = c_str

        # Create constant bitcast expression so it dominates all uses anywhere in the module
        ptr = global_var.bitcast(ir.PointerType(ir.IntType(8)))
        self._string_constants[text] = ptr
        return ptr

    def _push_scope(self):
        self._scopes.append({})

    def _pop_scope(self):
        self._scopes.pop()

    def _declare_var(self, name: str, alloca_ptr: ir.AllocaInstr):
        self._scopes[-1][name] = alloca_ptr

    def _lookup_var(self, name: str) -> ir.AllocaInstr | None:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def _is_block_terminated(self, block: ir.Block | None = None) -> bool:
        b = block or self._builder.block # type: ignore
        return b.is_terminated

    def emit_module(self, program: BoundProgram) -> ir.Module:
        # Create main() function
        func_type = ir.FunctionType(ir.IntType(32), [])
        self._main_func = ir.Function(self.module, func_type, name="main")
        self._entry_block = self._main_func.append_basic_block(name="entry")
        self._builder = ir.IRBuilder(self._entry_block)

        self._scopes = [{}]
        self._break_blocks = []
        self._continue_blocks = []

        for statement in program.statements:
            self._emit_statement(statement)

        # Ensure main function terminates properly
        if not self._is_block_terminated():
            self._builder.ret(ir.Constant(ir.IntType(32), 0))

        return self.module

    def _emit_statement(self, statement: BoundStatement):
        if self._is_block_terminated():
            return

        if isinstance(statement, BoundBlockStatement):
            self._push_scope()
            for s in statement.statements:
                self._emit_statement(s)
            self._pop_scope()

        elif isinstance(statement, BoundVariableDeclaration):
            llvm_t = to_llvm_type(statement.variable.type)
            # Create alloca in the entry block for efficient stack promotion
            with self._builder.goto_entry_block(): # type: ignore
                alloca = self._builder.alloca(llvm_t, name=statement.variable.name)
            self._declare_var(statement.variable.name, alloca)

            if statement.initializer is not None:
                val = self._emit_expression(statement.initializer)
                val = self._coerce_type(val, statement.initializer.type, statement.variable.type)
                self._builder.store(val, alloca)

        elif isinstance(statement, BoundIfStatement):
            cond_val = self._emit_expression(statement.condition)
            # Ensure condition is i1
            if cond_val.type != ir.IntType(1):
                cond_val = self._builder.icmp_signed("!=", cond_val, ir.Constant(cond_val.type, 0))

            then_block = self._main_func.append_basic_block("if.then")
            else_block = self._main_func.append_basic_block("if.else") if statement.else_statement else None
            merge_block = self._main_func.append_basic_block("if.end")

            if else_block:
                self._builder.cbranch(cond_val, then_block, else_block)
            else:
                self._builder.cbranch(cond_val, then_block, merge_block)

            # Then block
            self._builder.position_at_end(then_block)
            self._emit_statement(statement.then_statement)
            if not self._is_block_terminated():
                self._builder.branch(merge_block)

            # Else block
            if else_block and statement.else_statement:
                self._builder.position_at_end(else_block)
                self._emit_statement(statement.else_statement)
                if not self._is_block_terminated():
                    self._builder.branch(merge_block)

            self._builder.position_at_end(merge_block)

        elif isinstance(statement, BoundWhileStatement):
            cond_block = self._main_func.append_basic_block("while.cond")
            body_block = self._main_func.append_basic_block("while.body")
            after_block = self._main_func.append_basic_block("while.end")

            self._builder.branch(cond_block)

            # Cond
            self._builder.position_at_end(cond_block)
            cond_val = self._emit_expression(statement.condition)
            if cond_val.type != ir.IntType(1):
                cond_val = self._builder.icmp_signed("!=", cond_val, ir.Constant(cond_val.type, 0))
            self._builder.cbranch(cond_val, body_block, after_block)

            # Body
            self._builder.position_at_end(body_block)
            self._break_blocks.append(after_block)
            self._continue_blocks.append(cond_block)
            self._emit_statement(statement.body)
            self._break_blocks.pop()
            self._continue_blocks.pop()
            if not self._is_block_terminated():
                self._builder.branch(cond_block)

            self._builder.position_at_end(after_block)

        elif isinstance(statement, BoundForStatement):
            if statement.initializer:
                self._emit_statement(statement.initializer)

            cond_block = self._main_func.append_basic_block("for.cond")
            body_block = self._main_func.append_basic_block("for.body")
            inc_block = self._main_func.append_basic_block("for.inc")
            after_block = self._main_func.append_basic_block("for.end")

            self._builder.branch(cond_block)

            # Cond
            self._builder.position_at_end(cond_block)
            if statement.condition:
                cond_val = self._emit_expression(statement.condition)
                if cond_val.type != ir.IntType(1):
                    cond_val = self._builder.icmp_signed("!=", cond_val, ir.Constant(cond_val.type, 0))
                self._builder.cbranch(cond_val, body_block, after_block)
            else:
                self._builder.branch(body_block)

            # Body
            self._builder.position_at_end(body_block)
            self._break_blocks.append(after_block)
            self._continue_blocks.append(inc_block)
            self._emit_statement(statement.body)
            self._break_blocks.pop()
            self._continue_blocks.pop()
            if not self._is_block_terminated():
                self._builder.branch(inc_block)

            # Inc
            self._builder.position_at_end(inc_block)
            if statement.increment:
                self._emit_expression(statement.increment)
            if not self._is_block_terminated():
                self._builder.branch(cond_block)

            self._builder.position_at_end(after_block)

        elif isinstance(statement, BoundBreakStatement):
            if self._break_blocks:
                self._builder.branch(self._break_blocks[-1])

        elif isinstance(statement, BoundContinueStatement):
            if self._continue_blocks:
                self._builder.branch(self._continue_blocks[-1])

        elif isinstance(statement, BoundReturnStatement):
            ret_val = None
            if statement.expression:
                ret_val = self._emit_expression(statement.expression)
            else:
                ret_val = ir.Constant(ir.IntType(32), 0)
            if ret_val.type != ir.IntType(32):
                ret_val = self._builder.trunc(ret_val, ir.IntType(32))
            self._builder.ret(ret_val)

        elif isinstance(statement, BoundPrintStatement):
            for i, arg in enumerate(statement.arguments):
                val = self._emit_expression(arg)
                if arg.type == TypeInt:
                    fmt = self._get_string_constant("%lld")
                    self._builder.call(self._printf, [fmt, val])
                elif arg.type in (TypeFloat, TypeDouble):
                    fmt = self._get_string_constant("%g")
                    self._builder.call(self._printf, [fmt, val])
                elif arg.type == TypeBool:
                    true_str = self._get_string_constant("true")
                    false_str = self._get_string_constant("false")
                    bool_str = self._builder.select(val, true_str, false_str)
                    fmt = self._get_string_constant("%s")
                    self._builder.call(self._printf, [fmt, bool_str])
                elif arg.type == TypeString:
                    fmt = self._get_string_constant("%s")
                    self._builder.call(self._printf, [fmt, val])

                if i < len(statement.arguments) - 1:
                    space = self._get_string_constant(" ")
                    fmt_s = self._get_string_constant("%s")
                    self._builder.call(self._printf, [fmt_s, space])

            nl = self._get_string_constant("\n")
            fmt_s = self._get_string_constant("%s")
            self._builder.call(self._printf, [fmt_s, nl])

        elif isinstance(statement, BoundExpressionStatement):
            self._emit_expression(statement.expression)

    def _coerce_type(self, value: ir.Value, from_t, to_t) -> ir.Value:
        if from_t == to_t:
            return value
        if from_t == TypeInt and to_t in (TypeFloat, TypeDouble):
            return self._builder.sitofp(value, ir.DoubleType())
        if from_t in (TypeFloat, TypeDouble) and to_t == TypeInt:
            return self._builder.fptosi(value, ir.IntType(64))
        return value

    def _emit_expression(self, expr: BoundExpression) -> ir.Value:
        if isinstance(expr, BoundLiteralExpression):
            if expr.value is None:
                return ir.Constant(ir.IntType(64), 0)
            if isinstance(expr.value, bool):
                return ir.Constant(ir.IntType(1), 1 if expr.value else 0)
            if isinstance(expr.value, int):
                return ir.Constant(ir.IntType(64), expr.value)
            if isinstance(expr.value, float):
                return ir.Constant(ir.DoubleType(), expr.value)
            if isinstance(expr.value, str):
                return self._get_string_constant(expr.value)
            return ir.Constant(ir.IntType(64), 0)

        if isinstance(expr, BoundVariableExpression):
            alloca = self._lookup_var(expr.variable.name)
            if alloca is None:
                return ir.Constant(ir.IntType(64), 0)
            return self._builder.load(alloca, name=expr.variable.name)

        if isinstance(expr, BoundAssignmentExpression):
            alloca = self._lookup_var(expr.variable.name)
            if alloca is None:
                return ir.Constant(ir.IntType(64), 0)

            right_val = self._emit_expression(expr.expression)
            op = expr.operator_kind

            if op != "=":
                old_val = self._builder.load(alloca, name=expr.variable.name)
                # Compute arithmetic
                base_op = op[:-1]
                is_flt = (expr.variable.type in (TypeFloat, TypeDouble))
                if base_op == "+":
                    right_val = self._builder.fadd(old_val, right_val) if is_flt else self._builder.add(old_val, right_val)
                elif base_op == "-":
                    right_val = self._builder.fsub(old_val, right_val) if is_flt else self._builder.sub(old_val, right_val)
                elif base_op == "*":
                    right_val = self._builder.fmul(old_val, right_val) if is_flt else self._builder.mul(old_val, right_val)
                elif base_op == "/":
                    right_val = self._builder.fdiv(old_val, right_val) if is_flt else self._builder.sdiv(old_val, right_val)

            right_val = self._coerce_type(right_val, expr.expression.type, expr.variable.type)
            self._builder.store(right_val, alloca)
            return right_val

        if isinstance(expr, BoundUnaryExpression):
            op_kind = expr.operator.operator_kind
            operand_val = self._emit_expression(expr.operand)
            is_flt = (expr.operand.type in (TypeFloat, TypeDouble))

            if op_kind in ("++", "--"):
                if isinstance(expr.operand, BoundVariableExpression):
                    alloca = self._lookup_var(expr.operand.variable.name)
                    one = ir.Constant(ir.DoubleType(), 1.0) if is_flt else ir.Constant(ir.IntType(64), 1)
                    if op_kind == "++":
                        new_val = self._builder.fadd(operand_val, one) if is_flt else self._builder.add(operand_val, one)
                    else:
                        new_val = self._builder.fsub(operand_val, one) if is_flt else self._builder.sub(operand_val, one)
                    self._builder.store(new_val, alloca)
                    return operand_val if expr.is_postfix else new_val
                return operand_val

            if op_kind == "-":
                return self._builder.fneg(operand_val) if is_flt else self._builder.neg(operand_val)
            if op_kind == "+":
                return operand_val
            if op_kind == "!":
                if operand_val.type != ir.IntType(1):
                    operand_val = self._builder.icmp_signed("!=", operand_val, ir.Constant(operand_val.type, 0))
                return self._builder.not_(operand_val)
            if op_kind == "~":
                return self._builder.xor(operand_val, ir.Constant(ir.IntType(64), -1))

            return operand_val

        if isinstance(expr, BoundBinaryExpression):
            left_val = self._emit_expression(expr.left)
            right_val = self._emit_expression(expr.right)
            op = expr.operator.operator_kind

            # Coerce numbers if mixed int and float
            if expr.left.type == TypeInt and expr.right.type in (TypeFloat, TypeDouble):
                left_val = self._builder.sitofp(left_val, ir.DoubleType())
            elif expr.left.type in (TypeFloat, TypeDouble) and expr.right.type == TypeInt:
                right_val = self._builder.sitofp(right_val, ir.DoubleType())

            is_flt = (left_val.type == ir.DoubleType() or right_val.type == ir.DoubleType())

            # Arithmetic
            if op == "+":
                return self._builder.fadd(left_val, right_val) if is_flt else self._builder.add(left_val, right_val)
            if op == "-":
                return self._builder.fsub(left_val, right_val) if is_flt else self._builder.sub(left_val, right_val)
            if op == "*":
                return self._builder.fmul(left_val, right_val) if is_flt else self._builder.mul(left_val, right_val)
            if op == "/":
                return self._builder.fdiv(left_val, right_val) if is_flt else self._builder.sdiv(left_val, right_val)
            if op == "%":
                return self._builder.frem(left_val, right_val) if is_flt else self._builder.srem(left_val, right_val)
            if op == "**":
                if not is_flt:
                    left_val = self._builder.sitofp(left_val, ir.DoubleType())
                    right_val = self._builder.sitofp(right_val, ir.DoubleType())
                return self._builder.call(self._pow, [left_val, right_val])

            # Relational
            if op == "<":
                return self._builder.fcmp_ordered("<", left_val, right_val) if is_flt else self._builder.icmp_signed("<", left_val, right_val)
            if op == "<=":
                return self._builder.fcmp_ordered("<=", left_val, right_val) if is_flt else self._builder.icmp_signed("<=", left_val, right_val)
            if op == ">":
                return self._builder.fcmp_ordered(">", left_val, right_val) if is_flt else self._builder.icmp_signed(">", left_val, right_val)
            if op == ">=":
                return self._builder.fcmp_ordered(">=", left_val, right_val) if is_flt else self._builder.icmp_signed(">=", left_val, right_val)
            if op == "==":
                return self._builder.fcmp_ordered("==", left_val, right_val) if is_flt else self._builder.icmp_signed("==", left_val, right_val)
            if op == "!=":
                return self._builder.fcmp_ordered("!=", left_val, right_val) if is_flt else self._builder.icmp_signed("!=", left_val, right_val)

            # Logical
            if op in ("&&", "||"):
                if left_val.type != ir.IntType(1):
                    left_val = self._builder.icmp_signed("!=", left_val, ir.Constant(left_val.type, 0))
                if right_val.type != ir.IntType(1):
                    right_val = self._builder.icmp_signed("!=", right_val, ir.Constant(right_val.type, 0))
                return self._builder.and_(left_val, right_val) if op == "&&" else self._builder.or_(left_val, right_val)

            # Bitwise
            if op == "&":
                return self._builder.and_(left_val, right_val)
            if op == "|":
                return self._builder.or_(left_val, right_val)
            if op == "^":
                return self._builder.xor(left_val, right_val)
            if op == "<<":
                return self._builder.shl(left_val, right_val)
            if op == ">>":
                return self._builder.ashr(left_val, right_val)

        return ir.Constant(ir.IntType(64), 0)

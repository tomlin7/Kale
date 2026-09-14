from typing import Any
import llvmlite.ir as ir
import llvmlite.binding as llvm

from ..binding.bound_nodes import (
    BoundProgram,
    BoundStatement,
    BoundBlockStatement,
    BoundVariableDeclaration,
    BoundIfStatement,
    BoundSwitchStatement,
    BoundWhileStatement,
    BoundForStatement,
    BoundPrintStatement,
    BoundFreeStatement,
    BoundReturnStatement,
    BoundBreakStatement,
    BoundContinueStatement,
    BoundExpressionStatement,
    BoundExpression,
    BoundLiteralExpression,
    BoundVariableExpression,
    BoundAssignmentExpression,
    BoundCallExpression,
    BoundIndirectCallExpression,
    BoundFunctionPointerExpression,
    BoundUnaryExpression,
    BoundCastExpression,
    BoundBinaryExpression,
    BoundFunctionDeclaration,
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
    BoundStructDeclaration,
)
from ..binding.types import (
    TypeInt,
    TypeInt32,
    TypeFloat,
    TypeDouble,
    TypeBool,
    TypeString,
    TypeChar,
    TypeVoid,
    ArrayTypeSymbol,
    PointerTypeSymbol,
    StructTypeSymbol,
    EnumTypeSymbol,
    FunctionTypeSymbol,
)
from .llvm_types import to_llvm_type

class LLVMEmitter:
    """Compiles a typed BoundProgram into an LLVM IR Module."""
    def __init__(self, module_name: str = "kale_module"):
        self.context = ir.Context()
        self.module = ir.Module(name=module_name, context=self.context)
        try:
            self.module.triple = llvm.get_default_triple()
        except Exception:
            self.module.triple = "x86_64-pc-windows-msvc"

        self._builder: ir.IRBuilder | None = None
        self._main_func: ir.Function | None = None
        self._current_func: ir.Function | None = None
        self._entry_block: ir.Block | None = None

        # Functions map: name -> ir.Function
        self._functions: dict[str, ir.Function] = {}

        # Scopes: list of variable maps mapping name -> alloca_instruction
        self._scopes: list[dict[str, ir.AllocaInstr]] = [{}]
        self._break_blocks: list[ir.Block] = []
        self._continue_blocks: list[ir.Block] = []
        self._string_constants: dict[str, ir.Value] = {}

        # Declare external runtime functions
        self._printf = self._declare_printf()
        self._pow = self._declare_pow()
        self._malloc = self._declare_malloc()
        self._free = self._declare_free()
        self._functions["printf"] = self._printf
        self._functions["pow"] = self._pow
        self._functions["malloc"] = self._malloc
        self._functions["free"] = self._free

    def _declare_printf(self) -> ir.Function:
        func_type = ir.FunctionType(ir.IntType(32), [ir.PointerType()], var_arg=True)
        return ir.Function(self.module, func_type, name="printf")

    def _declare_pow(self) -> ir.Function:
        func_type = ir.FunctionType(ir.DoubleType(), [ir.DoubleType(), ir.DoubleType()])
        return ir.Function(self.module, func_type, name="pow")

    def _declare_malloc(self) -> ir.Function:
        func_type = ir.FunctionType(ir.PointerType(ir.IntType(8)), [ir.IntType(64)])
        return ir.Function(self.module, func_type, name="malloc")

    def _declare_free(self) -> ir.Function:
        func_type = ir.FunctionType(ir.VoidType(), [ir.PointerType(ir.IntType(8))])
        return ir.Function(self.module, func_type, name="free")

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
        self._functions = {
            "printf": self._printf,
            "pow": self._pow,
            "malloc": self._malloc,
            "free": self._free,
        }
        self._struct_types = {}

        # Pass 0: Register identified struct types (deduplicating by name)
        seen_struct_names = set()
        unique_structs = []
        for st_decl in program.structs:
            if st_decl.struct_type.name not in seen_struct_names:
                seen_struct_names.add(st_decl.struct_type.name)
                unique_structs.append(st_decl)

        for st_decl in unique_structs:
            s_name = f"struct.{st_decl.struct_type.name}"
            llvm_struct = self.module.context.get_identified_type(s_name)
            self._struct_types[st_decl.struct_type.name] = llvm_struct

        # Set struct body element types
        for st_decl in unique_structs:
            llvm_struct = self._struct_types[st_decl.struct_type.name]
            field_types = [to_llvm_type(ftype, self._struct_types) for _, ftype in st_decl.struct_type.fields]
            llvm_struct.set_body(*field_types)

        # Pass 1: Declare all user and extern functions
        for fn_decl in program.functions:
            fn_key = fn_decl.symbol.mangled_name or fn_decl.symbol.name
            if fn_key in self._functions:
                continue
            param_types = [to_llvm_type(p.type, self._struct_types) for p in fn_decl.symbol.parameters]
            ret_type = to_llvm_type(fn_decl.symbol.return_type or TypeVoid, self._struct_types)
            is_vararg = getattr(fn_decl.symbol, "is_var_args", False)
            func_type = ir.FunctionType(ret_type, param_types, var_arg=is_vararg)
            llvm_func = ir.Function(self.module, func_type, name=fn_key)
            self._functions[fn_key] = llvm_func

        # Pass 2: Emit user function bodies (skip extern functions)
        for fn_decl in program.functions:
            if fn_decl.symbol.is_extern or fn_decl.body is None:
                continue
            fn_key = fn_decl.symbol.mangled_name or fn_decl.symbol.name
            llvm_func = self._functions[fn_key]
            self._current_func = llvm_func
            self._current_fn_sym = fn_decl.symbol
            entry_block = llvm_func.append_basic_block(name="entry")
            self._builder = ir.IRBuilder(entry_block)
            self._scopes = [{}]
            self._break_blocks = []
            self._continue_blocks = []

            # Store parameters into stack allocas
            for p, arg in zip(fn_decl.symbol.parameters, llvm_func.args):
                arg.name = p.name
                alloca = self._builder.alloca(to_llvm_type(p.type, self._struct_types), name=p.name)
                self._builder.store(arg, alloca)
                self._declare_var(p.name, alloca)

            for statement in fn_decl.body.statements:
                self._emit_statement(statement)

            if not self._is_block_terminated():
                if fn_decl.symbol.return_type == TypeVoid or llvm_func.function_type.return_type == ir.VoidType():
                    self._builder.ret_void()
                else:
                    self._builder.ret(ir.Constant(to_llvm_type(fn_decl.symbol.return_type, self._struct_types), 0))

        # Pass 3: Create main() function for top-level statements
        func_type = ir.FunctionType(ir.IntType(32), [])
        self._main_func = ir.Function(self.module, func_type, name="main")
        self._current_func = self._main_func
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
            llvm_t = to_llvm_type(statement.variable.type, self._struct_types)
            # Create alloca in the entry block for efficient stack promotion
            with self._builder.goto_entry_block(): # type: ignore
                alloca = self._builder.alloca(llvm_t, name=statement.variable.name)
            self._declare_var(statement.variable.name, alloca)

            if statement.initializer is not None:
                val = self._emit_expression(statement.initializer)
                val = self._coerce_type(val, statement.initializer.type, statement.variable.type)
                if isinstance(statement.variable.type, StructTypeSymbol) and isinstance(val.type, ir.PointerType) and val.type.pointee == llvm_t:
                    val = self._builder.load(val)
                self._builder.store(val, alloca)
            elif isinstance(statement.variable.type, StructTypeSymbol):
                # Structs are cleanly zero-initialized by default
                self._builder.store(ir.Constant(llvm_t, None), alloca)

        elif isinstance(statement, BoundIfStatement):
            cond_val = self._emit_expression(statement.condition)
            # Ensure condition is i1
            if cond_val.type != ir.IntType(1):
                cond_val = self._builder.icmp_signed("!=", cond_val, ir.Constant(cond_val.type, 0))

            then_block = self._current_func.append_basic_block("if.then")
            else_block = self._current_func.append_basic_block("if.else") if statement.else_statement else None
            merge_block = self._current_func.append_basic_block("if.end")

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

        elif isinstance(statement, BoundSwitchStatement):
            cond_val = self._emit_expression(statement.condition)
            if cond_val.type != ir.IntType(64):
                cond_val = self._builder.sext(cond_val, ir.IntType(64))

            end_block = self._current_func.append_basic_block("switch.end")
            default_block = self._current_func.append_basic_block("switch.default") if statement.default_body is not None else end_block

            # Create switch instruction
            switch_inst = self._builder.switch(cond_val, default=default_block)

            self._break_blocks.append(end_block)

            # Emit each case
            for idx, case in enumerate(statement.cases):
                case_block = self._current_func.append_basic_block(f"switch.case_{idx}")
                for val_expr in case.case_values:
                    c_val = self._emit_expression(val_expr)
                    if c_val.type != ir.IntType(64):
                        if isinstance(c_val, ir.Constant):
                            c_val = ir.Constant(ir.IntType(64), c_val.constant)
                        else:
                            # Note: case expressions in C/LLVM must be constants
                            pass
                    switch_inst.add_case(c_val, case_block)

                self._builder.position_at_end(case_block)
                for s in case.body:
                    self._emit_statement(s)
                if not self._is_block_terminated():
                    self._builder.branch(end_block)

            # Emit default block if present
            if statement.default_body is not None:
                self._builder.position_at_end(default_block)
                for s in statement.default_body:
                    self._emit_statement(s)
                if not self._is_block_terminated():
                    self._builder.branch(end_block)

            self._break_blocks.pop()
            self._builder.position_at_end(end_block)

        elif isinstance(statement, BoundWhileStatement):
            cond_block = self._current_func.append_basic_block("while.cond")
            body_block = self._current_func.append_basic_block("while.body")
            after_block = self._current_func.append_basic_block("while.end")

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

            cond_block = self._current_func.append_basic_block("for.cond")
            body_block = self._current_func.append_basic_block("for.body")
            inc_block = self._current_func.append_basic_block("for.inc")
            after_block = self._current_func.append_basic_block("for.end")

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
            if self._current_func is None:
                return
            ret_t = self._current_func.function_type.return_type
            if statement.expression:
                ret_val = self._emit_expression(statement.expression)
                if ret_val.type != ret_t:
                    target_type_sym = getattr(getattr(self, "_current_fn_sym", None), "return_type", None)
                    if target_type_sym is None:
                        target_type_sym = TypeInt32 if ret_t == ir.IntType(32) else TypeInt
                    ret_val = self._coerce_type(ret_val, statement.expression.type, target_type_sym)
                    if ret_val.type != ret_t:
                        if isinstance(ret_t, (ir.FloatType, ir.DoubleType)) and isinstance(ret_val.type, ir.IntType):
                            ret_val = self._builder.sitofp(ret_val, ret_t)
                        elif isinstance(ret_t, ir.IntType) and isinstance(ret_val.type, (ir.FloatType, ir.DoubleType)):
                            ret_val = self._builder.fptosi(ret_val, ret_t)
                        elif isinstance(ret_t, ir.FloatType) and ret_val.type == ir.DoubleType():
                            ret_val = self._builder.fptrunc(ret_val, ir.FloatType())
                        elif isinstance(ret_t, ir.DoubleType) and ret_val.type == ir.FloatType():
                            ret_val = self._builder.fpext(ret_val, ir.DoubleType())
                        elif ret_t.is_pointer and ret_val.type.is_pointer:
                            ret_val = self._builder.bitcast(ret_val, ret_t)
                        elif isinstance(ret_t, ir.IntType) and isinstance(ret_val.type, ir.IntType):
                            if ret_val.type.width > ret_t.width:
                                ret_val = self._builder.trunc(ret_val, ret_t)
                            elif ret_val.type.width < ret_t.width:
                                ret_val = self._builder.sext(ret_val, ret_t)
                self._builder.ret(ret_val)
            else:
                if ret_t == ir.VoidType():
                    self._builder.ret_void()
                else:
                    self._builder.ret(ir.Constant(ret_t, 0))

        elif isinstance(statement, BoundPrintStatement):
            for i, arg in enumerate(statement.arguments):
                val = self._emit_expression(arg)
                if arg.type == TypeInt or isinstance(arg.type, EnumTypeSymbol):
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
                elif isinstance(arg.type, (PointerTypeSymbol, ArrayTypeSymbol)):
                    fmt = self._get_string_constant("%p")
                    self._builder.call(self._printf, [fmt, val])

                if i < len(statement.arguments) - 1:
                    space = self._get_string_constant(" ")
                    fmt_s = self._get_string_constant("%s")
                    self._builder.call(self._printf, [fmt_s, space])

            nl = self._get_string_constant("\n")
            fmt_s = self._get_string_constant("%s")
            self._builder.call(self._printf, [fmt_s, nl])

        elif isinstance(statement, BoundFreeStatement):
            ptr_val = self._emit_expression(statement.expression)
            i8_ptr_t = ir.PointerType(ir.IntType(8))
            if ptr_val.type != i8_ptr_t:
                ptr_val = self._builder.bitcast(ptr_val, i8_ptr_t)
            self._builder.call(self._free, [ptr_val])

        elif isinstance(statement, BoundExpressionStatement):
            self._emit_expression(statement.expression)

    def _coerce_type(self, value: ir.Value, from_t, to_t) -> ir.Value:
        if from_t == to_t:
            return value
        if from_t in (TypeInt, TypeInt32) and to_t in (TypeInt, TypeInt32):
            if to_t == TypeInt32:
                return self._builder.trunc(value, ir.IntType(32)) if value.type != ir.IntType(32) else value
            else:
                return self._builder.sext(value, ir.IntType(64)) if value.type != ir.IntType(64) else value
        if from_t in (TypeFloat, TypeDouble) and to_t in (TypeFloat, TypeDouble):
            if from_t == TypeFloat and to_t == TypeDouble:
                return self._builder.fpext(value, ir.DoubleType())
            elif from_t == TypeDouble and to_t == TypeFloat:
                return self._builder.fptrunc(value, ir.FloatType())
            return value
        if from_t in (TypeInt, TypeInt32) and to_t in (TypeFloat, TypeDouble):
            dest_t = ir.FloatType() if to_t == TypeFloat else ir.DoubleType()
            return self._builder.sitofp(value, dest_t)
        if from_t in (TypeFloat, TypeDouble) and to_t in (TypeInt, TypeInt32):
            dest_t = ir.IntType(32 if to_t == TypeInt32 else 64)
            return self._builder.fptosi(value, dest_t)
        if from_t in (TypeInt, TypeInt32) and to_t == TypeChar:
            return self._builder.trunc(value, ir.IntType(8))
        if from_t == TypeChar and to_t in (TypeInt, TypeInt32):
            return self._builder.sext(value, ir.IntType(32 if to_t == TypeInt32 else 64))
        if from_t == TypeString and isinstance(to_t, PointerTypeSymbol) and to_t.base_type in (TypeChar, TypeVoid):
            return self._builder.bitcast(value, ir.PointerType(ir.IntType(8)))
        if isinstance(from_t, PointerTypeSymbol) and from_t.base_type in (TypeChar, TypeVoid) and to_t == TypeString:
            return self._builder.bitcast(value, ir.PointerType(ir.IntType(8)))
        if from_t in (TypeInt, TypeInt32) and isinstance(to_t, (PointerTypeSymbol, FunctionTypeSymbol)):
            return self._builder.inttoptr(value, to_llvm_type(to_t, self._struct_types))
        if isinstance(from_t, (PointerTypeSymbol, FunctionTypeSymbol)) and to_t in (TypeInt, TypeInt32):
            return self._builder.ptrtoint(value, ir.IntType(32 if to_t == TypeInt32 else 64))
        if isinstance(from_t, (PointerTypeSymbol, FunctionTypeSymbol)) and isinstance(to_t, (PointerTypeSymbol, FunctionTypeSymbol)):
            target_llvm_t = to_llvm_type(to_t, self._struct_types)
            if value.type != target_llvm_t:
                return self._builder.bitcast(value, target_llvm_t)
        return value

    def _apply_compound_op(self, op: str, old_val: ir.Value, rhs_val: ir.Value, target_t: Any) -> ir.Value:
        base_op = op[:-1] # e.g. "+=", "&=", "<<=" -> "+", "&", "<<"
        is_flt = (target_t in (TypeFloat, TypeDouble))
        if is_flt and old_val.type != rhs_val.type:
            if old_val.type == ir.FloatType():
                rhs_val = self._builder.fptrunc(rhs_val, ir.FloatType()) if rhs_val.type == ir.DoubleType() else self._builder.sitofp(rhs_val, ir.FloatType())
            elif old_val.type == ir.DoubleType():
                rhs_val = self._builder.fpext(rhs_val, ir.DoubleType()) if rhs_val.type == ir.FloatType() else self._builder.sitofp(rhs_val, ir.DoubleType())
        if base_op == "+":
            return self._builder.fadd(old_val, rhs_val) if is_flt else self._builder.add(old_val, rhs_val)
        if base_op == "-":
            return self._builder.fsub(old_val, rhs_val) if is_flt else self._builder.sub(old_val, rhs_val)
        if base_op == "*":
            return self._builder.fmul(old_val, rhs_val) if is_flt else self._builder.mul(old_val, rhs_val)
        if base_op == "/":
            return self._builder.fdiv(old_val, rhs_val) if is_flt else self._builder.sdiv(old_val, rhs_val)
        if base_op == "%":
            return self._builder.frem(old_val, rhs_val) if is_flt else self._builder.srem(old_val, rhs_val)
        if base_op == "&":
            return self._builder.and_(old_val, rhs_val)
        if base_op == "|":
            return self._builder.or_(old_val, rhs_val)
        if base_op == "^":
            return self._builder.xor(old_val, rhs_val)
        if base_op == "<<":
            return self._builder.shl(old_val, rhs_val)
        if base_op == ">>":
            return self._builder.ashr(old_val, rhs_val)
        return rhs_val

    def _get_lvalue_ptr(self, expr: BoundExpression) -> ir.Value:
        if isinstance(expr, BoundVariableExpression):
            ptr = self._lookup_var(expr.variable.name)
            if ptr is None:
                raise RuntimeError(f"Undefined variable '{expr.variable.name}'")
            return ptr
        if isinstance(expr, BoundIndexExpression):
            target_ptr = self._emit_expression(expr.target)
            idx_val = self._emit_expression(expr.index)
            if idx_val.type != ir.IntType(64):
                idx_val = self._builder.sext(idx_val, ir.IntType(64)) if idx_val.type.width < 64 else self._builder.trunc(idx_val, ir.IntType(64))
            return self._builder.gep(target_ptr, [idx_val], inbounds=True, name="idx_lval_ptr")
        if isinstance(expr, BoundMemberAccessExpression):
            parent_ptr = self._get_lvalue_ptr(expr.target)
            return self._builder.gep(
                parent_ptr,
                [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), expr.member_index)],
                inbounds=True,
                name=f"member_{expr.member_name}_ptr"
            )
        if isinstance(expr, BoundDereferenceExpression):
            return self._emit_expression(expr.operand)
        raise RuntimeError(f"Cannot obtain lvalue pointer for {type(expr)}")

    def _emit_expression(self, expr: BoundExpression) -> ir.Value:
        if isinstance(expr, BoundLiteralExpression):
            if expr.value is None:
                return ir.Constant(ir.IntType(64), 0)
            if expr.type == TypeChar:
                char_int = expr.value if isinstance(expr.value, int) else (ord(expr.value[0]) if expr.value else 0)
                return ir.Constant(ir.IntType(8), char_int)
            if isinstance(expr.value, bool):
                return ir.Constant(ir.IntType(1), 1 if expr.value else 0)
            if isinstance(expr.value, int):
                return ir.Constant(ir.IntType(64), expr.value)
            if isinstance(expr.value, float):
                if expr.type == TypeFloat:
                    return ir.Constant(ir.FloatType(), expr.value)
                return ir.Constant(ir.DoubleType(), expr.value)
            if isinstance(expr.value, str):
                return self._get_string_constant(expr.value)
            return ir.Constant(ir.IntType(64), 0)

        if isinstance(expr, BoundVariableExpression):
            alloca = self._lookup_var(expr.variable.name)
            if alloca is None:
                return ir.Constant(ir.IntType(64), 0)
            return self._builder.load(alloca, name=expr.variable.name)

        if isinstance(expr, BoundCallExpression):
            fn_name = expr.function.mangled_name or expr.function.name
            llvm_func = self._functions.get(fn_name)
            if llvm_func is None:
                return ir.Constant(ir.IntType(64), 0)

            arg_values: list[ir.Value] = []
            for i, arg in enumerate(expr.arguments):
                val = self._emit_expression(arg)
                expected_type = expr.function.parameters[i].type
                val = self._coerce_type(val, arg.type, expected_type)
                if isinstance(expected_type, StructTypeSymbol) and isinstance(val.type, ir.PointerType):
                    val = self._builder.load(val)
                arg_values.append(val)

            call_name = f"call_{fn_name}" if llvm_func.function_type.return_type != ir.VoidType() else ""
            return self._builder.call(llvm_func, arg_values, name=call_name)

        if isinstance(expr, BoundFunctionPointerExpression):
            fn_name = expr.function.mangled_name or expr.function.name
            llvm_func = self._functions.get(fn_name)
            if llvm_func is None:
                return ir.Constant(ir.PointerType(ir.IntType(8)), None)
            return llvm_func

        if isinstance(expr, BoundIndirectCallExpression):
            callee_ptr = self._emit_expression(expr.callee)
            fn_t = expr.callee.type
            param_types = getattr(fn_t, "parameter_types", ())
            ret_t = getattr(fn_t, "return_type", TypeVoid)
            
            # If callee is pointer to function, get underlying function type
            llvm_ret_t = to_llvm_type(ret_t, self._struct_types)
            llvm_param_types = [to_llvm_type(p, self._struct_types) for p in param_types]
            llvm_fn_type = ir.FunctionType(llvm_ret_t, llvm_param_types)

            # Cast pointer to function pointer if needed
            fn_ptr_type = ir.PointerType(llvm_fn_type)
            if callee_ptr.type != fn_ptr_type:
                callee_ptr = self._builder.bitcast(callee_ptr, fn_ptr_type, name="fn_ptr_cast")

            arg_values: list[ir.Value] = []
            for i, arg in enumerate(expr.arguments):
                val = self._emit_expression(arg)
                if i < len(param_types):
                    val = self._coerce_type(val, arg.type, param_types[i])
                    if isinstance(param_types[i], StructTypeSymbol) and isinstance(val.type, ir.PointerType):
                        val = self._builder.load(val)
                arg_values.append(val)

            call_name = "indirect_call" if llvm_ret_t != ir.VoidType() else ""
            return self._builder.call(callee_ptr, arg_values, name=call_name)

        if isinstance(expr, BoundArrayLiteralExpression):
            count = len(expr.elements)
            elem_t = expr.array_type.element_type if isinstance(expr.array_type, ArrayTypeSymbol) else TypeInt
            llvm_elem_t = to_llvm_type(elem_t)
            # Allocate stack buffer for the array elements: [count x llvm_elem_t]
            arr_type = ir.ArrayType(llvm_elem_t, max(count, 1))
            with self._builder.goto_entry_block(): # type: ignore
                arr_alloca = self._builder.alloca(arr_type, name="arr_lit")

            # Store each element into its index in the stack buffer
            for i, elem in enumerate(expr.elements):
                val = self._emit_expression(elem)
                val = self._coerce_type(val, elem.type, elem_t)
                elem_ptr = self._builder.gep(
                    arr_alloca,
                    [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)],
                    inbounds=True,
                    name=f"arr_elem_{i}"
                )
                self._builder.store(val, elem_ptr)

            # Return a decayed pointer to the first element (llvm_elem_t*)
            first_elem_ptr = self._builder.gep(
                arr_alloca,
                [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)],
                inbounds=True,
                name="arr_decay"
            )
            return first_elem_ptr

        if isinstance(expr, BoundIndexExpression):
            target_ptr = self._emit_expression(expr.target)
            idx_val = self._emit_expression(expr.index)
            # Ensure idx_val is i64
            if idx_val.type != ir.IntType(64):
                idx_val = self._builder.sext(idx_val, ir.IntType(64)) if idx_val.type.width < 64 else self._builder.trunc(idx_val, ir.IntType(64))
            elem_ptr = self._builder.gep(target_ptr, [idx_val], inbounds=True, name="idx_ptr")
            return self._builder.load(elem_ptr, name="idx_val")

        if isinstance(expr, BoundIndexAssignmentExpression):
            target_ptr = self._emit_expression(expr.target)
            idx_val = self._emit_expression(expr.index)
            if idx_val.type != ir.IntType(64):
                idx_val = self._builder.sext(idx_val, ir.IntType(64)) if idx_val.type.width < 64 else self._builder.trunc(idx_val, ir.IntType(64))

            elem_ptr = self._builder.gep(target_ptr, [idx_val], inbounds=True, name="idx_assign_ptr")
            val = self._emit_expression(expr.value)
            elem_t = expr.target.type.element_type if isinstance(expr.target.type, ArrayTypeSymbol) else (expr.target.type.base_type if isinstance(expr.target.type, PointerTypeSymbol) else expr.value.type)
            val = self._coerce_type(val, expr.value.type, elem_t)

            op = expr.operator_kind
            if op != "=":
                old_val = self._builder.load(elem_ptr, name="old_elem_val")
                val = self._apply_compound_op(op, old_val, val, elem_t)

            self._builder.store(val, elem_ptr)
            return val

        if isinstance(expr, BoundMemberAccessExpression):
            field_ptr = self._get_lvalue_ptr(expr)
            if isinstance(expr.type, StructTypeSymbol):
                return field_ptr
            return self._builder.load(field_ptr, name=f"field_{expr.member_name}_val")

        if isinstance(expr, BoundMemberAssignmentExpression):
            target_expr = BoundMemberAccessExpression(expr.target, expr.member_name, expr.member_index, expr.member_type)
            field_ptr = self._get_lvalue_ptr(target_expr)
            val = self._emit_expression(expr.value)
            val = self._coerce_type(val, expr.value.type, expr.member_type)

            op = expr.operator_kind
            if op != "=":
                old_val = self._builder.load(field_ptr, name="old_field_val")
                val = self._apply_compound_op(op, old_val, val, expr.member_type)

            if isinstance(expr.member_type, StructTypeSymbol) and isinstance(val.type, ir.PointerType) and val.type.pointee == field_ptr.type.pointee:
                val = self._builder.load(val)

            self._builder.store(val, field_ptr)
            return val

        if isinstance(expr, BoundAddressOfExpression):
            # Take address of lvalue operand
            return self._get_lvalue_ptr(expr.operand)

        if isinstance(expr, BoundDereferenceExpression):
            ptr_val = self._emit_expression(expr.operand)
            if isinstance(expr.type, StructTypeSymbol):
                return ptr_val
            return self._builder.load(ptr_val, name="deref_val")

        if isinstance(expr, BoundDereferenceAssignmentExpression):
            ptr_val = self._emit_expression(expr.operand)
            val = self._emit_expression(expr.value)
            elem_t = expr.operand.type.base_type if isinstance(expr.operand.type, PointerTypeSymbol) else expr.value.type
            val = self._coerce_type(val, expr.value.type, elem_t)

            op = expr.operator_kind
            if op != "=":
                old_val = self._builder.load(ptr_val, name="old_deref_val")
                val = self._apply_compound_op(op, old_val, val, elem_t)

            self._builder.store(val, ptr_val)
            return val

        if isinstance(expr, BoundAllocExpression):
            llvm_elem_t = to_llvm_type(expr.allocated_type, self._struct_types)
            # Calculate sizeof(llvm_elem_t) using GEP null idiom
            null_ptr = ir.Constant(ir.PointerType(llvm_elem_t), None)
            gep_one = self._builder.gep(null_ptr, [ir.Constant(ir.IntType(32), 1)], name="sizeof_gep")
            sizeof_elem = self._builder.ptrtoint(gep_one, ir.IntType(64), name="sizeof_val")

            if expr.count is not None:
                count_val = self._emit_expression(expr.count)
                if count_val.type != ir.IntType(64):
                    count_val = self._builder.sext(count_val, ir.IntType(64)) if count_val.type.width < 64 else self._builder.trunc(count_val, ir.IntType(64))
                total_bytes = self._builder.mul(sizeof_elem, count_val, name="alloc_bytes")
            else:
                total_bytes = sizeof_elem

            raw_ptr = self._builder.call(self._malloc, [total_bytes], name="malloc_call")
            return self._builder.bitcast(raw_ptr, ir.PointerType(llvm_elem_t), name="alloc_ptr")

        if isinstance(expr, BoundCastExpression):
            inner_val = self._emit_expression(expr.expression)
            from_t = expr.expression.type
            to_t = expr.target_type
            dest_llvm_t = to_llvm_type(to_t, self._struct_types)

            # Same type
            if inner_val.type == dest_llvm_t:
                return inner_val

            # Float <-> Float (f32 <-> f64)
            if from_t in (TypeFloat, TypeDouble) and to_t in (TypeFloat, TypeDouble):
                if from_t == TypeFloat and to_t == TypeDouble:
                    return self._builder.fpext(inner_val, dest_llvm_t)
                elif from_t == TypeDouble and to_t == TypeFloat:
                    return self._builder.fptrunc(inner_val, dest_llvm_t)
                return inner_val

            # Int/Int32 <-> Float/Double
            if from_t in (TypeInt, TypeInt32) and to_t in (TypeFloat, TypeDouble):
                return self._builder.sitofp(inner_val, dest_llvm_t)
            if from_t in (TypeFloat, TypeDouble) and to_t in (TypeInt, TypeInt32):
                return self._builder.fptosi(inner_val, dest_llvm_t)

            # Int <-> Int32
            if from_t in (TypeInt, TypeInt32) and to_t in (TypeInt, TypeInt32):
                if to_t == TypeInt32:
                    return self._builder.trunc(inner_val, dest_llvm_t) if inner_val.type != dest_llvm_t else inner_val
                else:
                    return self._builder.sext(inner_val, dest_llvm_t) if inner_val.type != dest_llvm_t else inner_val

            # Pointer <-> Pointer
            if isinstance(from_t, PointerTypeSymbol) and isinstance(to_t, PointerTypeSymbol):
                return self._builder.bitcast(inner_val, dest_llvm_t)

            # Pointer <-> Int/Int32
            if isinstance(from_t, PointerTypeSymbol) and to_t in (TypeInt, TypeInt32):
                return self._builder.ptrtoint(inner_val, dest_llvm_t)
            if from_t in (TypeInt, TypeInt32) and isinstance(to_t, PointerTypeSymbol):
                return self._builder.inttoptr(inner_val, dest_llvm_t)

            # Int/Int32 <-> Char
            if from_t in (TypeInt, TypeInt32) and to_t == TypeChar:
                return self._builder.trunc(inner_val, dest_llvm_t)
            if from_t == TypeChar and to_t in (TypeInt, TypeInt32):
                return self._builder.sext(inner_val, dest_llvm_t)

            # Int/Int32 <-> Bool
            if from_t in (TypeInt, TypeInt32) and to_t == TypeBool:
                zero_c = ir.Constant(inner_val.type, 0)
                return self._builder.icmp_signed("!=", inner_val, zero_c)
            if from_t == TypeBool and to_t in (TypeInt, TypeInt32):
                return self._builder.zext(inner_val, dest_llvm_t)

            # Array <-> Pointer
            if isinstance(from_t, ArrayTypeSymbol) and isinstance(to_t, PointerTypeSymbol):
                return self._builder.bitcast(inner_val, dest_llvm_t)

            # Pointer / Function Pointer <-> Pointer
            if isinstance(inner_val.type, ir.PointerType) and isinstance(dest_llvm_t, ir.PointerType):
                return self._builder.bitcast(inner_val, dest_llvm_t)
            if not isinstance(inner_val.type, ir.PointerType) and isinstance(dest_llvm_t, ir.PointerType):
                return self._builder.inttoptr(inner_val, dest_llvm_t)
            if isinstance(inner_val.type, ir.PointerType) and not isinstance(dest_llvm_t, ir.PointerType):
                return self._builder.ptrtoint(inner_val, dest_llvm_t)

            # General bitcast fallback
            try:
                return self._builder.bitcast(inner_val, dest_llvm_t)
            except Exception:
                return inner_val

        if isinstance(expr, BoundAssignmentExpression):
            alloca = self._lookup_var(expr.variable.name)
            if alloca is None:
                return ir.Constant(ir.IntType(64), 0)

            right_val = self._emit_expression(expr.expression)
            op = expr.operator_kind

            if op != "=":
                old_val = self._builder.load(alloca, name=expr.variable.name)
                right_val = self._apply_compound_op(op, old_val, right_val, expr.variable.type)

            right_val = self._coerce_type(right_val, expr.expression.type, expr.variable.type)
            if isinstance(expr.variable.type, StructTypeSymbol) and isinstance(right_val.type, ir.PointerType) and right_val.type.pointee == alloca.type.pointee:
                right_val = self._builder.load(right_val)
            self._builder.store(right_val, alloca)
            return right_val

        if isinstance(expr, BoundUnaryExpression):
            op_kind = expr.operator.operator_kind
            operand_val = self._emit_expression(expr.operand)
            is_flt = (expr.operand.type in (TypeFloat, TypeDouble))

            if op_kind in ("++", "--"):
                lval_ptr = self._get_lvalue_ptr(expr.operand)
                one = ir.Constant(ir.DoubleType(), 1.0) if is_flt else ir.Constant(to_llvm_type(expr.operand.type, self._struct_types), 1)
                if op_kind == "++":
                    new_val = self._builder.fadd(operand_val, one) if is_flt else self._builder.add(operand_val, one)
                else:
                    new_val = self._builder.fsub(operand_val, one) if is_flt else self._builder.sub(operand_val, one)
                self._builder.store(new_val, lval_ptr)
                return operand_val if expr.is_postfix else new_val

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
            if expr.left.type in (TypeInt, TypeInt32) and expr.right.type in (TypeFloat, TypeDouble):
                target_flt = ir.FloatType() if expr.right.type == TypeFloat else ir.DoubleType()
                left_val = self._builder.sitofp(left_val, target_flt)
            elif expr.left.type in (TypeFloat, TypeDouble) and expr.right.type in (TypeInt, TypeInt32):
                target_flt = ir.FloatType() if expr.left.type == TypeFloat else ir.DoubleType()
                right_val = self._builder.sitofp(right_val, target_flt)

            # If both are float but one is float32 and other is float64: promote float32 to double
            if left_val.type == ir.FloatType() and right_val.type == ir.DoubleType():
                left_val = self._builder.fpext(left_val, ir.DoubleType())
            elif left_val.type == ir.DoubleType() and right_val.type == ir.FloatType():
                right_val = self._builder.fpext(right_val, ir.DoubleType())

            is_flt = isinstance(left_val.type, (ir.FloatType, ir.DoubleType))

            # Pointer arithmetic
            if isinstance(left_val.type, ir.PointerType) and isinstance(right_val.type, ir.IntType):
                if op == "+":
                    return self._builder.gep(left_val, [right_val], inbounds=True, name="ptr_add")
                elif op == "-":
                    neg_idx = self._builder.neg(right_val, name="ptr_neg_idx")
                    return self._builder.gep(left_val, [neg_idx], inbounds=True, name="ptr_sub")
            elif isinstance(right_val.type, ir.PointerType) and isinstance(left_val.type, ir.IntType) and op == "+":
                return self._builder.gep(right_val, [left_val], inbounds=True, name="ptr_add")

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

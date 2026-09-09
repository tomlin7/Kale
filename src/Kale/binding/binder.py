import os
from typing import Any, Optional
from ..diagnostics.diagnostic_bag import DiagnosticBag
from ..syntax.syntax_kind import SyntaxKind
from ..syntax.syntax_token import SyntaxToken
from ..ast.nodes import (
    CompilationUnit,
    Statement,
    BlockStatement,
    ParameterNode,
    FunctionDeclarationStatement,
    ExternFunctionDeclarationStatement,
    VariableDeclarationStatement,
    ExpressionStatement,
    IfStatement,
    WhileStatement,
    ForStatement,
    PrintStatement,
    ReturnStatement,
    BreakStatement,
    ContinueStatement,
    Expression,
    LiteralExpression,
    VariableExpression,
    GroupingExpression,
    UnaryExpression,
    BinaryExpression,
    AssignmentExpression,
    DereferenceAssignmentExpression,
    CallExpression,
    ArrayLiteralExpression,
    IndexExpression,
    IndexAssignmentExpression,
    MemberAccessExpression,
    MemberAssignmentExpression,
    ArrowAccessExpression,
    ArrowAssignmentExpression,
    AllocExpression,
    CastExpression,
    FreeStatement,
    StructDeclarationStatement,
    StructFieldNode,
    EnumMemberNode,
    EnumDeclarationStatement,
    SwitchCaseClause,
    SwitchDefaultClause,
    SwitchStatement,
    ImportStatement,
    FromImportStatement,
)
from .types import (
    TypeSymbol,
    TypeInt,
    TypeFloat,
    TypeDouble,
    TypeBool,
    TypeString,
    TypeChar,
    TypeVoid,
    TypeUnknown,
    ArrayTypeSymbol,
    PointerTypeSymbol,
    StructTypeSymbol,
    EnumTypeSymbol,
    ModuleTypeSymbol,
    lookup_type,
    is_numeric,
    can_convert,
    can_explicit_cast,
    get_promoted_numeric_type,
)
from .symbols import VariableSymbol, FunctionSymbol, ModuleSymbol, Symbol
from .scope import Scope
from .bound_nodes import (
    BoundProgram,
    BoundStatement,
    BoundBlockStatement,
    BoundVariableDeclaration,
    BoundFunctionDeclaration,
    BoundStructDeclaration,
    BoundEnumDeclaration,
    BoundExpressionStatement,
    BoundIfStatement,
    BoundWhileStatement,
    BoundForStatement,
    BoundSwitchCase,
    BoundSwitchStatement,
    BoundPrintStatement,
    BoundFreeStatement,
    BoundReturnStatement,
    BoundBreakStatement,
    BoundContinueStatement,
    BoundImportStatement,
    BoundExpression,
    BoundLiteralExpression,
    BoundVariableExpression,
    BoundCallExpression,
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
    BoundAssignmentExpression,
    BoundUnaryExpression,
    BoundUnaryOperator,
    BoundBinaryExpression,
    BoundBinaryOperator,
)

class Binder:
    """Walks the AST, resolves symbols, checks types, and produces a typed BoundProgram."""
    def __init__(self, diagnostics: DiagnosticBag, module_loader: Any = None, current_file: str | None = None):
        self.diagnostics = diagnostics
        self._module_loader = module_loader
        self._current_file = current_file
        self._current_scope = Scope()
        self._current_function: FunctionSymbol | None = None
        self._struct_types: dict[str, StructTypeSymbol] = {}
        self._enum_types: dict[str, EnumTypeSymbol] = {}
        self._module_symbols: dict[str, ModuleSymbol] = {}
        self._imported_functions: list[BoundFunctionDeclaration] = []
        self._imported_structs: list[BoundStructDeclaration] = []
        self._imported_enums: list[BoundEnumDeclaration] = []

    def _resolve_type(self, type_name: str) -> TypeSymbol:
        # Check qualified module types: e.g. geo.Point or math.Vec3 or math.Color
        if "." in type_name and not type_name.endswith("*") and not type_name.endswith("]"):
            parts = type_name.split(".", 1)
            mod_sym = self._current_scope.lookup(parts[0])
            if isinstance(mod_sym, ModuleSymbol) and isinstance(mod_sym.type, ModuleTypeSymbol):
                st = mod_sym.type.get_struct_type(parts[1])
                if st is not None:
                    return st
                et = mod_sym.type.get_enum_type(parts[1])
                if et is not None:
                    return et

        # Check custom structs
        if type_name in self._struct_types:
            return self._struct_types[type_name]
        # Check custom enums
        if type_name in self._enum_types:
            return self._enum_types[type_name]
        # Check pointer types (e.g. Point*, int*, Point**)
        if type_name.endswith("*"):
            base_name = type_name[:-1].strip()
            base_t = self._resolve_type(base_name)
            if base_t is not TypeUnknown:
                return PointerTypeSymbol(base_t)
        # Check array of struct/enum (e.g. Point[] or Point[10])
        if type_name.endswith("]"):
            bracket_start = type_name.find("[")
            if bracket_start != -1:
                base_name = type_name[:bracket_start].strip()
                size_str = type_name[bracket_start + 1:-1].strip()
                elem_t = self._resolve_type(base_name)
                if elem_t is not TypeUnknown:
                    sz = int(size_str) if size_str.isdigit() else None
                    return ArrayTypeSymbol(elem_t, sz)
        # Builtins
        looked_up = lookup_type(type_name)
        return looked_up if looked_up is not None else TypeUnknown

    def bind_program(self, compilation_unit: CompilationUnit) -> BoundProgram:
        # Pass 0: Discover and register all struct, enum, and extern declarations
        struct_decls: list[StructDeclarationStatement] = []
        enum_decls: list[EnumDeclarationStatement] = []
        extern_decls: list[ExternFunctionDeclarationStatement] = []
        function_decls: list[FunctionDeclarationStatement] = []
        import_stmts: list[Statement] = []
        top_level_stmts: list[Statement] = []

        for stmt in compilation_unit.statements:
            if isinstance(stmt, StructDeclarationStatement):
                struct_decls.append(stmt)
                s_name = stmt.identifier_token.text
                if s_name in self._struct_types:
                    self.diagnostics.report(stmt.identifier_token.span, f"Struct '{s_name}' is already defined.")
                else:
                    # Temporary empty struct symbol to allow self-referencing pointers if needed later
                    self._struct_types[s_name] = StructTypeSymbol(name=s_name, fields=())
            elif isinstance(stmt, EnumDeclarationStatement):
                enum_decls.append(stmt)
            elif isinstance(stmt, ExternFunctionDeclarationStatement):
                extern_decls.append(stmt)
            elif isinstance(stmt, FunctionDeclarationStatement):
                function_decls.append(stmt)
            elif isinstance(stmt, (ImportStatement, FromImportStatement)):
                import_stmts.append(stmt)
            else:
                top_level_stmts.append(stmt)

        # Pass 0.5: Bind all imports first so types, functions, and module symbols are known
        bound_import_statements: list[BoundStatement] = []
        for imp_stmt in import_stmts:
            bound_imp = self.bind_statement(imp_stmt)
            if bound_imp is not None:
                bound_import_statements.append(bound_imp)

        # Populate enum members
        bound_enums: list[BoundEnumDeclaration] = []
        for e_stmt in enum_decls:
            e_name = e_stmt.identifier_token.text
            if e_name in self._enum_types:
                self.diagnostics.report(e_stmt.identifier_token.span, f"Enum '{e_name}' is already defined.")
                continue
            member_list: list[tuple[str, int]] = []
            seen_members: set[str] = set()
            next_val = 0
            for m in e_stmt.members:
                m_name = m.identifier_token.text
                if m_name in seen_members:
                    self.diagnostics.report(m.identifier_token.span, f"Duplicate member '{m_name}' in enum '{e_name}'.")
                seen_members.add(m_name)
                if m.value_expression is not None:
                    bound_val = self.bind_expression(m.value_expression)
                    if isinstance(bound_val, BoundLiteralExpression) and isinstance(bound_val.value, int):
                        next_val = bound_val.value
                    else:
                        self.diagnostics.report(m.value_expression.span, f"Enum member value for '{m_name}' must be an integer literal.")
                m_val = next_val
                next_val += 1
                member_list.append((m_name, m_val))

            enum_sym = EnumTypeSymbol(name=e_name, members=tuple(member_list))
            self._enum_types[e_name] = enum_sym
            bound_enums.append(BoundEnumDeclaration(enum_sym))

        # Populate struct fields
        bound_structs: list[BoundStructDeclaration] = []
        for s_stmt in struct_decls:
            s_name = s_stmt.identifier_token.text
            field_list: list[tuple[str, TypeSymbol]] = []
            seen_fields: set[str] = set()
            for f in s_stmt.fields:
                fname = f.identifier_token.text
                if fname in seen_fields:
                    self.diagnostics.report(f.identifier_token.span, f"Duplicate field '{fname}' in struct '{s_name}'.")
                seen_fields.add(fname)
                ftype = self._resolve_type(f.type_token.text)
                if ftype == TypeUnknown:
                    self.diagnostics.report(f.type_token.span, f"Unknown type '{f.type_token.text}' for field '{fname}'.")
                field_list.append((fname, ftype))

            st_sym = StructTypeSymbol(name=s_name, fields=tuple(field_list))
            self._struct_types[s_name] = st_sym
            bound_structs.append(BoundStructDeclaration(st_sym))

        # Pass 1: Discover all function declarations (including externs) and register signatures
        for stmt in extern_decls:
            fn_name = stmt.identifier_token.text
            ret_type = self._resolve_type(stmt.return_type_token.text)
            if ret_type == TypeUnknown and stmt.return_type_token.text != "void":
                self.diagnostics.report(stmt.return_type_token.span, f"Unknown return type '{stmt.return_type_token.text}'.")
            params: list[VariableSymbol] = []
            for p in stmt.parameters:
                pt = self._resolve_type(p.type_token.text)
                if pt == TypeUnknown:
                    self.diagnostics.report(p.type_token.span, f"Unknown parameter type '{p.type_token.text}'.")
                params.append(VariableSymbol(name=p.identifier_token.text, type=pt))
            fn_sym = FunctionSymbol(
                name=fn_name,
                parameters=tuple(params),
                return_type=ret_type,
                is_extern=True,
                is_var_args=stmt.is_var_args,
            )
            if not self._current_scope.try_declare(fn_sym):
                self.diagnostics.report(stmt.identifier_token.span, f"Function '{fn_name}' is already declared in this scope.")

        for stmt in function_decls:
            fn_name = stmt.identifier_token.text
            ret_type = self._resolve_type(stmt.return_type_token.text)
            if ret_type == TypeUnknown and stmt.return_type_token.text != "void":
                self.diagnostics.report(stmt.return_type_token.span, f"Unknown return type '{stmt.return_type_token.text}'.")
            params: list[VariableSymbol] = []
            for p in stmt.parameters:
                pt = self._resolve_type(p.type_token.text)
                if pt == TypeUnknown:
                    self.diagnostics.report(p.type_token.span, f"Unknown parameter type '{p.type_token.text}'.")
                params.append(VariableSymbol(name=p.identifier_token.text, type=pt))
            fn_sym = FunctionSymbol(name=fn_name, parameters=tuple(params), return_type=ret_type)
            if not self._current_scope.try_declare(fn_sym):
                self.diagnostics.report(stmt.identifier_token.span, f"Function '{fn_name}' is already declared in this scope.")

        # Pass 2a: Bind function bodies
        bound_functions: list[BoundFunctionDeclaration] = []
        for ext_stmt in extern_decls:
            sym = self._current_scope.lookup(ext_stmt.identifier_token.text)
            if isinstance(sym, FunctionSymbol):
                bound_functions.append(BoundFunctionDeclaration(sym, body=None))

        for fn_stmt in function_decls:
            sym = self._current_scope.lookup(fn_stmt.identifier_token.text)
            if isinstance(sym, FunctionSymbol):
                self._current_scope = Scope(parent=self._current_scope)
                for p in sym.parameters:
                    self._current_scope.try_declare(p)
                self._current_function = sym
                bound_body = self._bind_block_statement(fn_stmt.body, new_scope=False)
                self._current_function = None
                self._current_scope = self._current_scope.parent # type: ignore
                bound_functions.append(BoundFunctionDeclaration(sym, bound_body))

        # Pass 2b: Bind top-level statements
        bound_statements: list[BoundStatement] = list(bound_import_statements)
        for statement in top_level_stmts:
            bound_stmt = self.bind_statement(statement)
            if bound_stmt is not None:
                bound_statements.append(bound_stmt)

        # Combine local structs and imported structs
        all_structs = list(self._imported_structs)
        for st in bound_structs:
            if not any(s.struct_type.name == st.struct_type.name for s in all_structs):
                all_structs.append(st)

        # Combine local enums and imported enums
        all_enums = list(self._imported_enums)
        for en in bound_enums:
            if not any(e.enum_type.name == en.enum_type.name for e in all_enums):
                all_enums.append(en)

        # Combine local functions and imported functions
        all_functions = list(self._imported_functions)
        for fn in bound_functions:
            if not any(f.symbol.name == fn.symbol.name and f.symbol.mangled_name == fn.symbol.mangled_name for f in all_functions):
                all_functions.append(fn)

        return BoundProgram(
            statements=bound_statements,
            root_scope=self._current_scope,
            functions=all_functions,
            structs=all_structs,
            enums=all_enums,
            module_symbols=self._module_symbols,
        )

    def bind_statement(self, statement: Statement) -> BoundStatement | None:
        if isinstance(statement, BlockStatement):
            return self._bind_block_statement(statement)
        if isinstance(statement, ImportStatement):
            return self._bind_import_statement(statement)
        if isinstance(statement, FromImportStatement):
            return self._bind_from_import_statement(statement)
        if isinstance(statement, VariableDeclarationStatement):
            return self._bind_variable_declaration(statement)
        if isinstance(statement, IfStatement):
            return self._bind_if_statement(statement)
        if isinstance(statement, SwitchStatement):
            return self._bind_switch_statement(statement)
        if isinstance(statement, WhileStatement):
            return self._bind_while_statement(statement)
        if isinstance(statement, ForStatement):
            return self._bind_for_statement(statement)
        if isinstance(statement, PrintStatement):
            return self._bind_print_statement(statement)
        if isinstance(statement, FreeStatement):
            return self._bind_free_statement(statement)
        if isinstance(statement, ReturnStatement):
            return self._bind_return_statement(statement)
        if isinstance(statement, BreakStatement):
            return BoundBreakStatement()
        if isinstance(statement, ContinueStatement):
            return BoundContinueStatement()
        if isinstance(statement, ExpressionStatement):
            return self._bind_expression_statement(statement)
        return None

    def _load_and_bind_module(self, module_rel_path: str, span: Any) -> tuple[str, ModuleTypeSymbol] | None:
        if self._module_loader is None:
            self.diagnostics.report(span, "No module loader configured to resolve imports.")
            return None

        norm_path, unit = self._module_loader.load_module(module_rel_path, importing_file=self._current_file, span=span)
        if unit is None or norm_path is None:
            return None

        # If already bound, return cached module symbol
        if norm_path in self._module_loader._bound_modules:
            return self._module_loader._bound_modules[norm_path]

        # Check for circular import in binding chain
        if norm_path in self._module_loader._binding_chain:
            chain = [os.path.basename(p) for p in self._module_loader._binding_chain] + [os.path.basename(norm_path)]
            self.diagnostics.report(span, f"Circular import dependency detected: {' -> '.join(chain)}.")
            return None

        self._module_loader._binding_chain.append(norm_path)

        # Bind the loaded module in a sub-binder
        try:
            sub_binder = Binder(self.diagnostics, module_loader=self._module_loader, current_file=norm_path)
            sub_program = sub_binder.bind_program(unit)
        finally:
            self._module_loader._binding_chain.pop()

        # Collect imported structs and functions into our own lists (with prefix mangling for uniqueness if needed)
        mod_base_name = os.path.splitext(os.path.basename(norm_path))[0]
        symbols: dict[str, Any] = {}
        structs: dict[str, Any] = {}
        enums: dict[str, Any] = {}

        for en in sub_program.enums:
            enums[en.enum_type.name] = en.enum_type
            if not any(e.enum_type.name == en.enum_type.name for e in self._imported_enums):
                self._imported_enums.append(en)

        for st in sub_program.structs:
            structs[st.struct_type.name] = st.struct_type
            if not any(s.struct_type.name == st.struct_type.name for s in self._imported_structs):
                self._imported_structs.append(st)

        for fn in sub_program.functions:
            fn_sym = fn.symbol
            # Keep extern functions un-mangled so they resolve to their actual C symbols
            if fn_sym.is_extern:
                mangled = fn_sym.name
            else:
                mangled = f"kale_{mod_base_name}_{fn_sym.name}"
            mangled_fn_sym = FunctionSymbol(
                name=fn_sym.name,
                parameters=fn_sym.parameters,
                return_type=fn_sym.return_type,
                mangled_name=mangled,
                is_extern=fn_sym.is_extern,
                is_var_args=fn_sym.is_var_args,
            )
            symbols[fn_sym.name] = mangled_fn_sym
            mangled_fn_decl = BoundFunctionDeclaration(mangled_fn_sym, fn.body)
            if not any(f.symbol.mangled_name == mangled for f in self._imported_functions):
                self._imported_functions.append(mangled_fn_decl)

        mod_type = ModuleTypeSymbol(module_name=mod_base_name, file_path=norm_path, symbols=symbols, structs=structs, enums=enums)
        self._module_loader._bound_modules[norm_path] = (mod_base_name, mod_type)
        return mod_base_name, mod_type

    def _bind_import_statement(self, statement: ImportStatement) -> BoundStatement | None:
        rel_path = str(statement.module_path_token.value)
        res = self._load_and_bind_module(rel_path, statement.module_path_token.span)
        if res is None:
            return None
        mod_base_name, mod_type = res
        alias = statement.alias_token.text if statement.alias_token else mod_base_name

        mod_sym = ModuleSymbol(name=alias, type=mod_type)
        if not self._current_scope.try_declare(mod_sym):
            self.diagnostics.report(
                statement.alias_token.span if statement.alias_token else statement.module_path_token.span,
                f"Symbol '{alias}' is already declared in this scope."
            )
        self._module_symbols[alias] = mod_sym
        return BoundImportStatement(module_path=rel_path, alias=alias, module_symbol=mod_sym)

    def _bind_from_import_statement(self, statement: FromImportStatement) -> BoundStatement | None:
        rel_path = str(statement.module_path_token.value)
        res = self._load_and_bind_module(rel_path, statement.module_path_token.span)
        if res is None:
            return None
        mod_base_name, mod_type = res

        for sym_token in statement.imported_symbols:
            sym_name = sym_token.text
            fn_sym = mod_type.get_member_symbol(sym_name)
            st_sym = mod_type.get_struct_type(sym_name)
            en_sym = mod_type.get_enum_type(sym_name)

            if fn_sym is not None:
                if not self._current_scope.try_declare(fn_sym):
                    self.diagnostics.report(sym_token.span, f"Symbol '{sym_name}' is already declared in this scope.")
            elif st_sym is not None:
                self._struct_types[sym_name] = st_sym
            elif en_sym is not None:
                self._enum_types[sym_name] = en_sym
            else:
                self.diagnostics.report(sym_token.span, f"Module '{mod_base_name}' has no member, struct, or enum named '{sym_name}'.")

        return None

    def _bind_block_statement(self, statement: BlockStatement, new_scope: bool = True) -> BoundBlockStatement:
        if new_scope:
            self._current_scope = Scope(parent=self._current_scope)
        bound_stmts: list[BoundStatement] = []
        for s in statement.statements:
            b = self.bind_statement(s)
            if b is not None:
                bound_stmts.append(b)
        if new_scope:
            self._current_scope = self._current_scope.parent # type: ignore
        return BoundBlockStatement(bound_stmts)

    def _bind_variable_declaration(self, statement: VariableDeclarationStatement) -> BoundVariableDeclaration:
        type_token = statement.type_token
        ident = statement.identifier_token
        name = ident.text
        is_const = (type_token.kind == SyntaxKind.ConstKeyword)

        # Bind initializer if present
        bound_init = None
        if statement.initializer is not None:
            bound_init = self.bind_expression(statement.initializer)

        # Determine variable type
        var_type: TypeSymbol = TypeUnknown
        if type_token.kind in (SyntaxKind.LetKeyword, SyntaxKind.VarKeyword, SyntaxKind.ConstKeyword):
            if bound_init is not None:
                var_type = bound_init.type
            else:
                var_type = TypeInt # default type
        else:
            var_type = self._resolve_type(type_token.text)

        # Check type compatibility
        if bound_init is not None and not can_convert(bound_init.type, var_type):
            self.diagnostics.report_cannot_convert(statement.initializer.span, str(bound_init.type), str(var_type))

        variable = VariableSymbol(name=name, type=var_type, is_read_only=is_const)
        if not self._current_scope.try_declare(variable):
            self.diagnostics.report_variable_already_declared(ident.span, name)

        return BoundVariableDeclaration(variable, bound_init)

    def _bind_if_statement(self, statement: IfStatement) -> BoundIfStatement:
        cond = self.bind_expression(statement.condition)
        if not can_convert(cond.type, TypeBool):
            self.diagnostics.report_cannot_convert(statement.condition.span, str(cond.type), "bool")
        then_stmt = self.bind_statement(statement.then_statement) or BoundBlockStatement([])
        else_stmt = None
        if statement.else_clause is not None:
            else_stmt = self.bind_statement(statement.else_clause.statement)
        return BoundIfStatement(cond, then_stmt, else_stmt)

    def _bind_switch_statement(self, statement: SwitchStatement) -> BoundSwitchStatement:
        cond = self.bind_expression(statement.condition)
        if not (cond.type == TypeInt or isinstance(cond.type, EnumTypeSymbol)):
            self.diagnostics.report(statement.condition.span, f"Switch condition must be integer or enum type, got '{cond.type}'.")

        bound_cases: list[BoundSwitchCase] = []
        for case_clause in statement.cases:
            case_val = self.bind_expression(case_clause.value_expression)
            if not can_convert(case_val.type, cond.type):
                self.diagnostics.report_cannot_convert(case_clause.value_expression.span, str(case_val.type), str(cond.type))
            case_stmts: list[BoundStatement] = []
            for s in case_clause.statements:
                b = self.bind_statement(s)
                if b is not None:
                    case_stmts.append(b)
            bound_cases.append(BoundSwitchCase([case_val], case_stmts))

        default_stmts: list[BoundStatement] | None = None
        if statement.default_clause is not None:
            default_stmts = []
            for s in statement.default_clause.statements:
                b = self.bind_statement(s)
                if b is not None:
                    default_stmts.append(b)

        return BoundSwitchStatement(cond, bound_cases, default_stmts)

    def _bind_while_statement(self, statement: WhileStatement) -> BoundWhileStatement:
        cond = self.bind_expression(statement.condition)
        if not can_convert(cond.type, TypeBool):
            self.diagnostics.report_cannot_convert(statement.condition.span, str(cond.type), "bool")
        body = self.bind_statement(statement.body) or BoundBlockStatement([])
        return BoundWhileStatement(cond, body)

    def _bind_for_statement(self, statement: ForStatement) -> BoundForStatement:
        self._current_scope = Scope(parent=self._current_scope)
        init = self.bind_statement(statement.initializer) if statement.initializer else None
        cond = self.bind_expression(statement.condition) if statement.condition else None
        if cond is not None and not can_convert(cond.type, TypeBool):
            self.diagnostics.report_cannot_convert(statement.condition.span, str(cond.type), "bool") # type: ignore
        inc = self.bind_expression(statement.increment) if statement.increment else None
        body = self.bind_statement(statement.body) or BoundBlockStatement([])
        self._current_scope = self._current_scope.parent # type: ignore
        return BoundForStatement(init, cond, inc, body)

    def _bind_print_statement(self, statement: PrintStatement) -> BoundPrintStatement:
        bound_args = [self.bind_expression(arg) for arg in statement.arguments]
        return BoundPrintStatement(bound_args)

    def _bind_free_statement(self, statement: FreeStatement) -> BoundFreeStatement:
        bound_expr = self.bind_expression(statement.expression)
        if not isinstance(bound_expr.type, (PointerTypeSymbol, ArrayTypeSymbol)):
            self.diagnostics.report(statement.expression.span, f"Cannot free non-pointer expression of type '{bound_expr.type}'.")
        return BoundFreeStatement(bound_expr)

    def _bind_return_statement(self, statement: ReturnStatement) -> BoundReturnStatement:
        bound_expr = self.bind_expression(statement.expression) if statement.expression else None
        if self._current_function is not None:
            expected_type = self._current_function.return_type or TypeVoid
            actual_type = bound_expr.type if bound_expr else TypeVoid
            if not can_convert(actual_type, expected_type):
                span = statement.expression.span if statement.expression else statement.return_keyword.span
                self.diagnostics.report_cannot_convert(span, str(actual_type), str(expected_type))
        return BoundReturnStatement(bound_expr)

    def _bind_expression_statement(self, statement: ExpressionStatement) -> BoundExpressionStatement:
        expr = self.bind_expression(statement.expression)
        return BoundExpressionStatement(expr)

    # ==========================================
    # Bind Expressions
    # ==========================================

    def bind_expression(self, expression: Expression) -> BoundExpression:
        if isinstance(expression, LiteralExpression):
            return self._bind_literal_expression(expression)
        if isinstance(expression, VariableExpression):
            return self._bind_variable_expression(expression)
        if isinstance(expression, CallExpression):
            return self._bind_call_expression(expression)
        if isinstance(expression, GroupingExpression):
            return self.bind_expression(expression.expression)
        if isinstance(expression, UnaryExpression):
            return self._bind_unary_expression(expression)
        if isinstance(expression, BinaryExpression):
            return self._bind_binary_expression(expression)
        if isinstance(expression, AssignmentExpression):
            return self._bind_assignment_expression(expression)
        if isinstance(expression, ArrayLiteralExpression):
            return self._bind_array_literal_expression(expression)
        if isinstance(expression, IndexExpression):
            return self._bind_index_expression(expression)
        if isinstance(expression, IndexAssignmentExpression):
            return self._bind_index_assignment_expression(expression)
        if isinstance(expression, MemberAccessExpression):
            return self._bind_member_access_expression(expression)
        if isinstance(expression, MemberAssignmentExpression):
            return self._bind_member_assignment_expression(expression)
        if isinstance(expression, ArrowAccessExpression):
            return self._bind_arrow_access_expression(expression)
        if isinstance(expression, ArrowAssignmentExpression):
            return self._bind_arrow_assignment_expression(expression)
        if isinstance(expression, AllocExpression):
            return self._bind_alloc_expression(expression)
        if isinstance(expression, CastExpression):
            return self._bind_cast_expression(expression)
        if isinstance(expression, DereferenceAssignmentExpression):
            return self._bind_dereference_assignment_expression(expression)
        return BoundLiteralExpression(None, TypeUnknown)

    def _bind_cast_expression(self, expression: CastExpression) -> BoundExpression:
        target_type = self._resolve_type(expression.target_type_token.text)
        if target_type == TypeUnknown:
            self.diagnostics.report(expression.target_type_token.span, f"Unknown type '{expression.target_type_token.text}' in cast.")
            return BoundLiteralExpression(None, TypeUnknown)

        bound_inner = self.bind_expression(expression.expression)
        if not can_explicit_cast(bound_inner.type, target_type):
            self.diagnostics.report(
                expression.span,
                f"Cannot cast expression of type '{bound_inner.type}' to '{target_type}'."
            )
            return BoundLiteralExpression(None, TypeUnknown)

        return BoundCastExpression(bound_inner, target_type)

    def _bind_member_access_expression(self, expression: MemberAccessExpression) -> BoundExpression:
        # Check if target is a simple variable expression that names an enum type: Color.Red
        if isinstance(expression.target, VariableExpression):
            target_name = expression.target.identifier_token.text
            if target_name in self._enum_types:
                enum_t = self._enum_types[target_name]
                m_name = expression.member_token.text
                val = enum_t.get_member_value(m_name)
                if val is None:
                    self.diagnostics.report(expression.member_token.span, f"Enum '{enum_t.name}' has no member named '{m_name}'.")
                    return BoundLiteralExpression(None, TypeUnknown)
                return BoundLiteralExpression(val, enum_t)

        target = self.bind_expression(expression.target)
        if isinstance(target.type, ModuleTypeSymbol):
            m_name = expression.member_token.text
            # Module enum access: module.Enum (not member access yet) or module function/variable
            sym = target.type.get_member_symbol(m_name)
            if sym is not None:
                if isinstance(sym, VariableSymbol):
                    return BoundVariableExpression(sym)
                if isinstance(sym, FunctionSymbol):
                    return BoundVariableExpression(VariableSymbol(name=sym.mangled_name or sym.name, type=sym.type))
            enum_t = target.type.get_enum_type(m_name)
            if enum_t is not None:
                # Return a pseudo-variable expression typed with EnumTypeSymbol so chained member access module.Enum.Member works!
                dummy_var = VariableSymbol(name=f"{target.type.module_name}.{m_name}", type=enum_t)
                return BoundVariableExpression(dummy_var)
            self.diagnostics.report(expression.member_token.span, f"Module '{target.type.module_name}' has no member named '{m_name}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        # Chained member access on EnumTypeSymbol: e.g. (module.Enum).Member or var.Member where var: Enum
        if isinstance(target.type, EnumTypeSymbol):
            m_name = expression.member_token.text
            val = target.type.get_member_value(m_name)
            if val is None:
                self.diagnostics.report(expression.member_token.span, f"Enum '{target.type.name}' has no member named '{m_name}'.")
                return BoundLiteralExpression(None, TypeUnknown)
            return BoundLiteralExpression(val, target.type)

        if not isinstance(target.type, StructTypeSymbol):
            self.diagnostics.report(expression.target.span, f"Cannot access member of non-struct type '{target.type}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        m_name = expression.member_token.text
        m_type = target.type.get_field_type(m_name)
        if m_type is None:
            self.diagnostics.report(expression.member_token.span, f"Struct '{target.type.name}' has no field named '{m_name}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        m_idx = target.type.get_field_index(m_name)
        return BoundMemberAccessExpression(target, m_name, m_idx, m_type)

    def _bind_member_assignment_expression(self, expression: MemberAssignmentExpression) -> BoundExpression:
        target = self.bind_expression(expression.target)
        if not isinstance(target.type, StructTypeSymbol):
            self.diagnostics.report(expression.target.span, f"Cannot access member of non-struct type '{target.type}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        m_name = expression.member_token.text
        m_type = target.type.get_field_type(m_name)
        if m_type is None:
            self.diagnostics.report(expression.member_token.span, f"Struct '{target.type.name}' has no field named '{m_name}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        m_idx = target.type.get_field_index(m_name)
        value = self.bind_expression(expression.value)
        if not can_convert(value.type, m_type):
            self.diagnostics.report_cannot_convert(expression.value.span, str(value.type), str(m_type))

        return BoundMemberAssignmentExpression(target, m_name, m_idx, m_type, value, expression.operator_token.text)

    def _bind_arrow_access_expression(self, expression: ArrowAccessExpression) -> BoundExpression:
        target = self.bind_expression(expression.target)
        if not (isinstance(target.type, PointerTypeSymbol) and isinstance(target.type.base_type, StructTypeSymbol)):
            self.diagnostics.report(expression.target.span, f"Cannot use '->' operator on non-struct pointer type '{target.type}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        struct_t: StructTypeSymbol = target.type.base_type # type: ignore
        m_name = expression.member_token.text
        m_type = struct_t.get_field_type(m_name)
        if m_type is None:
            self.diagnostics.report(expression.member_token.span, f"Struct '{struct_t.name}' has no field named '{m_name}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        m_idx = struct_t.get_field_index(m_name)
        # An arrow access ptr->member is semantically equivalent to (*ptr).member
        deref_target = BoundDereferenceExpression(target, struct_t)
        return BoundMemberAccessExpression(deref_target, m_name, m_idx, m_type)

    def _bind_arrow_assignment_expression(self, expression: ArrowAssignmentExpression) -> BoundExpression:
        target = self.bind_expression(expression.target)
        if not (isinstance(target.type, PointerTypeSymbol) and isinstance(target.type.base_type, StructTypeSymbol)):
            self.diagnostics.report(expression.target.span, f"Cannot use '->' operator on non-struct pointer type '{target.type}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        struct_t: StructTypeSymbol = target.type.base_type # type: ignore
        m_name = expression.member_token.text
        m_type = struct_t.get_field_type(m_name)
        if m_type is None:
            self.diagnostics.report(expression.member_token.span, f"Struct '{struct_t.name}' has no field named '{m_name}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        m_idx = struct_t.get_field_index(m_name)
        value = self.bind_expression(expression.value)
        if not can_convert(value.type, m_type):
            self.diagnostics.report_cannot_convert(expression.value.span, str(value.type), str(m_type))

        deref_target = BoundDereferenceExpression(target, struct_t)
        return BoundMemberAssignmentExpression(deref_target, m_name, m_idx, m_type, value, expression.operator_token.text)

    def _bind_alloc_expression(self, expression: AllocExpression) -> BoundExpression:
        elem_t = self._resolve_type(expression.type_token.text)
        if elem_t == TypeUnknown:
            self.diagnostics.report(expression.type_token.span, f"Unknown type '{expression.type_token.text}' in alloc().")
            return BoundLiteralExpression(None, TypeUnknown)

        bound_count = None
        if expression.count_expression:
            bound_count = self.bind_expression(expression.count_expression)
            if not can_convert(bound_count.type, TypeInt):
                self.diagnostics.report_cannot_convert(expression.count_expression.span, str(bound_count.type), "int")

        ptr_t = PointerTypeSymbol(elem_t)
        return BoundAllocExpression(elem_t, bound_count, ptr_t)

    def _bind_dereference_assignment_expression(self, expression: DereferenceAssignmentExpression) -> BoundExpression:
        target = self.bind_expression(expression.target)
        if not isinstance(target.type, PointerTypeSymbol):
            self.diagnostics.report(expression.target.span, f"Cannot dereference non-pointer expression of type '{target.type}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        value = self.bind_expression(expression.value)
        elem_t = target.type.base_type
        if not can_convert(value.type, elem_t):
            self.diagnostics.report_cannot_convert(expression.value.span, str(value.type), str(elem_t))

        return BoundDereferenceAssignmentExpression(target, value, expression.operator_token.text)

    def _bind_array_literal_expression(self, expression: ArrayLiteralExpression) -> BoundExpression:
        bound_elements = [self.bind_expression(elem) for elem in expression.elements]
        if not bound_elements:
            elem_type = TypeInt # Default empty array element type
        else:
            elem_type = bound_elements[0].type
            for elem in bound_elements[1:]:
                if not can_convert(elem.type, elem_type):
                    self.diagnostics.report_cannot_convert(expression.span, str(elem.type), str(elem_type))

        arr_type = ArrayTypeSymbol(element_type=elem_type, size=len(bound_elements))
        return BoundArrayLiteralExpression(bound_elements, arr_type)

    def _bind_index_expression(self, expression: IndexExpression) -> BoundExpression:
        target = self.bind_expression(expression.target)
        index = self.bind_expression(expression.index)

        if not isinstance(target.type, (ArrayTypeSymbol, PointerTypeSymbol)):
            self.diagnostics.report(expression.target.span, f"Cannot index a non-array type '{target.type}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        if not can_convert(index.type, TypeInt):
            self.diagnostics.report_cannot_convert(expression.index.span, str(index.type), "int")

        elem_type = target.type.element_type if isinstance(target.type, ArrayTypeSymbol) else target.type.base_type
        return BoundIndexExpression(target, index, elem_type)

    def _bind_index_assignment_expression(self, expression: IndexAssignmentExpression) -> BoundExpression:
        target = self.bind_expression(expression.target)
        index = self.bind_expression(expression.index)
        value = self.bind_expression(expression.value)

        if not isinstance(target.type, (ArrayTypeSymbol, PointerTypeSymbol)):
            self.diagnostics.report(expression.target.span, f"Cannot index a non-array type '{target.type}'.")
            return BoundLiteralExpression(None, TypeUnknown)

        if not can_convert(index.type, TypeInt):
            self.diagnostics.report_cannot_convert(expression.index.span, str(index.type), "int")

        elem_type = target.type.element_type if isinstance(target.type, ArrayTypeSymbol) else target.type.base_type
        if not can_convert(value.type, elem_type):
            self.diagnostics.report_cannot_convert(expression.value.span, str(value.type), str(elem_type))

        return BoundIndexAssignmentExpression(target, index, value, expression.operator_token.text)

    def _bind_call_expression(self, expression: CallExpression) -> BoundExpression:
        symbol = None
        func_name = ""
        callee_span = expression.span

        if isinstance(expression.callee, MemberAccessExpression):
            target = self.bind_expression(expression.callee.target)
            m_name = expression.callee.member_token.text
            callee_span = expression.callee.span
            if isinstance(target.type, ModuleTypeSymbol):
                sym = target.type.get_member_symbol(m_name)
                if isinstance(sym, FunctionSymbol):
                    symbol = sym
                    func_name = f"{target.type.module_name}.{m_name}"
                else:
                    self.diagnostics.report(expression.callee.member_token.span, f"Member '{m_name}' in module '{target.type.module_name}' is not a function.")
                    return BoundLiteralExpression(None, TypeUnknown)
            else:
                self.diagnostics.report(expression.callee.target.span, f"Cannot call member '{m_name}' on non-module type '{target.type}'.")
                return BoundLiteralExpression(None, TypeUnknown)
        elif expression.callee_token is not None:
            func_name = expression.callee_token.text
            callee_span = expression.callee_token.span
            sym = self._current_scope.lookup(func_name)
            if isinstance(sym, FunctionSymbol):
                symbol = sym
            else:
                self.diagnostics.report(callee_span, f"Function '{func_name}' is not defined.")
                return BoundLiteralExpression(None, TypeUnknown)
        else:
            self.diagnostics.report(expression.span, "Invalid function call target.")
            return BoundLiteralExpression(None, TypeUnknown)

        if symbol.is_var_args:
            if len(expression.arguments) < len(symbol.parameters):
                self.diagnostics.report(
                    expression.span,
                    f"Function '{func_name}' expects at least {len(symbol.parameters)} arguments, but got {len(expression.arguments)}."
                )
        elif len(expression.arguments) != len(symbol.parameters):
            self.diagnostics.report(
                expression.span,
                f"Function '{func_name}' expects {len(symbol.parameters)} arguments, but got {len(expression.arguments)}."
            )

        bound_args: list[BoundExpression] = []
        for i, arg in enumerate(expression.arguments):
            bound_arg = self.bind_expression(arg)
            if i < len(symbol.parameters):
                param_type = symbol.parameters[i].type
                if not can_convert(bound_arg.type, param_type):
                    self.diagnostics.report_cannot_convert(arg.span, str(bound_arg.type), str(param_type))
            bound_args.append(bound_arg)

        return BoundCallExpression(symbol, bound_args)

    def _bind_literal_expression(self, expression: LiteralExpression) -> BoundLiteralExpression:
        val = expression.value
        if isinstance(val, bool):
            return BoundLiteralExpression(val, TypeBool)
        if isinstance(val, int):
            return BoundLiteralExpression(val, TypeInt)
        if isinstance(val, float):
            return BoundLiteralExpression(val, TypeDouble)
        if isinstance(val, str):
            return BoundLiteralExpression(val, TypeString)
        if val is None:
            return BoundLiteralExpression(None, TypeVoid)
        return BoundLiteralExpression(val, TypeUnknown)

    def _bind_variable_expression(self, expression: VariableExpression) -> BoundExpression:
        name = expression.identifier_token.text
        symbol = self._current_scope.lookup(name)
        if symbol is None or not (isinstance(symbol, VariableSymbol) or isinstance(symbol, ModuleSymbol)):
            self.diagnostics.report_undefined_variable(expression.identifier_token.span, name)
            return BoundLiteralExpression(None, TypeUnknown)
        return BoundVariableExpression(symbol) # type: ignore

    def _bind_assignment_expression(self, expression: AssignmentExpression) -> BoundExpression:
        name = expression.identifier_token.text
        symbol = self._current_scope.lookup(name)
        if symbol is None or not isinstance(symbol, VariableSymbol):
            self.diagnostics.report_undefined_variable(expression.identifier_token.span, name)
            return BoundLiteralExpression(None, TypeUnknown)

        if symbol.is_read_only:
            self.diagnostics.report_cannot_assign_to_constant(expression.identifier_token.span, name)

        bound_right = self.bind_expression(expression.value)
        if not can_convert(bound_right.type, symbol.type):
            self.diagnostics.report_cannot_convert(expression.value.span, str(bound_right.type), str(symbol.type))

        return BoundAssignmentExpression(symbol, bound_right, expression.operator_token.text)

    def _bind_unary_expression(self, expression: UnaryExpression) -> BoundExpression:
        operand = self.bind_expression(expression.operand)
        op_tok = expression.operator_token

        # Increment / Decrement
        if op_tok.kind in (SyntaxKind.PlusPlusToken, SyntaxKind.MinusMinusToken):
            if not isinstance(operand, BoundVariableExpression):
                self.diagnostics.report(expression.span, "Increment/decrement operand must be a variable.")
                return operand
            if not is_numeric(operand.type):
                self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
            op = BoundUnaryOperator(op_tok.text, operand.type, operand.type)
            return BoundUnaryExpression(op, operand, is_postfix=expression.is_postfix)

        # Logical Not
        if op_tok.kind == SyntaxKind.BangToken:
            if not can_convert(operand.type, TypeBool):
                self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
            op = BoundUnaryOperator("!", TypeBool, TypeBool)
            return BoundUnaryExpression(op, operand, is_postfix=False)

        # Bitwise Not
        if op_tok.kind == SyntaxKind.TildeToken:
            if operand.type != TypeInt:
                self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
            op = BoundUnaryOperator("~", TypeInt, TypeInt)
            return BoundUnaryExpression(op, operand, is_postfix=False)

        # Unary + or -
        if op_tok.kind in (SyntaxKind.PlusToken, SyntaxKind.MinusToken):
            if not is_numeric(operand.type):
                self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
            op = BoundUnaryOperator(op_tok.text, operand.type, operand.type)
            return BoundUnaryExpression(op, operand, is_postfix=False)

        # Address-of (&)
        if op_tok.kind == SyntaxKind.AmpersandToken and not expression.is_postfix:
            if not isinstance(operand, (BoundVariableExpression, BoundIndexExpression, BoundMemberAccessExpression, BoundDereferenceExpression)):
                self.diagnostics.report(expression.span, "Address-of operator '&' can only be applied to lvalues (variables, array elements, struct fields).")
                return operand
            ptr_t = PointerTypeSymbol(operand.type)
            return BoundAddressOfExpression(operand, ptr_t)

        # Dereference (* prefix or ^ postfix)
        if (op_tok.kind == SyntaxKind.StarToken and not expression.is_postfix) or (op_tok.kind == SyntaxKind.CaretToken and expression.is_postfix):
            if not isinstance(operand.type, PointerTypeSymbol):
                self.diagnostics.report(expression.span, f"Cannot dereference non-pointer expression of type '{operand.type}'.")
                return operand
            return BoundDereferenceExpression(operand, operand.type.base_type)

        self.diagnostics.report_undefined_unary_operator(op_tok.span, op_tok.text, str(operand.type))
        return operand

    def _bind_binary_expression(self, expression: BinaryExpression) -> BoundExpression:
        left = self.bind_expression(expression.left)
        right = self.bind_expression(expression.right)
        op_tok = expression.operator_token

        # String concatenation
        if op_tok.kind == SyntaxKind.PlusToken and (left.type == TypeString or right.type == TypeString):
            op = BoundBinaryOperator("+", left.type, right.type, TypeString)
            return BoundBinaryExpression(left, op, right)

        # Numeric arithmetic: +, -, *, /, %, **
        if op_tok.kind in (
            SyntaxKind.PlusToken,
            SyntaxKind.MinusToken,
            SyntaxKind.StarToken,
            SyntaxKind.SlashToken,
            SyntaxKind.PercentToken,
            SyntaxKind.DoubleStarToken,
        ):
            if is_numeric(left.type) and is_numeric(right.type):
                res_type = get_promoted_numeric_type(left.type, right.type)
                op = BoundBinaryOperator(op_tok.text, left.type, right.type, res_type)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        # Relational: <, <=, >, >=
        if op_tok.kind in (
            SyntaxKind.LessToken,
            SyntaxKind.LessOrEqualsToken,
            SyntaxKind.GreaterToken,
            SyntaxKind.GreaterOrEqualsToken,
        ):
            if is_numeric(left.type) and is_numeric(right.type):
                op = BoundBinaryOperator(op_tok.text, left.type, right.type, TypeBool)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        # Equality: ==, !=
        if op_tok.kind in (SyntaxKind.EqualsEqualsToken, SyntaxKind.BangEqualsToken):
            if can_convert(left.type, right.type) or can_convert(right.type, left.type):
                op = BoundBinaryOperator(op_tok.text, left.type, right.type, TypeBool)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        # Logical: &&, ||
        if op_tok.kind in (SyntaxKind.AmpersandAmpersandToken, SyntaxKind.PipePipeToken):
            if can_convert(left.type, TypeBool) and can_convert(right.type, TypeBool):
                op = BoundBinaryOperator(op_tok.text, TypeBool, TypeBool, TypeBool)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        # Bitwise: &, |, ^, <<, >>
        if op_tok.kind in (
            SyntaxKind.AmpersandToken,
            SyntaxKind.PipeToken,
            SyntaxKind.HatToken,
            SyntaxKind.CaretToken,
            SyntaxKind.LeftShiftToken,
            SyntaxKind.RightShiftToken,
        ):
            if left.type == TypeInt and right.type == TypeInt:
                op = BoundBinaryOperator(op_tok.text, TypeInt, TypeInt, TypeInt)
                return BoundBinaryExpression(left, op, right)
            self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
            return left

        self.diagnostics.report_undefined_binary_operator(op_tok.span, op_tok.text, str(left.type), str(right.type))
        return left

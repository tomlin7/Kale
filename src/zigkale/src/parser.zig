const std = @import("std");
const token_mod = @import("token.zig");
const Token = token_mod.Token;
const TokenKind = token_mod.TokenKind;
const ast = @import("ast.zig");

pub const Parser = struct {
    allocator: std.mem.Allocator,
    tokens: []const Token,
    pos: usize = 0,
    errors: usize = 0,

    pub fn init(allocator: std.mem.Allocator, tokens: []const Token) Parser {
        return .{
            .allocator = allocator,
            .tokens = tokens,
            .pos = 0,
            .errors = 0,
        };
    }

    fn cur(self: *const Parser) Token {
        if (self.pos >= self.tokens.len) return self.tokens[self.tokens.len - 1];
        return self.tokens[self.pos];
    }

    fn peek(self: *const Parser, offset: usize) Token {
        const idx = self.pos + offset;
        if (idx >= self.tokens.len) return self.tokens[self.tokens.len - 1];
        return self.tokens[idx];
    }

    fn advance(self: *Parser) Token {
        const tok = self.cur();
        if (self.pos < self.tokens.len - 1) {
            self.pos += 1;
        }
        return tok;
    }

    fn check(self: *const Parser, kind: TokenKind) bool {
        return self.cur().kind == kind;
    }

    fn match(self: *Parser, kind: TokenKind) bool {
        if (self.check(kind)) {
            _ = self.advance();
            return true;
        }
        return false;
    }

    fn expect(self: *Parser, kind: TokenKind) !Token {
        if (self.check(kind)) {
            return self.advance();
        }
        self.errors += 1;
        return error.UnexpectedToken;
    }

    // -------------------------------------------------------------
    // Type Reference Parsing
    // -------------------------------------------------------------
    pub fn parseTypeRef(self: *Parser) !ast.TypeRef {
        var type_name: []const u8 = "";

        if (self.cur().isTypeKeyword()) {
            type_name = self.advance().text;
        } else if (self.check(.identifier)) {
            const first = self.advance().text;
            if (self.match(.dot) and self.check(.identifier)) {
                const second = self.advance().text;
                type_name = try std.fmt.allocPrint(self.allocator, "{s}.{s}", .{ first, second });
            } else {
                type_name = first;
            }
        } else if (self.match(.kw_fn)) {
            // Function pointer type: fn(T1, T2): RetType
            _ = try self.expect(.lparen);
            var params: std.ArrayList(ast.TypeRef) = .{};
            while (!self.check(.rparen) and !self.check(.eof)) {
                try params.append(self.allocator, try self.parseTypeRef());
                if (!self.match(.comma)) break;
            }
            _ = try self.expect(.rparen);
            _ = try self.expect(.colon);
            const ret_t = try self.allocator.create(ast.TypeRef);
            ret_t.* = try self.parseTypeRef();

            return ast.TypeRef{
                .name = "fn",
                .func_params = params.toOwnedSlice(self.allocator) catch null,
                .func_ret = ret_t,
            };
        } else {
            return error.ExpectedType;
        }

        var generic_arg: ?[]const u8 = null;
        if (self.match(.lt)) {
            if (self.check(.identifier)) {
                generic_arg = self.advance().text;
            }
            var depth: usize = 1;
            while (depth > 0 and !self.check(.eof)) {
                if (self.match(.lt)) {
                    depth += 1;
                } else if (self.match(.gt)) {
                    depth -= 1;
                } else {
                    _ = self.advance();
                }
            }
        }

        var ptr_depth: usize = 0;
        while (self.match(.star)) {
            ptr_depth += 1;
        }

        var is_array = false;
        var array_size: ?usize = null;
        if (self.match(.lbracket)) {
            is_array = true;
            if (self.check(.number_int)) {
                const sz_tok = self.advance();
                array_size = @intCast(sz_tok.int_val);
            }
            _ = try self.expect(.rbracket);
        }

        return ast.TypeRef{
            .name = type_name,
            .ptr_depth = ptr_depth,
            .is_array = is_array,
            .array_size = array_size,
            .generic_arg = generic_arg,
        };
    }

    fn isTypeStart(self: *const Parser) bool {
        if (self.cur().isTypeKeyword()) return true;
        if (self.check(.kw_fn)) return true;
        if (self.check(.identifier)) {
            // Could be a struct type or custom type name
            return true;
        }
        return false;
    }

    // -------------------------------------------------------------
    // Program & Statements
    // -------------------------------------------------------------
    pub fn parseProgram(self: *Parser) !ast.Program {
        var statements: std.ArrayList(ast.Stmt) = .{};
        while (!self.check(.eof)) {
            if (self.parseStatement()) |stmt| {
                try statements.append(self.allocator, stmt);
            } else |err| {
                self.errors += 1;
                self.synchronize();
                if (err == error.OutOfMemory) return err;
            }
        }
        return ast.Program{
            .statements = try statements.toOwnedSlice(self.allocator),
        };
    }

    fn synchronize(self: *Parser) void {
        _ = self.advance();
        while (!self.check(.eof)) {
            if (self.tokens[self.pos - 1].kind == .semicolon or self.tokens[self.pos - 1].kind == .rbrace) {
                return;
            }
            switch (self.cur().kind) {
                .kw_fn, .kw_let, .kw_var, .kw_const, .kw_struct, .kw_enum, .kw_extern, .kw_import, .kw_if, .kw_while, .kw_for, .kw_return, .kw_print => return,
                else => _ = self.advance(),
            }
        }
    }

    pub fn parseStatement(self: *Parser) !ast.Stmt {
        if (self.check(.kw_import)) {
            return self.parseImportStatement();
        }
        if (self.check(.kw_from)) {
            return self.parseFromImportStatement();
        }
        if (self.check(.kw_struct)) {
            return self.parseStructDeclaration();
        }
        if (self.check(.kw_enum)) {
            return self.parseEnumDeclaration();
        }
        if (self.check(.kw_extern)) {
            return self.parseExternDeclaration();
        }
        if (self.check(.lbrace)) {
            return self.parseBlockStatement();
        }
        if (self.check(.kw_if)) {
            return self.parseIfStatement();
        }
        if (self.check(.kw_while)) {
            return self.parseWhileStatement();
        }
        if (self.check(.kw_for)) {
            return self.parseForStatement();
        }
        if (self.check(.kw_switch)) {
            return self.parseSwitchStatement();
        }
        if (self.check(.kw_return)) {
            return self.parseReturnStatement();
        }
        if (self.check(.kw_break)) {
            _ = self.advance();
            _ = try self.expect(.semicolon);
            return ast.Stmt{ .kind = .break_stmt, .data = .{ .break_stmt = {} } };
        }
        if (self.check(.kw_continue)) {
            _ = self.advance();
            _ = try self.expect(.semicolon);
            return ast.Stmt{ .kind = .continue_stmt, .data = .{ .continue_stmt = {} } };
        }
        if (self.check(.kw_print)) {
            return self.parsePrintStatement();
        }
        if (self.check(.kw_free)) {
            return self.parseFreeStatement();
        }

        // Check for function declaration start
        if (self.isFunctionDeclarationStart()) {
            return self.parseFunctionDeclaration();
        }

        // Check for variable declaration start
        if (self.isVarDeclStart()) {
            return self.parseVarDeclStatement();
        }

        // Expression statement
        const expr = try self.parseExpression();
        _ = self.match(.semicolon);
        const expr_ptr = try self.allocator.create(ast.Expr);
        expr_ptr.* = expr;
        return ast.Stmt{
            .kind = .expr_stmt,
            .data = .{ .expr_stmt = expr_ptr },
        };
    }

    fn isFunctionDeclarationStart(self: *const Parser) bool {
        var idx: usize = 0;
        if (self.peek(idx).kind == .kw_fn) {
            if (self.peek(idx + 1).kind == .lparen) {
                // fn(...) is a function pointer type, not a function declaration
                return false;
            }
            return true;
        }

        // C-style function: RetType [Struct.]name(...) {
        const k0 = self.peek(idx).kind;
        if (!self.peek(idx).isTypeKeyword() and k0 != .identifier) return false;
        idx += 1;

        // Skip any qualifiers e.g. foo.bar
        if (self.peek(idx).kind == .dot and self.peek(idx + 1).kind == .identifier) {
            idx += 2;
        }
        if (self.peek(idx).kind == .lt) {
            var depth: usize = 1;
            idx += 1;
            while (depth > 0 and self.peek(idx).kind != .eof) {
                if (self.peek(idx).kind == .lt) depth += 1;
                if (self.peek(idx).kind == .gt) depth -= 1;
                idx += 1;
            }
        }

        // Skip pointer stars and array brackets
        while (self.peek(idx).kind == .star) {
            idx += 1;
        }
        while (self.peek(idx).kind == .lbracket) {
            idx += 1;
            if (self.peek(idx).kind == .number_int) idx += 1;
            if (self.peek(idx).kind == .rbracket) idx += 1;
        }
        while (self.peek(idx).kind == .star) {
            idx += 1;
        }

        // Next must be function name or operator
        if (self.peek(idx).kind != .identifier and self.peek(idx).kind != .kw_operator) return false;
        idx += 1;

        // Method qualifier Struct.method?
        if (self.peek(idx).kind == .dot) {
            idx += 1;
            if (self.peek(idx).kind == .kw_operator) {
                idx += 1;
                if (self.peek(idx).kind == .lbracket and self.peek(idx + 1).kind == .rbracket) {
                    idx += 2;
                }
            } else if (self.peek(idx).kind == .identifier) {
                idx += 1;
            }
        }

        // Must be '('
        return self.peek(idx).kind == .lparen;
    }

    fn isVarDeclStart(self: *const Parser) bool {
        const k0 = self.cur().kind;
        if (k0 == .kw_let or k0 == .kw_var or k0 == .kw_const) return true;
        if (k0 == .kw_fn and self.peek(1).kind == .lparen) return true;

        if (self.cur().isTypeKeyword()) {
            // Type name followed by identifier or * or [ ]
            var idx: usize = 1;
            while (self.peek(idx).kind == .star) idx += 1;
            while (self.peek(idx).kind == .lbracket) {
                idx += 1;
                if (self.peek(idx).kind == .number_int) idx += 1;
                if (self.peek(idx).kind == .rbracket) idx += 1;
            }
            while (self.peek(idx).kind == .star) idx += 1;
            return self.peek(idx).kind == .identifier;
        }

        // Custom struct/type: StructName [*] var_name [= | ;]
        if (k0 == .identifier) {
            var idx: usize = 1;
            if (self.peek(idx).kind == .dot and self.peek(idx + 1).kind == .identifier) {
                idx += 2;
            }
            if (self.peek(idx).kind == .lt) {
                var depth: usize = 1;
                idx += 1;
                while (depth > 0 and self.peek(idx).kind != .eof) {
                    if (self.peek(idx).kind == .lt) depth += 1;
                    if (self.peek(idx).kind == .gt) depth -= 1;
                    idx += 1;
                }
            }
            while (self.peek(idx).kind == .star) idx += 1;
            while (self.peek(idx).kind == .lbracket) {
                idx += 1;
                if (self.peek(idx).kind == .number_int) idx += 1;
                if (self.peek(idx).kind == .rbracket) idx += 1;
            }
            while (self.peek(idx).kind == .star) idx += 1;
            if (self.peek(idx).kind == .identifier) {
                const next_k = self.peek(idx + 1).kind;
                if (next_k == .eq or next_k == .semicolon or next_k == .comma or next_k == .lbracket) {
                    return true;
                }
            }
        }

        return false;
    }

    fn parseImportStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_import);
        const path_tok = try self.expect(.string_lit);
        var alias: ?[]const u8 = null;
        if (self.match(.kw_as)) {
            const alias_tok = try self.expect(.identifier);
            alias = alias_tok.text;
        }
        _ = try self.expect(.semicolon);

        return ast.Stmt{
            .kind = .import_stmt,
            .data = .{
                .import_stmt = .{
                    .path = path_tok.text,
                    .alias = alias,
                },
            },
        };
    }

    fn parseFromImportStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_from);
        const path_tok = try self.expect(.string_lit);
        _ = try self.expect(.kw_import);

        var items: std.ArrayList(ast.ImportItem) = .{};
        while (true) {
            const sym_tok = try self.expect(.identifier);
            var alias: ?[]const u8 = null;
            if (self.match(.kw_as)) {
                const a_tok = try self.expect(.identifier);
                alias = a_tok.text;
            }
            try items.append(self.allocator, .{ .name = sym_tok.text, .alias = alias });
            if (!self.match(.comma)) break;
        }
        _ = try self.expect(.semicolon);

        return ast.Stmt{
            .kind = .from_import_stmt,
            .data = .{
                .from_import_stmt = .{
                    .path = path_tok.text,
                    .symbols = try items.toOwnedSlice(self.allocator),
                },
            },
        };
    }

    fn parseStructDeclaration(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_struct);
        const name_tok = try self.expect(.identifier);
        var type_param: ?[]const u8 = null;
        if (self.match(.lt)) {
            if (self.check(.identifier)) {
                type_param = self.advance().text;
            }
            var depth: usize = 1;
            while (depth > 0 and !self.check(.eof)) {
                if (self.match(.lt)) {
                    depth += 1;
                } else if (self.match(.gt)) {
                    depth -= 1;
                } else {
                    _ = self.advance();
                }
            }
        }
        _ = try self.expect(.lbrace);

        var fields: std.ArrayList(ast.Field) = .{};
        while (!self.check(.rbrace) and !self.check(.eof)) {
            const ftype = try self.parseTypeRef();
            const fname = try self.expect(.identifier);
            _ = self.match(.semicolon);
            try fields.append(self.allocator, .{ .name = fname.text, .type_ref = ftype });
        }
        _ = try self.expect(.rbrace);
        _ = self.match(.semicolon);

        return ast.Stmt{
            .kind = .struct_decl,
            .data = .{
                .struct_decl = .{
                    .name = name_tok.text,
                    .type_param = type_param,
                    .fields = try fields.toOwnedSlice(self.allocator),
                },
            },
        };
    }

    fn parseEnumDeclaration(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_enum);
        const name_tok = try self.expect(.identifier);
        _ = try self.expect(.lbrace);

        var members: std.ArrayList(ast.EnumMember) = .{};
        while (!self.check(.rbrace) and !self.check(.eof)) {
            const mname = try self.expect(.identifier);
            var mval: ?i64 = null;
            if (self.match(.eq)) {
                const val_tok = try self.expect(.number_int);
                mval = val_tok.int_val;
            }
            try members.append(self.allocator, .{ .name = mname.text, .value = mval });
            if (!self.match(.comma)) break;
        }
        _ = try self.expect(.rbrace);
        _ = self.match(.semicolon);

        return ast.Stmt{
            .kind = .enum_decl,
            .data = .{
                .enum_decl = .{
                    .name = name_tok.text,
                    .members = try members.toOwnedSlice(self.allocator),
                },
            },
        };
    }

    fn parseExternDeclaration(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_extern);
        var ret_type = ast.TypeRef{ .name = "void" };
        if (self.isTypeStart()) {
            ret_type = try self.parseTypeRef();
        }

        const name_tok = try self.expect(.identifier);
        _ = try self.expect(.lparen);

        var params: std.ArrayList(ast.Param) = .{};
        var is_varargs = false;

        while (!self.check(.rparen) and !self.check(.eof)) {
            if (self.match(.dot) and self.match(.dot) and self.match(.dot)) {
                is_varargs = true;
                break;
            }
            const ptype = try self.parseTypeRef();
            var pname: []const u8 = "";
            if (self.check(.identifier)) {
                pname = self.advance().text;
            }
            try params.append(self.allocator, .{ .name = pname, .type_ref = ptype });
            if (!self.match(.comma)) break;
        }
        _ = try self.expect(.rparen);
        _ = try self.expect(.semicolon);

        return ast.Stmt{
            .kind = .fn_decl,
            .data = .{
                .fn_decl = .{
                    .name = name_tok.text,
                    .params = try params.toOwnedSlice(self.allocator),
                    .ret_type = ret_type,
                    .body = null,
                    .is_extern = true,
                    .is_varargs = is_varargs,
                    .struct_name = null,
                },
            },
        };
    }

    fn parseFunctionDeclaration(self: *Parser) !ast.Stmt {
        var ret_type = ast.TypeRef{ .name = "int" };
        var has_explicit_ret = false;

        if (self.match(.kw_fn)) {
            // fn [Type] name(...)
            // If current token is followed by dot and paren (e.g. fn Struct.method()), no explicit return type
            if (self.peek(1).kind == .dot and self.peek(3).kind == .lparen) {
                has_explicit_ret = false;
            } else if (self.peek(1).kind == .lparen) {
                has_explicit_ret = false;
            } else if (self.isTypeStart()) {
                ret_type = try self.parseTypeRef();
                has_explicit_ret = true;
            }
        } else {
            // C style: Type name(...)
            ret_type = try self.parseTypeRef();
            has_explicit_ret = true;
        }

        var fn_name = (try self.expect(.identifier)).text;
        var struct_name: ?[]const u8 = null;

        if (self.match(.dot)) {
            struct_name = fn_name;
            if (self.match(.kw_operator)) {
                if (self.match(.lbracket) and self.match(.rbracket)) {
                    fn_name = "operator_index";
                } else if (self.check(.identifier)) {
                    fn_name = self.advance().text;
                } else {
                    fn_name = "operator";
                }
            } else {
                fn_name = (try self.expect(.identifier)).text;
            }
        }

        _ = try self.expect(.lparen);
        var params: std.ArrayList(ast.Param) = .{};
        var is_varargs = false;

        while (!self.check(.rparen) and !self.check(.eof)) {
            if (self.match(.dot) and self.match(.dot) and self.match(.dot)) {
                is_varargs = true;
                break;
            }
            const pt = try self.parseTypeRef();
            const pn = (try self.expect(.identifier)).text;
            try params.append(self.allocator, .{ .name = pn, .type_ref = pt });
            if (!self.match(.comma)) break;
        }
        _ = try self.expect(.rparen);

        const body_stmt = try self.allocator.create(ast.Stmt);
        body_stmt.* = try self.parseBlockStatement();

        return ast.Stmt{
            .kind = .fn_decl,
            .data = .{
                .fn_decl = .{
                    .name = fn_name,
                    .params = try params.toOwnedSlice(self.allocator),
                    .ret_type = ret_type,
                    .body = body_stmt,
                    .is_extern = false,
                    .is_varargs = is_varargs,
                    .struct_name = struct_name,
                },
            },
        };
    }

    fn parseVarDeclStatement(self: *Parser) !ast.Stmt {
        var is_const = false;
        var type_ref: ?ast.TypeRef = null;

        if (self.match(.kw_let)) {
            is_const = true;
        } else if (self.match(.kw_const)) {
            is_const = true;
        } else if (self.match(.kw_var)) {
            is_const = false;
        } else {
            // Type first: e.g. int x = 10; or Point* p = alloc(Point);
            type_ref = try self.parseTypeRef();
        }

        // If 'const' or 'let' or 'var' was matched, an explicit type may still follow
        // e.g. `const int MULT = 5;` or `var float f = 1.0;` or `const Point p = ...;`
        if (type_ref == null) {
            if (self.cur().isTypeKeyword() or (self.cur().kind == .kw_fn and self.peek(1).kind == .lparen)) {
                type_ref = try self.parseTypeRef();
            } else if (self.cur().kind == .identifier) {
                var idx: usize = 1;
                if (self.peek(idx).kind == .dot and self.peek(idx + 1).kind == .identifier) {
                    idx += 2;
                }
                while (self.peek(idx).kind == .star) idx += 1;
                while (self.peek(idx).kind == .lbracket) {
                    idx += 1;
                    if (self.peek(idx).kind == .number_int) idx += 1;
                    if (self.peek(idx).kind == .rbracket) idx += 1;
                }
                while (self.peek(idx).kind == .star) idx += 1;
                if (self.peek(idx).kind == .identifier) {
                    type_ref = try self.parseTypeRef();
                }
            }
        }

        const name_tok = try self.expect(.identifier);

        if (type_ref == null and self.match(.colon)) {
            type_ref = try self.parseTypeRef();
        }

        var init_expr: ?*ast.Expr = null;
        if (self.match(.eq)) {
            const e = try self.allocator.create(ast.Expr);
            e.* = try self.parseExpression();
            init_expr = e;
        }

        _ = self.match(.semicolon);

        return ast.Stmt{
            .kind = .var_decl,
            .data = .{
                .var_decl = .{
                    .name = name_tok.text,
                    .type_ref = type_ref,
                    .init = init_expr,
                    .is_const = is_const,
                },
            },
        };
    }

    fn parseBlockStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.lbrace);
        var stmts: std.ArrayList(ast.Stmt) = .{};
        while (!self.check(.rbrace) and !self.check(.eof)) {
            try stmts.append(self.allocator, try self.parseStatement());
        }
        _ = try self.expect(.rbrace);

        return ast.Stmt{
            .kind = .block,
            .data = .{ .block = try stmts.toOwnedSlice(self.allocator) },
        };
    }

    fn parseIfStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_if);
        _ = try self.expect(.lparen);
        const cond = try self.allocator.create(ast.Expr);
        cond.* = try self.parseExpression();
        _ = try self.expect(.rparen);

        const then_stmt = try self.allocator.create(ast.Stmt);
        then_stmt.* = try self.parseStatement();

        var else_stmt: ?*ast.Stmt = null;
        if (self.match(.kw_else)) {
            const e = try self.allocator.create(ast.Stmt);
            e.* = try self.parseStatement();
            else_stmt = e;
        }

        return ast.Stmt{
            .kind = .if_stmt,
            .data = .{
                .if_stmt = .{
                    .cond = cond,
                    .then_stmt = then_stmt,
                    .else_stmt = else_stmt,
                },
            },
        };
    }

    fn parseWhileStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_while);
        _ = try self.expect(.lparen);
        const cond = try self.allocator.create(ast.Expr);
        cond.* = try self.parseExpression();
        _ = try self.expect(.rparen);

        const body = try self.allocator.create(ast.Stmt);
        body.* = try self.parseStatement();

        return ast.Stmt{
            .kind = .while_stmt,
            .data = .{
                .while_stmt = .{
                    .cond = cond,
                    .body = body,
                },
            },
        };
    }

    fn parseForStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_for);
        _ = try self.expect(.lparen);

        var init_stmt: ?*ast.Stmt = null;
        if (!self.match(.semicolon)) {
            const s = try self.allocator.create(ast.Stmt);
            if (self.isVarDeclStart()) {
                s.* = try self.parseVarDeclStatement();
            } else {
                const expr = try self.parseExpression();
                _ = try self.expect(.semicolon);
                const expr_ptr = try self.allocator.create(ast.Expr);
                expr_ptr.* = expr;
                s.* = ast.Stmt{ .kind = .expr_stmt, .data = .{ .expr_stmt = expr_ptr } };
            }
            init_stmt = s;
        }

        var cond_expr: ?*ast.Expr = null;
        if (!self.check(.semicolon)) {
            const c = try self.allocator.create(ast.Expr);
            c.* = try self.parseExpression();
            cond_expr = c;
        }
        _ = try self.expect(.semicolon);

        var inc_expr: ?*ast.Expr = null;
        if (!self.check(.rparen)) {
            const i = try self.allocator.create(ast.Expr);
            i.* = try self.parseExpression();
            inc_expr = i;
        }
        _ = try self.expect(.rparen);

        const body = try self.allocator.create(ast.Stmt);
        body.* = try self.parseStatement();

        return ast.Stmt{
            .kind = .for_stmt,
            .data = .{
                .for_stmt = .{
                    .init = init_stmt,
                    .cond = cond_expr,
                    .inc = inc_expr,
                    .body = body,
                },
            },
        };
    }

    fn parseSwitchStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_switch);
        _ = try self.expect(.lparen);
        const expr = try self.allocator.create(ast.Expr);
        expr.* = try self.parseExpression();
        _ = try self.expect(.rparen);

        _ = try self.expect(.lbrace);
        var cases: std.ArrayList(ast.SwitchCase) = .{};
        var default_body: ?[]ast.Stmt = null;

        while (!self.check(.rbrace) and !self.check(.eof)) {
            if (self.match(.kw_case)) {
                var vals: std.ArrayList(ast.Expr) = .{};
                while (true) {
                    try vals.append(self.allocator, try self.parseExpression());
                    if (!self.match(.comma)) break;
                }
                _ = try self.expect(.colon);
                var body: std.ArrayList(ast.Stmt) = .{};
                while (!self.check(.kw_case) and !self.check(.kw_default) and !self.check(.rbrace) and !self.check(.eof)) {
                    try body.append(self.allocator, try self.parseStatement());
                }
                try cases.append(self.allocator, .{ .values = try vals.toOwnedSlice(self.allocator), .body = try body.toOwnedSlice(self.allocator) });
            } else if (self.match(.kw_default)) {
                _ = try self.expect(.colon);
                var body: std.ArrayList(ast.Stmt) = .{};
                while (!self.check(.kw_case) and !self.check(.rbrace) and !self.check(.eof)) {
                    try body.append(self.allocator, try self.parseStatement());
                }
                default_body = try body.toOwnedSlice(self.allocator);
            } else {
                return error.ExpectedCaseOrDefault;
            }
        }
        _ = try self.expect(.rbrace);

        return ast.Stmt{
            .kind = .switch_stmt,
            .data = .{
                .switch_stmt = .{
                    .expr = expr,
                    .cases = try cases.toOwnedSlice(self.allocator),
                    .default_body = default_body,
                },
            },
        };
    }

    fn parseReturnStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_return);
        var expr: ?*ast.Expr = null;
        if (!self.check(.semicolon)) {
            const e = try self.allocator.create(ast.Expr);
            e.* = try self.parseExpression();
            expr = e;
        }
        _ = try self.expect(.semicolon);

        return ast.Stmt{
            .kind = .return_stmt,
            .data = .{ .return_stmt = expr },
        };
    }

    fn parsePrintStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_print);
        _ = try self.expect(.lparen);
        var args: std.ArrayList(ast.Expr) = .{};
        while (!self.check(.rparen) and !self.check(.eof)) {
            try args.append(self.allocator, try self.parseExpression());
            if (!self.match(.comma)) break;
        }
        _ = try self.expect(.rparen);
        _ = self.match(.semicolon);

        return ast.Stmt{
            .kind = .print_stmt,
            .data = .{ .print_stmt = try args.toOwnedSlice(self.allocator) },
        };
    }

    fn parseFreeStatement(self: *Parser) !ast.Stmt {
        _ = try self.expect(.kw_free);
        var expr_ptr: *ast.Expr = undefined;
        if (self.match(.lparen)) {
            const e = try self.allocator.create(ast.Expr);
            e.* = try self.parseExpression();
            _ = try self.expect(.rparen);
            expr_ptr = e;
        } else {
            const e = try self.allocator.create(ast.Expr);
            e.* = try self.parseExpression();
            expr_ptr = e;
        }
        _ = self.match(.semicolon);

        return ast.Stmt{
            .kind = .free_stmt,
            .data = .{ .free_stmt = expr_ptr },
        };
    }

    // -------------------------------------------------------------
    // Expressions
    // -------------------------------------------------------------
    pub fn parseExpression(self: *Parser) anyerror!ast.Expr {
        return self.parseAssignment();
    }

    fn parseAssignment(self: *Parser) anyerror!ast.Expr {
        const left = try self.parseLogicalOr();

        if (self.cur().isAssignmentOp()) {
            const op = self.advance().kind;
            const right = try self.parseAssignment();

            const left_ptr = try self.allocator.create(ast.Expr);
            left_ptr.* = left;
            const right_ptr = try self.allocator.create(ast.Expr);
            right_ptr.* = right;

            return ast.Expr{
                .kind = .assign,
                .data = .{
                    .assign = .{
                        .target = left_ptr,
                        .op = op,
                        .value = right_ptr,
                    },
                },
            };
        }

        return left;
    }

    fn parseLogicalOr(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseLogicalAnd();
        while (self.match(.pipe_pipe)) {
            const right = try self.parseLogicalAnd();
            expr = try self.makeBinary(.pipe_pipe, expr, right);
        }
        return expr;
    }

    fn parseLogicalAnd(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseBitwiseOr();
        while (self.match(.amp_amp)) {
            const right = try self.parseBitwiseOr();
            expr = try self.makeBinary(.amp_amp, expr, right);
        }
        return expr;
    }

    fn parseBitwiseOr(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseBitwiseXor();
        while (self.match(.pipe)) {
            const right = try self.parseBitwiseXor();
            expr = try self.makeBinary(.pipe, expr, right);
        }
        return expr;
    }

    fn parseBitwiseXor(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseBitwiseAnd();
        // Only Hat (^) when not followed by identifier/postfix
        while (self.match(.caret)) {
            const right = try self.parseBitwiseAnd();
            expr = try self.makeBinary(.caret, expr, right);
        }
        return expr;
    }

    fn parseBitwiseAnd(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseEquality();
        while (self.match(.amp)) {
            const right = try self.parseEquality();
            expr = try self.makeBinary(.amp, expr, right);
        }
        return expr;
    }

    fn parseEquality(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseRelational();
        while (self.check(.eq_eq) or self.check(.bang_eq)) {
            const op = self.advance().kind;
            const right = try self.parseRelational();
            expr = try self.makeBinary(op, expr, right);
        }
        return expr;
    }

    fn parseRelational(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseShift();
        while (self.check(.lt) or self.check(.lt_eq) or self.check(.gt) or self.check(.gt_eq)) {
            const op = self.advance().kind;
            const right = try self.parseShift();
            expr = try self.makeBinary(op, expr, right);
        }
        return expr;
    }

    fn parseShift(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseAdditive();
        while (self.check(.shl) or self.check(.shr)) {
            const op = self.advance().kind;
            const right = try self.parseAdditive();
            expr = try self.makeBinary(op, expr, right);
        }
        return expr;
    }

    fn parseAdditive(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parseMultiplicative();
        while (self.check(.plus) or self.check(.minus)) {
            const op = self.advance().kind;
            const right = try self.parseMultiplicative();
            expr = try self.makeBinary(op, expr, right);
        }
        return expr;
    }

    fn parseMultiplicative(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parsePower();
        while (self.check(.star) or self.check(.slash) or self.check(.percent)) {
            const op = self.advance().kind;
            const right = try self.parsePower();
            expr = try self.makeBinary(op, expr, right);
        }
        return expr;
    }

    fn parsePower(self: *Parser) anyerror!ast.Expr {
        const left = try self.parsePrefix();
        if (self.match(.star_star)) {
            const right = try self.parsePower(); // Right-associative
            return try self.makeBinary(.star_star, left, right);
        }
        return left;
    }

    fn parsePrefix(self: *Parser) anyerror!ast.Expr {
        // C-style cast: (Type)expr
        if (self.isCastStart()) {
            _ = try self.expect(.lparen);
            const target_type = try self.parseTypeRef();
            _ = try self.expect(.rparen);

            const operand = try self.parsePrefix();
            const op_ptr = try self.allocator.create(ast.Expr);
            op_ptr.* = operand;

            return ast.Expr{
                .kind = .cast,
                .data = .{
                    .cast = .{
                        .target_type = target_type,
                        .expr = op_ptr,
                    },
                },
            };
        }

        // Unary operators
        if (self.check(.minus) or self.check(.bang) or self.check(.tilde) or
            self.check(.amp) or self.check(.star) or
            self.check(.plus_plus) or self.check(.minus_minus))
        {
            const op = self.advance().kind;
            const operand = try self.parsePrefix();
            const op_ptr = try self.allocator.create(ast.Expr);
            op_ptr.* = operand;

            return ast.Expr{
                .kind = .unary,
                .data = .{
                    .unary = .{
                        .op = op,
                        .operand = op_ptr,
                        .is_postfix = false,
                    },
                },
            };
        }

        // alloc(Type) or alloc Type or alloc(Type, count)
        if (self.match(.kw_alloc)) {
            var has_paren = false;
            if (self.match(.lparen)) {
                has_paren = true;
            }
            const type_ref = try self.parseTypeRef();
            var count: ?*ast.Expr = null;
            if (has_paren and self.match(.comma)) {
                const c_expr = try self.allocator.create(ast.Expr);
                c_expr.* = try self.parseExpression();
                count = c_expr;
            }
            if (has_paren) {
                _ = try self.expect(.rparen);
            }

            return ast.Expr{
                .kind = .alloc,
                .data = .{
                    .alloc = .{
                        .type_ref = type_ref,
                        .count = count,
                    },
                },
            };
        }

        return self.parsePostfix();
    }

    fn isCastStart(self: *const Parser) bool {
        if (self.cur().kind != .lparen) return false;
        var idx: usize = 1;

        // Check if inside parentheses is a TypeRef:
        // Case 1: type keyword e.g. (int), (char*), (string), (void*)
        if (self.peek(idx).isTypeKeyword()) {
            idx += 1;
            while (self.peek(idx).kind == .star) idx += 1;
            return self.peek(idx).kind == .rparen;
        }

        // Case 2: Identifier followed by '*' and ')' e.g. (Token*), (ast.ASTNode*)
        if (self.peek(idx).kind == .identifier) {
            idx += 1;
            if (self.peek(idx).kind == .dot and self.peek(idx + 1).kind == .identifier) {
                idx += 2;
            }
            var has_star = false;
            while (self.peek(idx).kind == .star) {
                idx += 1;
                has_star = true;
            }
            if (has_star and self.peek(idx).kind == .rparen) {
                return true;
            }
        }

        // Case 3: Function pointer type e.g. (fn(int): void)
        if (self.peek(idx).kind == .kw_fn and self.peek(idx + 1).kind == .lparen) {
            idx += 2;
            var depth: usize = 1;
            while (depth > 0 and self.peek(idx).kind != .eof) {
                if (self.peek(idx).kind == .lparen) depth += 1;
                if (self.peek(idx).kind == .rparen) depth -= 1;
                idx += 1;
            }
            if (self.peek(idx).kind == .colon) {
                idx += 1;
                // Skip return type
                if (self.peek(idx).isTypeKeyword() or self.peek(idx).kind == .identifier) {
                    idx += 1;
                    while (self.peek(idx).kind == .star) idx += 1;
                }
            }
            return self.peek(idx).kind == .rparen;
        }

        return false;
    }

    fn parsePostfix(self: *Parser) anyerror!ast.Expr {
        var expr = try self.parsePrimary();

        while (true) {
            if (self.match(.lparen)) {
                // Call
                var args: std.ArrayList(ast.Expr) = .{};
                while (!self.check(.rparen) and !self.check(.eof)) {
                    try args.append(self.allocator, try self.parseExpression());
                    if (!self.match(.comma)) break;
                }
                _ = try self.expect(.rparen);

                const callee = try self.allocator.create(ast.Expr);
                callee.* = expr;
                expr = ast.Expr{
                    .kind = .call,
                    .data = .{
                        .call = .{
                            .callee = callee,
                            .args = try args.toOwnedSlice(self.allocator),
                        },
                    },
                };
            } else if (self.match(.lbracket)) {
                // Index
                const idx = try self.parseExpression();
                _ = try self.expect(.rbracket);

                const target = try self.allocator.create(ast.Expr);
                target.* = expr;
                const index_ptr = try self.allocator.create(ast.Expr);
                index_ptr.* = idx;

                expr = ast.Expr{
                    .kind = .index,
                    .data = .{
                        .index = .{
                            .target = target,
                            .index = index_ptr,
                        },
                    },
                };
            } else if (self.match(.dot)) {
                // Dot member
                const mname = (try self.expect(.identifier)).text;
                const target = try self.allocator.create(ast.Expr);
                target.* = expr;

                expr = ast.Expr{
                    .kind = .member,
                    .data = .{
                        .member = .{
                            .target = target,
                            .member = mname,
                            .is_arrow = false,
                        },
                    },
                };
            } else if (self.match(.arrow)) {
                // Arrow member ->
                const mname = (try self.expect(.identifier)).text;
                const target = try self.allocator.create(ast.Expr);
                target.* = expr;

                expr = ast.Expr{
                    .kind = .member,
                    .data = .{
                        .member = .{
                            .target = target,
                            .member = mname,
                            .is_arrow = true,
                        },
                    },
                };
            } else if (self.cur().kind == .caret) {
                // If followed by an expression-starting token, break to let binary XOR handle it!
                const next_k = self.peek(1).kind;
                const can_start_expr = switch (next_k) {
                    .number_int, .number_float, .string_lit, .char_lit, .identifier,
                    .kw_true, .kw_false, .kw_null, .lparen, .lbracket, .kw_alloc,
                    .minus, .bang, .tilde, .amp, .star, .plus_plus, .minus_minus => true,
                    else => false,
                };
                if (can_start_expr) {
                    break;
                }
                _ = self.advance();
                // Postfix dereference ^
                const target = try self.allocator.create(ast.Expr);
                target.* = expr;

                expr = ast.Expr{
                    .kind = .unary,
                    .data = .{
                        .unary = .{
                            .op = .caret,
                            .operand = target,
                            .is_postfix = true,
                        },
                    },
                };
            } else if (self.match(.plus_plus)) {
                const target = try self.allocator.create(ast.Expr);
                target.* = expr;

                expr = ast.Expr{
                    .kind = .unary,
                    .data = .{
                        .unary = .{
                            .op = .plus_plus,
                            .operand = target,
                            .is_postfix = true,
                        },
                    },
                };
            } else if (self.match(.minus_minus)) {
                const target = try self.allocator.create(ast.Expr);
                target.* = expr;

                expr = ast.Expr{
                    .kind = .unary,
                    .data = .{
                        .unary = .{
                            .op = .minus_minus,
                            .operand = target,
                            .is_postfix = true,
                        },
                    },
                };
            } else if (self.match(.kw_as)) {
                // as Type cast
                const target_type = try self.parseTypeRef();
                const target = try self.allocator.create(ast.Expr);
                target.* = expr;

                expr = ast.Expr{
                    .kind = .cast,
                    .data = .{
                        .cast = .{
                            .target_type = target_type,
                            .expr = target,
                        },
                    },
                };
            } else {
                break;
            }
        }

        return expr;
    }

    fn parsePrimary(self: *Parser) anyerror!ast.Expr {
        if (self.check(.number_int)) {
            const tok = self.advance();
            return ast.Expr{
                .kind = .literal,
                .data = .{ .literal = .{ .int_val = tok.int_val } },
            };
        }
        if (self.check(.number_float)) {
            const tok = self.advance();
            return ast.Expr{
                .kind = .literal,
                .data = .{ .literal = .{ .float_val = tok.float_val } },
            };
        }
        if (self.check(.string_lit)) {
            const tok = self.advance();
            return ast.Expr{
                .kind = .literal,
                .data = .{ .literal = .{ .str_val = tok.text } },
            };
        }
        if (self.check(.char_lit)) {
            const tok = self.advance();
            return ast.Expr{
                .kind = .literal,
                .data = .{ .literal = .{ .char_val = @intCast(tok.int_val) } },
            };
        }
        if (self.match(.kw_true)) {
            return ast.Expr{
                .kind = .literal,
                .data = .{ .literal = .{ .bool_val = true } },
            };
        }
        if (self.match(.kw_false)) {
            return ast.Expr{
                .kind = .literal,
                .data = .{ .literal = .{ .bool_val = false } },
            };
        }
        if (self.match(.kw_null)) {
            return ast.Expr{
                .kind = .literal,
                .data = .{ .literal = .{ .null_val = {} } },
            };
        }

        if (self.check(.identifier)) {
            const tok = self.advance();
            return ast.Expr{
                .kind = .variable,
                .data = .{ .variable = tok.text },
            };
        }

        if (self.match(.lparen)) {
            const inner = try self.parseExpression();
            _ = try self.expect(.rparen);
            const inner_ptr = try self.allocator.create(ast.Expr);
            inner_ptr.* = inner;
            return ast.Expr{
                .kind = .grouping,
                .data = .{ .grouping = inner_ptr },
            };
        }

        if (self.match(.lbracket)) {
            var elems: std.ArrayList(ast.Expr) = .{};
            while (!self.check(.rbracket) and !self.check(.eof)) {
                try elems.append(self.allocator, try self.parseExpression());
                if (!self.match(.comma)) break;
            }
            _ = try self.expect(.rbracket);

            return ast.Expr{
                .kind = .array_literal,
                .data = .{ .array_literal = .{ .elements = try elems.toOwnedSlice(self.allocator) } },
            };
        }

        self.errors += 1;
        return error.UnexpectedToken;
    }

    fn makeBinary(self: *Parser, op: TokenKind, left: ast.Expr, right: ast.Expr) anyerror!ast.Expr {
        const left_ptr = try self.allocator.create(ast.Expr);
        left_ptr.* = left;
        const right_ptr = try self.allocator.create(ast.Expr);
        right_ptr.* = right;

        return ast.Expr{
            .kind = .binary,
            .data = .{
                .binary = .{
                    .op = op,
                    .left = left_ptr,
                    .right = right_ptr,
                },
            },
        };
    }
};

test "parse basic function" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    const src = "fn int add(int a, int b) { return a + b; }";
    var lexer = @import("lexer.zig").Lexer.init(allocator, src);
    const tokens = try lexer.tokenizeAll();

    var parser = Parser.init(allocator, tokens);
    const prog = try parser.parseProgram();

    try std.testing.expectEqual(@as(usize, 1), prog.statements.len);
    try std.testing.expect(prog.statements[0].kind == .fn_decl);
}

test "parse all kale_self files" {
    var arena = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    const files = [_][]const u8{
        "../kale_self/token.kl",
        "../kale_self/ast.kl",
        "../kale_self/lexer.kl",
        "../kale_self/parser.kl",
        "../kale_self/checker.kl",
        "../kale_self/codegen.kl",
        "../kale_self/main.kl",
    };

    for (files) |path| {
        const file = try std.fs.cwd().openFile(path, .{});
        defer file.close();
        const src = try file.readToEndAlloc(allocator, 1024 * 1024);

        var lexer = @import("lexer.zig").Lexer.init(allocator, src);
        const tokens = try lexer.tokenizeAll();

        var parser = Parser.init(allocator, tokens);
        const prog = try parser.parseProgram();

        try std.testing.expect(prog.statements.len > 0);
        try std.testing.expectEqual(@as(usize, 0), parser.errors);
    }
}



const std = @import("std");
const TokenKind = @import("token.zig").TokenKind;

pub const TypeRef = struct {
    name: []const u8,
    ptr_depth: usize = 0,
    is_array: bool = false,
    array_size: ?usize = null,
    func_params: ?[]TypeRef = null,
    func_ret: ?*TypeRef = null,

    pub fn format(self: TypeRef, comptime fmt: []const u8, options: std.fmt.FormatOptions, writer: anytype) !void {
        _ = fmt;
        _ = options;
        try writer.writeAll(self.name);
        var i: usize = 0;
        while (i < self.ptr_depth) : (i += 1) {
            try writer.writeAll("*");
        }
        if (self.is_array) {
            if (self.array_size) |sz| {
                try writer.print("[{d}]", .{sz});
            } else {
                try writer.writeAll("[]");
            }
        }
    }
};

pub const LiteralValue = union(enum) {
    int_val: i64,
    float_val: f64,
    str_val: []const u8,
    char_val: u8,
    bool_val: bool,
    null_val: void,
};

pub const ExprKind = enum {
    literal,
    variable,
    grouping,
    unary,
    binary,
    call,
    index,
    member,
    assign,
    cast,
    alloc,
    array_literal,
};

pub const Expr = struct {
    kind: ExprKind,
    data: Data,

    pub const Data = union(ExprKind) {
        literal: LiteralValue,
        variable: []const u8,
        grouping: *Expr,
        unary: struct {
            op: TokenKind,
            operand: *Expr,
            is_postfix: bool = false,
        },
        binary: struct {
            op: TokenKind,
            left: *Expr,
            right: *Expr,
        },
        call: struct {
            callee: *Expr,
            args: []Expr,
        },
        index: struct {
            target: *Expr,
            index: *Expr,
        },
        member: struct {
            target: *Expr,
            member: []const u8,
            is_arrow: bool = false,
        },
        assign: struct {
            target: *Expr,
            op: TokenKind,
            value: *Expr,
        },
        cast: struct {
            target_type: TypeRef,
            expr: *Expr,
        },
        alloc: struct {
            type_ref: TypeRef,
            count: ?*Expr = null,
        },
        array_literal: struct {
            elements: []Expr,
        },
    };
};

pub const Param = struct {
    name: []const u8,
    type_ref: TypeRef,
};

pub const Field = struct {
    name: []const u8,
    type_ref: TypeRef,
};

pub const EnumMember = struct {
    name: []const u8,
    value: ?i64 = null,
};

pub const SwitchCase = struct {
    values: []Expr,
    body: []Stmt,
};

pub const ImportItem = struct {
    name: []const u8,
    alias: ?[]const u8 = null,
};

pub const StmtKind = enum {
    block,
    var_decl,
    if_stmt,
    while_stmt,
    for_stmt,
    switch_stmt,
    return_stmt,
    break_stmt,
    continue_stmt,
    print_stmt,
    free_stmt,
    expr_stmt,
    fn_decl,
    struct_decl,
    enum_decl,
    import_stmt,
    from_import_stmt,
};

pub const Stmt = struct {
    kind: StmtKind,
    data: Data,

    pub const Data = union(StmtKind) {
        block: []Stmt,
        var_decl: struct {
            name: []const u8,
            type_ref: ?TypeRef,
            init: ?*Expr,
            is_const: bool,
        },
        if_stmt: struct {
            cond: *Expr,
            then_stmt: *Stmt,
            else_stmt: ?*Stmt,
        },
        while_stmt: struct {
            cond: *Expr,
            body: *Stmt,
        },
        for_stmt: struct {
            init: ?*Stmt,
            cond: ?*Expr,
            inc: ?*Expr,
            body: *Stmt,
        },
        switch_stmt: struct {
            expr: *Expr,
            cases: []SwitchCase,
            default_body: ?[]Stmt,
        },
        return_stmt: ?*Expr,
        break_stmt: void,
        continue_stmt: void,
        print_stmt: []Expr,
        free_stmt: *Expr,
        expr_stmt: *Expr,
        fn_decl: struct {
            name: []const u8,
            params: []Param,
            ret_type: TypeRef,
            body: ?*Stmt,
            is_extern: bool,
            is_varargs: bool,
            struct_name: ?[]const u8,
        },
        struct_decl: struct {
            name: []const u8,
            fields: []Field,
        },
        enum_decl: struct {
            name: []const u8,
            members: []EnumMember,
        },
        import_stmt: struct {
            path: []const u8,
            alias: ?[]const u8,
        },
        from_import_stmt: struct {
            path: []const u8,
            symbols: []ImportItem,
        },
    };
};

pub const Program = struct {
    statements: []Stmt,
};

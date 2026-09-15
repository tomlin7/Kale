const std = @import("std");

pub const TokenKind = enum {
    // Special
    eof,
    bad,

    // Identifiers & Literals
    identifier,
    number_int,
    number_float,
    string_lit,
    char_lit,

    // Keywords - Values
    kw_true,
    kw_false,
    kw_null,

    // Keywords - Declarations
    kw_fn,
    kw_let,
    kw_var,
    kw_const,
    kw_struct,
    kw_enum,
    kw_extern,
    kw_operator,
    kw_import,
    kw_from,
    kw_as,

    // Keywords - Control Flow
    kw_if,
    kw_else,
    kw_while,
    kw_for,
    kw_switch,
    kw_case,
    kw_default,
    kw_return,
    kw_break,
    kw_continue,
    kw_goto,
    kw_label,

    // Keywords - Built-in functions
    kw_print,
    kw_input,
    kw_alloc,
    kw_free,

    // Keywords - Types
    kw_int,
    kw_int32,
    kw_float,
    kw_double,
    kw_string,
    kw_bool,
    kw_char,
    kw_void,

    // Punctuators
    lparen, // (
    rparen, // )
    lbrace, // {
    rbrace, // }
    lbracket, // [
    rbracket, // ]
    comma, // ,
    semicolon, // ;
    colon, // :
    dot, // .
    arrow, // ->
    caret, // ^

    // Operators - Arithmetic
    plus, // +
    minus, // -
    star, // *
    slash, // /
    percent, // %
    star_star, // **

    // Operators - Relational
    eq_eq, // ==
    bang_eq, // !=
    lt, // <
    lt_eq, // <=
    gt, // >
    gt_eq, // >=

    // Operators - Logical
    amp_amp, // &&
    pipe_pipe, // ||
    bang, // !

    // Operators - Bitwise
    amp, // &
    pipe, // |
    tilde, // ~
    shl, // <<
    shr, // >>

    // Operators - Increment / Decrement
    plus_plus, // ++
    minus_minus, // --

    // Operators - Assignment
    eq, // =
    plus_eq, // +=
    minus_eq, // -=
    star_eq, // *=
    slash_eq, // /=
    percent_eq, // %=
    amp_eq, // &=
    pipe_eq, // |=
    caret_eq, // ^=
    shl_eq, // <<=
    shr_eq, // >>=
};

pub const Token = struct {
    kind: TokenKind,
    text: []const u8,
    int_val: i64 = 0,
    float_val: f64 = 0.0,
    line: usize,
    col: usize,

    pub fn isTypeKeyword(self: Token) bool {
        return switch (self.kind) {
            .kw_int, .kw_int32, .kw_float, .kw_double, .kw_string, .kw_bool, .kw_char, .kw_void => true,
            else => false,
        };
    }

    pub fn isAssignmentOp(self: Token) bool {
        return switch (self.kind) {
            .eq, .plus_eq, .minus_eq, .star_eq, .slash_eq, .percent_eq, .amp_eq, .pipe_eq, .caret_eq, .shl_eq, .shr_eq => true,
            else => false,
        };
    }
};

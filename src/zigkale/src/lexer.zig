const std = @import("std");
const token_mod = @import("token.zig");
const Token = token_mod.Token;
const TokenKind = token_mod.TokenKind;

pub const Lexer = struct {
    source: []const u8,
    cursor: usize = 0,
    line: usize = 1,
    col: usize = 1,
    allocator: std.mem.Allocator,

    pub fn init(allocator: std.mem.Allocator, source: []const u8) Lexer {
        return .{
            .source = source,
            .cursor = 0,
            .line = 1,
            .col = 1,
            .allocator = allocator,
        };
    }

    fn peek(self: *const Lexer) u8 {
        if (self.cursor >= self.source.len) return 0;
        return self.source[self.cursor];
    }

    fn peekNext(self: *const Lexer) u8 {
        if (self.cursor + 1 >= self.source.len) return 0;
        return self.source[self.cursor + 1];
    }

    fn advance(self: *Lexer) u8 {
        if (self.cursor >= self.source.len) return 0;
        const c = self.source[self.cursor];
        self.cursor += 1;
        if (c == '\n') {
            self.line += 1;
            self.col = 1;
        } else {
            self.col += 1;
        }
        return c;
    }

    fn match(self: *Lexer, expected: u8) bool {
        if (self.peek() == expected) {
            _ = self.advance();
            return true;
        }
        return false;
    }

    fn skipWhitespaceAndComments(self: *Lexer) void {
        while (self.cursor < self.source.len) {
            const c = self.peek();
            if (c == ' ' or c == '\t' or c == '\r' or c == '\n') {
                _ = self.advance();
            } else if (c == '/' and self.peekNext() == '/') {
                _ = self.advance();
                _ = self.advance();
                while (self.cursor < self.source.len and self.peek() != '\n') {
                    _ = self.advance();
                }
            } else if (c == '/' and self.peekNext() == '*') {
                _ = self.advance();
                _ = self.advance();
                while (self.cursor < self.source.len) {
                    if (self.peek() == '*' and self.peekNext() == '/') {
                        _ = self.advance();
                        _ = self.advance();
                        break;
                    }
                    _ = self.advance();
                }
            } else {
                break;
            }
        }
    }

    pub fn nextToken(self: *Lexer) !Token {
        self.skipWhitespaceAndComments();

        const start_pos = self.cursor;
        const start_line = self.line;
        const start_col = self.col;

        if (self.cursor >= self.source.len) {
            return Token{
                .kind = .eof,
                .text = "",
                .line = start_line,
                .col = start_col,
            };
        }

        const c = self.advance();

        // Identifier or keyword
        if (isAlpha(c)) {
            while (isAlphanumeric(self.peek())) {
                _ = self.advance();
            }
            const text = self.source[start_pos..self.cursor];
            const kind = checkKeyword(text);
            return Token{
                .kind = kind,
                .text = text,
                .line = start_line,
                .col = start_col,
            };
        }

        // Numbers (decimal, hex, binary, float)
        if (isDigit(c)) {
            if (c == '0' and (self.peek() == 'x' or self.peek() == 'X')) {
                _ = self.advance(); // consume 'x'
                const num_start = self.cursor;
                while (isHexDigit(self.peek())) {
                    _ = self.advance();
                }
                const hex_str = self.source[num_start..self.cursor];
                const val = std.fmt.parseInt(i64, hex_str, 16) catch 0;
                return Token{
                    .kind = .number_int,
                    .text = self.source[start_pos..self.cursor],
                    .int_val = val,
                    .line = start_line,
                    .col = start_col,
                };
            } else if (c == '0' and (self.peek() == 'b' or self.peek() == 'B')) {
                _ = self.advance(); // consume 'b'
                const num_start = self.cursor;
                while (self.peek() == '0' or self.peek() == '1') {
                    _ = self.advance();
                }
                const bin_str = self.source[num_start..self.cursor];
                const val = std.fmt.parseInt(i64, bin_str, 2) catch 0;
                return Token{
                    .kind = .number_int,
                    .text = self.source[start_pos..self.cursor],
                    .int_val = val,
                    .line = start_line,
                    .col = start_col,
                };
            } else {
                var is_float = false;
                while (isDigit(self.peek())) {
                    _ = self.advance();
                }
                if (self.peek() == '.' and isDigit(self.peekNext())) {
                    is_float = true;
                    _ = self.advance(); // consume '.'
                    while (isDigit(self.peek())) {
                        _ = self.advance();
                    }
                }
                if (self.peek() == 'f' or self.peek() == 'F') {
                    is_float = true;
                    _ = self.advance();
                }

                const raw_text = self.source[start_pos..self.cursor];
                if (is_float) {
                    var parse_slice = raw_text;
                    if (std.mem.endsWith(u8, parse_slice, "f") or std.mem.endsWith(u8, parse_slice, "F")) {
                        parse_slice = parse_slice[0 .. parse_slice.len - 1];
                    }
                    const fval = std.fmt.parseFloat(f64, parse_slice) catch 0.0;
                    return Token{
                        .kind = .number_float,
                        .text = raw_text,
                        .float_val = fval,
                        .line = start_line,
                        .col = start_col,
                    };
                } else {
                    const ival = std.fmt.parseInt(i64, raw_text, 10) catch 0;
                    return Token{
                        .kind = .number_int,
                        .text = raw_text,
                        .int_val = ival,
                        .line = start_line,
                        .col = start_col,
                    };
                }
            }
        }

        // Strings
        if (c == '"') {
            var str_buf: std.ArrayList(u8) = .{};
            defer str_buf.deinit(self.allocator);

            while (self.cursor < self.source.len and self.peek() != '"') {
                if (self.peek() == '\\') {
                    _ = self.advance();
                    const esc = self.advance();
                    switch (esc) {
                        'n' => try str_buf.append(self.allocator, '\n'),
                        't' => try str_buf.append(self.allocator, '\t'),
                        'r' => try str_buf.append(self.allocator, '\r'),
                        '0' => try str_buf.append(self.allocator, 0),
                        '"' => try str_buf.append(self.allocator, '"'),
                        '\\' => try str_buf.append(self.allocator, '\\'),
                        else => {
                            try str_buf.append(self.allocator, '\\');
                            try str_buf.append(self.allocator, esc);
                        },
                    }
                } else {
                    try str_buf.append(self.allocator, self.advance());
                }
            }
            if (self.peek() == '"') {
                _ = self.advance();
            }

            const unescaped = try self.allocator.dupe(u8, str_buf.items);
            return Token{
                .kind = .string_lit,
                .text = unescaped,
                .line = start_line,
                .col = start_col,
            };
        }

        // Characters
        if (c == '\'') {
            var char_val: u8 = 0;
            if (self.peek() == '\\') {
                _ = self.advance();
                const esc = self.advance();
                char_val = switch (esc) {
                    'n' => '\n',
                    't' => '\t',
                    'r' => '\r',
                    '0' => 0,
                    '\'' => '\'',
                    '\\' => '\\',
                    else => esc,
                };
            } else {
                char_val = self.advance();
            }
            if (self.peek() == '\'') {
                _ = self.advance();
            }
            return Token{
                .kind = .char_lit,
                .text = self.source[start_pos..self.cursor],
                .int_val = char_val,
                .line = start_line,
                .col = start_col,
            };
        }

        // Single and multi-char punctuators and operators
        switch (c) {
            '(' => return self.makeToken(.lparen, start_line, start_col, start_pos),
            ')' => return self.makeToken(.rparen, start_line, start_col, start_pos),
            '{' => return self.makeToken(.lbrace, start_line, start_col, start_pos),
            '}' => return self.makeToken(.rbrace, start_line, start_col, start_pos),
            '[' => return self.makeToken(.lbracket, start_line, start_col, start_pos),
            ']' => return self.makeToken(.rbracket, start_line, start_col, start_pos),
            ',' => return self.makeToken(.comma, start_line, start_col, start_pos),
            ';' => return self.makeToken(.semicolon, start_line, start_col, start_pos),
            ':' => return self.makeToken(.colon, start_line, start_col, start_pos),
            '.' => return self.makeToken(.dot, start_line, start_col, start_pos),
            '~' => return self.makeToken(.tilde, start_line, start_col, start_pos),
            '^' => {
                if (self.match('=')) return self.makeToken(.caret_eq, start_line, start_col, start_pos);
                return self.makeToken(.caret, start_line, start_col, start_pos);
            },
            '+' => {
                if (self.match('+')) return self.makeToken(.plus_plus, start_line, start_col, start_pos);
                if (self.match('=')) return self.makeToken(.plus_eq, start_line, start_col, start_pos);
                return self.makeToken(.plus, start_line, start_col, start_pos);
            },
            '-' => {
                if (self.match('>')) return self.makeToken(.arrow, start_line, start_col, start_pos);
                if (self.match('-')) return self.makeToken(.minus_minus, start_line, start_col, start_pos);
                if (self.match('=')) return self.makeToken(.minus_eq, start_line, start_col, start_pos);
                return self.makeToken(.minus, start_line, start_col, start_pos);
            },
            '*' => {
                if (self.match('*')) return self.makeToken(.star_star, start_line, start_col, start_pos);
                if (self.match('=')) return self.makeToken(.star_eq, start_line, start_col, start_pos);
                return self.makeToken(.star, start_line, start_col, start_pos);
            },
            '/' => {
                if (self.match('=')) return self.makeToken(.slash_eq, start_line, start_col, start_pos);
                return self.makeToken(.slash, start_line, start_col, start_pos);
            },
            '%' => {
                if (self.match('=')) return self.makeToken(.percent_eq, start_line, start_col, start_pos);
                return self.makeToken(.percent, start_line, start_col, start_pos);
            },
            '=' => {
                if (self.match('=')) return self.makeToken(.eq_eq, start_line, start_col, start_pos);
                return self.makeToken(.eq, start_line, start_col, start_pos);
            },
            '!' => {
                if (self.match('=')) return self.makeToken(.bang_eq, start_line, start_col, start_pos);
                return self.makeToken(.bang, start_line, start_col, start_pos);
            },
            '<' => {
                if (self.match('<')) {
                    if (self.match('=')) return self.makeToken(.shl_eq, start_line, start_col, start_pos);
                    return self.makeToken(.shl, start_line, start_col, start_pos);
                }
                if (self.match('=')) return self.makeToken(.lt_eq, start_line, start_col, start_pos);
                return self.makeToken(.lt, start_line, start_col, start_pos);
            },
            '>' => {
                if (self.match('>')) {
                    if (self.match('=')) return self.makeToken(.shr_eq, start_line, start_col, start_pos);
                    return self.makeToken(.shr, start_line, start_col, start_pos);
                }
                if (self.match('=')) return self.makeToken(.gt_eq, start_line, start_col, start_pos);
                return self.makeToken(.gt, start_line, start_col, start_pos);
            },
            '&' => {
                if (self.match('&')) return self.makeToken(.amp_amp, start_line, start_col, start_pos);
                if (self.match('=')) return self.makeToken(.amp_eq, start_line, start_col, start_pos);
                return self.makeToken(.amp, start_line, start_col, start_pos);
            },
            '|' => {
                if (self.match('|')) return self.makeToken(.pipe_pipe, start_line, start_col, start_pos);
                if (self.match('=')) return self.makeToken(.pipe_eq, start_line, start_col, start_pos);
                return self.makeToken(.pipe, start_line, start_col, start_pos);
            },
            else => {
                return Token{
                    .kind = .bad,
                    .text = self.source[start_pos..self.cursor],
                    .line = start_line,
                    .col = start_col,
                };
            },
        }
    }

    fn makeToken(self: *const Lexer, kind: TokenKind, line: usize, col: usize, start_pos: usize) Token {
        return Token{
            .kind = kind,
            .text = self.source[start_pos..self.cursor],
            .line = line,
            .col = col,
        };
    }

    pub fn tokenizeAll(self: *Lexer) ![]Token {
        var tokens: std.ArrayList(Token) = .{};
        while (true) {
            const tok = try self.nextToken();
            try tokens.append(self.allocator, tok);
            if (tok.kind == .eof) break;
        }
        return tokens.toOwnedSlice(self.allocator);
    }
};

fn isAlpha(c: u8) bool {
    return (c >= 'a' and c <= 'z') or (c >= 'A' and c <= 'Z') or c == '_';
}

fn isDigit(c: u8) bool {
    return c >= '0' and c <= '9';
}

fn isHexDigit(c: u8) bool {
    return isDigit(c) or (c >= 'a' and c <= 'f') or (c >= 'A' and c <= 'F');
}

fn isAlphanumeric(c: u8) bool {
    return isAlpha(c) or isDigit(c);
}

fn checkKeyword(text: []const u8) TokenKind {
    if (std.mem.eql(u8, text, "fn")) return .kw_fn;
    if (std.mem.eql(u8, text, "let")) return .kw_let;
    if (std.mem.eql(u8, text, "var")) return .kw_var;
    if (std.mem.eql(u8, text, "const")) return .kw_const;
    if (std.mem.eql(u8, text, "struct")) return .kw_struct;
    if (std.mem.eql(u8, text, "enum")) return .kw_enum;
    if (std.mem.eql(u8, text, "extern")) return .kw_extern;
    if (std.mem.eql(u8, text, "operator")) return .kw_operator;
    if (std.mem.eql(u8, text, "import")) return .kw_import;
    if (std.mem.eql(u8, text, "from")) return .kw_from;
    if (std.mem.eql(u8, text, "as")) return .kw_as;
    if (std.mem.eql(u8, text, "if")) return .kw_if;
    if (std.mem.eql(u8, text, "else")) return .kw_else;
    if (std.mem.eql(u8, text, "while")) return .kw_while;
    if (std.mem.eql(u8, text, "for")) return .kw_for;
    if (std.mem.eql(u8, text, "switch")) return .kw_switch;
    if (std.mem.eql(u8, text, "case")) return .kw_case;
    if (std.mem.eql(u8, text, "default")) return .kw_default;
    if (std.mem.eql(u8, text, "return")) return .kw_return;
    if (std.mem.eql(u8, text, "break")) return .kw_break;
    if (std.mem.eql(u8, text, "continue")) return .kw_continue;
    if (std.mem.eql(u8, text, "print")) return .kw_print;
    if (std.mem.eql(u8, text, "input")) return .kw_input;
    if (std.mem.eql(u8, text, "alloc")) return .kw_alloc;
    if (std.mem.eql(u8, text, "free")) return .kw_free;

    if (std.mem.eql(u8, text, "int")) return .kw_int;
    if (std.mem.eql(u8, text, "int32") or std.mem.eql(u8, text, "i32")) return .kw_int32;
    if (std.mem.eql(u8, text, "float") or std.mem.eql(u8, text, "float32") or std.mem.eql(u8, text, "f32")) return .kw_float;
    if (std.mem.eql(u8, text, "double") or std.mem.eql(u8, text, "float64") or std.mem.eql(u8, text, "f64")) return .kw_double;
    if (std.mem.eql(u8, text, "string")) return .kw_string;
    if (std.mem.eql(u8, text, "bool")) return .kw_bool;
    if (std.mem.eql(u8, text, "char")) return .kw_char;
    if (std.mem.eql(u8, text, "void")) return .kw_void;

    if (std.mem.eql(u8, text, "true")) return .kw_true;
    if (std.mem.eql(u8, text, "false")) return .kw_false;
    if (std.mem.eql(u8, text, "null")) return .kw_null;

    return .identifier;
}

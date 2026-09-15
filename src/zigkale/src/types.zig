const std = @import("std");

pub const TypeKind = enum {
    primitive,
    pointer,
    array,
    struct_type,
    enum_type,
    function,
    module,
    unknown,
};

pub const PrimitiveKind = enum {
    int_t, // 64-bit int
    int32_t, // 32-bit int
    float_t, // 32-bit float
    double_t, // 64-bit float
    bool_t,
    string_t, // const char*
    char_t, // 8-bit char
    void_t,
};

pub const Type = struct {
    kind: TypeKind,
    data: Data,

    pub const Data = union {
        primitive: PrimitiveKind,
        pointer: *Type,
        array: struct {
            elem_type: *Type,
            size: ?usize,
        },
        struct_type: struct {
            name: []const u8,
            fields: []StructField,
        },
        enum_type: struct {
            name: []const u8,
            members: []EnumMember,
        },
        function: struct {
            param_types: []*Type,
            ret_type: *Type,
        },
        module: struct {
            name: []const u8,
            path: []const u8,
        },
        unknown: void,
    };

    pub const StructField = struct {
        name: []const u8,
        type: *Type,
    };

    pub const EnumMember = struct {
        name: []const u8,
        value: i64,
    };

    pub fn isNumeric(self: *const Type) bool {
        if (self.kind == .primitive) {
            return switch (self.data.primitive) {
                .int_t, .int32_t, .float_t, .double_t, .char_t => true,
                else => false,
            };
        }
        return false;
    }

    pub fn isInteger(self: *const Type) bool {
        if (self.kind == .primitive) {
            return switch (self.data.primitive) {
                .int_t, .int32_t, .char_t => true,
                else => false,
            };
        }
        if (self.kind == .enum_type) return true;
        return false;
    }

    pub fn isPointer(self: *const Type) bool {
        return self.kind == .pointer;
    }

    pub fn isVoidPointer(self: *const Type) bool {
        if (self.kind == .pointer) {
            return self.data.pointer.kind == .primitive and self.data.pointer.data.primitive == .void_t;
        }
        return false;
    }

    pub fn isEqual(self: *const Type, other: *const Type) bool {
        if (self == other) return true;
        if (self.kind != other.kind) return false;
        return switch (self.kind) {
            .primitive => self.data.primitive == other.data.primitive,
            .pointer => self.data.pointer.isEqual(other.data.pointer),
            .array => self.data.array.elem_type.isEqual(other.data.array.elem_type) and (self.data.array.size == other.data.array.size),
            .struct_type => std.mem.eql(u8, self.data.struct_type.name, other.data.struct_type.name),
            .enum_type => std.mem.eql(u8, self.data.enum_type.name, other.data.enum_type.name),
            .function => blk: {
                if (!self.data.function.ret_type.isEqual(other.data.function.ret_type)) break :blk false;
                if (self.data.function.param_types.len != other.data.function.param_types.len) break :blk false;
                var i: usize = 0;
                while (i < self.data.function.param_types.len) : (i += 1) {
                    if (!self.data.function.param_types[i].isEqual(other.data.function.param_types[i])) break :blk false;
                }
                break :blk true;
            },
            .module => std.mem.eql(u8, self.data.module.name, other.data.module.name),
            .unknown => true,
        };
    }

    pub fn canConvert(from: *const Type, to: *const Type) bool {
        if (from.isEqual(to)) return true;
        if (from.kind == .unknown or to.kind == .unknown) return true;

        // Void pointer (null pointer or generic pointer) <-> any pointer
        if (from.isVoidPointer() and to.isPointer()) return true;
        if (from.isPointer() and to.isVoidPointer()) return true;

        // Pointer <-> Pointer conversion (permissive C-like type system in Kale)
        if (from.isPointer() and to.isPointer()) return true;

        // String (const char*) <-> char* or void*
        if (from.kind == .primitive and from.data.primitive == .string_t and to.isPointer()) return true;
        if (from.isPointer() and to.kind == .primitive and to.data.primitive == .string_t) return true;

        // Numeric widening: int/int32 <-> float/double/char
        if (from.isNumeric() and to.isNumeric()) return true;

        // Enum <-> int
        if (from.kind == .enum_type and to.isInteger()) return true;
        if (from.isInteger() and to.kind == .enum_type) return true;

        // Array decay to pointer: T[] -> T*
        if (from.kind == .array and to.kind == .pointer) {
            return from.data.array.elem_type.isEqual(to.data.pointer);
        }

        // Pointer <-> integer (e.g. 0 as null pointer)
        if (from.isInteger() and to.isPointer()) return true;
        if (from.isPointer() and to.isInteger()) return true;

        return false;
    }

    pub fn canCast(from: *const Type, to: *const Type) bool {
        if (canConvert(from, to)) return true;
        // Pointer <-> int casts
        if (from.isPointer() and to.isInteger()) return true;
        if (from.isInteger() and to.isPointer()) return true;
        // Pointer <-> Pointer (any)
        if (from.isPointer() and to.isPointer()) return true;
        // Numeric <-> Numeric
        if (from.isNumeric() and to.isNumeric()) return true;
        return true;
    }
};

pub const TypeContext = struct {
    allocator: std.mem.Allocator,
    type_int: *Type,
    type_int32: *Type,
    type_float: *Type,
    type_double: *Type,
    type_bool: *Type,
    type_string: *Type,
    type_char: *Type,
    type_void: *Type,
    type_unknown: *Type,

    pub fn init(allocator: std.mem.Allocator) !TypeContext {
        const type_int = try createPrimitive(allocator, .int_t);
        const type_int32 = try createPrimitive(allocator, .int32_t);
        const type_float = try createPrimitive(allocator, .float_t);
        const type_double = try createPrimitive(allocator, .double_t);
        const type_bool = try createPrimitive(allocator, .bool_t);
        const type_string = try createPrimitive(allocator, .string_t);
        const type_char = try createPrimitive(allocator, .char_t);
        const type_void = try createPrimitive(allocator, .void_t);
        const type_unknown = try allocator.create(Type);
        type_unknown.* = Type{ .kind = .unknown, .data = .{ .unknown = {} } };

        return .{
            .allocator = allocator,
            .type_int = type_int,
            .type_int32 = type_int32,
            .type_float = type_float,
            .type_double = type_double,
            .type_bool = type_bool,
            .type_string = type_string,
            .type_char = type_char,
            .type_void = type_void,
            .type_unknown = type_unknown,
        };
    }

    fn createPrimitive(allocator: std.mem.Allocator, kind: PrimitiveKind) !*Type {
        const t = try allocator.create(Type);
        t.* = Type{ .kind = .primitive, .data = .{ .primitive = kind } };
        return t;
    }

    pub fn getPointerTo(self: *TypeContext, base: *Type) !*Type {
        const t = try self.allocator.create(Type);
        t.* = Type{ .kind = .pointer, .data = .{ .pointer = base } };
        return t;
    }

    pub fn getArrayOf(self: *TypeContext, elem: *Type, size: ?usize) !*Type {
        const t = try self.allocator.create(Type);
        t.* = Type{ .kind = .array, .data = .{ .array = .{ .elem_type = elem, .size = size } } };
        return t;
    }
};

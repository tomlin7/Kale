import llvmlite.ir as ir
from ..binding.types import (
    TypeSymbol,
    TypeInt,
    TypeInt32,
    TypeUInt64,
    TypeUInt32,
    TypeUInt8,
    TypeFloat,
    TypeDouble,
    TypeBool,
    TypeString,
    TypeChar,
    TypeVoid,
    ArrayTypeSymbol,
    PointerTypeSymbol,
    FunctionTypeSymbol,
    StructTypeSymbol,
    EnumTypeSymbol,
)

def to_llvm_type(type_symbol: TypeSymbol, struct_map: dict[str, ir.Type] | None = None) -> ir.Type:
    """Converts a Kale TypeSymbol into a corresponding llvmlite.ir.Type."""
    if isinstance(type_symbol, PointerTypeSymbol):
        if type_symbol.base_type == TypeVoid:
            return ir.PointerType(ir.IntType(8))
        base_t = to_llvm_type(type_symbol.base_type, struct_map)
        return ir.PointerType(base_t)
    if isinstance(type_symbol, FunctionTypeSymbol):
        param_types = [to_llvm_type(p, struct_map) for p in type_symbol.parameter_types]
        ret_t = to_llvm_type(type_symbol.return_type, struct_map)
        fn_type = ir.FunctionType(ret_t, param_types)
        return ir.PointerType(fn_type)
    if isinstance(type_symbol, StructTypeSymbol):
        if struct_map and type_symbol.name in struct_map:
            return struct_map[type_symbol.name]
        # Fallback anonymous struct or empty struct
        field_types = [to_llvm_type(ftype, struct_map) for _, ftype in type_symbol.fields]
        return ir.LiteralStructType(field_types)
    if isinstance(type_symbol, ArrayTypeSymbol):
        elem_t = to_llvm_type(type_symbol.element_type, struct_map)
        if type_symbol.size is not None:
            return ir.ArrayType(elem_t, type_symbol.size)
        return ir.PointerType(elem_t)
    if type_symbol in (TypeInt32, TypeUInt32):
        return ir.IntType(32)
    if type_symbol in (TypeUInt8, TypeChar):
        return ir.IntType(8)
    if type_symbol in (TypeInt, TypeUInt64) or isinstance(type_symbol, EnumTypeSymbol):
        return ir.IntType(64)
    if type_symbol == TypeFloat:
        return ir.FloatType()
    if type_symbol == TypeDouble:
        return ir.DoubleType()
    if type_symbol == TypeBool:
        return ir.IntType(1)
    if type_symbol == TypeChar:
        return ir.IntType(8)
    if type_symbol == TypeString:
        return ir.PointerType(ir.IntType(8))
    if type_symbol == TypeVoid:
        return ir.VoidType()
    # Default fallback
    return ir.IntType(64)

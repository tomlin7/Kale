import llvmlite.ir as ir
from ..binding.types import (
    TypeSymbol,
    TypeInt,
    TypeFloat,
    TypeDouble,
    TypeBool,
    TypeString,
    TypeChar,
    TypeVoid,
    ArrayTypeSymbol,
)

def to_llvm_type(type_symbol: TypeSymbol) -> ir.Type:
    """Converts a Kale TypeSymbol into a corresponding llvmlite.ir.Type."""
    if isinstance(type_symbol, ArrayTypeSymbol):
        elem_t = to_llvm_type(type_symbol.element_type)
        return ir.PointerType(elem_t)
    if type_symbol == TypeInt:
        return ir.IntType(64)
    if type_symbol in (TypeFloat, TypeDouble):
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

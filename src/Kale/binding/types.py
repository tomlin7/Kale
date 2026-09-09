from dataclasses import dataclass

@dataclass(frozen=True)
class TypeSymbol:
    name: str

    def __repr__(self) -> str:
        return self.name

# Built-in primitive types
TypeInt = TypeSymbol("int")
TypeFloat = TypeSymbol("float")
TypeDouble = TypeSymbol("double")
TypeBool = TypeSymbol("bool")
TypeString = TypeSymbol("string")
TypeChar = TypeSymbol("char")
TypeVoid = TypeSymbol("void")
TypeUnknown = TypeSymbol("<unknown>")

TYPE_MAP: dict[str, TypeSymbol] = {
    "int": TypeInt,
    "float": TypeFloat,
    "double": TypeDouble,
    "bool": TypeBool,
    "string": TypeString,
    "char": TypeChar,
    "void": TypeVoid,
}

def lookup_type(name: str) -> TypeSymbol | None:
    return TYPE_MAP.get(name)

def is_numeric(t: TypeSymbol) -> bool:
    return t in (TypeInt, TypeFloat, TypeDouble)

def can_convert(from_type: TypeSymbol, to_type: TypeSymbol) -> bool:
    """Checks whether from_type can be assigned or implicitly converted to to_type."""
    if from_type == to_type:
        return True
    if from_type == TypeUnknown or to_type == TypeUnknown:
        return True
    # Implicit numeric widening
    if from_type == TypeInt and to_type in (TypeFloat, TypeDouble):
        return True
    if from_type == TypeFloat and to_type == TypeDouble:
        return True
    return False

def get_promoted_numeric_type(left: TypeSymbol, right: TypeSymbol) -> TypeSymbol:
    """Returns the common promoted type for numeric operations."""
    if TypeDouble in (left, right):
        return TypeDouble
    if TypeFloat in (left, right):
        return TypeFloat
    return TypeInt

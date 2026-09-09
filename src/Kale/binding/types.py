from dataclasses import dataclass

@dataclass(frozen=True)
class TypeSymbol:
    name: str

    def __repr__(self) -> str:
        return self.name

@dataclass(frozen=True)
class ArrayTypeSymbol(TypeSymbol):
    element_type: TypeSymbol = None  # type: ignore
    size: int | None = None

    def __init__(self, element_type: TypeSymbol, size: int | None = None):
        sz_str = f"{size}" if size is not None else ""
        name = f"{element_type.name}[{sz_str}]"
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "element_type", element_type)
        object.__setattr__(self, "size", size)

    def __repr__(self) -> str:
        return self.name

@dataclass(frozen=True)
class PointerTypeSymbol(TypeSymbol):
    base_type: TypeSymbol = None  # type: ignore

    def __init__(self, base_type: TypeSymbol):
        name = f"{base_type.name}*"
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "base_type", base_type)

    def __repr__(self) -> str:
        return self.name

@dataclass(frozen=True)
class StructTypeSymbol(TypeSymbol):
    fields: tuple[tuple[str, TypeSymbol], ...] = ()

    def __init__(self, name: str, fields: tuple[tuple[str, TypeSymbol], ...] = ()):
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "fields", fields)

    def get_field_type(self, field_name: str) -> TypeSymbol | None:
        for fname, ftype in self.fields:
            if fname == field_name:
                return ftype
        return None

    def get_field_index(self, field_name: str) -> int:
        for idx, (fname, _) in enumerate(self.fields):
            if fname == field_name:
                return idx
        return -1

    def __repr__(self) -> str:
        fields_str = ", ".join(f"{fname}: {ftype}" for fname, ftype in self.fields)
        return f"struct {self.name} {{{fields_str}}}"

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
    if name in TYPE_MAP:
        return TYPE_MAP[name]
    # Handle pointer types like int* or Point*
    if name.endswith("*"):
        base_name = name[:-1].strip()
        base_t = lookup_type(base_name)
        if base_t is not None:
            return PointerTypeSymbol(base_t)
    # Handle array types like int[] or int[10]
    if name.endswith("]"):
        bracket_start = name.find("[")
        if bracket_start != -1:
            base_name = name[:bracket_start].strip()
            size_str = name[bracket_start + 1:-1].strip()
            elem_t = lookup_type(base_name)
            if elem_t is not None:
                sz = int(size_str) if size_str.isdigit() else None
                return ArrayTypeSymbol(elem_t, sz)
    return None

def is_numeric(t: TypeSymbol) -> bool:
    return t in (TypeInt, TypeFloat, TypeDouble)

def can_convert(from_type: TypeSymbol, to_type: TypeSymbol) -> bool:
    """Checks whether from_type can be assigned or implicitly converted to to_type."""
    if from_type == to_type:
        return True
    if from_type == TypeUnknown or to_type == TypeUnknown:
        return True
    # Pointer conversions (int* to int*, or array decaying to pointer int[] -> int*)
    if isinstance(from_type, PointerTypeSymbol) and isinstance(to_type, PointerTypeSymbol):
        return can_convert(from_type.base_type, to_type.base_type)
    if isinstance(from_type, ArrayTypeSymbol) and isinstance(to_type, PointerTypeSymbol):
        return can_convert(from_type.element_type, to_type.base_type)
    # Array conversions: int[5] can convert to int[]
    if isinstance(from_type, ArrayTypeSymbol) and isinstance(to_type, ArrayTypeSymbol):
        if can_convert(from_type.element_type, to_type.element_type):
            if to_type.size is None or from_type.size == to_type.size:
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

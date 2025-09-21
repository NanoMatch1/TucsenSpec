from enum import IntEnum

class TUCAMRET(IntEnum):
    TUCAMRET_SUCCESS     = 0x00000001
    TUCAMRET_FAILURE     = 0x80000000
    TUCAMRET_NO_MEMORY   = 0x80000101
    TUCAMRET_NO_RESOURCE = 0x80000102
    TUCAMRET_NO_MODULE   = 0x80000103
    TUCAMRET_NO_DRIVER   = 0x80000104
    TUCAMRET_NO_CAMERA   = 0x80000105
    TUCAMRET_NO_GRABBER  = 0x80000106
    TUCAMRET_NO_PROPERTY = 0x80000107

# Optional short descriptions (expand as you encounter more)
_EXPLAIN = {
    TUCAMRET.TUCAMRET_SUCCESS:     "Success",
    TUCAMRET.TUCAMRET_FAILURE:     "Generic failure",
    TUCAMRET.TUCAMRET_NO_MEMORY:   "Insufficient memory",
    TUCAMRET.TUCAMRET_NO_RESOURCE: "Required resource unavailable",
    TUCAMRET.TUCAMRET_NO_MODULE:   "Module missing",
    TUCAMRET.TUCAMRET_NO_DRIVER:   "Driver not found",
    TUCAMRET.TUCAMRET_NO_CAMERA:   "No camera detected",
    TUCAMRET.TUCAMRET_NO_GRABBER:  "No frame grabber",
    TUCAMRET.TUCAMRET_NO_PROPERTY: "Property not supported",
}

class TucamError(RuntimeError):
    """Raised when a TUCAMRET indicates failure."""

def _to_int(code) -> int:
    """Best-effort normalization to Python int from enums, ctypes, numpy, str."""
    # Enum or ctypes have .value, but Python Enums also are ints if IntEnum
    if hasattr(code, "value"):
        try:
            return int(code.value)
        except Exception:
            pass

    # ctypes: c_int / c_uint32 etc.
    try:
        import ctypes
        if isinstance(code, ctypes._SimpleCData):  # c_int, c_uint, etc.
            return int(code.value)
    except Exception:
        pass

    # numpy scalar
    try:
        import numpy as np  # type: ignore
        if isinstance(code, np.generic):
            return int(code)
    except Exception:
        pass

    # strings like "0x80000105" or "1"
    if isinstance(code, str):
        return int(code, 0)  # base=0 -> auto 0x, 0o, etc.

    # plain int or IntEnum
    return int(code)

def is_success(code) -> bool:
    return _to_int(code) == int(TUCAMRET.TUCAMRET_SUCCESS)

def is_error(code) -> bool:
    """Treat any code with the high bit set (0x8000_0000) as error."""
    v = _to_int(code)
    return (v & 0x80000000) != 0

def code_name(code) -> str:
    v = _to_int(code)
    try:
        return TUCAMRET(v).name
    except ValueError:
        return f"UNKNOWN_0x{v:08X}"

def code_value_hex(code) -> str:
    return f"0x{_to_int(code):08X}"

def explain(code) -> str:
    v = _to_int(code)
    try:
        enum = TUCAMRET(v)
        return _EXPLAIN.get(enum, enum.name)
    except ValueError:
        return "Unrecognized return code"

def summarize(code) -> str:
    """Human-friendly one-liner."""
    return f"{code_name(code)} ({code_value_hex(code)}): {explain(code)}"

def check_ok(code, *, context: str = "", logger=None, raise_on_error: bool = False) -> bool:
    """
    Returns True on success. On error:
      - logs (if logger provided),
      - raises TucamError if raise_on_error=True,
      - returns False otherwise.
    """
    if is_success(code):
        return True

    msg = f"TUCAM error"
    if context:
        msg += f" during {context}"
    msg += f": {summarize(code)}"

    if logger:
        logger.error(msg)

    if raise_on_error:
        raise TucamError(msg)

    return False

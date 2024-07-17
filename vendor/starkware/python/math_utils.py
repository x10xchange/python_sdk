# Custom import of igcdex to support multiple sympy versions.
try:
    from sympy.core.numbers import igcdex
except (ModuleNotFoundError, ImportError):
    from sympy.core.intfunc import igcdex  # type: ignore[no-redef]


def div_ceil(x, y):
    assert isinstance(x, int) and isinstance(y, int)
    return -((-x) // y)

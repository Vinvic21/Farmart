
from importlib import import_module

__all__ = [
    'auth_bp',
    'animals_bp',
    'cart_bp',
    'orders_bp',
    'payments_bp',
    'admin_bp',
]

_MODULE_MAP = {
    'auth_bp': '.auth',
    'animals_bp': '.animals',
    'cart_bp': '.cart',
    'orders_bp': '.orders',
    'payments_bp': '.payments',
    'admin_bp': '.admin',
}


def __getattr__(name):
    if name in _MODULE_MAP:
        module = import_module(_MODULE_MAP[name], __package__ or __name__)
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
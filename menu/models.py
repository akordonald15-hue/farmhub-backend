"""
Compatibility shim for legacy imports.

The real models live in products.models. Importing them here keeps tests and
older code working without duplicating model definitions.
"""

from products.models import Category, MenuItem

__all__ = ["Category", "MenuItem"]

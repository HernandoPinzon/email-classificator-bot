"""
Módulo de repositorios para persistencia de datos
"""

from .sqlite import SQLiteEmailRepository, InMemoryEmailRepository

__all__ = [
    "SQLiteEmailRepository",
    "InMemoryEmailRepository",
]

"""
Módulo de clasificadores de correos
"""

from .bank import BankEmailClassifier, MockEmailClassifier

__all__ = [
    "BankEmailClassifier",
    "MockEmailClassifier",
]

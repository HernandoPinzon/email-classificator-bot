"""
Módulo de fetchers para obtener correos
"""

from .gmail import GmailFetcher, MockEmailFetcher

__all__ = [
    "GmailFetcher",
    "MockEmailFetcher",
]

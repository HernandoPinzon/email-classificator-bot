#!/usr/bin/env python3
"""
Entry point para ejecutar el procesador de correos.
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import main

if __name__ == "__main__":
    main()

"""
Proveedor de IA para Ollama local
"""

import json
import re
from typing import Dict

from ..core.interfaces import AIProvider
from ..config import OllamaConfig
from ..utils import RequestsHttpClient


class OllamaProvider(AIProvider):
    """Proveedor para Ollama local"""

    def __init__(self, config: OllamaConfig = None, http_client=None,
                 host: str = None, model: str = None):
        """
        Args:
            config: Configuración de Ollama
            http_client: Cliente HTTP inyectable
            host: Host de Ollama (legacy, para compatibilidad)
            model: Modelo a usar (legacy, para compatibilidad)
        """
        if config:
            self.host = config.host
            self.model = config.model
        else:
            self.host = host or "http://localhost:11434"
            self.model = model or "llama3.2"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"Ollama ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Ollama local"""
        try:
            response = self.http_client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '{}')
                return self._parse_response(response_text)
            else:
                raise Exception(f"Ollama error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Error en Ollama: {e}")

    def _parse_response(self, response_text: str) -> Dict:
        """Parsea y limpia la respuesta JSON"""
        response_text = response_text.strip()
        if response_text.startswith('```'):
            response_text = re.sub(r'```json\s*|\s*```', '', response_text)
        return json.loads(response_text)

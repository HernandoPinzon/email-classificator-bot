"""
Proveedor de IA para Cerebras API
"""

import json
from typing import Dict

from ..core.interfaces import AIProvider
from ..config import CerebrasConfig
from ..utils import RequestsHttpClient


class CerebrasProvider(AIProvider):
    """Proveedor para Cerebras API - Hasta 30 llamadas/minuto gratis"""

    def __init__(self, config: CerebrasConfig = None, http_client=None,
                 api_key: str = None, model: str = None):
        if config:
            self.api_key = config.api_key
            self.model = config.model
            self.base_url = config.base_url
        else:
            self.api_key = api_key or ""
            self.model = model or "llama3.1-8b"
            self.base_url = "https://api.cerebras.ai/v1"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"Cerebras ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Cerebras API"""
        try:
            response = self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                raise Exception(f"Cerebras error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Error en Cerebras: {e}")

"""
Proveedor de IA para Groq API
"""

import json
from typing import Dict

from ..core.interfaces import AIProvider
from ..config import GroqConfig
from ..utils import RequestsHttpClient


class GroqProvider(AIProvider):
    """Proveedor para Groq API - Hasta 60 llamadas/minuto gratis"""

    def __init__(self, config: GroqConfig = None, http_client=None,
                 api_key: str = None, model: str = None):
        if config:
            self.api_key = config.api_key
            self.model = config.model
            self.base_url = config.base_url
        else:
            self.api_key = api_key or ""
            self.model = model or "mixtral-8x7b-32768"
            self.base_url = "https://api.groq.com/openai/v1"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"Groq ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Groq API"""
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
                raise Exception(f"Groq error: {response.status_code} - {response.text}")

        except Exception as e:
            raise Exception(f"Error en Groq: {e}")

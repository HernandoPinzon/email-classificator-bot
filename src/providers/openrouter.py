"""
Proveedor de IA para OpenRouter API
"""

import json
from typing import Dict

from ..core.interfaces import AIProvider
from ..config import OpenRouterConfig
from ..utils import RequestsHttpClient


class OpenRouterProvider(AIProvider):
    """Proveedor para OpenRouter - Múltiples modelos con capa gratuita"""

    def __init__(self, config: OpenRouterConfig = None, http_client=None,
                 api_key: str = None, model: str = None):
        if config:
            self.api_key = config.api_key
            self.model = config.model
            self.base_url = config.base_url
        else:
            self.api_key = api_key or ""
            self.model = model or "meta-llama/llama-3.2-3b-instruct:free"
            self.base_url = "https://openrouter.ai/api/v1"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"OpenRouter ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando OpenRouter API"""
        try:
            response = self.http_client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/email-classifier",
                    "X-Title": "Email Classifier"
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
                raise Exception(f"OpenRouter error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Error en OpenRouter: {e}")

"""
Proveedor de IA para Google Gemini API
"""

import json
from typing import Dict

from ..core.interfaces import AIProvider
from ..config import GeminiConfig
from ..utils import RequestsHttpClient


class GeminiProvider(AIProvider):
    """Proveedor para Google Gemini API - Hasta 60 llamadas/minuto gratis"""

    def __init__(self, config: GeminiConfig = None, http_client=None,
                 api_key: str = None, model: str = None):
        if config:
            self.api_key = config.api_key
            self.model = config.model
            self.base_url = config.base_url
        else:
            self.api_key = api_key or ""
            self.model = model or "gemini-1.5-flash"
            self.base_url = "https://generativelanguage.googleapis.com/v1beta"

        self.http_client = http_client or RequestsHttpClient()

    def get_name(self) -> str:
        return f"Gemini ({self.model})"

    def generate(self, prompt: str) -> Dict:
        """Genera respuesta usando Gemini API"""
        try:
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

            response = self.http_client.post(
                url,
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json"
                    }
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['candidates'][0]['content']['parts'][0]['text']
                return json.loads(content)
            else:
                raise Exception(f"Gemini error: {response.status_code}")

        except Exception as e:
            raise Exception(f"Error en Gemini: {e}")

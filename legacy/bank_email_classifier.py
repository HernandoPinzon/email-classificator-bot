"""
Clasificador de correos bancarios personalizado usando Ollama
"""
import json
import re
import logging
import requests
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class BankEmailClassifier:
    """Clasifica correos de bancos y extrae información relevante"""
    
    # Categorías con sus prioridades
    CATEGORIES = {
        'pago_urgente': 'urgent',        # Pagos que debo hacer
        'transferencia': 'normal',       # Transferencias recibidas/hechas
        'movimiento': 'low',             # Movimientos en cuenta
        'extracto': 'low',               # Extractos bancarios
        'factura': 'normal',             # Facturas a pagar
        'confirmacion': 'low',           # Confirmaciones de operaciones
        'anuncio': 'low',                # Anuncios del banco
        'promocion': 'low',              # Promociones
        'notificacion': 'low',           # Notificaciones generales
        'otro': 'low'                    # Otros
    }
    
    def __init__(self, ollama_host: str = "http://localhost:11434", 
                 model: str = "llama3.2:3b"):
        """
        Inicializa el clasificador
        
        Args:
            ollama_host: URL del servidor Ollama
            model: Modelo a usar (recomendado: llama3.2:3b o qwen2.5:7b)
        """
        self.ollama_host = ollama_host
        self.model = model
        logger.info(f"Clasificador inicializado con modelo {model}")
    
    def classify_email(self, subject: str, body: str, sender: str) -> Dict:
        """
        Clasifica un correo y extrae información relevante
        
        Args:
            subject: Asunto del correo
            body: Cuerpo del correo
            sender: Remitente
            
        Returns:
            Diccionario con:
            - category: Categoría del correo
            - priority: urgent, normal, low
            - summary: Resumen breve del correo
            - amount: Monto (si aplica)
            - confidence: Confianza de la clasificación (0-1)
        """
        # Preparar prompt para el LLM
        prompt = self._build_prompt(subject, body, sender)
        
        try:
            # Llamar a Ollama
            response = self._call_ollama(prompt)
            
            # Parsear respuesta
            result = self._parse_llm_response(response)
            
            # Asignar prioridad según categoría
            result['priority'] = self.CATEGORIES.get(result['category'], 'low')
            
            # Extraer monto si no lo hizo el LLM
            if not result.get('amount'):
                result['amount'] = self._extract_amount(subject + " " + body)
            
            logger.info(f"Correo clasificado: {result['category']} - {result['priority']}")
            return result
            
        except Exception as e:
            logger.error(f"Error al clasificar correo: {e}")
            return {
                'category': 'otro',
                'priority': 'low',
                'summary': subject[:100],
                'amount': None,
                'confidence': 0.0
            }
    
    def _build_prompt(self, subject: str, body: str, sender: str) -> str:
        """Construye el prompt para el LLM"""
        
        # Limpiar body (máximo 500 caracteres)
        clean_body = self._clean_text(body)[:500]
        
        categories_list = ", ".join(self.CATEGORIES.keys())
        
        prompt = f"""Eres un asistente experto en clasificar correos bancarios.

Analiza este correo y clasifícalo en UNA de estas categorías:
{categories_list}

Reglas de clasificación:
- pago_urgente: SOLO si es un pago que YO debo hacer (vencimiento de tarjeta, cuota, servicio)
- transferencia: Transferencias recibidas o enviadas
- movimiento: Compras, débitos, movimientos en cuenta
- extracto: Resumen de cuenta, estados de cuenta
- factura: Facturas por pagar
- confirmacion: Confirmación de operaciones ya realizadas
- anuncio: Comunicados del banco
- promocion: Ofertas, promociones
- notificacion: Avisos generales
- otro: Si no encaja en ninguna categoría

Información del correo:
Remitente: {sender}
Asunto: {subject}
Cuerpo: {clean_body}

Responde SOLO en formato JSON (sin markdown, sin explicaciones):
{{
  "category": "nombre_categoria",
  "summary": "resumen muy breve (máximo 50 caracteres)",
  "amount": "monto si hay (ej: $1500, USD 200) o null",
  "confidence": 0.95
}}

Si hay un monto, inclúyelo en el summary. Por ejemplo:
- "Pago de $1,234 en Farmacia"
- "Transferencia de $5,000"
- "Factura de $890 - Luz"
"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """Llama a la API de Ollama"""
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Baja temperatura para más consistencia
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al llamar a Ollama: {e}")
            raise
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parsea la respuesta JSON del LLM"""
        try:
            # Limpiar respuesta (a veces el LLM agrega texto extra)
            response = response.strip()
            
            # Buscar JSON en la respuesta
            json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
            if json_match:
                response = json_match.group(0)
            
            result = json.loads(response)
            
            # Validar categoría
            if result.get('category') not in self.CATEGORIES:
                logger.warning(f"Categoría inválida: {result.get('category')}, usando 'otro'")
                result['category'] = 'otro'
            
            # Asegurar campos requeridos
            return {
                'category': result.get('category', 'otro'),
                'summary': result.get('summary', '')[:100],
                'amount': result.get('amount'),
                'confidence': float(result.get('confidence', 0.7))
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error al parsear respuesta del LLM: {e}\nRespuesta: {response}")
            return {
                'category': 'otro',
                'summary': 'Error en clasificación',
                'amount': None,
                'confidence': 0.0
            }
    
    def _extract_amount(self, text: str) -> Optional[str]:
        """Extrae montos del texto usando regex"""
        # Patrones comunes para montos
        patterns = [
            r'\$\s*[\d,]+\.?\d*',           # $1,234.56
            r'USD\s*[\d,]+\.?\d*',          # USD 1234
            r'MXN\s*[\d,]+\.?\d*',          # MXN 1234
            r'[\d,]+\.?\d*\s*(?:pesos|USD|MXN|dólares)',  # 1234 pesos
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """Limpia texto eliminando HTML y caracteres extraños"""
        # Eliminar HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Eliminar múltiples espacios
        text = re.sub(r'\s+', ' ', text)
        # Eliminar caracteres especiales problemáticos
        text = text.replace('\r', '').replace('\n', ' ')
        return text.strip()
    
    def get_priority_emoji(self, priority: str) -> str:
        """Obtiene emoji según prioridad"""
        emoji_map = {
            'urgent': '🚨',
            'normal': '📬',
            'low': '📭'
        }
        return emoji_map.get(priority, '📧')


# Función auxiliar para crear instancia
def create_classifier(ollama_host: str = None, model: str = None) -> BankEmailClassifier:
    """
    Crea una instancia del clasificador
    
    Args:
        ollama_host: URL del servidor Ollama (por defecto: http://localhost:11434)
        model: Modelo a usar (por defecto: llama3.2:3b)
    """
    import os
    
    host = ollama_host or os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    model_name = model or os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
    
    return BankEmailClassifier(ollama_host=host, model=model_name)

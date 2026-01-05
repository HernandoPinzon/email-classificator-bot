"""
Clasificador especializado para correos bancarios
Identifica prioridades y extrae montos de transacciones
"""

import re
import json
from typing import Dict, Optional, List

from interfaces import EmailClassifier, EmailClassification, AIProvider
from config import ClassifierConfig
from http_client import RequestsHttpClient


class BankEmailClassifier(EmailClassifier):
    """Clasificador especializado para correos bancarios"""

    def __init__(
        self,
        config: ClassifierConfig = None,
        ai_provider: AIProvider = None,
        http_client=None
    ):
        """
        Inicializa el clasificador

        Args:
            config: Configuración del clasificador (keywords, patterns)
            ai_provider: Proveedor de IA para clasificación
            http_client: Cliente HTTP (para modo legacy Ollama directo)
        """
        self.config = config or ClassifierConfig()
        self.ai_provider = ai_provider
        self.http_client = http_client or RequestsHttpClient()

        # Cargar patrones y keywords desde config
        self.amount_patterns = self.config.amount_patterns
        self.urgent_keywords = self.config.urgent_keywords
        self.payment_keywords = self.config.payment_keywords
        self.low_priority_keywords = self.config.low_priority_keywords

        # Cargar listas de remitentes por prioridad
        self.low_priority_senders = [s.lower() for s in (self.config.low_priority_senders or [])]
        self.high_priority_senders = [s.lower() for s in (self.config.high_priority_senders or [])]

    @classmethod
    def with_provider_manager(cls, provider_manager, config: ClassifierConfig = None):
        """
        Factory method para crear clasificador con provider manager.
        """
        return cls(config=config, ai_provider=provider_manager)

    @classmethod
    def with_ollama(cls, host: str = "http://localhost:11434",
                    model: str = "llama3.2", config: ClassifierConfig = None):
        """
        Factory method para crear clasificador con Ollama directo.
        Mantiene compatibilidad con código legacy.
        """
        from ai_providers import OllamaProvider
        provider = OllamaProvider(host=host, model=model)
        return cls(config=config, ai_provider=provider)

    def extract_amount(self, text: str) -> Optional[str]:
        """
        Extrae el monto de una transacción del texto

        Args:
            text: Texto del correo (asunto + cuerpo)

        Returns:
            Monto encontrado o None
        """
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                amount = matches[0].strip()
                if not amount.startswith('$'):
                    amount = f"${amount}"
                return amount

        return None

    def detect_priority_by_sender(self, sender: str) -> Optional[str]:
        """
        Detecta prioridad basándose en el remitente

        Args:
            sender: Dirección de correo del remitente

        Returns:
            'urgente', 'sin_prioridad', o None si no hay coincidencia
        """
        sender_lower = sender.lower()

        # Primero verificar remitentes de alta prioridad
        if any(s in sender_lower for s in self.high_priority_senders):
            return 'urgente'

        # Luego verificar remitentes de baja prioridad
        if any(s in sender_lower for s in self.low_priority_senders):
            return 'sin_prioridad'

        return None

    def detect_priority_by_keywords(self, subject: str, body: str, sender: str = "") -> str:
        """
        Detecta prioridad usando palabras clave y remitente (método rápido sin LLM)

        Args:
            subject: Asunto del correo
            body: Cuerpo del correo
            sender: Remitente del correo

        Returns:
            'urgente', 'normal', o 'sin_prioridad'
        """
        # Primero verificar por remitente (tiene prioridad sobre keywords)
        sender_priority = self.detect_priority_by_sender(sender)
        if sender_priority:
            return sender_priority

        text = f"{subject} {body}".lower()

        if any(keyword in text for keyword in self.urgent_keywords):
            return 'urgente'

        if any(keyword in text for keyword in self.low_priority_keywords):
            return 'sin_prioridad'

        return 'normal'

    def classify_with_llm(self, subject: str, body: str, sender: str = "") -> Dict:
        """
        Clasifica un correo usando el proveedor de IA configurado

        Args:
            subject: Asunto del correo
            body: Cuerpo del correo (primeros 1000 caracteres)
            sender: Remitente del correo

        Returns:
            Diccionario con clasificación del LLM
        """
        body_truncated = body[:1000] if len(body) > 1000 else body

        prompt = f"""Eres un asistente que clasifica correos bancarios en español.

Analiza este correo y responde SOLO con un JSON (sin explicaciones adicionales):

Remitente: {sender}
Asunto: {subject}
Cuerpo: {body_truncated}

Clasifica el correo en:

1. CATEGORÍA (elige una):
   - "pago": Pagos que debo hacer, cargos, domiciliaciones
   - "transferencia": Transferencias recibidas o realizadas
   - "estado_cuenta": Estados de cuenta, resúmenes
   - "movimiento": Movimientos, retiros, depósitos
   - "promocion": Promociones, ofertas, publicidad
   - "notificacion": Notificaciones generales del banco
   - "otro": Otros

2. PRIORIDAD (elige una):
   - "urgente": Requiere acción inmediata (pagos pendientes, verificaciones)
   - "normal": Informativo importante (movimientos, transferencias)
   - "sin_prioridad": No requiere acción (promociones, newsletter)

3. RESUMEN: Una línea describiendo el correo. Si es un pago o transferencia,
   menciona el monto así: "Pago de $X en [lugar]" o "Transferencia de $X"

Responde EXACTAMENTE en este formato JSON:
{{
  "category": "categoria_aqui",
  "priority": "prioridad_aqui",
  "summary": "resumen_aqui",
  "action_required": true/false
}}"""

        try:
            if self.ai_provider:
                return self.ai_provider.generate(prompt)
            else:
                return self._fallback_classification(subject, body, sender)

        except Exception as e:
            print(f"Error clasificando con LLM: {e}")
            return self._fallback_classification(subject, body, sender)

    def _fallback_classification(self, subject: str, body: str, sender: str = "") -> Dict:
        """Clasificación de respaldo cuando el LLM falla"""
        text_lower = f"{subject} {body}".lower()

        if any(kw in text_lower for kw in ['pago', 'cargo', 'compra']):
            category = 'pago'
        elif any(kw in text_lower for kw in ['transferencia', 'depósito']):
            category = 'transferencia'
        elif any(kw in text_lower for kw in ['estado de cuenta', 'resumen']):
            category = 'estado_cuenta'
        elif any(kw in text_lower for kw in ['promoción', 'oferta', 'descuento']):
            category = 'promocion'
        else:
            category = 'notificacion'

        priority = self.detect_priority_by_keywords(subject, body, sender)

        return {
            'category': category,
            'priority': priority,
            'summary': subject[:100],
            'action_required': priority == 'urgente'
        }

    def classify(self, subject: str, body: str, sender: str = "") -> EmailClassification:
        """
        Clasifica un correo completamente

        Args:
            subject: Asunto del correo
            body: Cuerpo del correo
            sender: Remitente

        Returns:
            EmailClassification con toda la información
        """
        llm_result = self.classify_with_llm(subject, body, sender)

        full_text = f"{subject} {body}"
        amount = self.extract_amount(full_text)

        return EmailClassification(
            category=llm_result.get('category', 'otro'),
            priority=llm_result.get('priority', 'normal'),
            summary=llm_result.get('summary', subject),
            amount=amount,
            action_required=llm_result.get('action_required', False)
        )


class MockEmailClassifier(EmailClassifier):
    """
    Clasificador mock para testing.
    Permite configurar respuestas predefinidas.
    """

    def __init__(self):
        self.classifications: Dict[str, EmailClassification] = {}
        self.default_classification = EmailClassification(
            category='notificacion',
            priority='normal',
            summary='Mock classification',
            amount=None,
            action_required=False
        )
        self.calls: List[Dict] = []

    def set_classification(self, subject: str, classification: EmailClassification):
        """Configura una clasificación para un asunto específico"""
        self.classifications[subject] = classification

    def set_default_classification(self, classification: EmailClassification):
        """Configura la clasificación por defecto"""
        self.default_classification = classification

    def classify(self, subject: str, body: str, sender: str = "") -> EmailClassification:
        """Retorna la clasificación configurada o la por defecto"""
        self.calls.append({
            'subject': subject,
            'body': body,
            'sender': sender
        })

        if subject in self.classifications:
            return self.classifications[subject]

        return self.default_classification

    def get_calls(self) -> List[Dict]:
        """Retorna las llamadas realizadas"""
        return self.calls

    def clear(self):
        """Limpia configuraciones y llamadas"""
        self.classifications.clear()
        self.calls.clear()

"""
Clasificador especializado para correos bancarios
Identifica prioridades y extrae montos de transacciones
"""

import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class EmailClassification:
    """Resultado de clasificación de un correo"""
    category: str
    priority: str  # 'urgente', 'normal', 'sin_prioridad'
    summary: str
    amount: Optional[str] = None
    action_required: bool = False


class BankEmailClassifier:
    """Clasificador especializado para correos bancarios"""
    
    # Patrones para detectar montos (pesos mexicanos, dólares, etc.)
    AMOUNT_PATTERNS = [
        r'\$\s*[\d,]+\.?\d{0,2}',  # $1,234.56 o $1234
        r'[\d,]+\.?\d{0,2}\s*(?:pesos|MXN|USD|EUR)',  # 1234.56 pesos
        r'(?:total|monto|importe|cantidad|cargo):\s*\$?\s*[\d,]+\.?\d{0,2}',
    ]
    
    # Palabras clave para identificar correos urgentes
    URGENT_KEYWORDS = [
        'pago pendiente',
        'pago vencido',
        'acción requerida',
        'urgente',
        'importante',
        'verificación requerida',
        'confirma tu',
        'por vencer',
        'último día',
        'fecha límite',
        'cobro próximo',
        'cargo próximo',
        'saldo insuficiente',
        'cuenta bloqueada',
        'suspensión',
    ]
    
    # Palabras clave para pagos/transacciones
    PAYMENT_KEYWORDS = [
        'pago',
        'cargo',
        'compra',
        'transferencia',
        'retiro',
        'depósito',
        'comisión',
        'intereses',
        'domiciliación',
    ]
    
    # Palabras clave para sin prioridad
    LOW_PRIORITY_KEYWORDS = [
        'promoción',
        'oferta',
        'descuento',
        'newsletter',
        'boletín',
        'tips',
        'consejos',
        'beneficios',
        'programa de puntos',
        'invitación',
        'evento',
        'encuesta',
        'noticia',
    ]
    
    def __init__(self, provider_manager=None, ollama_host: str = "http://localhost:11434",
                 model: str = "llama3.2"):
        """
        Inicializa el clasificador

        Args:
            provider_manager: Gestor de proveedores de IA (nuevo - opcional)
            ollama_host: URL del servidor Ollama (legacy - para compatibilidad)
            model: Modelo a usar (legacy - para compatibilidad)
        """
        # Usar el nuevo sistema de proveedores si está disponible
        if provider_manager is not None:
            self.provider_manager = provider_manager
            self.use_provider_manager = True
        else:
            # Modo legacy: solo Ollama
            self.ollama_host = ollama_host
            self.model = model
            self.provider_manager = None
            self.use_provider_manager = False
    
    def extract_amount(self, text: str) -> Optional[str]:
        """
        Extrae el monto de una transacción del texto
        
        Args:
            text: Texto del correo (asunto + cuerpo)
            
        Returns:
            Monto encontrado o None
        """
        text_lower = text.lower()
        
        for pattern in self.AMOUNT_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Retornar el primer monto encontrado, limpiado
                amount = matches[0].strip()
                # Asegurar que tenga el símbolo $
                if not amount.startswith('$'):
                    amount = f"${amount}"
                return amount
        
        return None
    
    def detect_priority_by_keywords(self, subject: str, body: str) -> str:
        """
        Detecta prioridad usando palabras clave (método rápido sin LLM)
        
        Args:
            subject: Asunto del correo
            body: Cuerpo del correo
            
        Returns:
            'urgente', 'normal', o 'sin_prioridad'
        """
        text = f"{subject} {body}".lower()
        
        # Verificar urgente
        if any(keyword in text for keyword in self.URGENT_KEYWORDS):
            return 'urgente'
        
        # Verificar baja prioridad
        if any(keyword in text for keyword in self.LOW_PRIORITY_KEYWORDS):
            return 'sin_prioridad'
        
        # Por defecto, prioridad normal
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
        import requests

        # Truncar el cuerpo si es muy largo
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
            # NUEVO: Usar el gestor de proveedores si está disponible
            if self.use_provider_manager:
                classification = self.provider_manager.generate(prompt)
                return classification

            # LEGACY: Usar Ollama directamente
            else:
                response = requests.post(
                    f"{self.ollama_host}/api/generate",
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

                    # Limpiar respuesta si tiene markdown
                    response_text = response_text.strip()
                    if response_text.startswith('```'):
                        response_text = re.sub(r'```json\s*|\s*```', '', response_text)

                    import json
                    classification = json.loads(response_text)
                    return classification
                else:
                    print(f"⚠️ Error en Ollama: {response.status_code}")
                    return self._fallback_classification(subject, body)

        except Exception as e:
            print(f"⚠️ Error clasificando con LLM: {e}")
            return self._fallback_classification(subject, body)
    
    def _fallback_classification(self, subject: str, body: str) -> Dict:
        """Clasificación de respaldo cuando el LLM falla"""
        text_lower = f"{subject} {body}".lower()
        
        # Categoría básica
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
        
        priority = self.detect_priority_by_keywords(subject, body)
        
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
        # Clasificar con LLM
        llm_result = self.classify_with_llm(subject, body, sender)
        
        # Extraer monto
        full_text = f"{subject} {body}"
        amount = self.extract_amount(full_text)
        
        return EmailClassification(
            category=llm_result.get('category', 'otro'),
            priority=llm_result.get('priority', 'normal'),
            summary=llm_result.get('summary', subject),
            amount=amount,
            action_required=llm_result.get('action_required', False)
        )


# Ejemplo de uso
if __name__ == "__main__":
    classifier = BankEmailClassifier()
    
    # Ejemplo 1: Pago pendiente
    example1 = classifier.classify(
        subject="Recordatorio: Pago de tarjeta vence mañana",
        body="Tu pago mínimo de $2,500.00 vence el 03/01/2026. Realiza tu pago a tiempo.",
        sender="notificaciones@banco.com"
    )
    
    print("Ejemplo 1 - Pago urgente:")
    print(f"  Categoría: {example1.category}")
    print(f"  Prioridad: {example1.priority}")
    print(f"  Resumen: {example1.summary}")
    print(f"  Monto: {example1.amount}")
    print(f"  Acción requerida: {example1.action_required}")
    print()
    
    # Ejemplo 2: Transferencia
    example2 = classifier.classify(
        subject="Transferencia recibida",
        body="Has recibido una transferencia de $15,000.00 en tu cuenta de ahorros.",
        sender="alertas@banco.com"
    )
    
    print("Ejemplo 2 - Transferencia:")
    print(f"  Categoría: {example2.category}")
    print(f"  Prioridad: {example2.priority}")
    print(f"  Resumen: {example2.summary}")
    print(f"  Monto: {example2.amount}")
    print()
    
    # Ejemplo 3: Promoción
    example3 = classifier.classify(
        subject="¡Oferta especial! Crédito pre-aprobado",
        body="Aprovecha tu crédito pre-aprobado de hasta $100,000. Promoción válida hasta fin de mes.",
        sender="promociones@banco.com"
    )
    
    print("Ejemplo 3 - Promoción:")
    print(f"  Categoría: {example3.category}")
    print(f"  Prioridad: {example3.priority}")
    print(f"  Resumen: {example3.summary}")

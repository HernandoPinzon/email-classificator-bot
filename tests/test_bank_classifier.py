"""
Pruebas unitarias para BankEmailClassifier.
"""

import pytest
from src.classifiers import BankEmailClassifier, MockEmailClassifier
from src.providers import MockAIProvider
from src.core import EmailClassification
from src.config import ClassifierConfig


class TestExtractAmount:
    """Pruebas para extracción de montos"""

    def test_extract_amount_with_dollar_sign(self, classifier_config):
        """Extrae monto con símbolo de dólar"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.extract_amount("Tu pago es de $1,234.56")

        assert result == "$1,234.56"

    def test_extract_amount_without_decimals(self, classifier_config):
        """Extrae monto sin decimales"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.extract_amount("Cargo de $5000 en tu cuenta")

        assert result == "$5000"

    def test_extract_amount_with_pesos(self, classifier_config):
        """Extrae monto con palabra 'pesos'"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.extract_amount("Total: 2500.00 pesos")

        assert result == "$2500.00 pesos"

    def test_extract_amount_with_mxn(self, classifier_config):
        """Extrae monto con MXN"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.extract_amount("Monto: 10000 MXN")

        assert result == "$10000 MXN"

    def test_extract_amount_returns_none_when_no_amount(self, classifier_config):
        """Retorna None si no hay monto"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.extract_amount("Este correo no tiene montos")

        assert result is None

    def test_extract_amount_returns_first_match(self, classifier_config):
        """Retorna el primer monto encontrado"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.extract_amount("Pago de $100.00 y cargo de $200.00")

        assert result == "$100.00"


class TestDetectPriorityByKeywords:
    """Pruebas para detección de prioridad por keywords"""

    def test_detect_urgent_priority(self, classifier_config):
        """Detecta prioridad urgente"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.detect_priority_by_keywords(
            subject="URGENTE: Acción requerida",
            body="Por favor revisa tu cuenta"
        )

        assert result == "urgente"

    def test_detect_urgent_with_payment_due(self, classifier_config):
        """Detecta urgente con pago pendiente"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.detect_priority_by_keywords(
            subject="Recordatorio",
            body="Tu pago pendiente debe realizarse hoy"
        )

        assert result == "urgente"

    def test_detect_urgent_with_expires_tomorrow(self, classifier_config):
        """Detecta urgente cuando vence mañana"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.detect_priority_by_keywords(
            subject="Aviso",
            body="Tu tarjeta vence mañana"
        )

        assert result == "urgente"

    def test_detect_low_priority_promo(self, classifier_config):
        """Detecta baja prioridad en promociones"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.detect_priority_by_keywords(
            subject="Promoción especial",
            body="Aprovecha esta oferta única"
        )

        assert result == "sin_prioridad"

    def test_detect_low_priority_newsletter(self, classifier_config):
        """Detecta baja prioridad en newsletter"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.detect_priority_by_keywords(
            subject="Newsletter mensual",
            body="Las noticias del mes"
        )

        assert result == "sin_prioridad"

    def test_detect_normal_priority_default(self, classifier_config):
        """Prioridad normal por defecto"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.detect_priority_by_keywords(
            subject="Confirmación de transferencia",
            body="Tu transferencia fue exitosa"
        )

        assert result == "normal"

    def test_priority_case_insensitive(self, classifier_config):
        """Detección es case insensitive"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier.detect_priority_by_keywords(
            subject="URGENTE",
            body="Mensaje importante"
        )

        assert result == "urgente"


class TestClassifyWithLLM:
    """Pruebas para clasificación con LLM"""

    def test_classify_with_mock_ai_provider(self, classifier_config):
        """Clasifica usando mock de AI provider"""
        mock_provider = MockAIProvider()
        mock_provider.set_default_response({
            "category": "pago",
            "priority": "urgente",
            "summary": "Pago pendiente de tarjeta",
            "action_required": True
        })

        classifier = BankEmailClassifier(
            config=classifier_config,
            ai_provider=mock_provider
        )

        result = classifier.classify_with_llm(
            subject="Pago pendiente",
            body="Tu pago vence mañana",
            sender="banco@test.com"
        )

        assert result["category"] == "pago"
        assert result["priority"] == "urgente"
        assert result["action_required"] is True

    def test_classify_calls_ai_provider(self, classifier_config):
        """Verifica que se llama al AI provider"""
        mock_provider = MockAIProvider()

        classifier = BankEmailClassifier(
            config=classifier_config,
            ai_provider=mock_provider
        )

        classifier.classify_with_llm(
            subject="Test",
            body="Test body",
            sender="test@test.com"
        )

        assert len(mock_provider.get_calls()) == 1
        assert "Test" in mock_provider.get_calls()[0]

    def test_classify_fallback_on_ai_failure(self, classifier_config):
        """Usa fallback cuando AI falla"""
        mock_provider = MockAIProvider()
        mock_provider.set_failure(True, "API Error")

        classifier = BankEmailClassifier(
            config=classifier_config,
            ai_provider=mock_provider
        )

        result = classifier.classify_with_llm(
            subject="Pago de tarjeta",
            body="Realiza tu pago",
            sender="banco@test.com"
        )

        # Fallback debería clasificar como pago
        assert result["category"] == "pago"

    def test_classify_fallback_without_ai_provider(self, classifier_config):
        """Usa fallback cuando no hay AI provider"""
        classifier = BankEmailClassifier(
            config=classifier_config,
            ai_provider=None
        )

        result = classifier.classify_with_llm(
            subject="Transferencia recibida",
            body="Has recibido un depósito",
            sender="banco@test.com"
        )

        assert result["category"] == "transferencia"


class TestFallbackClassification:
    """Pruebas para clasificación de respaldo"""

    def test_fallback_detects_payment(self, classifier_config):
        """Fallback detecta pagos"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier._fallback_classification(
            subject="Pago recibido",
            body="Tu pago fue procesado"
        )

        assert result["category"] == "pago"

    def test_fallback_detects_transfer(self, classifier_config):
        """Fallback detecta transferencias"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier._fallback_classification(
            subject="Transferencia exitosa",
            body="Se realizó la transferencia"
        )

        assert result["category"] == "transferencia"

    def test_fallback_detects_promo(self, classifier_config):
        """Fallback detecta promociones"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier._fallback_classification(
            subject="Promoción especial",
            body="Aprovecha esta oferta"
        )

        assert result["category"] == "promocion"

    def test_fallback_default_notification(self, classifier_config):
        """Fallback usa notificacion por defecto"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier._fallback_classification(
            subject="Información general",
            body="Mensaje del banco"
        )

        assert result["category"] == "notificacion"

    def test_fallback_sets_action_required_for_urgent(self, classifier_config):
        """Fallback marca action_required para urgentes"""
        classifier = BankEmailClassifier(config=classifier_config)

        result = classifier._fallback_classification(
            subject="URGENTE: Pago pendiente",
            body="Realiza tu pago hoy"
        )

        assert result["action_required"] is True
        assert result["priority"] == "urgente"


class TestClassify:
    """Pruebas para método classify completo"""

    def test_classify_returns_email_classification(self, classifier_config):
        """classify retorna EmailClassification"""
        mock_provider = MockAIProvider()
        mock_provider.set_default_response({
            "category": "pago",
            "priority": "normal",
            "summary": "Test summary",
            "action_required": False
        })

        classifier = BankEmailClassifier(
            config=classifier_config,
            ai_provider=mock_provider
        )

        result = classifier.classify(
            subject="Test",
            body="Test body $100.00",
            sender="test@test.com"
        )

        assert isinstance(result, EmailClassification)
        assert result.category == "pago"
        assert result.priority == "normal"
        assert result.amount == "$100.00"

    def test_classify_extracts_amount(self, classifier_config):
        """classify extrae el monto correctamente"""
        mock_provider = MockAIProvider()

        classifier = BankEmailClassifier(
            config=classifier_config,
            ai_provider=mock_provider
        )

        result = classifier.classify(
            subject="Cargo de $2,500.00",
            body="Se realizó un cargo en tu tarjeta",
            sender="banco@test.com"
        )

        assert result.amount == "$2,500.00"

    def test_classify_without_amount(self, classifier_config):
        """classify maneja correos sin monto"""
        mock_provider = MockAIProvider()

        classifier = BankEmailClassifier(
            config=classifier_config,
            ai_provider=mock_provider
        )

        result = classifier.classify(
            subject="Bienvenido",
            body="Gracias por unirte a nuestro banco",
            sender="banco@test.com"
        )

        assert result.amount is None


class TestCustomKeywords:
    """Pruebas con keywords personalizados"""

    def test_custom_urgent_keywords(self):
        """Usa keywords urgentes personalizados"""
        custom_config = ClassifierConfig(
            urgent_keywords=['alerta', 'critico'],
            payment_keywords=[],
            low_priority_keywords=[]
        )

        classifier = BankEmailClassifier(config=custom_config)

        result = classifier.detect_priority_by_keywords(
            subject="ALERTA de seguridad",
            body="Revisa tu cuenta"
        )

        assert result == "urgente"

    def test_custom_low_priority_keywords(self):
        """Usa keywords de baja prioridad personalizados"""
        custom_config = ClassifierConfig(
            urgent_keywords=[],
            payment_keywords=[],
            low_priority_keywords=['spam', 'publicidad']
        )

        classifier = BankEmailClassifier(config=custom_config)

        result = classifier.detect_priority_by_keywords(
            subject="Publicidad del banco",
            body="Nuevos productos"
        )

        assert result == "sin_prioridad"


class TestMockEmailClassifier:
    """Pruebas para el clasificador mock"""

    def test_mock_returns_default_classification(self):
        """Mock retorna clasificación por defecto"""
        mock = MockEmailClassifier()

        result = mock.classify("Test", "Body", "sender@test.com")

        assert result.category == "notificacion"
        assert result.priority == "normal"

    def test_mock_returns_configured_classification(self):
        """Mock retorna clasificación configurada"""
        mock = MockEmailClassifier()
        custom = EmailClassification(
            category="pago",
            priority="urgente",
            summary="Custom",
            amount="$100"
        )
        mock.set_classification("Pago urgente", custom)

        result = mock.classify("Pago urgente", "Body", "sender@test.com")

        assert result.category == "pago"
        assert result.priority == "urgente"

    def test_mock_records_calls(self):
        """Mock registra las llamadas"""
        mock = MockEmailClassifier()

        mock.classify("Subject 1", "Body 1", "sender1@test.com")
        mock.classify("Subject 2", "Body 2", "sender2@test.com")

        calls = mock.get_calls()
        assert len(calls) == 2
        assert calls[0]["subject"] == "Subject 1"
        assert calls[1]["subject"] == "Subject 2"

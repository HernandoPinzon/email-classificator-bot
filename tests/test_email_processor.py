"""
Pruebas de integración para EmailProcessor.
"""

import pytest
from src.core import EmailProcessor
from src.fetchers import MockEmailFetcher
from src.repositories import InMemoryEmailRepository
from src.classifiers import MockEmailClassifier
from src.notifiers import MockNotifier
from src.core import Email, EmailClassification


class TestEmailProcessorInit:
    """Pruebas de inicialización del procesador"""

    def test_init_with_all_dependencies(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, mock_notifier
    ):
        """Inicializa con todas las dependencias"""
        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier,
            notifier=mock_notifier
        )

        assert processor.email_fetcher is not None
        assert processor.repository is not None
        assert processor.classifier is not None
        assert processor.notifier is not None

    def test_init_with_minimal_dependencies(self):
        """Inicializa con dependencias mínimas"""
        processor = EmailProcessor()

        assert processor.email_fetcher is None
        assert processor.repository is None
        assert processor.classifier is None
        assert processor.notifier is None


class TestAuthenticate:
    """Pruebas de autenticación"""

    def test_authenticate_success(self, mock_email_fetcher):
        """Autenticación exitosa"""
        processor = EmailProcessor(email_fetcher=mock_email_fetcher)

        # MockEmailFetcher ya está autenticado en el fixture
        result = processor.authenticate()

        assert result is True

    def test_authenticate_failure(self):
        """Autenticación fallida"""
        fetcher = MockEmailFetcher()
        fetcher.set_auth_failure()

        processor = EmailProcessor(email_fetcher=fetcher)

        result = processor.authenticate()

        assert result is False

    def test_authenticate_without_fetcher(self):
        """Autenticación sin fetcher configurado"""
        processor = EmailProcessor()

        result = processor.authenticate()

        assert result is False


class TestProcessEmails:
    """Pruebas de procesamiento de correos"""

    def test_process_single_email(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, sample_normal_email, normal_classification
    ):
        """Procesa un solo correo"""
        mock_email_fetcher.add_email(sample_normal_email)
        mock_classifier.set_default_classification(normal_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier
        )

        result = processor.process_emails(send_notifications=False)

        assert result['processed'] == 1
        assert result['errors'] == 0

    def test_process_multiple_emails(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, sample_emails, normal_classification
    ):
        """Procesa múltiples correos"""
        for email in sample_emails:
            mock_email_fetcher.add_email(email)

        mock_classifier.set_default_classification(normal_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier
        )

        result = processor.process_emails(send_notifications=False)

        assert result['processed'] == 3

    def test_process_saves_to_repository(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, sample_normal_email, normal_classification
    ):
        """Guarda clasificación en el repositorio"""
        mock_email_fetcher.add_email(sample_normal_email)
        mock_classifier.set_default_classification(normal_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier
        )

        processor.process_emails(send_notifications=False)

        assert in_memory_repository.is_processed(sample_normal_email.id)

    def test_skip_already_processed_emails(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, sample_normal_email, normal_classification
    ):
        """Salta correos ya procesados"""
        mock_email_fetcher.add_email(sample_normal_email)
        mock_classifier.set_default_classification(normal_classification)

        # Marcar como procesado
        in_memory_repository.save_classification(
            sample_normal_email, normal_classification
        )

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier
        )

        result = processor.process_emails(send_notifications=False)

        # No debería procesar ninguno
        assert result['processed'] == 0

    def test_process_empty_inbox(
        self, mock_email_fetcher, in_memory_repository, mock_classifier
    ):
        """Maneja inbox vacío"""
        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier
        )

        result = processor.process_emails()

        assert result['processed'] == 0
        assert result['urgent'] == 0

    def test_process_without_fetcher(self, mock_classifier):
        """Retorna vacío sin fetcher"""
        processor = EmailProcessor(classifier=mock_classifier)

        result = processor.process_emails()

        assert result['processed'] == 0

    def test_process_without_classifier(self, mock_email_fetcher):
        """Retorna vacío sin clasificador"""
        processor = EmailProcessor(email_fetcher=mock_email_fetcher)

        result = processor.process_emails()

        assert result['processed'] == 0


class TestProcessEmailsWithNotifications:
    """Pruebas de procesamiento con notificaciones"""

    def test_sends_notification_for_urgent_email(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, mock_notifier,
        sample_urgent_email, urgent_classification
    ):
        """Envía notificación para correo urgente"""
        mock_email_fetcher.add_email(sample_urgent_email)
        mock_classifier.set_default_classification(urgent_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier,
            notifier=mock_notifier
        )

        result = processor.process_emails(send_notifications=True)

        assert result['urgent'] == 1
        assert len(mock_notifier.alerts) == 1
        assert mock_notifier.alerts[0]['priority'] == 'urgente'

    def test_sends_notification_for_normal_email(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, mock_notifier,
        sample_normal_email, normal_classification
    ):
        """Envía notificación para correo normal"""
        mock_email_fetcher.add_email(sample_normal_email)
        mock_classifier.set_default_classification(normal_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier,
            notifier=mock_notifier
        )

        processor.process_emails(send_notifications=True)

        assert len(mock_notifier.alerts) == 1
        assert mock_notifier.alerts[0]['priority'] == 'normal'

    def test_no_notification_for_low_priority(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, mock_notifier,
        sample_promo_email, promo_classification
    ):
        """No envía notificación para baja prioridad"""
        mock_email_fetcher.add_email(sample_promo_email)
        mock_classifier.set_default_classification(promo_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier,
            notifier=mock_notifier
        )

        processor.process_emails(send_notifications=True)

        assert len(mock_notifier.alerts) == 0

    def test_no_notification_when_disabled(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, mock_notifier,
        sample_urgent_email, urgent_classification
    ):
        """No envía notificación cuando está deshabilitado"""
        mock_email_fetcher.add_email(sample_urgent_email)
        mock_classifier.set_default_classification(urgent_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier,
            notifier=mock_notifier
        )

        processor.process_emails(send_notifications=False)

        assert len(mock_notifier.alerts) == 0

    def test_notification_includes_email_data(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, mock_notifier,
        sample_urgent_email, urgent_classification
    ):
        """Notificación incluye datos del correo"""
        mock_email_fetcher.add_email(sample_urgent_email)
        mock_classifier.set_default_classification(urgent_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier,
            notifier=mock_notifier
        )

        processor.process_emails(send_notifications=True)

        alert = mock_notifier.alerts[0]
        assert alert['subject'] == sample_urgent_email.subject
        assert alert['from'] == sample_urgent_email.sender
        assert alert['category'] == urgent_classification.category
        assert alert['amount'] == urgent_classification.amount


class TestProcessEmailsWithErrors:
    """Pruebas de manejo de errores"""

    def test_continues_on_classification_error(
        self, mock_email_fetcher, in_memory_repository, mock_notifier
    ):
        """Continúa procesando tras error de clasificación"""
        email1 = Email(id="1", subject="Test 1", sender="a@b.com", body="Body 1")
        email2 = Email(id="2", subject="Test 2", sender="a@b.com", body="Body 2")

        mock_email_fetcher.add_email(email1)
        mock_email_fetcher.add_email(email2)

        # Clasificador que falla en el primer email
        classifier = MockEmailClassifier()

        # Configurar para que el segundo tenga clasificación
        classifier.set_classification(
            "Test 2",
            EmailClassification(
                category="notificacion",
                priority="normal",
                summary="Test 2"
            )
        )

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=classifier,
            notifier=mock_notifier
        )

        result = processor.process_emails(send_notifications=False)

        # Ambos deberían ser procesados (el primero con clasificación por defecto)
        assert result['processed'] == 2


class TestDailySummary:
    """Pruebas de resumen diario"""

    def test_send_daily_summary_without_notifier(self, in_memory_repository):
        """Retorna False sin notificador"""
        processor = EmailProcessor(repository=in_memory_repository)

        result = processor.send_daily_summary()

        assert result is False

    def test_send_daily_summary_without_repository(self, mock_notifier):
        """Retorna False sin repositorio"""
        processor = EmailProcessor(notifier=mock_notifier)

        result = processor.send_daily_summary()

        assert result is False

    def test_send_daily_summary_no_emails_today(
        self, in_memory_repository, mock_notifier
    ):
        """Retorna False si no hay correos hoy"""
        processor = EmailProcessor(
            repository=in_memory_repository,
            notifier=mock_notifier
        )

        result = processor.send_daily_summary()

        assert result is False

    def test_send_daily_summary_success(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, mock_notifier,
        sample_urgent_email, urgent_classification
    ):
        """Envía resumen diario exitosamente"""
        # Primero procesar un correo para que haya datos
        mock_email_fetcher.add_email(sample_urgent_email)
        mock_classifier.set_default_classification(urgent_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier,
            notifier=mock_notifier
        )

        processor.process_emails(send_notifications=False)

        # Ahora enviar resumen
        result = processor.send_daily_summary()

        assert result is True
        assert len(mock_notifier.summaries) == 1

    def test_daily_summary_includes_stats(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, mock_notifier, sample_emails
    ):
        """Resumen diario incluye estadísticas correctas"""
        # Agregar correos con diferentes prioridades
        for email in sample_emails:
            mock_email_fetcher.add_email(email)

        # Clasificar cada uno con diferente prioridad
        classifications = [
            EmailClassification(category="pago", priority="urgente", summary="Urgente"),
            EmailClassification(category="transferencia", priority="normal", summary="Normal"),
            EmailClassification(category="promocion", priority="sin_prioridad", summary="Promo"),
        ]

        classifier = MockEmailClassifier()
        for email, classification in zip(sample_emails, classifications):
            classifier.set_classification(email.subject, classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=classifier,
            notifier=mock_notifier
        )

        processor.process_emails(send_notifications=False)
        processor.send_daily_summary()

        summary = mock_notifier.summaries[0]
        assert summary['total_emails'] == 3
        assert len(summary['urgent']) == 1
        assert len(summary['normal']) == 1
        assert len(summary['low_priority']) == 1


class TestProcessorWithoutOptionalDependencies:
    """Pruebas de procesador sin dependencias opcionales"""

    def test_process_without_repository(
        self, mock_email_fetcher, mock_classifier,
        sample_normal_email, normal_classification
    ):
        """Procesa sin repositorio (no guarda)"""
        mock_email_fetcher.add_email(sample_normal_email)
        mock_classifier.set_default_classification(normal_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            classifier=mock_classifier
        )

        result = processor.process_emails(send_notifications=False)

        # Debería procesar sin error
        assert result['processed'] == 1

    def test_process_without_notifier(
        self, mock_email_fetcher, in_memory_repository,
        mock_classifier, sample_urgent_email, urgent_classification
    ):
        """Procesa sin notificador"""
        mock_email_fetcher.add_email(sample_urgent_email)
        mock_classifier.set_default_classification(urgent_classification)

        processor = EmailProcessor(
            email_fetcher=mock_email_fetcher,
            repository=in_memory_repository,
            classifier=mock_classifier
        )

        result = processor.process_emails(send_notifications=True)

        # Debería procesar sin error aunque pida notificaciones
        assert result['processed'] == 1
        assert result['urgent'] == 0  # No cuenta como notificado

"""
Procesador principal de correos
Integra Gmail API, clasificación con LLM y notificaciones Telegram
"""

from datetime import datetime
from typing import List, Dict, Optional

from interfaces import (
    EmailFetcher, EmailRepository, Notifier, EmailClassifier,
    Email, EmailClassification
)
from config import AppConfig, load_config_from_env, DatabaseConfig, TelegramConfig
from repositories import SQLiteEmailRepository
from email_fetchers import GmailFetcher
from telegram_notifier import TelegramNotifier
from bank_classifier import BankEmailClassifier
from ai_providers import create_provider_from_config


class EmailProcessor:
    """Procesador principal de correos bancarios"""

    def __init__(
        self,
        email_fetcher: EmailFetcher = None,
        repository: EmailRepository = None,
        classifier: EmailClassifier = None,
        notifier: Notifier = None,
        config: AppConfig = None
    ):
        """
        Inicializa el procesador con dependencias inyectables.

        Args:
            email_fetcher: Servicio para obtener correos (Gmail, mock, etc.)
            repository: Repositorio para persistencia
            classifier: Clasificador de correos
            notifier: Servicio de notificaciones
            config: Configuración de la aplicación
        """
        self.config = config
        self._email_fetcher = email_fetcher
        self._repository = repository
        self._classifier = classifier
        self._notifier = notifier

    @classmethod
    def create_default(cls, config: AppConfig = None) -> 'EmailProcessor':
        """
        Factory method para crear un procesador con la configuración por defecto.
        Carga configuración desde .env si no se proporciona.
        """
        if config is None:
            config = load_config_from_env()

        repository = SQLiteEmailRepository(config.database)
        repository.init_database()

        email_fetcher = GmailFetcher(config.gmail)

        provider_manager = create_provider_from_config(config.ai_provider)
        classifier = BankEmailClassifier.with_provider_manager(
            provider_manager,
            config.classifier
        )

        notifier = None
        if config.telegram.bot_token and config.telegram.chat_id:
            try:
                notifier = TelegramNotifier(config.telegram)
            except Exception as e:
                print(f"Telegram no configurado: {e}")

        return cls(
            email_fetcher=email_fetcher,
            repository=repository,
            classifier=classifier,
            notifier=notifier,
            config=config
        )

    @property
    def email_fetcher(self) -> Optional[EmailFetcher]:
        return self._email_fetcher

    @property
    def repository(self) -> Optional[EmailRepository]:
        return self._repository

    @property
    def classifier(self) -> Optional[EmailClassifier]:
        return self._classifier

    @property
    def notifier(self) -> Optional[Notifier]:
        return self._notifier

    def authenticate(self) -> bool:
        """
        Autentica con el servicio de correo.

        Returns:
            True si la autenticación fue exitosa
        """
        if not self._email_fetcher:
            print("Email fetcher no configurado")
            return False

        result = self._email_fetcher.authenticate()
        if result:
            print("Autenticación exitosa")
        else:
            print("Error en autenticación")
        return result

    def process_emails(self, send_notifications: bool = True) -> Dict:
        """
        Procesa correos del día anterior hasta ahora.

        El bot está diseñado para ejecutarse en la mañana temprano y analizar
        TODOS los correos desde el día anterior hasta la hora de ejecución,
        sin importar si están leídos o no.

        Args:
            send_notifications: Si True, envía notificaciones

        Returns:
            Dict con estadísticas del procesamiento
        """
        if not self._email_fetcher or not self._classifier:
            print("Falta inicializar email fetcher o clasificador")
            return {'processed': 0, 'urgent': 0, 'errors': 0}

        # Obtener correos desde ayer hasta ahora (leídos y no leídos)
        emails = self._email_fetcher.get_emails(since_yesterday=True)

        if not emails:
            print("No hay correos en el período (ayer hasta ahora)")
            return {'processed': 0, 'urgent': 0, 'errors': 0}

        print(f"Encontrados {len(emails)} correos (ayer hasta ahora)")

        processed_count = 0
        urgent_count = 0
        error_count = 0

        for email in emails:
            if self._repository and self._repository.is_processed(email.id):
                continue

            print(f"\nProcesando: {email.subject[:50]}...")

            try:
                classification = self._classifier.classify(
                    email.subject,
                    email.body,
                    email.sender
                )

                print(f"   Categoría: {classification.category}")
                print(f"   Prioridad: {classification.priority}")
                print(f"   Resumen: {classification.summary}")
                if classification.amount:
                    print(f"   Monto: {classification.amount}")

                if self._repository:
                    self._repository.save_classification(email, classification)

                processed_count += 1

                if send_notifications and self._notifier:
                    if classification.priority in ['urgente', 'normal']:
                        if classification.priority == 'urgente':
                            urgent_count += 1

                        email_data = {
                            'subject': email.subject,
                            'from': email.sender,
                            'category': classification.category,
                            'priority': classification.priority,
                            'summary': classification.summary,
                            'amount': classification.amount
                        }

                        self._notifier.send_email_alert(email_data)

            except Exception as e:
                print(f"Error procesando correo {email.id}: {e}")
                error_count += 1

        print(f"\nProcesados {processed_count} correos nuevos")
        if urgent_count > 0:
            print(f"{urgent_count} correos urgentes notificados")

        return {
            'processed': processed_count,
            'urgent': urgent_count,
            'errors': error_count
        }

    def send_daily_summary(self) -> bool:
        """
        Envía resumen diario.

        Returns:
            True si se envió correctamente
        """
        if not self._notifier:
            print("Notificador no configurado")
            return False

        if not self._repository:
            print("Repositorio no configurado")
            return False

        today = datetime.now().strftime('%Y-%m-%d')

        rows = self._repository.get_daily_stats(today)

        if not rows:
            print("No hay correos hoy para resumir")
            return False

        urgent = []
        normal = []
        low_priority = []

        for row in rows:
            email_info = {
                'subject': row['subject'],
                'summary': row['summary'] or row['subject'],
                'amount': row['amount']
            }

            if row['priority'] == 'urgente':
                urgent.append(email_info)
            elif row['priority'] == 'normal':
                normal.append(email_info)
            else:
                low_priority.append(email_info)

        summary_data = {
            'date': datetime.now().strftime('%d/%m/%Y'),
            'total_emails': len(rows),
            'urgent': urgent,
            'normal': normal,
            'low_priority': low_priority
        }

        result = self._notifier.send_daily_summary(summary_data)

        if result:
            print("Resumen diario enviado")
        else:
            print("Error enviando resumen diario")

        return result


def main():
    """Función principal para ejecutar el procesador"""
    import sys

    processor = EmailProcessor.create_default()

    if not processor.authenticate():
        sys.exit(1)

    print("\n" + "=" * 50)
    print("Procesando correos...")
    print("=" * 50)

    processor.process_emails()

    print("\n" + "=" * 50)
    print("Enviando resumen diario...")
    print("=" * 50)

    processor.send_daily_summary()


if __name__ == "__main__":
    main()

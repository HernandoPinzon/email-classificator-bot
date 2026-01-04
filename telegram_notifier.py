"""
Módulo de notificaciones para Telegram
Envía alertas de correos importantes y resumen diario
"""

from typing import List, Dict, Optional
from datetime import datetime

from interfaces import Notifier, HttpResponse
from config import TelegramConfig
from http_client import RequestsHttpClient


class TelegramConfigError(Exception):
    """Error de configuración de Telegram"""
    pass


class TelegramNotifier(Notifier):
    """Gestor de notificaciones a Telegram"""

    def __init__(self, config: TelegramConfig, http_client=None, validate: bool = True):
        """
        Inicializa el notificador de Telegram

        Args:
            config: Configuración de Telegram
            http_client: Cliente HTTP (inyectable para testing)
            validate: Si True, valida que las credenciales no estén vacías

        Raises:
            TelegramConfigError: Si las credenciales están vacías y validate=True
        """
        if validate:
            if not config.bot_token or not config.bot_token.strip():
                raise TelegramConfigError(
                    "TELEGRAM_BOT_TOKEN no configurado. "
                    "Obtén un token de @BotFather en Telegram."
                )
            if not config.chat_id or not config.chat_id.strip():
                raise TelegramConfigError(
                    "TELEGRAM_CHAT_ID no configurado. "
                    "Usa @userinfobot en Telegram para obtener tu chat ID."
                )

        self.bot_token = config.bot_token
        self.chat_id = config.chat_id
        self.api_url = f"{config.api_url}/bot{config.bot_token}"
        self.http_client = http_client or RequestsHttpClient(timeout=10)
        self._configured = bool(config.bot_token and config.chat_id)

    @property
    def is_configured(self) -> bool:
        """Retorna True si el notificador está configurado correctamente"""
        return self._configured

    @classmethod
    def from_credentials(cls, bot_token: str, chat_id: str, http_client=None):
        """
        Factory method para crear notificador desde credenciales directas.
        Mantiene compatibilidad con código existente.
        """
        config = TelegramConfig(bot_token=bot_token, chat_id=chat_id)
        return cls(config, http_client)

    def send_message(self, message: str, parse_mode: str = "HTML",
                     silent: bool = False) -> bool:
        """
        Envía un mensaje a Telegram

        Args:
            message: Texto del mensaje
            parse_mode: Formato del mensaje (HTML o Markdown)
            silent: Si True, envía sin notificación sonora

        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_notification': silent
            }

            response = self.http_client.post(url, data=data)

            if response.status_code == 200:
                result = response.json()
                return result.get('ok', False)
            return False

        except Exception as e:
            print(f"Error enviando mensaje a Telegram: {e}")
            return False

    def send_email_alert(self, email_data: Dict) -> bool:
        """
        Envía alerta de correo (implementación de Notifier)
        """
        return self.send_urgent_email_alert(email_data)

    def send_urgent_email_alert(self, email_data: Dict) -> bool:
        """
        Envía alerta de correo urgente

        Args:
            email_data: Diccionario con información del correo
                {
                    'subject': str,
                    'from': str,
                    'category': str,
                    'priority': str,
                    'summary': str,
                    'amount': Optional[str]
                }
        """
        emoji_map = {
            'urgente': '🚨',
            'importante': '⚠️',
            'normal': '📧'
        }

        priority = email_data.get('priority', 'normal').lower()
        emoji = emoji_map.get(priority, '📧')

        message = f"{emoji} <b>CORREO {priority.upper()}</b>\n\n"
        message += f"<b>De:</b> {email_data.get('from', 'Desconocido')}\n"
        message += f"<b>Asunto:</b> {email_data.get('subject', 'Sin asunto')}\n"

        if email_data.get('amount'):
            message += f"<b>💰 Monto:</b> {email_data['amount']}\n"

        message += f"\n<b>📝 Resumen:</b>\n{email_data.get('summary', 'Sin resumen')}"

        silent = priority not in ['urgente', 'importante']

        return self.send_message(message, silent=silent)

    def send_daily_summary(self, summary_data: Dict) -> bool:
        """
        Envía resumen diario de correos

        Args:
            summary_data: Diccionario con estadísticas del día
                {
                    'total_emails': int,
                    'urgent': List[Dict],
                    'normal': List[Dict],
                    'low_priority': List[Dict],
                    'date': str
                }
        """
        date = summary_data.get('date', datetime.now().strftime('%d/%m/%Y'))
        total = summary_data.get('total_emails', 0)

        message = f"📊 <b>RESUMEN DIARIO - {date}</b>\n"
        message += f"{'=' * 30}\n\n"
        message += f"📬 Total de correos procesados: {total}\n\n"

        urgent = summary_data.get('urgent', [])
        if urgent:
            message += f"🚨 <b>URGENTES ({len(urgent)}):</b>\n"
            for email in urgent[:5]:
                subject = email.get('summary', email.get('subject', 'Sin asunto'))
                message += f"  • {subject}\n"
            if len(urgent) > 5:
                message += f"  ... y {len(urgent) - 5} más\n"
            message += "\n"

        normal = summary_data.get('normal', [])
        if normal:
            message += f"📧 <b>Normales ({len(normal)}):</b>\n"
            for email in normal[:3]:
                subject = email.get('summary', email.get('subject', 'Sin asunto'))
                message += f"  • {subject}\n"
            if len(normal) > 3:
                message += f"  ... y {len(normal) - 3} más\n"
            message += "\n"

        low = summary_data.get('low_priority', [])
        if low:
            message += f"📭 Sin prioridad: {len(low)} correos\n"

        return self.send_message(message, silent=True)

    def test_connection(self) -> bool:
        """
        Prueba la conexión con Telegram

        Returns:
            True si la conexión es exitosa
        """
        test_message = "✅ Conexión con Telegram establecida correctamente"
        return self.send_message(test_message)


class MockNotifier(Notifier):
    """
    Notificador mock para testing.
    Registra todos los mensajes enviados sin hacer llamadas reales.
    """

    def __init__(self):
        self.messages: List[str] = []
        self.alerts: List[Dict] = []
        self.summaries: List[Dict] = []
        self.connection_works = True

    def send_message(self, message: str, silent: bool = False) -> bool:
        """Registra el mensaje"""
        self.messages.append({'text': message, 'silent': silent})
        return self.connection_works

    def send_email_alert(self, email_data: Dict) -> bool:
        """Registra la alerta"""
        self.alerts.append(email_data)
        return self.connection_works

    def send_daily_summary(self, summary_data: Dict) -> bool:
        """Registra el resumen"""
        self.summaries.append(summary_data)
        return self.connection_works

    def test_connection(self) -> bool:
        """Retorna el estado configurado"""
        return self.connection_works

    def set_connection_failure(self):
        """Configura para simular fallo de conexión"""
        self.connection_works = False

    def clear(self):
        """Limpia todos los registros"""
        self.messages.clear()
        self.alerts.clear()
        self.summaries.clear()
        self.connection_works = True

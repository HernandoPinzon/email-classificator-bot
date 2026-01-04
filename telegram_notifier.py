"""
Módulo de notificaciones para Telegram
Envía alertas de correos importantes y resumen diario
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import os


class TelegramNotifier:
    """Gestor de notificaciones a Telegram"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Inicializa el notificador de Telegram
        
        Args:
            bot_token: Token del bot de Telegram (de @BotFather)
            chat_id: ID del chat donde enviar mensajes
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, message: str, parse_mode: str = "HTML", 
                    disable_notification: bool = False) -> bool:
        """
        Envía un mensaje a Telegram
        
        Args:
            message: Texto del mensaje
            parse_mode: Formato del mensaje (HTML o Markdown)
            disable_notification: Si True, envía sin notificación sonora
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_notification': disable_notification
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('ok', False)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error enviando mensaje a Telegram: {e}")
            return False
    
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
        
        # No notificación sonora para prioridad normal o baja
        silent = priority not in ['urgente', 'importante']
        
        return self.send_message(message, disable_notification=silent)
    
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
        message += f"{'='*30}\n\n"
        message += f"📬 Total de correos procesados: {total}\n\n"
        
        # Correos urgentes
        urgent = summary_data.get('urgent', [])
        if urgent:
            message += f"🚨 <b>URGENTES ({len(urgent)}):</b>\n"
            for email in urgent[:5]:  # Máximo 5
                subject = email.get('summary', email.get('subject', 'Sin asunto'))
                message += f"  • {subject}\n"
            if len(urgent) > 5:
                message += f"  ... y {len(urgent) - 5} más\n"
            message += "\n"
        
        # Correos normales
        normal = summary_data.get('normal', [])
        if normal:
            message += f"📧 <b>Normales ({len(normal)}):</b>\n"
            for email in normal[:3]:  # Máximo 3
                subject = email.get('summary', email.get('subject', 'Sin asunto'))
                message += f"  • {subject}\n"
            if len(normal) > 3:
                message += f"  ... y {len(normal) - 3} más\n"
            message += "\n"
        
        # Correos de baja prioridad
        low = summary_data.get('low_priority', [])
        if low:
            message += f"📭 Sin prioridad: {len(low)} correos\n"
        
        return self.send_message(message, disable_notification=True)
    
    def test_connection(self) -> bool:
        """
        Prueba la conexión con Telegram
        
        Returns:
            True si la conexión es exitosa
        """
        test_message = "✅ Conexión con Telegram establecida correctamente"
        return self.send_message(test_message)


def test_telegram_config():
    """Función de prueba para verificar configuración de Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("❌ Error: Variables TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID no configuradas")
        print("\nConfigura las variables en tu archivo .env:")
        print("TELEGRAM_BOT_TOKEN=tu_token_aquí")
        print("TELEGRAM_CHAT_ID=tu_chat_id_aquí")
        return False
    
    notifier = TelegramNotifier(bot_token, chat_id)
    
    print("🔄 Probando conexión con Telegram...")
    if notifier.test_connection():
        print("✅ ¡Conexión exitosa! Revisa tu Telegram")
        
        # Enviar un ejemplo de correo urgente
        print("\n📧 Enviando ejemplo de correo urgente...")
        example_email = {
            'subject': 'Pago pendiente - Tarjeta de crédito',
            'from': 'banco@ejemplo.com',
            'category': 'Pago',
            'priority': 'urgente',
            'summary': 'Pago de $5,432.00 en Amazon',
            'amount': '$5,432.00'
        }
        notifier.send_urgent_email_alert(example_email)
        
        # Enviar ejemplo de resumen diario
        print("📊 Enviando ejemplo de resumen diario...")
        example_summary = {
            'date': datetime.now().strftime('%d/%m/%Y'),
            'total_emails': 15,
            'urgent': [
                {'summary': 'Pago de $5,432.00 en Amazon'},
                {'summary': 'Transferencia de $10,000.00 pendiente'},
            ],
            'normal': [
                {'summary': 'Estado de cuenta diciembre'},
                {'summary': 'Confirmación de transferencia'},
                {'summary': 'Movimiento en cuenta de ahorros'},
            ],
            'low_priority': [
                {'summary': 'Promociones bancarias'},
                {'summary': 'Newsletter del banco'},
            ]
        }
        notifier.send_daily_summary(example_summary)
        
        print("\n✅ Prueba completada. Revisa tu Telegram!")
        return True
    else:
        print("❌ Error al conectar con Telegram")
        print("Verifica que el token y chat_id sean correctos")
        return False


if __name__ == "__main__":
    test_telegram_config()

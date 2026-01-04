#!/usr/bin/env python3
"""
Gmail Bank Classifier - Clasificador automático de correos bancarios
Integra Gmail API + Ollama + Telegram
"""
import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv
import sqlite3

# Importar módulos propios
from bank_email_classifier import create_classifier
from telegram_notifier import create_telegram_notifier

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_classifier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GmailBankClassifier:
    """Clase principal que coordina todo el proceso"""
    
    def __init__(self, dry_run: bool = False):
        """
        Inicializa el clasificador
        
        Args:
            dry_run: Si es True, no aplica cambios ni envía notificaciones
        """
        load_dotenv()
        
        self.dry_run = dry_run
        self.db_path = os.getenv('DATABASE_PATH', './gmail_classifier.db')
        
        # Inicializar componentes
        logger.info("Inicializando componentes...")
        self.classifier = create_classifier()
        self.telegram = create_telegram_notifier()
        
        # Inicializar base de datos
        self._init_database()
        
        logger.info("Clasificador inicializado correctamente")
    
    def _init_database(self):
        """Inicializa la base de datos SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_emails (
                email_id TEXT PRIMARY KEY,
                subject TEXT,
                sender TEXT,
                category TEXT,
                priority TEXT,
                summary TEXT,
                amount TEXT,
                processed_at TIMESTAMP,
                notified BOOLEAN DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                date TEXT PRIMARY KEY,
                total_emails INTEGER,
                urgent_count INTEGER,
                normal_count INTEGER,
                low_count INTEGER,
                sent_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada")
    
    def process_emails(self, max_emails: int = 50):
        """
        Procesa correos nuevos de Gmail
        
        Args:
            max_emails: Número máximo de correos a procesar
        """
        logger.info(f"Procesando hasta {max_emails} correos...")
        
        # Aquí iría la integración con Gmail API
        # Por ahora simularemos con datos de ejemplo
        
        # TODO: Integrar con gmail-llm-labeler para obtener correos reales
        # from email_labeler import EmailProcessor
        # processor = EmailProcessor()
        # emails = processor.get_unread_emails(max_results=max_emails)
        
        # Simulación temporal para testing
        emails = self._get_sample_emails()
        
        urgent_emails = []
        normal_emails = []
        low_emails = []
        
        for email in emails:
            # Verificar si ya fue procesado
            if self._is_processed(email['id']):
                logger.info(f"Email {email['id']} ya procesado, saltando...")
                continue
            
            # Clasificar email
            logger.info(f"Clasificando: {email['subject']}")
            classification = self.classifier.classify_email(
                subject=email['subject'],
                body=email['body'],
                sender=email['sender']
            )
            
            # Agregar info adicional
            email_data = {
                **email,
                **classification
            }
            
            # Guardar en BD
            self._save_processed_email(email_data)
            
            # Categorizar por prioridad
            if classification['priority'] == 'urgent':
                urgent_emails.append(email_data)
            elif classification['priority'] == 'normal':
                normal_emails.append(email_data)
            else:
                low_emails.append(email_data)
        
        # Enviar notificaciones de urgentes inmediatamente
        if urgent_emails and not self.dry_run:
            logger.info(f"Enviando notificación de {len(urgent_emails)} correos urgentes")
            self.telegram.send_urgent_notification(urgent_emails)
        
        # Resumen del procesamiento
        logger.info(f"""
        Procesamiento completado:
        - Urgentes: {len(urgent_emails)}
        - Normales: {len(normal_emails)}
        - Baja prioridad: {len(low_emails)}
        """)
        
        return {
            'urgent': urgent_emails,
            'normal': normal_emails,
            'low_priority': low_emails
        }
    
    def send_daily_summary(self):
        """Envía el resumen diario a Telegram"""
        logger.info("Generando resumen diario...")
        
        # Obtener estadísticas del día
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Contar por prioridad
        cursor.execute('''
            SELECT priority, COUNT(*) 
            FROM processed_emails 
            WHERE DATE(processed_at) = ?
            GROUP BY priority
        ''', (today,))
        
        priority_counts = dict(cursor.fetchall())
        
        # Contar por categoría
        cursor.execute('''
            SELECT category, COUNT(*) 
            FROM processed_emails 
            WHERE DATE(processed_at) = ?
            GROUP BY category
        ''', (today,))
        
        category_counts = dict(cursor.fetchall())
        
        # Obtener urgentes del día
        cursor.execute('''
            SELECT subject, summary, category, amount
            FROM processed_emails 
            WHERE DATE(processed_at) = ? AND priority = 'urgent'
            ORDER BY processed_at DESC
        ''', (today,))
        
        urgent_emails = [
            {
                'subject': row[0],
                'summary': row[1],
                'category': row[2],
                'amount': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        # Preparar resumen
        summary_data = {
            'total': sum(priority_counts.values()),
            'urgent': urgent_emails,
            'normal': [],  # No los incluimos en el resumen
            'low_priority': [],
            'categories': category_counts
        }
        
        # Enviar a Telegram
        if not self.dry_run and summary_data['total'] > 0:
            success = self.telegram.send_daily_summary(summary_data)
            
            if success:
                # Registrar envío
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO daily_summaries 
                    (date, total_emails, urgent_count, normal_count, low_count, sent_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    today,
                    summary_data['total'],
                    len(urgent_emails),
                    priority_counts.get('normal', 0),
                    priority_counts.get('low', 0),
                    datetime.now()
                ))
                conn.commit()
                conn.close()
                logger.info("Resumen diario enviado correctamente")
            else:
                logger.error("Error al enviar resumen diario")
        else:
            logger.info("Modo dry-run o sin correos para resumir")
    
    def _is_processed(self, email_id: str) -> bool:
        """Verifica si un correo ya fue procesado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM processed_emails WHERE email_id = ?', (email_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def _save_processed_email(self, email_data: Dict):
        """Guarda un correo procesado en la BD"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO processed_emails
            (email_id, subject, sender, category, priority, summary, amount, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            email_data['id'],
            email_data['subject'],
            email_data['sender'],
            email_data['category'],
            email_data['priority'],
            email_data['summary'],
            email_data.get('amount'),
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
    
    def _get_sample_emails(self) -> List[Dict]:
        """Genera correos de ejemplo para testing"""
        return [
            {
                'id': 'msg_001',
                'subject': 'Pago mínimo de tu tarjeta Banamex vence en 3 días',
                'body': 'Tu pago mínimo de $1,234.56 vence el 05/01/2026',
                'sender': 'notificaciones@banamex.com'
            },
            {
                'id': 'msg_002',
                'subject': 'Transferencia recibida por $5,000.00',
                'body': 'Has recibido una transferencia SPEI por $5,000.00 de Juan Pérez',
                'sender': 'alertas@santander.com'
            },
            {
                'id': 'msg_003',
                'subject': 'Compra aprobada en Amazon',
                'body': 'Se aprobó tu compra por $890.50 en Amazon MX',
                'sender': 'notificaciones@bbva.com'
            },
            {
                'id': 'msg_004',
                'subject': 'Tu estado de cuenta está disponible',
                'body': 'Ya puedes consultar tu estado de cuenta del periodo 01/12 al 31/12',
                'sender': 'bancomer@bbva.com'
            }
        ]
    
    def test_setup(self):
        """Prueba la configuración del sistema"""
        logger.info("Probando configuración...")
        
        print("\n=== TEST DE CONFIGURACIÓN ===\n")
        
        # Test Ollama
        print("1. Probando conexión con Ollama...")
        try:
            test_result = self.classifier.classify_email(
                subject="Test de conexión",
                body="Este es un correo de prueba",
                sender="test@example.com"
            )
            print(f"   ✅ Ollama funciona - Resultado: {test_result['category']}")
        except Exception as e:
            print(f"   ❌ Error con Ollama: {e}")
        
        # Test Telegram
        print("\n2. Probando conexión con Telegram...")
        if self.telegram.test_connection():
            print("   ✅ Telegram funciona - Revisa tu chat")
        else:
            print("   ❌ Error con Telegram - Verifica tu token y chat_id")
        
        # Test Base de datos
        print("\n3. Probando base de datos...")
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            print(f"   ✅ Base de datos OK - {self.db_path}")
        except Exception as e:
            print(f"   ❌ Error con BD: {e}")
        
        print("\n=== FIN DEL TEST ===\n")


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Clasificador de correos bancarios con Ollama y Telegram')
    parser.add_argument('--dry-run', action='store_true', help='Ejecutar sin aplicar cambios')
    parser.add_argument('--test', action='store_true', help='Probar configuración')
    parser.add_argument('--daily-summary', action='store_true', help='Enviar resumen diario')
    parser.add_argument('--max-emails', type=int, default=50, help='Máximo de correos a procesar')
    
    args = parser.parse_args()
    
    try:
        classifier = GmailBankClassifier(dry_run=args.dry_run)
        
        if args.test:
            classifier.test_setup()
        elif args.daily_summary:
            classifier.send_daily_summary()
        else:
            classifier.process_emails(max_emails=args.max_emails)
            
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

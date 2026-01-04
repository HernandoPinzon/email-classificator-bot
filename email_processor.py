"""
Procesador principal de correos
Integra Gmail API, clasificación con LLM y notificaciones Telegram
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

from bank_classifier import BankEmailClassifier, EmailClassification
from telegram_notifier import TelegramNotifier


# Alcances de Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


class EmailProcessor:
    """Procesador principal de correos bancarios"""
    
    def __init__(self, config_dir: str = "./config", db_path: str = "./emails.db"):
        """
        Inicializa el procesador
        
        Args:
            config_dir: Directorio donde están credentials.json y token.json
            db_path: Ruta a la base de datos SQLite
        """
        self.config_dir = Path(config_dir)
        self.db_path = db_path
        
        # Componentes
        self.gmail_service = None
        self.classifier = None
        self.notifier = None
        
        # Inicializar base de datos
        self._init_database()
    
    def _init_database(self):
        """Crea las tablas necesarias en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de correos procesados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gmail_id TEXT UNIQUE NOT NULL,
                subject TEXT,
                sender TEXT,
                category TEXT,
                priority TEXT,
                summary TEXT,
                amount TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notified BOOLEAN DEFAULT 0
            )
        ''')
        
        # Tabla de métricas diarias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                total_emails INTEGER DEFAULT 0,
                urgent_count INTEGER DEFAULT 0,
                normal_count INTEGER DEFAULT 0,
                low_priority_count INTEGER DEFAULT 0,
                summary_sent BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def authenticate_gmail(self) -> bool:
        """
        Autentica con Gmail API
        
        Returns:
            True si la autenticación fue exitosa
        """
        try:
            creds = None
            token_path = self.config_dir / 'token.json'
            credentials_path = self.config_dir / 'credentials.json'
            
            # Cargar credenciales guardadas
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            
            # Si no hay credenciales válidas, solicitar login
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not credentials_path.exists():
                        print(f"❌ No se encontró {credentials_path}")
                        print("Descarga credentials.json desde Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Guardar credenciales
                token_path.write_text(creds.to_json())
            
            # Crear servicio de Gmail
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            print("✅ Autenticación con Gmail exitosa")
            return True
            
        except Exception as e:
            print(f"❌ Error en autenticación Gmail: {e}")
            return False
    
    def setup_classifier(self, ollama_host: str = None, model: str = None,
                         use_new_providers: bool = True):
        """
        Configura el clasificador de correos

        Args:
            ollama_host: URL de Ollama (legacy - para compatibilidad)
            model: Modelo a usar (legacy - para compatibilidad)
            use_new_providers: Si True, usa el nuevo sistema de proveedores desde .env
        """
        # NUEVO: Usar el sistema de proveedores configurado en .env
        if use_new_providers:
            try:
                from ai_providers import create_provider_from_config
                provider_manager = create_provider_from_config()
                self.classifier = BankEmailClassifier(provider_manager=provider_manager)
                print("✅ Clasificador configurado con nuevo sistema de proveedores")
                return
            except Exception as e:
                print(f"⚠️ Error configurando nuevo sistema de proveedores: {e}")
                print("ℹ️ Usando modo legacy (solo Ollama)")

        # LEGACY: Usar solo Ollama
        if ollama_host is None:
            ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        if model is None:
            model = os.getenv('OLLAMA_MODEL', 'llama3.2')

        self.classifier = BankEmailClassifier(ollama_host=ollama_host, model=model)
        print(f"✅ Clasificador configurado (legacy): {model} @ {ollama_host}")
    
    def setup_telegram(self, bot_token: str = None, chat_id: str = None):
        """
        Configura las notificaciones de Telegram
        
        Args:
            bot_token: Token del bot (default: desde .env)
            chat_id: ID del chat (default: desde .env)
        """
        if bot_token is None:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if chat_id is None:
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            print("⚠️ Telegram no configurado (opcional)")
            print("Configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env")
            return False
        
        self.notifier = TelegramNotifier(bot_token, chat_id)
        
        # Probar conexión
        if self.notifier.test_connection():
            print("✅ Telegram configurado correctamente")
            return True
        else:
            print("❌ Error conectando con Telegram")
            return False
    
    def get_unread_emails(self, max_results: int = 50, query: str = "is:unread") -> List[Dict]:
        """
        Obtiene correos no leídos de Gmail
        
        Args:
            max_results: Número máximo de correos a obtener
            query: Query de búsqueda de Gmail
            
        Returns:
            Lista de correos con su información
        """
        if not self.gmail_service:
            print("❌ Gmail no autenticado. Llama a authenticate_gmail() primero")
            return []
        
        try:
            # Buscar correos
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("📭 No hay correos no leídos")
                return []
            
            print(f"📬 Encontrados {len(messages)} correos no leídos")
            
            # Obtener detalles de cada correo
            emails = []
            for msg in messages:
                msg_data = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()
                
                # Extraer información
                headers = msg_data['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sin asunto')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconocido')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                # Extraer cuerpo
                body = self._get_email_body(msg_data['payload'])
                
                emails.append({
                    'id': msg['id'],
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'body': body
                })
            
            return emails
            
        except Exception as e:
            print(f"❌ Error obteniendo correos: {e}")
            return []
    
    def _get_email_body(self, payload: Dict) -> str:
        """Extrae el cuerpo del correo del payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8')
                        break
        elif 'body' in payload and 'data' in payload['body']:
            body = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
        
        return body[:2000]  # Limitar longitud
    
    def is_processed(self, gmail_id: str) -> bool:
        """Verifica si un correo ya fue procesado"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM processed_emails WHERE gmail_id = ?', (gmail_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def save_classification(self, gmail_id: str, email: Dict, 
                           classification: EmailClassification):
        """Guarda la clasificación en la base de datos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO processed_emails 
            (gmail_id, subject, sender, category, priority, summary, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            gmail_id,
            email['subject'],
            email['sender'],
            classification.category,
            classification.priority,
            classification.summary,
            classification.amount
        ))
        
        conn.commit()
        conn.close()
    
    def process_emails(self, send_notifications: bool = True):
        """
        Procesa correos no leídos
        
        Args:
            send_notifications: Si True, envía notificaciones a Telegram
        """
        if not self.gmail_service or not self.classifier:
            print("❌ Falta inicializar Gmail o Clasificador")
            return
        
        # Obtener correos no leídos
        emails = self.get_unread_emails()
        
        if not emails:
            return
        
        processed_count = 0
        urgent_count = 0
        
        for email in emails:
            # Verificar si ya fue procesado
            if self.is_processed(email['id']):
                continue
            
            print(f"\n📧 Procesando: {email['subject'][:50]}...")
            
            # Clasificar
            classification = self.classifier.classify(
                email['subject'],
                email['body'],
                email['sender']
            )
            
            print(f"   Categoría: {classification.category}")
            print(f"   Prioridad: {classification.priority}")
            print(f"   Resumen: {classification.summary}")
            if classification.amount:
                print(f"   Monto: {classification.amount}")
            
            # Guardar en BD
            self.save_classification(email['id'], email, classification)
            processed_count += 1
            
            # Enviar notificación si es urgente o importante
            if send_notifications and self.notifier and classification.priority in ['urgente', 'normal']:
                if classification.priority == 'urgente':
                    urgent_count += 1
                
                email_data = {
                    'subject': email['subject'],
                    'from': email['sender'],
                    'category': classification.category,
                    'priority': classification.priority,
                    'summary': classification.summary,
                    'amount': classification.amount
                }
                
                self.notifier.send_urgent_email_alert(email_data)
        
        print(f"\n✅ Procesados {processed_count} correos nuevos")
        if urgent_count > 0:
            print(f"🚨 {urgent_count} correos urgentes notificados")
    
    def send_daily_summary(self):
        """Envía resumen diario a Telegram"""
        if not self.notifier:
            print("⚠️ Telegram no configurado")
            return
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener estadísticas del día
        cursor.execute('''
            SELECT priority, subject, summary, amount
            FROM processed_emails
            WHERE DATE(processed_at) = ?
            ORDER BY 
                CASE priority
                    WHEN 'urgente' THEN 1
                    WHEN 'normal' THEN 2
                    ELSE 3
                END
        ''', (today,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print("📭 No hay correos hoy para resumir")
            return
        
        # Organizar por prioridad
        urgent = []
        normal = []
        low_priority = []
        
        for priority, subject, summary, amount in rows:
            email_info = {
                'subject': subject,
                'summary': summary or subject,
                'amount': amount
            }
            
            if priority == 'urgente':
                urgent.append(email_info)
            elif priority == 'normal':
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
        
        if self.notifier.send_daily_summary(summary_data):
            print("✅ Resumen diario enviado a Telegram")
        else:
            print("❌ Error enviando resumen diario")


# Script principal
if __name__ == "__main__":
    import sys
    
    processor = EmailProcessor()
    
    # Autenticar con Gmail
    if not processor.authenticate_gmail():
        sys.exit(1)
    
    # Configurar clasificador
    processor.setup_classifier()
    
    # Configurar Telegram (opcional)
    processor.setup_telegram()
    
    # Procesar correos
    print("\n" + "="*50)
    print("Procesando correos...")
    print("="*50)
    processor.process_emails()
    
    print("\n" + "="*50)
    print("¿Enviar resumen diario? (s/n): ", end='')
    if input().lower() == 's':
        processor.send_daily_summary()

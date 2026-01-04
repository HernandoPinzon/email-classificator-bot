"""
Implementaciones del patrón Repository para persistencia de datos.
Permite abstraer el acceso a datos y facilita testing.
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

from interfaces import EmailRepository, Email, EmailClassification
from config import DatabaseConfig


class SQLiteEmailRepository(EmailRepository):
    """
    Implementación de EmailRepository usando SQLite.
    Esta es la implementación real para producción.
    """

    def __init__(self, config: DatabaseConfig):
        self.db_path = config.path
        self._connection: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene una conexión a la base de datos"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
        return self._connection

    def close(self):
        """Cierra la conexión a la base de datos"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def init_database(self) -> None:
        """Crea las tablas necesarias en la base de datos"""
        conn = self._get_connection()
        cursor = conn.cursor()

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

    def is_processed(self, email_id: str) -> bool:
        """Verifica si un correo ya fue procesado"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id FROM processed_emails WHERE gmail_id = ?',
            (email_id,)
        )
        result = cursor.fetchone()
        return result is not None

    def save_classification(self, email: Email, classification: EmailClassification) -> None:
        """Guarda la clasificación en la base de datos"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO processed_emails
            (gmail_id, subject, sender, category, priority, summary, amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            email.id,
            email.subject,
            email.sender,
            classification.category,
            classification.priority,
            classification.summary,
            classification.amount
        ))

        conn.commit()

    def get_daily_stats(self, date: str) -> List[Dict]:
        """Obtiene estadísticas del día"""
        conn = self._get_connection()
        cursor = conn.cursor()

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
        ''', (date,))

        rows = cursor.fetchall()
        return [
            {
                'priority': row[0],
                'subject': row[1],
                'summary': row[2],
                'amount': row[3]
            }
            for row in rows
        ]

    def get_all_processed(self) -> List[Dict]:
        """Obtiene todos los correos procesados"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT gmail_id, subject, sender, category, priority, summary, amount, processed_at
            FROM processed_emails
            ORDER BY processed_at DESC
        ''')

        rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'subject': row[1],
                'sender': row[2],
                'category': row[3],
                'priority': row[4],
                'summary': row[5],
                'amount': row[6],
                'processed_at': row[7]
            }
            for row in rows
        ]


class InMemoryEmailRepository(EmailRepository):
    """
    Implementación en memoria de EmailRepository.
    Útil para testing sin necesidad de base de datos real.
    """

    def __init__(self):
        self.emails: Dict[str, Dict] = {}
        self.initialized = False

    def init_database(self) -> None:
        """Simula inicialización de base de datos"""
        self.initialized = True

    def is_processed(self, email_id: str) -> bool:
        """Verifica si un correo ya fue procesado"""
        return email_id in self.emails

    def save_classification(self, email: Email, classification: EmailClassification) -> None:
        """Guarda la clasificación en memoria"""
        self.emails[email.id] = {
            'email': email,
            'classification': classification,
            'processed_at': datetime.now().isoformat()
        }

    def get_daily_stats(self, date: str) -> List[Dict]:
        """Obtiene estadísticas del día"""
        results = []
        for email_id, data in self.emails.items():
            processed_date = data['processed_at'][:10]
            if processed_date == date:
                classification = data['classification']
                email = data['email']
                results.append({
                    'priority': classification.priority,
                    'subject': email.subject,
                    'summary': classification.summary,
                    'amount': classification.amount
                })
        return results

    def clear(self):
        """Limpia todos los datos (útil entre tests)"""
        self.emails.clear()

    def get_all(self) -> Dict[str, Dict]:
        """Retorna todos los datos almacenados"""
        return self.emails.copy()

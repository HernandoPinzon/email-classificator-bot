"""
Punto de entrada principal para el procesador de correos
"""

import sys

from .core import EmailProcessor
from .config import load_config_from_env


def main():
    """Función principal para ejecutar el procesador"""
    processor = EmailProcessor.create_default()
    config = processor.config

    if not processor.authenticate():
        sys.exit(1)

    check_mode = config.schedule.check_mode

    if check_mode == "hourly":
        # Modo horario: revisar últimas N horas, solo notificar si hay importantes
        hours = config.schedule.check_interval_hours
        buffer = config.schedule.check_buffer_minutes

        print("\n" + "=" * 50)
        print(f"Modo horario: revisando correos de las últimas {hours}h...")
        print("=" * 50)

        # No enviar notificaciones individuales en modo horario
        stats = processor.process_emails(
            send_notifications=False,
            hours_ago=hours,
            buffer_minutes=buffer
        )

        # Solo enviar mensaje si hay correos importantes
        important_emails = stats.get('important_emails', [])
        if important_emails and processor.notifier:
            print(f"\nEnviando resumen: {len(important_emails)} correo(s) importante(s)")
            processor.notifier.send_hourly_summary(important_emails)
        else:
            print("\nNo hay correos importantes, no se envía notificación")

    else:
        # Modo diario: comportamiento original
        print("\n" + "=" * 50)
        print("Modo diario: procesando correos...")
        print("=" * 50)

        processor.process_emails()

        print("\n" + "=" * 50)
        print("Enviando resumen diario...")
        print("=" * 50)

        processor.send_daily_summary()


if __name__ == "__main__":
    main()

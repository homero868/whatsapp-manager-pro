# test_scheduler.py - Prueba del scheduler

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from message_scheduler import MessageScheduler
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=== Prueba del Scheduler ===")
print("Este script verificará que el scheduler esté funcionando correctamente")
print("Deberías ver mensajes cada minuto diciendo 'Verificando campañas programadas...'")
print("Presiona Ctrl+C para detener\n")

# Crear e iniciar scheduler
scheduler = MessageScheduler()
scheduler.start()

try:
    # Mantener el script corriendo
    while True:
        time.sleep(10)
        print(".", end="", flush=True)
except KeyboardInterrupt:
    print("\n\nDeteniendo scheduler...")
    scheduler.stop()
    print("Scheduler detenido")

import logging
import logging.handlers
import os
from datetime import datetime
from config import Config

def setup_logger():
    """Configurar el sistema de logging"""

    # Crear carpeta de logs si no existe
    Config.init_folders()

    # Configurar formato de logs
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Handler para archivo
    file_handler = logging.handlers.RotatingFileHandler(
        Config.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)

    # Handler para consola (solo en desarrollo)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_format)

    # Agregar handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Configurar loggers específicos
    logging.getLogger('mysql.connector').setLevel(logging.WARNING)
    logging.getLogger('twilio').setLevel(logging.WARNING)

    logger.info("Sistema de logging inicializado")

class ActivityLogger:
    """Logger específico para actividades de usuario"""

    def __init__(self, user_id: int = None):
        self.logger = logging.getLogger('activity')
        self.user_id = user_id

    def log(self, action: str, details: str = None, level: str = 'info'):
        """Registrar una actividad"""
        message = f"[User: {self.user_id or 'Anonymous'}] {action}"
        if details:
            message += f" - {details}"

        if level == 'error':
            self.logger.error(message)
        elif level == 'warning':
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def log_login(self, username: str, success: bool):
        """Registrar intento de login"""
        if success:
            self.log('LOGIN_SUCCESS', f"Usuario: {username}")
        else:
            self.log('LOGIN_FAILED', f"Usuario: {username}", 'warning')

    def log_import(self, filename: str, contacts_count: int, errors_count: int):
        """Registrar importación de contactos"""
        self.log(
            'IMPORT_CONTACTS',
            f"Archivo: {filename}, Contactos: {contacts_count}, Errores: {errors_count}"
        )

    def log_campaign(self, campaign_name: str, action: str, details: str = None):
        """Registrar acción de campaña"""
        self.log(
            f'CAMPAIGN_{action.upper()}',
            f"Campaña: {campaign_name}" + (f", {details}" if details else "")
        )

    def log_template(self, template_name: str, action: str):
        """Registrar acción de plantilla"""
        self.log(
            f'TEMPLATE_{action.upper()}',
            f"Plantilla: {template_name}"
        )

    def log_error(self, error_type: str, error_message: str):
        """Registrar error"""
        self.log(
            f'ERROR_{error_type.upper()}',
            error_message,
            'error'
        )

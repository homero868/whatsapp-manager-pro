import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Configuración de la aplicación
    APP_NAME = "WhatsApp Manager Pro"
    APP_VERSION = "1.0.0"
    
    # Configuración de base de datos MySQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'whatsapp_manager')
    
    # Configuración de Twilio
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_WHATSAPP_FROM = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
    
    # Configuración de archivos
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    # Configuración de logs
    LOG_FOLDER = os.path.join(os.path.dirname(__file__), 'logs')
    LOG_FILE = os.path.join(LOG_FOLDER, 'app.log')
    
    # Configuración de envíos
    MESSAGES_PER_SECOND = 1  # Límite de Twilio
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAY_MINUTES = 10
    
    # Configuración de seguridad
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    SESSION_TIMEOUT_MINUTES = 30
    
    # País por defecto (Guatemala)
    DEFAULT_COUNTRY_CODE = '+502'
    DEFAULT_PHONE_LENGTH = 8
    
    @classmethod
    def init_folders(cls):
        """Crear carpetas necesarias si no existen"""
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.LOG_FOLDER, exist_ok=True)
        
    @classmethod
    def get_db_config(cls):
        """Obtener configuración de base de datos como diccionario"""
        return {
            'host': cls.DB_HOST,
            'port': cls.DB_PORT,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': False
        }

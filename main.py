import sys
import os
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Configurar path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from logger import setup_logger
from database import DatabaseManager
from ui.login_window import LoginWindow
from main_window import MainWindow
from apply_cursors import setup_global_cursors
import logging

logger = logging.getLogger(__name__)

class WhatsAppManagerApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_application()
        self.main_window = None
        self.login_window = None
    
    def setup_application(self):
        """Configurar la aplicación"""
        # Configurar información de la aplicación
        self.app.setApplicationName(Config.APP_NAME)
        self.app.setOrganizationName("WhatsApp Manager")
        
        # Configurar cursores pointer para elementos clickeables
        self.cursor_changer = setup_global_cursors(self.app)
        
        # Configurar estilo global base
        self.app.setStyleSheet("""
            QWidget {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                font-size: 14px;
            }
        """)
    
    def check_requirements(self):
        """Verificar requisitos del sistema"""
        try:
            # Inicializar carpetas
            Config.init_folders()
            
            # Configurar logging
            setup_logger()
            logger.info(f"Iniciando {Config.APP_NAME} v{Config.APP_VERSION}")
            
            # Verificar conexión a base de datos
            db = DatabaseManager()
            if not db.test_connection():
                QMessageBox.critical(
                    None,
                    "Error de Conexión",
                    "No se pudo conectar a la base de datos MySQL.\n\n"
                    "Por favor verifique:\n"
                    "1. MySQL está ejecutándose\n"
                    "2. Las credenciales en el archivo .env son correctas\n"
                    "3. La base de datos 'whatsapp_manager' existe"
                )
                return False
            
            logger.info("Conexión a base de datos establecida")
            return True
            
        except Exception as e:
            logger.error(f"Error verificando requisitos: {e}")
            QMessageBox.critical(
                None,
                "Error Fatal",
                f"Error al inicializar la aplicación:\n{str(e)}"
            )
            return False
    
    def show_login(self):
        """Mostrar ventana de login"""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_success)
        self.login_window.show()
    
    def on_login_success(self, user_data):
        """Manejar login exitoso"""
        logger.info(f"Login exitoso para usuario: {user_data['username']}")
        
        # Cerrar ventana de login
        if self.login_window:
            self.login_window.close()
        
        # Crear y mostrar ventana principal
        self.main_window = MainWindow()
        self.main_window.set_activity_logger(user_data['id'])
        self.main_window.logout_signal.connect(self.on_logout)
        
        # Mostrar maximizada respetando la barra de tareas
        self.main_window.showMaximized()
    
    def on_logout(self):
        """Manejar logout"""
        logger.info("Usuario cerró sesión")
        
        # Cerrar ventana principal
        if self.main_window:
            self.main_window.close()
        
        # Mostrar login nuevamente
        self.show_login()
    
    def run(self):
        """Ejecutar la aplicación"""
        # Verificar requisitos
        if not self.check_requirements():
            return 1
        
        # Mostrar login
        self.show_login()
        
        # Ejecutar aplicación
        return self.app.exec()


def main():
    """Función principal"""
    try:
        # Habilitar DPI alto en Windows
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        
        # Crear y ejecutar aplicación
        app = WhatsAppManagerApp()
        sys.exit(app.run())
        
    except Exception as e:
        print(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

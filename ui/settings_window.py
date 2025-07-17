from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTabWidget, QWidget,
                             QGroupBox, QSpinBox, QCheckBox, QMessageBox,
                             QTextEdit)
from PyQt6.QtCore import Qt
import os
from config import Config
from twilio_service import TwilioService
from database import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setMinimumSize(600, 500)
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Tabs de configuración
        self.tabs = QTabWidget()
        
        # Tab de Twilio
        self.twilio_tab = self.create_twilio_tab()
        self.tabs.addTab(self.twilio_tab, "📱 Twilio")
        
        # Tab de Base de Datos
        self.database_tab = self.create_database_tab()
        self.tabs.addTab(self.database_tab, "🗄️ Base de Datos")
        
        # Tab de Aplicación
        self.app_tab = self.create_app_tab()
        self.tabs.addTab(self.app_tab, "⚙️ Aplicación")
        
        layout.addWidget(self.tabs)
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def create_twilio_tab(self):
        """Crear tab de configuración de Twilio"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Credenciales
        cred_group = QGroupBox("Credenciales de Twilio")
        cred_layout = QVBoxLayout()
        
        # Account SID
        sid_layout = QHBoxLayout()
        sid_layout.addWidget(QLabel("Account SID:"))
        self.account_sid_input = QLineEdit()
        self.account_sid_input.setPlaceholderText("ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        sid_layout.addWidget(self.account_sid_input)
        cred_layout.addLayout(sid_layout)
        
        # Auth Token
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Auth Token:"))
        self.auth_token_input = QLineEdit()
        self.auth_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.auth_token_input.setPlaceholderText("********************************")
        token_layout.addWidget(self.auth_token_input)
        cred_layout.addLayout(token_layout)
        
        # WhatsApp From Number
        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("Número WhatsApp:"))
        self.whatsapp_from_input = QLineEdit()
        self.whatsapp_from_input.setPlaceholderText("whatsapp:+14155238886")
        from_layout.addWidget(self.whatsapp_from_input)
        cred_layout.addLayout(from_layout)
        
        cred_group.setLayout(cred_layout)
        layout.addWidget(cred_group)
        
        # Botón de prueba
        test_btn = QPushButton("🔍 Probar Conexión")
        test_btn.clicked.connect(self.test_twilio_connection)
        layout.addWidget(test_btn)
        
        # Información
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setHtml("""
            <h3>Configuración de Twilio</h3>
            <p>Para obtener sus credenciales de Twilio:</p>
            <ol>
                <li>Inicie sesión en <a href="https://console.twilio.com">console.twilio.com</a></li>
                <li>Encuentre su Account SID y Auth Token en el Dashboard</li>
                <li>Configure un número de WhatsApp en la sección de Messaging</li>
                <li>Use el formato: whatsapp:+[número] para el campo "Número WhatsApp"</li>
            </ol>
        """)
        layout.addWidget(info_text)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_database_tab(self):
        """Crear tab de configuración de base de datos"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Conexión
        conn_group = QGroupBox("Conexión MySQL")
        conn_layout = QVBoxLayout()
        
        # Host
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("Host:"))
        self.db_host_input = QLineEdit()
        self.db_host_input.setPlaceholderText("localhost")
        host_layout.addWidget(self.db_host_input)
        conn_layout.addLayout(host_layout)
        
        # Puerto
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Puerto:"))
        self.db_port_input = QSpinBox()
        self.db_port_input.setMinimum(1)
        self.db_port_input.setMaximum(65535)
        self.db_port_input.setValue(3306)
        port_layout.addWidget(self.db_port_input)
        conn_layout.addLayout(port_layout)
        
        # Usuario
        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Usuario:"))
        self.db_user_input = QLineEdit()
        self.db_user_input.setPlaceholderText("root")
        user_layout.addWidget(self.db_user_input)
        conn_layout.addLayout(user_layout)
        
        # Contraseña
        pass_layout = QHBoxLayout()
        pass_layout.addWidget(QLabel("Contraseña:"))
        self.db_password_input = QLineEdit()
        self.db_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        pass_layout.addWidget(self.db_password_input)
        conn_layout.addLayout(pass_layout)
        
        # Base de datos
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Base de datos:"))
        self.db_name_input = QLineEdit()
        self.db_name_input.setPlaceholderText("whatsapp_manager")
        db_layout.addWidget(self.db_name_input)
        conn_layout.addLayout(db_layout)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Botón de prueba
        test_btn = QPushButton("🔍 Probar Conexión")
        test_btn.clicked.connect(self.test_db_connection)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_app_tab(self):
        """Crear tab de configuración de aplicación"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Límites
        limits_group = QGroupBox("Límites y Tiempos")
        limits_layout = QVBoxLayout()
        
        # Mensajes por segundo
        mps_layout = QHBoxLayout()
        mps_layout.addWidget(QLabel("Mensajes por segundo:"))
        self.messages_per_second_input = QSpinBox()
        self.messages_per_second_input.setMinimum(1)
        self.messages_per_second_input.setMaximum(10)
        self.messages_per_second_input.setValue(1)
        mps_layout.addWidget(self.messages_per_second_input)
        limits_layout.addLayout(mps_layout)
        
        # Reintentos
        retry_layout = QHBoxLayout()
        retry_layout.addWidget(QLabel("Máximo de reintentos:"))
        self.max_retries_input = QSpinBox()
        self.max_retries_input.setMinimum(0)
        self.max_retries_input.setMaximum(10)
        self.max_retries_input.setValue(3)
        retry_layout.addWidget(self.max_retries_input)
        limits_layout.addLayout(retry_layout)
        
        # Delay de reintentos
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Minutos entre reintentos:"))
        self.retry_delay_input = QSpinBox()
        self.retry_delay_input.setMinimum(1)
        self.retry_delay_input.setMaximum(60)
        self.retry_delay_input.setValue(10)
        delay_layout.addWidget(self.retry_delay_input)
        limits_layout.addLayout(delay_layout)
        
        limits_group.setLayout(limits_layout)
        layout.addWidget(limits_group)
        
        # Configuración regional
        regional_group = QGroupBox("Configuración Regional")
        regional_layout = QVBoxLayout()
        
        # Código de país
        country_layout = QHBoxLayout()
        country_layout.addWidget(QLabel("Código de país por defecto:"))
        self.country_code_input = QLineEdit()
        self.country_code_input.setPlaceholderText("+502")
        self.country_code_input.setMaximumWidth(100)
        country_layout.addWidget(self.country_code_input)
        country_layout.addStretch()
        regional_layout.addLayout(country_layout)
        
        # Longitud de teléfono
        phone_layout = QHBoxLayout()
        phone_layout.addWidget(QLabel("Longitud de teléfono local:"))
        self.phone_length_input = QSpinBox()
        self.phone_length_input.setMinimum(7)
        self.phone_length_input.setMaximum(15)
        self.phone_length_input.setValue(8)
        phone_layout.addWidget(self.phone_length_input)
        phone_layout.addStretch()
        regional_layout.addLayout(phone_layout)
        
        regional_group.setLayout(regional_layout)
        layout.addWidget(regional_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def load_settings(self):
        """Cargar configuración actual"""
        # Twilio
        self.account_sid_input.setText(Config.TWILIO_ACCOUNT_SID)
        self.auth_token_input.setText(Config.TWILIO_AUTH_TOKEN)
        self.whatsapp_from_input.setText(Config.TWILIO_WHATSAPP_FROM)
        
        # Base de datos
        self.db_host_input.setText(Config.DB_HOST)
        self.db_port_input.setValue(Config.DB_PORT)
        self.db_user_input.setText(Config.DB_USER)
        self.db_password_input.setText(Config.DB_PASSWORD)
        self.db_name_input.setText(Config.DB_NAME)
        
        # Aplicación
        self.messages_per_second_input.setValue(Config.MESSAGES_PER_SECOND)
        self.max_retries_input.setValue(Config.MAX_RETRY_ATTEMPTS)
        self.retry_delay_input.setValue(Config.RETRY_DELAY_MINUTES)
        self.country_code_input.setText(Config.DEFAULT_COUNTRY_CODE)
        self.phone_length_input.setValue(Config.DEFAULT_PHONE_LENGTH)
    
    def save_settings(self):
        """Guardar configuración"""
        try:
            # Crear o actualizar archivo .env
            env_content = f"""# Configuración de Twilio
TWILIO_ACCOUNT_SID={self.account_sid_input.text()}
TWILIO_AUTH_TOKEN={self.auth_token_input.text()}
TWILIO_WHATSAPP_FROM={self.whatsapp_from_input.text()}

# Configuración de Base de Datos
DB_HOST={self.db_host_input.text()}
DB_PORT={self.db_port_input.value()}
DB_USER={self.db_user_input.text()}
DB_PASSWORD={self.db_password_input.text()}
DB_NAME={self.db_name_input.text()}
"""
            
            env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            QMessageBox.information(
                self,
                "Configuración Guardada",
                "La configuración se ha guardado exitosamente.\n"
                "Reinicie la aplicación para aplicar los cambios."
            )
            
            self.accept()
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando configuración: {str(e)}")
    
    def test_twilio_connection(self):
        """Probar conexión con Twilio"""
        try:
            # Crear servicio temporal con nueva configuración
            test_service = TwilioService()
            test_service.account_sid = self.account_sid_input.text()
            test_service.auth_token = self.auth_token_input.text()
            
            if test_service.test_connection():
                QMessageBox.information(
                    self,
                    "Conexión Exitosa",
                    "✅ La conexión con Twilio fue exitosa!"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error de Conexión",
                    "❌ No se pudo conectar con Twilio.\n"
                    "Verifique sus credenciales."
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error probando conexión: {str(e)}")
    
    def test_db_connection(self):
        """Probar conexión con base de datos"""
        try:
            # Crear configuración temporal
            test_config = {
                'host': self.db_host_input.text(),
                'port': self.db_port_input.value(),
                'user': self.db_user_input.text(),
                'password': self.db_password_input.text(),
                'database': self.db_name_input.text(),
                'charset': 'utf8mb4',
                'use_unicode': True
            }
            
            # Probar conexión
            import mysql.connector
            conn = mysql.connector.connect(**test_config)
            
            if conn.is_connected():
                conn.close()
                QMessageBox.information(
                    self,
                    "Conexión Exitosa",
                    "✅ La conexión con MySQL fue exitosa!"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error de Conexión",
                    "❌ No se pudo conectar con MySQL."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de Conexión",
                f"❌ Error conectando con MySQL:\n{str(e)}"
            )

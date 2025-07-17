from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QCheckBox, QMessageBox,
                             QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
from auth import auth_manager
from config import Config
import logging

logger = logging.getLogger(__name__)

class LoginWindow(QDialog):
    login_successful = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle(f"{Config.APP_NAME} - Iniciar Sesión")
        self.setFixedSize(450, 550)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        
        # Layout principal
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Logo/Título
        title_label = QLabel("WhatsApp Manager Pro")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #25D366;")
        layout.addWidget(title_label)
        
        # Subtítulo
        subtitle_label = QLabel("Sistema de Mensajes Masivos")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666; font-size: 16px;")
        layout.addWidget(subtitle_label)
        
        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #e0e0e0;")
        layout.addWidget(line)
        
        # Campo de usuario
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("👤 Nombre de usuario")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border-color: #25D366;
            }
        """)
        layout.addWidget(self.username_input)
        
        # Campo de contraseña
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("🔒 Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                font-size: 16px;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
            QLineEdit:focus {
                border-color: #25D366;
            }
        """)
        layout.addWidget(self.password_input)
        
        # Checkbox recordar
        self.remember_checkbox = QCheckBox("Recordar usuario")
        self.remember_checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remember_checkbox.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(self.remember_checkbox)
        
        # Botón de login
        self.login_button = QPushButton("Iniciar Sesión")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #20BD5A;
            }
            QPushButton:pressed {
                background-color: #1AAE52;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)
        
        # Enlaces adicionales
        links_layout = QHBoxLayout()
        
        register_label = QLabel('<a href="#" style="color: #25D366;">Registrar nuevo usuario</a>')
        register_label.setOpenExternalLinks(False)
        register_label.linkActivated.connect(self.show_register_dialog)
        register_label.setCursor(Qt.CursorShape.PointingHandCursor)
        links_layout.addWidget(register_label)
        
        links_layout.addStretch()
        
        help_label = QLabel('<a href="#" style="color: #25D366;">¿Necesita ayuda?</a>')
        help_label.setOpenExternalLinks(False)
        help_label.linkActivated.connect(self.show_help)
        help_label.setCursor(Qt.CursorShape.PointingHandCursor)
        links_layout.addWidget(help_label)
        
        layout.addLayout(links_layout)
        
        layout.addStretch()
        
        # Información de versión
        version_label = QLabel(f"Versión {Config.APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(version_label)
        
        self.setLayout(layout)
        
        # Configurar tecla Enter
        self.username_input.returnPressed.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Enfocar campo de usuario
        self.username_input.setFocus()
    
    def handle_login(self):
        """Manejar intento de login"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(
                self,
                "Campos Vacíos",
                "Por favor ingrese usuario y contraseña."
            )
            return
        
        # Deshabilitar controles durante login
        self.set_controls_enabled(False)
        
        # Intentar login
        user = auth_manager.login(username, password)
        
        if user:
            # Login exitoso
            QMessageBox.information(
                self,
                "Bienvenido",
                f"¡Bienvenido {user['username']}!"
            )
            self.login_successful.emit(user)
        else:
            # Login fallido
            QMessageBox.critical(
                self,
                "Error de Autenticación",
                "Usuario o contraseña incorrectos."
            )
            self.password_input.clear()
            self.password_input.setFocus()
        
        # Rehabilitar controles
        self.set_controls_enabled(True)
    
    def show_register_dialog(self):
        """Mostrar diálogo de registro"""
        from ui.register_dialog import RegisterDialog
        dialog = RegisterDialog(self)
        if dialog.exec():
            # Usuario registrado exitosamente
            self.username_input.setText(dialog.username)
            self.password_input.setFocus()
    
    def show_help(self):
        """Mostrar ayuda"""
        QMessageBox.information(
            self,
            "Ayuda de Inicio de Sesión",
            "Para iniciar sesión:\n\n"
            "1. Ingrese su nombre de usuario\n"
            "2. Ingrese su contraseña\n"
            "3. Haga clic en 'Iniciar Sesión'\n\n"
            "Si es la primera vez, use:\n"
            "Usuario: admin\n"
            "Contraseña: admin123\n\n"
            "Para crear un nuevo usuario, haga clic en 'Registrar nuevo usuario'."
        )
    
    def set_controls_enabled(self, enabled: bool):
        """Habilitar/deshabilitar controles"""
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)
        self.login_button.setEnabled(enabled)
        self.remember_checkbox.setEnabled(enabled)
        
        if not enabled:
            self.login_button.setText("Iniciando sesión...")
        else:
            self.login_button.setText("Iniciar Sesión")

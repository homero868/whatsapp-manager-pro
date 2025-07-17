from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                            QLineEdit, QPushButton, QMessageBox, QSpacerItem,
                            QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from auth import auth_manager
import re

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.username = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("Registrar nuevo usuario")
        self.setFixedSize(500, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Título
        title_label = QLabel("Crear nueva cuenta")
        title_label.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #25D366;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Campo de usuario
        user_label = QLabel("Usuario:")
        user_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(user_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de usuario (mínimo 4 caracteres)")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #25D366;
            }
        """)
        layout.addWidget(self.username_input)
        
        # Campo de email
        email_label = QLabel("Email (opcional):")
        email_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("correo@ejemplo.com")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #25D366;
            }
        """)
        layout.addWidget(self.email_input)
        
        # Campo de contraseña
        pass_label = QLabel("Contraseña:")
        pass_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(pass_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña (mínimo 6 caracteres)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #25D366;
            }
        """)
        layout.addWidget(self.password_input)
        
        # Campo de confirmar contraseña
        confirm_label = QLabel("Confirmar Contraseña:")
        confirm_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(confirm_label)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirmar contraseña")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #25D366;
            }
        """)
        layout.addWidget(self.confirm_password_input)
        
        # Espaciador
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Botones
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 10px 25px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        cancel_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        self.register_button = QPushButton("Registrar")
        self.register_button.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 10px 25px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #20BD5A;
            }
            QPushButton:pressed {
                background-color: #1AAE52;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.register_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.register_button.clicked.connect(self.handle_register)
        buttons_layout.addWidget(self.register_button)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Enfocar primer campo
        self.username_input.setFocus()
    
    def handle_register(self):
        """Manejar registro de usuario"""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        # Validaciones
        if not username:
            QMessageBox.warning(self, "Error", "El nombre de usuario es requerido.")
            self.username_input.setFocus()
            return
        
        if len(username) < 4:
            QMessageBox.warning(self, "Error", "El nombre de usuario debe tener al menos 4 caracteres.")
            self.username_input.setFocus()
            return
        
        if not re.match("^[a-zA-Z0-9_]+$", username):
            QMessageBox.warning(self, "Error", "El nombre de usuario solo puede contener letras, números y guiones bajos.")
            self.username_input.setFocus()
            return
        
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            QMessageBox.warning(self, "Error", "El formato del email no es válido.")
            self.email_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Error", "La contraseña es requerida.")
            self.password_input.setFocus()
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Error", "La contraseña debe tener al menos 6 caracteres.")
            self.password_input.setFocus()
            return
        
        if password != confirm_password:
            QMessageBox.warning(self, "Error", "Las contraseñas no coinciden.")
            self.confirm_password_input.setFocus()
            self.confirm_password_input.clear()
            return
        
        # Intentar registrar
        self.register_button.setEnabled(False)
        self.register_button.setText("Registrando...")
        
        try:
            if auth_manager.register(username, password, email if email else None):
                self.username = username
                QMessageBox.information(
                    self,
                    "Registro Exitoso",
                    f"Usuario '{username}' registrado exitosamente.\n"
                    "Ahora puede iniciar sesión con sus credenciales."
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Error de Registro",
                    "No se pudo registrar el usuario.\n"
                    "Es posible que el nombre de usuario ya esté en uso."
                )
                self.register_button.setEnabled(True)
                self.register_button.setText("Registrar")
                self.username_input.setFocus()
                self.username_input.selectAll()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error inesperado al registrar usuario:\n{str(e)}"
            )
            self.register_button.setEnabled(True)
            self.register_button.setText("Registrar")

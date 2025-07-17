from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QTabWidget, QPushButton, QLabel, QStatusBar,
                             QMenuBar, QMenu, QMessageBox, QToolBar, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QScreen
import sys
from datetime import datetime

from auth import auth_manager
from logger import ActivityLogger
from message_scheduler import MessageScheduler
from config import Config
from themes import theme_manager

# Importar ventanas de módulos
from ui.login_window import LoginWindow
from ui.contacts_window import ContactsWindow
from ui.templates_window import TemplatesWindow
from ui.campaigns_window import CampaignsWindow
from ui.reports_window import ReportsWindow
from ui.settings_window import SettingsWindow

class MainWindow(QMainWindow):
    logout_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.scheduler = MessageScheduler()
        self.activity_logger = None
        self.init_ui()
        self.setup_connections()
        
        # Iniciar scheduler
        self.scheduler.start()
        
        # Timer para actualizar UI
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Actualizar cada 5 segundos
    
    def init_ui(self):
        """Inicializar la interfaz de usuario"""
        self.setWindowTitle(f"{Config.APP_NAME} v{Config.APP_VERSION}")
        
        # Obtener el tamaño disponible de la pantalla
        screen = QApplication.primaryScreen()
        available_geometry = screen.availableGeometry()
        
        # Configurar ventana para usar el espacio disponible (no toda la pantalla)
        self.setGeometry(available_geometry)
        
        # Permitir minimizar pero no redimensionar
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.CustomizeWindowHint
        )
        
        # Widget central
        central_widget = QWidget()
        central_widget.setObjectName("centralwidget")  # Importante para el tema
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Información de usuario
        self.user_info_widget = self.create_user_info_widget()
        main_layout.addWidget(self.user_info_widget)
        
        # Tabs principales
        self.tab_widget = QTabWidget()
        
        # Configurar cursor para las pestañas
        self.tab_widget.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Crear ventanas de módulos
        self.contacts_window = ContactsWindow()
        self.templates_window = TemplatesWindow()
        self.campaigns_window = CampaignsWindow(self.scheduler)
        self.reports_window = ReportsWindow()
        
        # Agregar tabs
        self.tab_widget.addTab(self.contacts_window, "📞 Contactos")
        self.tab_widget.addTab(self.templates_window, "📄 Plantillas")
        self.tab_widget.addTab(self.campaigns_window, "📨 Campañas")
        self.tab_widget.addTab(self.reports_window, "📊 Reportes")
        
        main_layout.addWidget(self.tab_widget)
        
        # Barra de menú
        self.create_menu_bar()
        
        # Barra de herramientas
        self.create_toolbar()
        
        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo")
        
        # Aplicar tema inicial
        self.apply_theme()
        
        # Ajustar el tamaño del contenido si es necesario
        self.adjust_content_size()
    
    def create_user_info_widget(self):
        """Crear widget de información de usuario"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Información de usuario
        user = auth_manager.get_current_user()
        if user:
            self.user_label = QLabel(f"👤 Usuario: {user['username']}")
            self.user_label.setStyleSheet("font-weight: bold; padding: 5px;")
            layout.addWidget(self.user_label)
        
        layout.addStretch()
        
        # Botón de cambiar tema
        self.theme_btn = QPushButton("🌙 Tema Oscuro")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(self.theme_btn)
        
        # Botón de cerrar sesión
        logout_btn = QPushButton("🚪 Cerrar Sesión")
        logout_btn.clicked.connect(self.logout)
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        layout.addWidget(logout_btn)
        
        widget.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #dee2e6;")
        return widget
    
    def apply_theme(self):
        """Aplicar el tema actual a toda la aplicación"""
        # Aplicar a la ventana principal
        self.setStyleSheet(theme_manager.get_current_theme())
        
        # Forzar actualización de todos los widgets
        self.update()
        self.repaint()
        
        # Aplicar a todas las ventanas hijas
        for widget in self.findChildren(QWidget):
            widget.update()
    
    def toggle_theme(self):
        """Cambiar entre tema claro y oscuro"""
        theme_manager.toggle_theme()
        self.apply_theme()
        
        # Actualizar texto del botón
        if theme_manager.get_theme_name() == "dark":
            self.theme_btn.setText("☀️ Tema Claro")
        else:
            self.theme_btn.setText("🌙 Tema Oscuro")
    
    def create_menu_bar(self):
        """Crear barra de menú"""
        menubar = self.menuBar()
        menubar.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Menú Archivo
        file_menu = menubar.addMenu("&Archivo")
        file_menu.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Importar contactos
        import_action = QAction("📥 Importar Contactos", self)
        import_action.triggered.connect(self.contacts_window.import_contacts)
        file_menu.addAction(import_action)
        
        # Exportar contactos
        export_action = QAction("📤 Exportar Contactos", self)
        export_action.triggered.connect(self.contacts_window.export_contacts)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Salir
        exit_action = QAction("❌ Salir", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Herramientas
        tools_menu = menubar.addMenu("&Herramientas")
        
        # Configuración
        settings_action = QAction("⚙️ Configuración", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # Logs
        logs_action = QAction("📋 Ver Logs", self)
        logs_action.triggered.connect(self.show_logs)
        tools_menu.addAction(logs_action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu("&Ayuda")
        
        # Documentación
        docs_action = QAction("📚 Documentación", self)
        docs_action.triggered.connect(self.show_documentation)
        help_menu.addAction(docs_action)
        
        # Acerca de
        about_action = QAction("ℹ️ Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_toolbar(self):
        """Crear barra de herramientas"""
        toolbar = QToolBar("Herramientas principales")
        self.addToolBar(toolbar)
        
        # Botón nuevo contacto
        new_contact_action = QAction("➕ Nuevo Contacto", self)
        new_contact_action.triggered.connect(self.contacts_window.add_contact)
        toolbar.addAction(new_contact_action)
        
        # Botón nueva plantilla
        new_template_action = QAction("📝 Nueva Plantilla", self)
        new_template_action.triggered.connect(self.templates_window.add_template)
        toolbar.addAction(new_template_action)
        
        toolbar.addSeparator()
        
        # Botón envío rápido
        quick_send_action = QAction("⚡ Envío Rápido", self)
        quick_send_action.triggered.connect(self.campaigns_window.quick_send)
        toolbar.addAction(quick_send_action)
        
        # Botón programar campaña
        schedule_action = QAction("📅 Programar Campaña", self)
        schedule_action.triggered.connect(self.campaigns_window.schedule_campaign)
        toolbar.addAction(schedule_action)
        
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QToolButton:hover {
                background-color: #e9ecef;
            }
        """)
    
    def setup_connections(self):
        """Configurar conexiones entre ventanas"""
        # Conectar señales entre ventanas
        self.templates_window.template_saved.connect(self.campaigns_window.refresh_templates)
        self.contacts_window.contacts_updated.connect(self.campaigns_window.refresh_contacts)
        self.campaigns_window.campaign_started.connect(self.reports_window.refresh_data)
    
    def update_status(self):
        """Actualizar barra de estado"""
        try:
            # Obtener estadísticas
            from database import ContactModel, MessageModel
            contact_model = ContactModel()
            message_model = MessageModel()
            
            contacts_count = contact_model.get_contact_count()
            stats = message_model.get_message_stats()
            
            status_text = (
                f"📞 Contactos: {contacts_count} | "
                f"✉️ Mensajes: {stats.get('total', 0)} | "
                f"✅ Enviados: {stats.get('sent', 0)} | "
                f"📬 Entregados: {stats.get('delivered', 0)} | "
                f"❌ Fallidos: {stats.get('failed', 0)}"
            )
            
            self.status_bar.showMessage(status_text)
            
        except Exception as e:
            self.status_bar.showMessage("Error actualizando estado")
    
    def logout(self):
        """Cerrar sesión"""
        reply = QMessageBox.question(
            self,
            "Cerrar Sesión",
            "¿Está seguro que desea cerrar sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.activity_logger:
                self.activity_logger.log('LOGOUT', 'Usuario cerró sesión')
            auth_manager.logout()
            self.logout_signal.emit()
            self.close()
    
    def show_settings(self):
        """Mostrar ventana de configuración"""
        settings_window = SettingsWindow(self)
        settings_window.exec()
    
    def show_logs(self):
        """Mostrar visor de logs"""
        from ui.logs_viewer import LogsViewer
        logs_viewer = LogsViewer(self)
        logs_viewer.exec()
    
    def show_documentation(self):
        """Mostrar documentación"""
        QMessageBox.information(
            self,
            "Documentación",
            "La documentación completa está disponible en:\n\n"
            "1. Configuración de Twilio: Menú Herramientas > Configuración\n"
            "2. Importar contactos: Use archivos Excel (.xlsx o .xls)\n"
            "3. Crear plantillas: Use {nombre}, {email}, etc. para personalizar\n"
            "4. Programar envíos: Seleccione fecha y hora en Campañas\n\n"
            "Para más información, visite la documentación en línea."
        )
    
    def show_about(self):
        """Mostrar información sobre la aplicación"""
        QMessageBox.about(
            self,
            f"Acerca de {Config.APP_NAME}",
            f"{Config.APP_NAME} v{Config.APP_VERSION}\n\n"
            "Aplicación de gestión de mensajes masivos de WhatsApp\n"
            "Desarrollado con Python y PyQt6\n\n"
            "© 2025 - Todos los derechos reservados"
        )
    
    def closeEvent(self, event):
        """Manejar cierre de ventana"""
        reply = QMessageBox.question(
            self,
            "Confirmar Salida",
            "¿Está seguro que desea salir de la aplicación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Detener scheduler
            self.scheduler.stop()
            
            # Registrar cierre
            if self.activity_logger:
                self.activity_logger.log('APP_CLOSE', 'Aplicación cerrada')
            
            event.accept()
        else:
            event.ignore()
    
    def set_activity_logger(self, user_id: int):
        """Configurar logger de actividades"""
        self.activity_logger = ActivityLogger(user_id)
        
        # Pasar logger a las ventanas
        self.contacts_window.set_activity_logger(self.activity_logger)
        self.templates_window.set_activity_logger(self.activity_logger)
        self.campaigns_window.set_activity_logger(self.activity_logger)
    
    def adjust_content_size(self):
        """Ajustar el tamaño del contenido según la resolución de pantalla"""
        screen = QApplication.primaryScreen()
        available = screen.availableGeometry()
        
        # Si la pantalla es pequeña, ajustar el tamaño de fuente y espaciado
        if available.height() < 768:
            # Pantallas pequeñas (menos de 768px de alto)
            self.setStyleSheet(self.styleSheet() + """
                QWidget {
                    font-size: 12px;
                }
                QPushButton {
                    padding: 6px 12px;
                }
                QTabBar::tab {
                    padding: 8px 16px;
                }
                QToolBar {
                    padding: 3px;
                }
            """)
        elif available.height() < 900:
            # Pantallas medianas
            self.setStyleSheet(self.styleSheet() + """
                QWidget {
                    font-size: 13px;
                }
                QPushButton {
                    padding: 7px 14px;
                }
            """)
    
    def showEvent(self, event):
        """Evento cuando se muestra la ventana"""
        super().showEvent(event)
        
        # Solo ejecutar la primera vez
        if not hasattr(self, '_initialized'):
            self._initialized = True
            
            # Obtener el área de trabajo disponible (excluyendo barra de tareas)
            screen = QApplication.primaryScreen()
            available = screen.availableGeometry()
            
            # Establecer el tamaño máximo disponible
            self.setMaximumSize(available.width(), available.height())
            
            # Mover la ventana a la esquina superior izquierda del área disponible
            self.move(available.x(), available.y())
            
            # Maximizar dentro del área disponible
            self.resize(available.width(), available.height())
            
            # Prevenir redimensionamiento manual
            self.setFixedSize(self.size())

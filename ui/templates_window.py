from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QTextEdit, QLabel, QLineEdit,
                             QMessageBox, QDialog, QGroupBox, QListWidgetItem,
                             QSplitter, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import json
import re
from typing import Dict, List, Optional

from database import TemplateModel, ContactModel
from twilio_service import TwilioService
from auth import auth_manager
from config import Config
import logging

logger = logging.getLogger(__name__)

class TemplatesWindow(QWidget):
    template_saved = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.template_model = TemplateModel()
        self.contact_model = ContactModel()
        self.twilio_service = TwilioService()
        self.activity_logger = None
        self.current_template_id = None
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QHBoxLayout()
        
        # Panel izquierdo - Lista de plantillas
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("Plantillas")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        left_layout.addWidget(title_label)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        new_btn = QPushButton("➕ Nueva")
        new_btn.clicked.connect(self.new_template)
        new_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #20BD5A;
            }
        """)
        buttons_layout.addWidget(new_btn)
        
        delete_btn = QPushButton("🗑️ Eliminar")
        delete_btn.clicked.connect(self.delete_template)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        buttons_layout.addWidget(delete_btn)
        
        left_layout.addLayout(buttons_layout)
        
        # Lista de plantillas
        self.templates_list = QListWidget()
        self.templates_list.itemClicked.connect(self.load_template)
        left_layout.addWidget(self.templates_list)
        
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(300)
        
        # Panel derecho - Editor
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Nombre de plantilla
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nombre:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre de la plantilla")
        name_layout.addWidget(self.name_input)
        right_layout.addLayout(name_layout)
        
        # Editor de contenido
        content_group = QGroupBox("Contenido del Mensaje")
        content_layout = QVBoxLayout()
        
        # Barra de herramientas del editor
        editor_toolbar = QHBoxLayout()
        
        # Insertar variable
        variable_btn = QPushButton("📝 Insertar Variable")
        variable_btn.clicked.connect(self.insert_variable)
        editor_toolbar.addWidget(variable_btn)
        
        # Adjuntar archivo
        attach_btn = QPushButton("📎 Adjuntar Archivo")
        attach_btn.clicked.connect(self.attach_file)
        editor_toolbar.addWidget(attach_btn)
        
        editor_toolbar.addStretch()
        
        # Verificar cumplimiento
        check_btn = QPushButton("✅ Verificar")
        check_btn.clicked.connect(self.check_compliance)
        editor_toolbar.addWidget(check_btn)
        
        content_layout.addLayout(editor_toolbar)
        
        # Editor de texto
        self.content_editor = QTextEdit()
        self.content_editor.setPlaceholderText(
            "Escriba el contenido del mensaje aquí...\n\n"
            "Use {nombre}, {email}, {empresa} para personalizar el mensaje."
        )
        content_layout.addWidget(self.content_editor)
        
        # Variables detectadas
        self.variables_label = QLabel("Variables: ninguna")
        self.variables_label.setStyleSheet("color: #666; padding: 5px;")
        content_layout.addWidget(self.variables_label)
        
        content_group.setLayout(content_layout)
        right_layout.addWidget(content_group)
        
        # Vista previa
        preview_group = QGroupBox("Vista Previa")
        preview_layout = QVBoxLayout()
        
        # Selector de contacto para preview
        preview_contact_layout = QHBoxLayout()
        preview_contact_layout.addWidget(QLabel("Contacto de prueba:"))
        self.preview_contact_combo = QComboBox()
        self.preview_contact_combo.currentIndexChanged.connect(self.update_preview)
        preview_contact_layout.addWidget(self.preview_contact_combo)
        preview_layout.addLayout(preview_contact_layout)
        
        # Texto de vista previa
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setStyleSheet("background-color: #f8f9fa; border: 1px solid #ddd;")
        preview_layout.addWidget(self.preview_text)
        
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        # Botones de acción
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        save_btn = QPushButton("💾 Guardar Plantilla")
        save_btn.clicked.connect(self.save_template)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        actions_layout.addWidget(save_btn)
        
        right_layout.addLayout(actions_layout)
        
        right_panel.setLayout(right_layout)
        
        # Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Conectar eventos
        self.content_editor.textChanged.connect(self.on_content_changed)
        
        # Cargar contactos para preview
        self.load_preview_contacts()
    
    def load_templates(self):
        """Cargar lista de plantillas"""
        try:
            templates = self.template_model.get_templates()
            self.templates_list.clear()
            
            for template in templates:
                item = QListWidgetItem(f"📄 {template['name']}")
                item.setData(Qt.ItemDataRole.UserRole, template)
                self.templates_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Error cargando plantillas: {e}")
    
    def load_template(self, item: QListWidgetItem):
        """Cargar plantilla seleccionada"""
        template = item.data(Qt.ItemDataRole.UserRole)
        if template:
            self.current_template_id = template['id']
            self.name_input.setText(template['name'])
            self.content_editor.setText(template['content'])
            self.update_preview()
    
    def new_template(self):
        """Crear nueva plantilla"""
        self.current_template_id = None
        self.name_input.clear()
        self.content_editor.clear()
        self.preview_text.clear()
        self.name_input.setFocus()
    
    def save_template(self):
        """Guardar plantilla actual"""
        name = self.name_input.text().strip()
        content = self.content_editor.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "El nombre de la plantilla es requerido")
            return
        
        if not content:
            QMessageBox.warning(self, "Error", "El contenido de la plantilla es requerido")
            return
        
        try:
            # Detectar variables
            variables = re.findall(r'\{([^}]+)\}', content)
            variables_json = json.dumps(list(set(variables)))
            
            user = auth_manager.get_current_user()
            
            if self.current_template_id:
                # Actualizar plantilla existente
                success = self.template_model.update_template(
                    self.current_template_id,
                    name,
                    content,
                    variables_json
                )
                action = 'UPDATE'
            else:
                # Crear nueva plantilla
                self.current_template_id = self.template_model.create_template(
                    name,
                    content,
                    variables_json,
                    user['id']
                )
                success = self.current_template_id is not None
                action = 'CREATE'
            
            if success:
                QMessageBox.information(self, "Éxito", "Plantilla guardada exitosamente")
                self.load_templates()
                self.template_saved.emit()
                
                if self.activity_logger:
                    self.activity_logger.log_template(name, action)
            else:
                QMessageBox.critical(self, "Error", "Error guardando plantilla")
                
        except Exception as e:
            logger.error(f"Error guardando plantilla: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando plantilla: {str(e)}")
    
    def delete_template(self):
        """Eliminar plantilla seleccionada"""
        current_item = self.templates_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Aviso", "Seleccione una plantilla para eliminar")
            return
        
        template = current_item.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar la plantilla '{template['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.template_model.delete_template(template['id']):
                    QMessageBox.information(self, "Éxito", "Plantilla eliminada")
                    self.load_templates()
                    self.new_template()
                    
                    if self.activity_logger:
                        self.activity_logger.log_template(template['name'], 'DELETE')
                else:
                    QMessageBox.critical(self, "Error", "Error eliminando plantilla")
                    
            except Exception as e:
                logger.error(f"Error eliminando plantilla: {e}")
                QMessageBox.critical(self, "Error", f"Error eliminando plantilla: {str(e)}")
    
    def insert_variable(self):
        """Insertar variable en el cursor"""
        variables = ['nombre', 'email', 'empresa', 'telefono']
        
        dialog = VariableDialog(variables, self)
        if dialog.exec():
            variable = dialog.get_selected_variable()
            if variable:
                cursor = self.content_editor.textCursor()
                cursor.insertText(f"{{{variable}}}")
    
    def attach_file(self):
        """Adjuntar archivo a la plantilla"""
        QMessageBox.information(
            self,
            "Función en Desarrollo",
            "La función de adjuntar archivos estará disponible próximamente."
        )
    
    def check_compliance(self):
        """Verificar cumplimiento de la plantilla"""
        content = self.content_editor.toPlainText()
        
        if not content:
            QMessageBox.warning(self, "Aviso", "La plantilla está vacía")
            return
        
        result = self.twilio_service.check_template_compliance(content)
        
        if result['compliant']:
            QMessageBox.information(
                self,
                "Verificación Exitosa",
                "✅ La plantilla cumple con las políticas de WhatsApp"
            )
        else:
            warnings = "\n".join(f"⚠️ {warning}" for warning in result['warnings'])
            QMessageBox.warning(
                self,
                "Advertencias de Cumplimiento",
                f"La plantilla tiene las siguientes advertencias:\n\n{warnings}"
            )
    
    def on_content_changed(self):
        """Manejar cambios en el contenido"""
        content = self.content_editor.toPlainText()
        
        # Detectar variables
        variables = re.findall(r'\{([^}]+)\}', content)
        unique_variables = list(set(variables))
        
        if unique_variables:
            self.variables_label.setText(f"Variables: {', '.join(unique_variables)}")
        else:
            self.variables_label.setText("Variables: ninguna")
        
        # Actualizar vista previa
        self.update_preview()
    
    def load_preview_contacts(self):
        """Cargar contactos para vista previa"""
        try:
            contacts = self.contact_model.get_contacts(limit=10)
            
            self.preview_contact_combo.clear()
            self.preview_contact_combo.addItem("-- Seleccionar contacto --", None)
            
            for contact in contacts:
                display_name = contact.get('name', contact.get('phone_number', 'Sin nombre'))
                self.preview_contact_combo.addItem(display_name, contact)
                
        except Exception as e:
            logger.error(f"Error cargando contactos de preview: {e}")
    
    def update_preview(self):
        """Actualizar vista previa del mensaje"""
        content = self.content_editor.toPlainText()
        contact = self.preview_contact_combo.currentData()
        
        if not content:
            self.preview_text.clear()
            return
        
        if not contact:
            self.preview_text.setText(content)
            return
        
        # Preparar datos del contacto
        contact_data = {
            'nombre': contact.get('name', ''),
            'email': contact.get('email', ''),
            'empresa': contact.get('company', ''),
            'telefono': contact.get('phone_number', '')
        }
        
        # Agregar datos extra si existen
        if contact.get('extra_data'):
            try:
                extra = json.loads(contact['extra_data'])
                contact_data.update(extra)
            except:
                pass
        
        # Formatear mensaje
        formatted_message = self.twilio_service.format_message(content, contact_data)
        self.preview_text.setText(formatted_message)
    
    def add_template(self):
        """Método público para agregar plantilla (llamado desde toolbar)"""
        self.new_template()
    
    def set_activity_logger(self, logger):
        """Configurar logger de actividades"""
        self.activity_logger = logger


class VariableDialog(QDialog):
    """Diálogo para seleccionar variable"""
    
    def __init__(self, variables: List[str], parent=None):
        super().__init__(parent)
        self.variables = variables
        self.selected_variable = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle("Insertar Variable")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Seleccione una variable:"))
        
        self.variables_list = QListWidget()
        for var in self.variables:
            self.variables_list.addItem(f"{{{var}}} - {var.capitalize()}")
        
        self.variables_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.variables_list)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        insert_btn = QPushButton("Insertar")
        insert_btn.clicked.connect(self.accept)
        insert_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }
        """)
        buttons_layout.addWidget(insert_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def get_selected_variable(self):
        """Obtener variable seleccionada"""
        current_item = self.variables_list.currentItem()
        if current_item:
            # Extraer nombre de variable del texto
            text = current_item.text()
            return text.split(' - ')[0].strip('{}')
        return None

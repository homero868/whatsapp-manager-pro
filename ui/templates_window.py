# Actualización completa de ui/templates_window.py con soporte para archivos adjuntos

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QListWidget, QTextEdit, QLabel, QLineEdit,
                             QMessageBox, QDialog, QGroupBox, QListWidgetItem,
                             QSplitter, QFileDialog, QComboBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QProgressDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QIcon, QPixmap
import json
import re
import os
from typing import Dict, List, Optional

from database import TemplateModel, ContactModel, AttachmentModel
from twilio_service import TwilioService
from file_uploader import FileUploader
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
        self.attachment_model = AttachmentModel()
        self.twilio_service = TwilioService()
        self.file_uploader = FileUploader()
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
        
        # Archivos adjuntos
        attachments_group = QGroupBox("Archivos Adjuntos")
        attachments_layout = QVBoxLayout()
        
        # Tabla de archivos adjuntos
        self.attachments_table = QTableWidget()
        self.attachments_table.setColumnCount(5)
        self.attachments_table.setHorizontalHeaderLabels([
            "Archivo", "Tipo", "Tamaño", "Vista Previa", "Acciones"
        ])
        
        header = self.attachments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.attachments_table.setColumnWidth(1, 80)
        self.attachments_table.setColumnWidth(2, 80)
        self.attachments_table.setColumnWidth(3, 100)
        self.attachments_table.setColumnWidth(4, 100)
        
        self.attachments_table.setMaximumHeight(150)
        self.attachments_table.setAlternatingRowColors(True)
        
        attachments_layout.addWidget(self.attachments_table)
        
        # Información de archivos
        self.attachments_info = QLabel("Sin archivos adjuntos")
        self.attachments_info.setStyleSheet("color: #666; padding: 5px;")
        attachments_layout.addWidget(self.attachments_info)
        
        attachments_group.setLayout(attachments_layout)
        right_layout.addWidget(attachments_group)
        
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
            self.load_attachments()
            self.update_preview()
    
    def load_attachments(self):
        """Cargar archivos adjuntos de la plantilla actual"""
        if not self.current_template_id:
            self.attachments_table.setRowCount(0)
            self.attachments_info.setText("Sin archivos adjuntos")
            return
        
        try:
            attachments = self.attachment_model.get_template_attachments(self.current_template_id)
            
            # Limitar a 10 archivos según límite de WhatsApp
            if len(attachments) > 10:
                attachments = attachments[:10]
                logger.warning(f"La plantilla tiene más de 10 archivos. Solo se mostrarán los primeros 10.")
            
            self.attachments_table.setRowCount(len(attachments))
            
            total_size = 0
            
            for row, attachment in enumerate(attachments):
                # Nombre del archivo
                self.attachments_table.setItem(row, 0, QTableWidgetItem(attachment['file_name']))
                
                # Tipo
                self.attachments_table.setItem(row, 1, QTableWidgetItem(attachment['file_type']))
                
                # Tamaño
                size_mb = attachment['file_size'] / (1024 * 1024)
                self.attachments_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.2f} MB"))
                total_size += attachment['file_size']
                
                # Vista previa
                preview_btn = QPushButton("👁️ Ver")
                preview_btn.clicked.connect(lambda checked, path=attachment['file_path']: self.preview_file(path))
                self.attachments_table.setCellWidget(row, 3, preview_btn)
                
                # Acciones
                delete_btn = QPushButton("🗑️ Eliminar")
                delete_btn.clicked.connect(lambda checked, att_id=attachment['id']: self.delete_attachment(att_id))
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        padding: 4px 8px;
                        border-radius: 3px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: #c82333;
                    }
                """)
                self.attachments_table.setCellWidget(row, 4, delete_btn)
            
            # Actualizar información con límite de WhatsApp
            total_size_mb = total_size / (1024 * 1024)
            info_text = f"{len(attachments)} archivo(s) - Tamaño total: {total_size_mb:.2f} MB"
            
            if len(attachments) >= 10:
                info_text += " (Límite máximo de WhatsApp: 10 archivos)"
            
            self.attachments_info.setText(info_text)
            
        except Exception as e:
            logger.error(f"Error cargando archivos adjuntos: {e}")
    
    def new_template(self):
        """Crear nueva plantilla"""
        self.current_template_id = None
        self.name_input.clear()
        self.content_editor.clear()
        self.preview_text.clear()
        self.attachments_table.setRowCount(0)
        self.attachments_info.setText("Sin archivos adjuntos")
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
            f"¿Está seguro de eliminar la plantilla '{template['name']}'?\n"
            "También se eliminarán todos los archivos adjuntos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Eliminar archivos adjuntos
                self.attachment_model.delete_template_attachments(template['id'])
                
                # Eliminar plantilla
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
        if not self.current_template_id:
            # Si no hay plantilla actual, guardar primero
            reply = QMessageBox.question(
                self,
                "Guardar Plantilla",
                "Debe guardar la plantilla antes de adjuntar archivos.\n"
                "¿Desea guardar ahora?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.save_template()
                if not self.current_template_id:
                    return
            else:
                return
        
        # Verificar límite de archivos de WhatsApp
        current_attachments = self.attachment_model.get_template_attachments(self.current_template_id)
        if len(current_attachments) >= 10:
            QMessageBox.warning(
                self,
                "Límite de archivos alcanzado",
                "WhatsApp permite un máximo de 10 archivos por mensaje.\n"
                "Debe eliminar algún archivo antes de agregar uno nuevo."
            )
            return
        
        # Seleccionar archivo
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        # Crear filtro de archivos según tipos permitidos por WhatsApp
        filter_groups = {
            "Imágenes (WhatsApp)": ["jpg", "jpeg", "png"],
            "Documentos": ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt"],
            "Audio": ["mp3", "aac", "ogg", "opus", "amr"],
            "Video": ["mp4", "3gp"]
        }
        
        filters = []
        for group, exts in filter_groups.items():
            filter_str = f"{group} ({' '.join('*.' + ext for ext in exts)})"
            filters.append(filter_str)
        
        # Agregar filtro para todos los archivos permitidos
        all_extensions = []
        for exts in filter_groups.values():
            all_extensions.extend(exts)
        filters.insert(0, "Todos los archivos permitidos (*." + " *.".join(all_extensions) + ")")
        
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Seleccionar archivo",
            "",
            ";;".join(filters)
        )
        
        if not file_path:
            return
        
        # Procesar archivo
        self.process_file_attachment(file_path)
    
    def process_file_attachment(self, file_path: str):
        """Procesar archivo adjunto"""
        try:
            # Mostrar diálogo de progreso
            progress = QProgressDialog("Procesando archivo...", "Cancelar", 0, 100, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            progress.setValue(20)
            
            # Obtener nombre original
            original_name = os.path.basename(file_path)
            
            # Guardar archivo
            success, message, file_info = self.file_uploader.save_file(
                file_path, original_name, self.current_template_id
            )
            
            progress.setValue(60)
            
            if not success:
                progress.close()
                QMessageBox.critical(self, "Error", message)
                return
            
            # Guardar en base de datos
            attachment_id = self.attachment_model.create_attachment(
                template_id=self.current_template_id,
                file_name=file_info['file_name'],
                file_path=file_info['file_path'],
                file_type=file_info['file_type'],
                file_size=file_info['file_size'],
                mime_type=file_info['mime_type']
            )
            
            progress.setValue(80)
            
            if attachment_id:
                # Obtener URL pública usando el servidor local
                public_url = self.file_uploader.get_file_url(file_info['file_path'])
                if public_url:
                    self.attachment_model.update_attachment_url(attachment_id, public_url)
                    logger.info(f"URL pública generada: {public_url}")
                else:
                    logger.warning("No se pudo generar URL pública para el archivo")
                
                progress.setValue(100)
                progress.close()
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Archivo '{original_name}' adjuntado exitosamente.\n"
                    f"Total de archivos: {len(self.attachment_model.get_template_attachments(self.current_template_id))}"
                )
                
                # Recargar archivos adjuntos
                self.load_attachments()
                
                if self.activity_logger:
                    self.activity_logger.log(
                        'ATTACHMENT_ADD',
                        f"Archivo adjuntado a plantilla: {original_name}"
                    )
            else:
                progress.close()
                # Si falla, eliminar archivo físico
                self.file_uploader.delete_file(file_info['file_path'])
                QMessageBox.critical(self, "Error", "Error guardando información del archivo")
                
        except Exception as e:
            logger.error(f"Error procesando archivo adjunto: {e}")
            QMessageBox.critical(self, "Error", f"Error procesando archivo: {str(e)}")
    
    def delete_attachment(self, attachment_id: int):
        """Eliminar archivo adjunto"""
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            "¿Está seguro de eliminar este archivo adjunto?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.attachment_model.delete_attachment(attachment_id):
                    QMessageBox.information(self, "Éxito", "Archivo eliminado")
                    self.load_attachments()
                else:
                    QMessageBox.critical(self, "Error", "Error eliminando archivo")
                    
            except Exception as e:
                logger.error(f"Error eliminando archivo: {e}")
                QMessageBox.critical(self, "Error", f"Error eliminando archivo: {str(e)}")
    
    def preview_file(self, file_path: str):
        """Mostrar vista previa del archivo"""
        try:
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "Error", "El archivo no existe")
                return
            
            # Obtener tipo de archivo
            ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
            
            # Para imágenes, mostrar en un diálogo
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                dialog = ImagePreviewDialog(file_path, self)
                dialog.exec()
            else:
                # Para otros archivos, abrir con aplicación predeterminada
                import subprocess
                import platform
                
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.call(['open', file_path])
                else:  # Linux
                    subprocess.call(['xdg-open', file_path])
                    
        except Exception as e:
            logger.error(f"Error mostrando vista previa: {e}")
            QMessageBox.critical(self, "Error", f"Error mostrando archivo: {str(e)}")
    
    def check_compliance(self):
        """Verificar cumplimiento de la plantilla"""
        content = self.content_editor.toPlainText()
        
        if not content:
            QMessageBox.warning(self, "Aviso", "La plantilla está vacía")
            return
        
        result = self.twilio_service.check_template_compliance(content)
        
        # Verificar también archivos adjuntos
        if self.current_template_id:
            attachments = self.attachment_model.get_template_attachments(self.current_template_id)
            if attachments:
                total_size = sum(att['file_size'] for att in attachments) / (1024 * 1024)
                if total_size > 16:
                    result['compliant'] = False
                    result['warnings'].append(
                        f"El tamaño total de archivos adjuntos ({total_size:.1f}MB) "
                        "excede el límite recomendado de 16MB"
                    )
        
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
        
        # Agregar información de archivos adjuntos
        if self.current_template_id:
            attachments = self.attachment_model.get_template_attachments(self.current_template_id)
            if attachments:
                formatted_message += "\n\n📎 Archivos adjuntos:"
                for att in attachments:
                    formatted_message += f"\n• {att['file_name']}"
        
        self.preview_text.setText(formatted_message)
    
    def add_template(self):
        """Método público para agregar plantilla (llamado desde toolbar)"""
        self.new_template()
    
    def cancel_campaign(self, campaign_id: int):
        """Cancelar campaña programada"""
        reply = QMessageBox.question(
            self,
            "Confirmar Cancelación",
            "¿Está seguro de cancelar esta campaña programada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.scheduler.cancel_campaign(campaign_id):
                QMessageBox.information(self, "Éxito", "Campaña cancelada")
                self.load_campaigns()
            else:
                QMessageBox.critical(self, "Error", "Error cancelando campaña")
    
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


class ImagePreviewDialog(QDialog):
    """Diálogo para vista previa de imágenes"""
    
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle("Vista Previa de Imagen")
        self.setMinimumSize(400, 400)
        
        layout = QVBoxLayout()
        
        # Etiqueta para la imagen
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1px solid #ddd; background-color: #f8f9fa;")
        
        # Cargar imagen
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            # Escalar imagen manteniendo proporción
            scaled_pixmap = pixmap.scaled(
                600, 600,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("No se pudo cargar la imagen")
        
        layout.addWidget(self.image_label)
        
        # Información de la imagen
        file_name = os.path.basename(self.image_path)
        file_size = os.path.getsize(self.image_path) / (1024 * 1024)
        info_label = QLabel(f"Archivo: {file_name} | Tamaño: {file_size:.2f} MB")
        info_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(info_label)
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

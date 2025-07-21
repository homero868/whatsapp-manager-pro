from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QDialog, QLabel, QLineEdit,
                             QComboBox, QDateTimeEdit, QGroupBox,
                             QProgressBar, QListWidget, QCheckBox,
                             QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime, QTimer
from PyQt6.QtGui import QColor
from datetime import datetime
import logging

from database import CampaignModel, TemplateModel, ContactModel
from message_scheduler import MessageScheduler
from auth import auth_manager

logger = logging.getLogger(__name__)

class CampaignsWindow(QWidget):
    campaign_started = pyqtSignal(int)
    
    def __init__(self, scheduler: MessageScheduler):
        super().__init__()
        self.scheduler = scheduler
        self.campaign_model = CampaignModel()
        self.template_model = TemplateModel()
        self.contact_model = ContactModel()
        self.activity_logger = None
        
        self.active_campaigns = {}
        self.init_ui()
        self.load_campaigns()
        
        # Timer para actualizar progreso
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(2000)  # Actualizar cada 2 segundos
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Tabs para diferentes vistas
        self.tabs = QTabWidget()
        
        # Tab de campañas activas
        self.active_tab = self.create_active_tab()
        self.tabs.addTab(self.active_tab, "📨 Campañas Activas")
        
        # Tab de historial
        self.history_tab = self.create_history_tab()
        self.tabs.addTab(self.history_tab, "📋 Historial")
        
        # Tab de programadas
        self.scheduled_tab = self.create_scheduled_tab()
        self.tabs.addTab(self.scheduled_tab, "📅 Programadas")
        
        layout.addWidget(self.tabs)
        
        # Barra de herramientas principal
        toolbar_layout = QHBoxLayout()
        
        # Botón envío rápido
        quick_btn = QPushButton("⚡ Envío Rápido")
        quick_btn.clicked.connect(self.quick_send)
        quick_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #20BD5A;
            }
        """)
        toolbar_layout.addWidget(quick_btn)
        
        # Botón programar
        schedule_btn = QPushButton("📅 Programar Campaña")
        schedule_btn.clicked.connect(self.schedule_campaign)
        schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        toolbar_layout.addWidget(schedule_btn)
        
        toolbar_layout.addStretch()
        
        # Botón actualizar
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.load_campaigns)
        toolbar_layout.addWidget(refresh_btn)
        
        layout.insertLayout(0, toolbar_layout)
        
        self.setLayout(layout)
    
    def create_active_tab(self):
        """Crear tab de campañas activas"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Lista de campañas activas
        self.active_campaigns_list = QVBoxLayout()
        layout.addLayout(self.active_campaigns_list)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_history_tab(self):
        """Crear tab de historial"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Tabla de historial
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Campaña", "Fecha", "Total", "Enviados", "Entregados", "Leídos", "Fallidos"
        ])
        
        header = self.history_table.horizontalHeader()
        
        # Configurar modo de redimensionamiento ANTES de establecer anchos
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        
        # Establecer anchos de columna
        self.history_table.setColumnWidth(0, 250)  # Campaña
        self.history_table.setColumnWidth(1, 150)  # Fecha
        self.history_table.setColumnWidth(2, 80)   # Total
        self.history_table.setColumnWidth(3, 80)   # Enviados
        self.history_table.setColumnWidth(4, 90)   # Entregados
        self.history_table.setColumnWidth(5, 80)   # Leídos
        self.history_table.setColumnWidth(6, 80)   # Fallidos
        
        # Configurar header para evitar movimientos
        header.setHighlightSections(False)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setStretchLastSection(True)
        
        # Configurar altura de filas
        self.history_table.verticalHeader().setDefaultSectionSize(35)
        self.history_table.verticalHeader().setVisible(True)
        
        # Estilos mejorados
        self.history_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                font-size: 13px;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #ddd;
                border-bottom: 1px solid #ddd;
            }
            QHeaderView::section:hover {
                background-color: #e9ecef;
            }
        """)
        
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSortingEnabled(False)  # Se habilitará después de cargar datos
        
        layout.addWidget(self.history_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_scheduled_tab(self):
        """Crear tab de campañas programadas"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Tabla de programadas
        self.scheduled_table = QTableWidget()
        self.scheduled_table.setColumnCount(5)
        self.scheduled_table.setHorizontalHeaderLabels([
            "Campaña", "Plantilla", "Fecha Programada", "Contactos", "Acciones"
        ])
        
        header = self.scheduled_table.horizontalHeader()
        
        # Configurar modo de redimensionamiento
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        # Establecer anchos
        self.scheduled_table.setColumnWidth(0, 200)  # Campaña
        self.scheduled_table.setColumnWidth(1, 200)  # Plantilla
        self.scheduled_table.setColumnWidth(2, 150)  # Fecha
        self.scheduled_table.setColumnWidth(3, 100)  # Contactos
        self.scheduled_table.setColumnWidth(4, 120)  # Acciones
        
        # Configurar header
        header.setHighlightSections(False)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setStretchLastSection(True)
        
        # Aplicar los mismos estilos
        self.scheduled_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                font-size: 13px;
                selection-background-color: #e3f2fd;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #ddd;
                border-bottom: 1px solid #ddd;
            }
            QHeaderView::section:hover {
                background-color: #e9ecef;
            }
        """)
        
        self.scheduled_table.setSortingEnabled(False)
        
        layout.addWidget(self.scheduled_table)
        
        widget.setLayout(layout)
        return widget
    
    def load_campaigns(self):
        """Cargar todas las campañas"""
        try:
            # Deshabilitar ordenamiento temporalmente
            self.history_table.setSortingEnabled(False)
            self.scheduled_table.setSortingEnabled(False)
            
            # Cargar estadísticas para historial
            stats = self.campaign_model.get_campaign_stats()
            self.populate_history_table(stats)
            
            # Cargar campañas programadas
            self.load_scheduled_campaigns()
            
            # Actualizar campañas activas
            self.update_active_campaigns()
            
            # Habilitar ordenamiento
            self.history_table.setSortingEnabled(True)
            self.scheduled_table.setSortingEnabled(True)
            
        except Exception as e:
            logger.error(f"Error cargando campañas: {e}")
    
    def populate_history_table(self, stats):
        """Poblar tabla de historial"""
        self.history_table.setRowCount(len(stats))
        
        for row, stat in enumerate(stats):
            self.history_table.setItem(row, 0, QTableWidgetItem(stat['name']))
            self.history_table.setItem(row, 1, QTableWidgetItem(
                stat['created_at'].strftime('%Y-%m-%d %H:%M') if stat['created_at'] else ''
            ))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(stat['total_contacts'])))
            self.history_table.setItem(row, 3, QTableWidgetItem(str(stat['sent_messages'])))
            self.history_table.setItem(row, 4, QTableWidgetItem(str(stat['delivered'])))
            self.history_table.setItem(row, 5, QTableWidgetItem(str(stat.get('read', 0))))
            self.history_table.setItem(row, 6, QTableWidgetItem(str(stat['failed'])))
            
            # Colorear filas según estado
            if stat['failed'] > 0:
                for col in range(7):
                    item = self.history_table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 230, 230))
    
    def load_scheduled_campaigns(self):
        """Cargar campañas programadas"""
        # Por implementar: cargar campañas con estado 'pending' y scheduled_at futuro
        pass
    
    def update_active_campaigns(self):
        """Actualizar lista de campañas activas"""
        # Limpiar lista actual
        while self.active_campaigns_list.count():
            child = self.active_campaigns_list.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Agregar campañas activas
        for campaign_id, campaign_widget in self.active_campaigns.items():
            self.active_campaigns_list.addWidget(campaign_widget)
    
    def quick_send(self):
        """Envío rápido de mensajes"""
        dialog = QuickSendDialog(self.template_model, self.contact_model, self)
        if dialog.exec():
            template_id = dialog.get_template_id()
            contact_ids = dialog.get_selected_contact_ids()
            
            if template_id and contact_ids:
                try:
                    user = auth_manager.get_current_user()
                    
                    # Crear campaña inmediata
                    campaign_id = self.scheduler.send_immediate(
                        template_id,
                        contact_ids,
                        user['id'],
                        callback=self.on_campaign_update
                    )
                    
                    # Crear widget de progreso
                    campaign_widget = CampaignProgressWidget(
                        campaign_id,
                        f"Envío Rápido - {datetime.now().strftime('%H:%M')}",
                        len(contact_ids)
                    )
                    
                    self.active_campaigns[campaign_id] = campaign_widget
                    self.update_active_campaigns()
                    
                    self.campaign_started.emit(campaign_id)
                    
                    QMessageBox.information(
                        self,
                        "Campaña Iniciada",
                        f"Se ha iniciado el envío a {len(contact_ids)} contactos"
                    )
                    
                    if self.activity_logger:
                        self.activity_logger.log_campaign(
                            f"Envío Rápido",
                            "START",
                            f"{len(contact_ids)} contactos"
                        )
                    
                except Exception as e:
                    logger.error(f"Error iniciando envío rápido: {e}")
                    QMessageBox.critical(self, "Error", f"Error iniciando envío: {str(e)}")
    
    def schedule_campaign(self):
        """Programar nueva campaña"""
        dialog = ScheduleCampaignDialog(self.template_model, self)
        if dialog.exec():
            name = dialog.get_campaign_name()
            template_id = dialog.get_template_id()
            scheduled_dt = dialog.get_scheduled_datetime()
            
            try:
                user = auth_manager.get_current_user()
                
                campaign_id = self.scheduler.schedule_campaign(
                    name,
                    template_id,
                    scheduled_dt,
                    user['id'],
                    callback=self.on_campaign_update
                )
                
                QMessageBox.information(
                    self,
                    "Campaña Programada",
                    f"La campaña '{name}' ha sido programada para:\n"
                    f"{scheduled_dt.strftime('%Y-%m-%d %H:%M')}"
                )
                
                self.load_campaigns()
                
                if self.activity_logger:
                    self.activity_logger.log_campaign(name, "SCHEDULE", 
                                                    scheduled_dt.strftime('%Y-%m-%d %H:%M'))
                
            except Exception as e:
                logger.error(f"Error programando campaña: {e}")
                QMessageBox.critical(self, "Error", f"Error programando campaña: {str(e)}")
    
    def on_campaign_update(self, status, data):
        """Callback para actualizaciones de campaña"""
        logger.info(f"Actualización de campaña: {status} - {data}")
    
    def update_progress(self):
        """Actualizar progreso de campañas activas"""
        for campaign_id, widget in list(self.active_campaigns.items()):
            progress = self.scheduler.get_campaign_progress(campaign_id)
            widget.update_progress(progress)
            
            # Si la campaña terminó, moverla a historial
            if progress['progress_percentage'] >= 100:
                self.active_campaigns.pop(campaign_id)
                self.update_active_campaigns()
                self.load_campaigns()
    
    def refresh_templates(self):
        """Actualizar lista de plantillas (llamado desde templates_window)"""
        # Se actualizará cuando se abra un diálogo
        pass
    
    def refresh_contacts(self):
        """Actualizar lista de contactos (llamado desde contacts_window)"""
        # Se actualizará cuando se abra un diálogo
        pass
    
    def set_activity_logger(self, logger):
        """Configurar logger de actividades"""
        self.activity_logger = logger


class CampaignProgressWidget(QGroupBox):
    """Widget para mostrar progreso de campaña"""
    
    def __init__(self, campaign_id: int, name: str, total_contacts: int):
        super().__init__(name)
        self.campaign_id = campaign_id
        self.total_contacts = total_contacts
        self.init_ui()
    
    def init_ui(self):
        """Inicializar interfaz"""
        layout = QVBoxLayout()
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Estadísticas
        stats_layout = QHBoxLayout()
        
        self.pending_label = QLabel("⏳ Pendientes: 0")
        stats_layout.addWidget(self.pending_label)
        
        self.sent_label = QLabel("✉️ Enviados: 0")
        stats_layout.addWidget(self.sent_label)
        
        self.delivered_label = QLabel("✅ Entregados: 0")
        stats_layout.addWidget(self.delivered_label)
        
        self.failed_label = QLabel("❌ Fallidos: 0")
        stats_layout.addWidget(self.failed_label)
        
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #25D366;
            }
        """)
    
    def update_progress(self, progress: dict):
        """Actualizar progreso"""
        self.progress_bar.setValue(int(progress['progress_percentage']))
        self.pending_label.setText(f"⏳ Pendientes: {progress['pending']}")
        self.sent_label.setText(f"✉️ Enviados: {progress['sent']}")
        self.delivered_label.setText(f"✅ Entregados: {progress['delivered']}")
        self.failed_label.setText(f"❌ Fallidos: {progress['failed']}")


class QuickSendDialog(QDialog):
    """Diálogo para envío rápido"""
    
    def __init__(self, template_model, contact_model, parent=None):
        super().__init__(parent)
        self.template_model = template_model
        self.contact_model = contact_model
        self.selected_contact_ids = []
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle("Envío Rápido")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        
        # Selección de plantilla
        template_group = QGroupBox("Seleccionar Plantilla")
        template_layout = QVBoxLayout()
        
        self.template_combo = QComboBox()
        template_layout.addWidget(self.template_combo)
        
        template_group.setLayout(template_layout)
        layout.addWidget(template_group)
        
        # Selección de contactos
        contacts_group = QGroupBox("Seleccionar Contactos")
        contacts_layout = QVBoxLayout()
        
        # Opciones de selección
        select_layout = QHBoxLayout()
        
        self.all_contacts_radio = QCheckBox("Todos los contactos")
        self.all_contacts_radio.toggled.connect(self.on_selection_changed)
        select_layout.addWidget(self.all_contacts_radio)
        
        self.select_contacts_radio = QCheckBox("Seleccionar contactos")
        self.select_contacts_radio.setChecked(True)
        self.select_contacts_radio.toggled.connect(self.on_selection_changed)
        select_layout.addWidget(self.select_contacts_radio)
        
        contacts_layout.addLayout(select_layout)
        
        # Lista de contactos
        self.contacts_list = QListWidget()
        self.contacts_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        contacts_layout.addWidget(self.contacts_list)
        
        # Información de selección
        self.selection_info = QLabel("0 contactos seleccionados")
        contacts_layout.addWidget(self.selection_info)
        
        contacts_group.setLayout(contacts_layout)
        layout.addWidget(contacts_group)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        self.send_btn = QPushButton("Enviar Ahora")
        self.send_btn.clicked.connect(self.process_send)
        self.send_btn.setEnabled(False)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #20BD5A;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        buttons_layout.addWidget(self.send_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Conectar eventos
        self.contacts_list.itemSelectionChanged.connect(self.update_selection_info)
        self.template_combo.currentIndexChanged.connect(self.validate_form)
    
    def load_data(self):
        """Cargar plantillas y contactos"""
        try:
            # Cargar plantillas
            templates = self.template_model.get_templates()
            self.template_combo.clear()
            self.template_combo.addItem("-- Seleccionar plantilla --", None)
            
            for template in templates:
                self.template_combo.addItem(template['name'], template['id'])
            
            # Cargar contactos
            contacts = self.contact_model.get_contacts()
            self.contacts_list.clear()
            
            for contact in contacts:
                display_text = f"{contact.get('name', 'Sin nombre')} - {contact['phone_number']}"
                item = self.contacts_list.addItem(display_text)
                self.contacts_list.item(self.contacts_list.count() - 1).setData(
                    Qt.ItemDataRole.UserRole, contact['id']
                )
                
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
    
    def on_selection_changed(self):
        """Manejar cambio en tipo de selección"""
        if self.all_contacts_radio.isChecked():
            self.contacts_list.setEnabled(False)
            self.contacts_list.clearSelection()
            
            # Seleccionar todos los IDs
            self.selected_contact_ids = []
            for i in range(self.contacts_list.count()):
                item = self.contacts_list.item(i)
                self.selected_contact_ids.append(item.data(Qt.ItemDataRole.UserRole))
            
            self.selection_info.setText(f"{len(self.selected_contact_ids)} contactos seleccionados")
        else:
            self.contacts_list.setEnabled(True)
            self.update_selection_info()
        
        self.validate_form()
    
    def update_selection_info(self):
        """Actualizar información de selección"""
        if not self.all_contacts_radio.isChecked():
            selected_items = self.contacts_list.selectedItems()
            self.selected_contact_ids = [
                item.data(Qt.ItemDataRole.UserRole) for item in selected_items
            ]
            self.selection_info.setText(f"{len(self.selected_contact_ids)} contactos seleccionados")
        
        self.validate_form()
    
    def validate_form(self):
        """Validar formulario"""
        template_selected = self.template_combo.currentData() is not None
        contacts_selected = len(self.selected_contact_ids) > 0
        
        self.send_btn.setEnabled(template_selected and contacts_selected)
    
    def process_send(self):
        """Procesar envío"""
        if not self.selected_contact_ids:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar al menos un contacto")
            return
        
        template_id = self.template_combo.currentData()
        if not template_id:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar una plantilla")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Envío",
            f"¿Está seguro de enviar mensajes a {len(self.selected_contact_ids)} contactos?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
    
    def get_template_id(self):
        """Obtener ID de plantilla seleccionada"""
        return self.template_combo.currentData()
    
    def get_selected_contact_ids(self):
        """Obtener IDs de contactos seleccionados"""
        return self.selected_contact_ids


class ScheduleCampaignDialog(QDialog):
    """Diálogo para programar campaña"""
    
    def __init__(self, template_model, parent=None):
        super().__init__(parent)
        self.template_model = template_model
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle("Programar Campaña")
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout()
        
        # Nombre de campaña
        layout.addWidget(QLabel("Nombre de la Campaña:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Promoción Navideña")
        layout.addWidget(self.name_input)
        
        # Plantilla
        layout.addWidget(QLabel("Plantilla:"))
        self.template_combo = QComboBox()
        layout.addWidget(self.template_combo)
        
        # Fecha y hora
        layout.addWidget(QLabel("Fecha y Hora de Envío:"))
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        layout.addWidget(self.datetime_edit)
        
        # Información
        info_label = QLabel(
            "ℹ️ La campaña se enviará a todos los contactos disponibles "
            "en la fecha y hora especificada."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 10px; background-color: #f8f9fa;")
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        self.schedule_btn = QPushButton("Programar")
        self.schedule_btn.clicked.connect(self.validate_and_accept)
        self.schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        buttons_layout.addWidget(self.schedule_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_templates(self):
        """Cargar plantillas"""
        try:
            templates = self.template_model.get_templates()
            self.template_combo.clear()
            self.template_combo.addItem("-- Seleccionar plantilla --", None)
            
            for template in templates:
                self.template_combo.addItem(template['name'], template['id'])
                
        except Exception as e:
            logger.error(f"Error cargando plantillas: {e}")
    
    def validate_and_accept(self):
        """Validar y aceptar"""
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Aviso", "El nombre de la campaña es requerido")
            return
        
        if self.template_combo.currentData() is None:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar una plantilla")
            return
        
        if self.datetime_edit.dateTime() <= QDateTime.currentDateTime():
            QMessageBox.warning(self, "Aviso", "La fecha debe ser futura")
            return
        
        self.accept()
    
    def get_campaign_name(self):
        """Obtener nombre de campaña"""
        return self.name_input.text().strip()
    
    def get_template_id(self):
        """Obtener ID de plantilla"""
        return self.template_combo.currentData()
    
    def get_scheduled_datetime(self):
        """Obtener fecha y hora programada"""
        return self.datetime_edit.dateTime().toPyDateTime()

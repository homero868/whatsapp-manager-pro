from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QFileDialog, QDialog, QLabel,
                             QLineEdit, QComboBox, QTextEdit, QGroupBox,
                             QSpinBox, QCheckBox, QProgressDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QEvent
from PyQt6.QtGui import QColor, QPainter
import pandas as pd
from typing import List, Dict
import json

from database import ContactModel
from excel_handler import ExcelHandler
from auth import auth_manager
import logging

logger = logging.getLogger(__name__)


class CustomHeaderView(QHeaderView):
    """Header personalizado que evita ordenamiento en columnas específicas"""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.non_sortable_columns = set()
    
    def set_non_sortable_column(self, logical_index):
        """Marcar una columna como no ordenable"""
        self.non_sortable_columns.add(logical_index)
    
    def paintSection(self, painter, rect, logicalIndex):
        """Pintar sección del header - ocultar indicador en columnas no ordenables"""
        if logicalIndex in self.non_sortable_columns:
            # Guardar el indicador actual
            current_indicator = self.sortIndicatorSection()
            
            # Temporalmente cambiar el indicador si está en esta columna
            if current_indicator == logicalIndex:
                self.setSortIndicator(-1, self.sortIndicatorOrder())
            
            # Pintar la sección
            super().paintSection(painter, rect, logicalIndex)
            
            # Restaurar el indicador
            if current_indicator == logicalIndex:
                self.setSortIndicator(current_indicator, self.sortIndicatorOrder())
        else:
            super().paintSection(painter, rect, logicalIndex)
    
    def mousePressEvent(self, event):
        """Interceptar clics del mouse"""
        logical_index = self.logicalIndexAt(event.pos())
        if logical_index in self.non_sortable_columns:
            # Ignorar el clic en columnas no ordenables
            event.ignore()
            return
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Interceptar liberación del mouse"""
        logical_index = self.logicalIndexAt(event.pos())
        if logical_index in self.non_sortable_columns:
            # Ignorar el evento en columnas no ordenables
            event.ignore()
            return
        super().mouseReleaseEvent(event)

class ContactsWindow(QWidget):
    contacts_updated = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.contact_model = ContactModel()
        self.excel_handler = ExcelHandler()
        self.activity_logger = None
        self.current_page = 1
        self.page_size = 100
        self.init_ui()
        self.load_contacts()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        # Botón importar
        import_btn = QPushButton("📥 Importar Excel")
        import_btn.clicked.connect(self.import_contacts)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        toolbar_layout.addWidget(import_btn)
        
        # Botón exportar
        export_btn = QPushButton("📤 Exportar Excel")
        export_btn.clicked.connect(self.export_contacts)
        toolbar_layout.addWidget(export_btn)
        
        # Botón agregar
        add_btn = QPushButton("➕ Agregar Contacto")
        add_btn.clicked.connect(self.add_contact)
        toolbar_layout.addWidget(add_btn)
        
        # Botón eliminar
        delete_btn = QPushButton("🗑️ Eliminar Seleccionados")
        delete_btn.clicked.connect(self.delete_selected)
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
        toolbar_layout.addWidget(delete_btn)
        
        toolbar_layout.addStretch()
        
        # Buscar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar contacto...")
        self.search_input.setMaximumWidth(300)
        self.search_input.textChanged.connect(self.filter_contacts)
        toolbar_layout.addWidget(self.search_input)
        
        layout.addLayout(toolbar_layout)
        
        # Tabla de contactos
        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(6)
        self.contacts_table.setHorizontalHeaderLabels([
            "Seleccionar", "Teléfono", "Nombre", "Email", "Empresa", "Fecha Registro"
        ])
        
        # Reemplazar el header con uno personalizado
        custom_header = CustomHeaderView(Qt.Orientation.Horizontal, self.contacts_table)
        custom_header.set_non_sortable_column(0)  # Columna "Seleccionar" no ordenable
        self.contacts_table.setHorizontalHeader(custom_header)
        
        # Configurar tabla
        header = self.contacts_table.horizontalHeader()
        
        # IMPORTANTE: Configurar modo de redimensionamiento ANTES de establecer anchos
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        
        # Establecer anchos de columna DESPUÉS del modo de redimensionamiento
        self.contacts_table.setColumnWidth(0, 120)   # Seleccionar (aumentado de 100 a 120)
        self.contacts_table.setColumnWidth(1, 150)   # Teléfono
        # Columnas 2, 3, 4 se ajustan automáticamente con Stretch
        self.contacts_table.setColumnWidth(5, 150)   # Fecha
        
        # Configurar header para evitar movimientos al ordenar
        header.setHighlightSections(False)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        header.setStretchLastSection(True)
        
        # Configurar altura de filas
        self.contacts_table.verticalHeader().setDefaultSectionSize(40)
        self.contacts_table.verticalHeader().setMinimumSectionSize(35)
        
        # Mostrar números de fila
        self.contacts_table.verticalHeader().setVisible(True)
        
        # Estilos para mejorar la visualización
        self.contacts_table.setStyleSheet("""
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
                padding-right: 25px; /* Espacio extra para el indicador */
                font-weight: bold;
                border: none;
                border-right: 1px solid #ddd;
                border-bottom: 1px solid #ddd;
            }
            QHeaderView::section:hover {
                background-color: #e9ecef;
            }
            QTableWidget QTableCornerButton::section {
                background-color: #f8f9fa;
                border: none;
                border-right: 1px solid #ddd;
                border-bottom: 1px solid #ddd;
            }
            QHeaderView::down-arrow {
                subcontrol-position: right center;
                subcontrol-origin: padding;
                right: 5px;
                width: 10px;
                height: 10px;
            }
            QHeaderView::up-arrow {
                subcontrol-position: right center;
                subcontrol-origin: padding;
                right: 5px;
                width: 10px;
                height: 10px;
            }
        """)
        
        self.contacts_table.setAlternatingRowColors(True)
        self.contacts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # IMPORTANTE: Deshabilitar el ordenamiento hasta que los datos estén cargados
        self.contacts_table.setSortingEnabled(False)
        
        # Establecer ordenamiento inicial en una columna que no sea la de checkbox
        self.contacts_table.sortByColumn(1, Qt.SortOrder.AscendingOrder)  # Ordenar por Teléfono inicialmente
        
        layout.addWidget(self.contacts_table)
        
        # Información de contactos
        self.info_label = QLabel("Total contactos: 0")
        self.info_label.setStyleSheet("padding: 10px; background-color: #f8f9fa;")
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
    
    def load_contacts(self):
        """Cargar contactos en la tabla"""
        try:
            # Deshabilitar ordenamiento temporalmente
            self.contacts_table.setSortingEnabled(False)
            
            contacts = self.contact_model.get_contacts()
            self.populate_table(contacts)
            self.update_info()
            
            # Habilitar ordenamiento después de cargar datos
            self.contacts_table.setSortingEnabled(True)
            
            # Establecer ordenamiento inicial si no hay uno definido
            if self.contacts_table.horizontalHeader().sortIndicatorSection() == -1:
                self.contacts_table.sortByColumn(5, Qt.SortOrder.DescendingOrder)  # Ordenar por fecha descendente
            
        except Exception as e:
            logger.error(f"Error cargando contactos: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando contactos: {str(e)}")
    
    def populate_table(self, contacts: List[Dict]):
        """Poblar tabla con contactos"""
        # Guardar estado de ordenamiento actual
        current_sort_column = self.contacts_table.horizontalHeader().sortIndicatorSection()
        current_sort_order = self.contacts_table.horizontalHeader().sortIndicatorOrder()
        
        self.contacts_table.setRowCount(len(contacts))
        
        for row, contact in enumerate(contacts):
            # Checkbox - Usar QTableWidgetItem con CheckState en lugar de QWidget
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.CheckState.Unchecked)
            checkbox_item.setData(Qt.ItemDataRole.UserRole, contact['id'])
            checkbox_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.contacts_table.setItem(row, 0, checkbox_item)
            
            # Datos
            self.contacts_table.setItem(row, 1, QTableWidgetItem(contact.get('phone_number', '')))
            self.contacts_table.setItem(row, 2, QTableWidgetItem(contact.get('name', '')))
            self.contacts_table.setItem(row, 3, QTableWidgetItem(contact.get('email', '')))
            self.contacts_table.setItem(row, 4, QTableWidgetItem(contact.get('company', '')))
            
            # Fecha formateada
            fecha_item = QTableWidgetItem(
                contact.get('created_at', '').strftime('%Y-%m-%d %H:%M') 
                if contact.get('created_at') else ''
            )
            self.contacts_table.setItem(row, 5, fecha_item)
            
            # Alinear texto al centro verticalmente
            for col in range(1, 6):
                item = self.contacts_table.item(row, col)
                if item:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        # Restaurar estado de ordenamiento
        if current_sort_column >= 0:
            self.contacts_table.sortItems(current_sort_column, current_sort_order)
    
    def get_selected_contact_ids(self):
        """Obtener IDs de contactos seleccionados"""
        selected_ids = []
        
        for row in range(self.contacts_table.rowCount()):
            checkbox_item = self.contacts_table.item(row, 0)
            if checkbox_item and checkbox_item.checkState() == Qt.CheckState.Checked:
                selected_ids.append(checkbox_item.data(Qt.ItemDataRole.UserRole))
        
        return selected_ids
    
    def import_contacts(self):
        """Importar contactos desde Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo Excel",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return
        
        try:
            # Validar archivo
            validation = self.excel_handler.validate_excel_file(file_path)
            if not validation['valid']:
                QMessageBox.critical(self, "Error", validation['error'])
                return
            
            # Mostrar diálogo de importación
            import_dialog = ImportDialog(file_path, self.excel_handler, self)
            if import_dialog.exec():
                contacts = import_dialog.get_contacts()
                errors = import_dialog.get_errors()
                
                if contacts:
                    # Guardar contactos
                    progress = QProgressDialog("Guardando contactos...", "Cancelar", 0, len(contacts), self)
                    progress.setWindowModality(Qt.WindowModality.WindowModal)
                    progress.show()
                    
                    user = auth_manager.get_current_user()
                    saved = self.contact_model.create_contacts(contacts, user['id'])
                    
                    progress.close()
                    
                    # Mostrar resultado
                    message = f"Se importaron {saved} contactos exitosamente."
                    if errors:
                        message += f"\n\nSe encontraron {len(errors)} errores:\n"
                        message += "\n".join(errors[:5])
                        if len(errors) > 5:
                            message += f"\n... y {len(errors) - 5} errores más"
                    
                    QMessageBox.information(self, "Importación Completa", message)
                    
                    # Actualizar tabla
                    self.load_contacts()
                    self.contacts_updated.emit()
                    
                    # Registrar actividad
                    if self.activity_logger:
                        self.activity_logger.log_import(file_path, saved, len(errors))
                else:
                    QMessageBox.warning(self, "Sin contactos", "No se encontraron contactos para importar.")
                
        except Exception as e:
            logger.error(f"Error importando contactos: {e}")
            QMessageBox.critical(self, "Error", f"Error importando contactos: {str(e)}")
    
    def export_contacts(self):
        """Exportar contactos a Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo Excel",
            "contactos.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            contacts = self.contact_model.get_contacts()
            if self.excel_handler.export_contacts_to_excel(contacts, file_path):
                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Se exportaron {len(contacts)} contactos a:\n{file_path}"
                )
                
                if self.activity_logger:
                    self.activity_logger.log('EXPORT_CONTACTS', 
                                           f"Exportados {len(contacts)} contactos")
            else:
                QMessageBox.critical(self, "Error", "Error exportando contactos")
                
        except Exception as e:
            logger.error(f"Error exportando contactos: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando contactos: {str(e)}")
    
    def add_contact(self):
        """Agregar nuevo contacto"""
        dialog = ContactDialog(self)
        if dialog.exec():
            contact_data = dialog.get_contact_data()
            
            try:
                user = auth_manager.get_current_user()
                self.contact_model.create_contacts([contact_data], user['id'])
                
                QMessageBox.information(self, "Éxito", "Contacto agregado exitosamente")
                
                self.load_contacts()
                self.contacts_updated.emit()
                
                if self.activity_logger:
                    self.activity_logger.log('ADD_CONTACT', 
                                           f"Contacto: {contact_data.get('phone_number')}")
                
            except Exception as e:
                logger.error(f"Error agregando contacto: {e}")
                QMessageBox.critical(self, "Error", f"Error agregando contacto: {str(e)}")
    
    def delete_selected(self):
        """Eliminar contactos seleccionados"""
        selected_ids = self.get_selected_contact_ids()
        
        if not selected_ids:
            QMessageBox.warning(self, "Aviso", "No hay contactos seleccionados")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Está seguro de eliminar {len(selected_ids)} contacto(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for contact_id in selected_ids:
                    self.contact_model.delete_contact(contact_id)
                
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Se eliminaron {len(selected_ids)} contacto(s)"
                )
                
                self.load_contacts()
                self.contacts_updated.emit()
                
                if self.activity_logger:
                    self.activity_logger.log('DELETE_CONTACTS', 
                                           f"Eliminados {len(selected_ids)} contactos")
                
            except Exception as e:
                logger.error(f"Error eliminando contactos: {e}")
                QMessageBox.critical(self, "Error", f"Error eliminando contactos: {str(e)}")
    
    def filter_contacts(self, text: str):
        """Filtrar contactos en la tabla"""
        for row in range(self.contacts_table.rowCount()):
            match = False
            for col in range(1, self.contacts_table.columnCount()):
                item = self.contacts_table.item(row, col)
                if item and text.lower() in item.text().lower():
                    match = True
                    break
            
            self.contacts_table.setRowHidden(row, not match)
    
    def update_info(self):
        """Actualizar información de contactos"""
        total = self.contact_model.get_contact_count()
        visible = sum(1 for row in range(self.contacts_table.rowCount()) 
                     if not self.contacts_table.isRowHidden(row))
        
        self.info_label.setText(f"Total contactos: {total} | Mostrando: {visible}")
    
    def set_activity_logger(self, logger):
        """Configurar logger de actividades"""
        self.activity_logger = logger


class ImportDialog(QDialog):
    """Diálogo para importar contactos desde Excel"""
    
    def __init__(self, file_path: str, excel_handler: ExcelHandler, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.excel_handler = excel_handler
        self.df = None
        self.columns = []
        self.contacts = []
        self.errors = []
        
        self.init_ui()
        self.load_file()
    
    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle("Importar Contactos desde Excel")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # Información del archivo
        self.file_label = QLabel(f"Archivo: {self.file_path}")
        self.file_label.setStyleSheet("padding: 10px; background-color: #f8f9fa;")
        layout.addWidget(self.file_label)
        
        # Configuración de columnas
        config_group = QGroupBox("Configuración de Columnas")
        config_layout = QVBoxLayout()
        
        # Columna de teléfono
        phone_layout = QHBoxLayout()
        phone_layout.addWidget(QLabel("Columna de Teléfono:"))
        self.phone_combo = QComboBox()
        self.phone_combo.currentIndexChanged.connect(self.preview_data)
        phone_layout.addWidget(self.phone_combo)
        config_layout.addLayout(phone_layout)
        
        # Mapeo de columnas
        self.column_mappings = {}
        for field in ['name', 'email', 'company']:
            field_layout = QHBoxLayout()
            field_layout.addWidget(QLabel(f"Columna de {field.capitalize()}:"))
            combo = QComboBox()
            combo.addItem("-- No asignar --", -1)
            combo.currentIndexChanged.connect(self.preview_data)
            self.column_mappings[field] = combo
            field_layout.addWidget(combo)
            config_layout.addLayout(field_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Vista previa
        preview_group = QGroupBox("Vista Previa de Datos")
        preview_layout = QVBoxLayout()
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        # Configurar altura de filas
        self.preview_table.verticalHeader().setDefaultSectionSize(30)
        self.preview_table.setAlternatingRowColors(True)
        preview_layout.addWidget(self.preview_table)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Información de importación
        self.import_info = QTextEdit()
        self.import_info.setReadOnly(True)
        self.import_info.setMaximumHeight(100)
        layout.addWidget(self.import_info)
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        self.import_btn = QPushButton("Importar Contactos")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self.process_import)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        buttons_layout.addWidget(self.import_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_file(self):
        """Cargar archivo Excel"""
        try:
            self.df, self.columns = self.excel_handler.read_excel_file(self.file_path)
            
            # Llenar combo de teléfono
            self.phone_combo.clear()
            self.phone_combo.addItems(self.columns)
            
            # Llenar combos de mapeo de columnas
            for combo in self.column_mappings.values():
                combo.clear()
                # Primero agregar la opción de no asignar
                combo.addItem("-- No asignar --", -1)
                # Luego agregar todas las columnas disponibles
                for idx, col in enumerate(self.columns):
                    combo.addItem(col, idx)
            
            # Obtener estadísticas de columnas
            stats = self.excel_handler.get_column_statistics(self.df)
            
            # Auto-detectar columna de teléfono
            for stat in stats:
                if stat['potential_phone_column']:
                    self.phone_combo.setCurrentIndex(stat['column_index'])
                    break
            
            # Actualizar información
            self.file_label.setText(
                f"Archivo: {self.file_path} - "
                f"{len(self.df)} filas, {len(self.columns)} columnas"
            )
            
            self.preview_data()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando archivo: {str(e)}")
            self.reject()
    
    def preview_data(self):
        """Mostrar vista previa de datos"""
        if self.df is None:
            return
        
        # Obtener índices de columnas seleccionadas
        phone_col = self.phone_combo.currentIndex()
        
        if phone_col < 0:
            self.import_btn.setEnabled(False)
            return
        
        # Obtener mapeo de columnas
        column_mapping = {}
        for field, combo in self.column_mappings.items():
            # Obtener el índice de la columna seleccionada
            if combo.currentIndex() > 0:  # 0 es "-- No asignar --"
                column_mapping[field] = combo.currentIndex() - 1  # Restar 1 porque agregamos "-- No asignar --"
            else:
                column_mapping[field] = -1  # No asignado
        
        # Mostrar vista previa
        preview_data = self.excel_handler.preview_data(self.df, 5)
        
        # Configurar tabla de vista previa
        headers = ["Teléfono"]
        for field, col_idx in column_mapping.items():
            if col_idx >= 0:
                headers.append(field.capitalize())
        
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)
        self.preview_table.setRowCount(len(preview_data))
        
        # Llenar tabla
        for row_idx, row_data in enumerate(preview_data):
            # Teléfono
            if phone_col < len(row_data):
                phone = str(row_data[phone_col])
                self.preview_table.setItem(row_idx, 0, QTableWidgetItem(phone))
            
            # Otros campos
            col_idx = 1
            for field, mapping_idx in column_mapping.items():
                if mapping_idx >= 0 and mapping_idx < len(row_data):
                    value = str(row_data[mapping_idx]) if row_data[mapping_idx] else ""
                    self.preview_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
                    col_idx += 1
        
        # Habilitar botón de importar
        self.import_btn.setEnabled(True)
        
        # Actualizar información
        self.update_import_info()
    
    def update_import_info(self):
        """Actualizar información de importación"""
        info = f"Total de filas: {len(self.df)}\n"
        info += f"Columna de teléfono: {self.columns[self.phone_combo.currentIndex()]}\n"
        
        mapped_fields = []
        for field, combo in self.column_mappings.items():
            if combo.currentIndex() > 0:  # Si se seleccionó algo diferente a "-- No asignar --"
                col_idx = combo.currentIndex() - 1
                mapped_fields.append(f"{field}: {self.columns[col_idx]}")
        
        if mapped_fields:
            info += "Campos mapeados: " + ", ".join(mapped_fields)
        
        self.import_info.setText(info)
    
    def process_import(self):
        """Procesar importación"""
        try:
            # Obtener configuración
            phone_col = self.phone_combo.currentIndex()
            column_mapping = {}
            
            for field, combo in self.column_mappings.items():
                # Si el índice es mayor a 0, significa que se seleccionó una columna
                if combo.currentIndex() > 0:
                    column_mapping[field] = combo.currentIndex() - 1  # Restar 1 por "-- No asignar --"
            
            # Extraer contactos
            self.contacts, self.errors = self.excel_handler.extract_contacts(
                self.df, phone_col, column_mapping
            )
            
            if self.contacts:
                QMessageBox.information(
                    self,
                    "Vista Previa de Importación",
                    f"Se encontraron {len(self.contacts)} contactos válidos.\n"
                    f"Errores: {len(self.errors)}\n\n"
                    "Presione OK para continuar con la importación."
                )
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Sin Contactos Válidos",
                    "No se encontraron contactos válidos para importar.\n\n"
                    "Verifique que la columna de teléfono sea correcta."
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error procesando datos: {str(e)}")
    
    def get_contacts(self):
        """Obtener contactos procesados"""
        return self.contacts
    
    def get_errors(self):
        """Obtener errores de importación"""
        return self.errors


class ContactDialog(QDialog):
    """Diálogo para agregar/editar contacto"""
    
    def __init__(self, parent=None, contact=None):
        super().__init__(parent)
        self.contact = contact
        self.init_ui()
        
        if contact:
            self.load_contact()
    
    def init_ui(self):
        """Inicializar interfaz"""
        self.setWindowTitle("Agregar contacto" if not self.contact else "Editar contacto")
        self.setFixedSize(400, 400)
        
        layout = QVBoxLayout()
        
        # Campo de teléfono
        layout.addWidget(QLabel("Teléfono:"))
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+502 1234 5678")
        layout.addWidget(self.phone_input)
        
        # Campo de nombre
        layout.addWidget(QLabel("Nombre:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)
        
        # Campo de email
        layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        layout.addWidget(self.email_input)
        
        # Campo de empresa
        layout.addWidget(QLabel("Empresa:"))
        self.company_input = QLineEdit()
        layout.addWidget(self.company_input)
        
        layout.addStretch()
        
        # Botones
        buttons_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Guardar")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #25D366;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #20BD5A;
            }
        """)
        save_btn.clicked.connect(self.save_contact)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def load_contact(self):
        """Cargar datos del contacto"""
        if self.contact:
            self.phone_input.setText(self.contact.get('phone_number', ''))
            self.name_input.setText(self.contact.get('name', ''))
            self.email_input.setText(self.contact.get('email', ''))
            self.company_input.setText(self.contact.get('company', ''))
    
    def save_contact(self):
        """Validar y guardar contacto"""
        phone = self.phone_input.text().strip()
        
        if not phone:
            QMessageBox.warning(self, "Error", "El teléfono es requerido")
            return
        
        # Validar teléfono
        from twilio_service import TwilioService
        twilio = TwilioService()
        validation = twilio.validate_phone_number(phone)
        
        if not validation['valid']:
            QMessageBox.warning(self, "Error", validation['error'])
            return
        
        self.accept()
    
    def get_contact_data(self):
        """Obtener datos del contacto"""
        from twilio_service import TwilioService
        twilio = TwilioService()
        validation = twilio.validate_phone_number(self.phone_input.text().strip())
        
        return {
            'phone_number': validation['formatted'],
            'name': self.name_input.text().strip() or None,
            'email': self.email_input.text().strip() or None,
            'company': self.company_input.text().strip() or None
        }

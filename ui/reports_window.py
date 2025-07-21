from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QDateEdit, QComboBox, QGroupBox,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont
import pandas as pd
from datetime import datetime, timedelta
import logging

from database import MessageModel, CampaignModel, ContactModel, ActivityLogModel
from auth import auth_manager

logger = logging.getLogger(__name__)

class ReportsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.message_model = MessageModel()
        self.campaign_model = CampaignModel()
        self.contact_model = ContactModel()
        self.activity_log_model = ActivityLogModel()
        self.init_ui()
        self.load_summary()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título
        title_label = QLabel("📊 Reportes y Estadísticas")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;")
        layout.addWidget(title_label)
        
        # Filtros
        filters_group = QGroupBox("Filtros")
        filters_layout = QHBoxLayout()
        
        # Rango de fechas
        filters_layout.addWidget(QLabel("Desde:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.dateChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.date_from)
        
        filters_layout.addWidget(QLabel("Hasta:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.apply_filters)
        filters_layout.addWidget(self.date_to)
        
        # Tipo de reporte
        filters_layout.addWidget(QLabel("Tipo:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            "Resumen General",
            "Por Campaña",
            "Por Estado",
            "Actividad de Usuarios"
        ])
        self.report_type_combo.currentIndexChanged.connect(self.change_report_type)
        filters_layout.addWidget(self.report_type_combo)
        
        filters_layout.addStretch()
        
        # Botón exportar
        export_btn = QPushButton("📤 Exportar Excel")
        export_btn.clicked.connect(self.export_report)
        filters_layout.addWidget(export_btn)
        
        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)
        
        # Panel de resumen
        self.summary_panel = self.create_summary_panel()
        layout.addWidget(self.summary_panel)
        
        # Tabla de detalles
        self.details_table = QTableWidget()
        self.details_table.setAlternatingRowColors(True)
        
        # Configurar altura de filas
        self.details_table.verticalHeader().setDefaultSectionSize(35)
        self.details_table.verticalHeader().setVisible(True)
        
        # Configurar header para evitar movimientos
        header = self.details_table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionsClickable(True)
        header.setSortIndicatorShown(True)
        
        # Estilos mejorados para prevenir saltos visuales
        self.details_table.setStyleSheet("""
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
            QTableWidget QTableCornerButton::section {
                background-color: #f8f9fa;
                border: none;
                border-right: 1px solid #ddd;
                border-bottom: 1px solid #ddd;
            }
        """)
        
        # Deshabilitar ordenamiento inicialmente
        self.details_table.setSortingEnabled(False)
        
        layout.addWidget(self.details_table)
        
        self.setLayout(layout)
    
    def create_summary_panel(self):
        """Crear panel de resumen"""
        panel = QGroupBox("Resumen")
        layout = QHBoxLayout()
        
        # Métricas principales
        self.metrics = {
            'total_sent': self.create_metric_widget("📨 Total Enviados", "0"),
            'delivered': self.create_metric_widget("✅ Entregados", "0"),
            'read': self.create_metric_widget("👁️ Leídos", "0"),
            'failed': self.create_metric_widget("❌ Fallidos", "0"),
            'delivery_rate': self.create_metric_widget("📊 Tasa de Entrega", "0%"),
            'read_rate': self.create_metric_widget("📖 Tasa de Lectura", "0%")
        }
        
        for metric in self.metrics.values():
            layout.addWidget(metric)
        
        panel.setLayout(layout)
        return panel
    
    def create_metric_widget(self, title: str, value: str):
        """Crear widget de métrica"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #666; font-size: 12px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #25D366;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        widget.setLayout(layout)
        widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                min-width: 120px;
            }
        """)
        
        return widget
    
    def load_summary(self):
        """Cargar resumen de estadísticas"""
        try:
            stats = self.message_model.get_message_stats()
            
            if stats:
                # Actualizar métricas con valores por defecto si son None
                total = stats.get('total') or 0
                delivered = stats.get('delivered') or 0
                read = stats.get('read') or 0
                failed = stats.get('failed') or 0
                sent = stats.get('sent') or 0
            else:
                # Si no hay estadísticas, usar valores por defecto
                total = delivered = read = failed = sent = 0
            
            self.update_metric('total_sent', str(sent))
            self.update_metric('delivered', str(delivered))
            self.update_metric('read', str(read))
            self.update_metric('failed', str(failed))
            
            # Calcular tasas
            if sent > 0:
                delivery_rate = (delivered / sent) * 100
                self.update_metric('delivery_rate', f"{delivery_rate:.1f}%")
            else:
                self.update_metric('delivery_rate', "0%")
            
            if delivered > 0:
                read_rate = (read / delivered) * 100
                self.update_metric('read_rate', f"{read_rate:.1f}%")
            else:
                self.update_metric('read_rate', "0%")
            
            # Cargar tabla según tipo seleccionado
            self.load_details_table()
            
        except Exception as e:
            logger.error(f"Error cargando resumen: {e}")
            # Establecer valores por defecto en caso de error
            self.update_metric('total_sent', "0")
            self.update_metric('delivered', "0")
            self.update_metric('read', "0")
            self.update_metric('failed', "0")
            self.update_metric('delivery_rate', "0%")
            self.update_metric('read_rate', "0%")
    
    def update_metric(self, metric_name: str, value: str):
        """Actualizar valor de métrica"""
        if metric_name in self.metrics:
            value_label = self.metrics[metric_name].findChild(QLabel, "value")
            if value_label:
                value_label.setText(value)
    
    def apply_filters(self):
        """Aplicar filtros y recargar datos"""
        self.load_summary()
    
    def change_report_type(self):
        """Cambiar tipo de reporte"""
        self.load_details_table()
    
    def load_details_table(self):
        """Cargar tabla de detalles según tipo de reporte"""
        # Deshabilitar ordenamiento mientras se cargan datos
        self.details_table.setSortingEnabled(False)
        
        report_type = self.report_type_combo.currentText()
        
        if report_type == "Resumen General":
            self.load_general_summary()
        elif report_type == "Por Campaña":
            self.load_campaign_report()
        elif report_type == "Por Estado":
            self.load_status_report()
        elif report_type == "Actividad de Usuarios":
            self.load_activity_report()
        
        # Habilitar ordenamiento después de cargar datos
        self.details_table.setSortingEnabled(True)
    
    def load_general_summary(self):
        """Cargar resumen general"""
        try:
            # Configurar tabla
            self.details_table.setColumnCount(2)
            self.details_table.setHorizontalHeaderLabels(["Métrica", "Valor"])
            
            # Configurar anchos de columna
            header = self.details_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setStretchLastSection(True)
            
            self.details_table.setColumnWidth(0, 300)
            self.details_table.setColumnWidth(1, 150)
            
            # Obtener estadísticas
            stats = self.message_model.get_message_stats()
            contact_count = self.contact_model.get_contact_count()
            campaigns = self.campaign_model.get_campaign_stats()
            
            # Valores con manejo de None
            total_sent = stats.get('sent', 0) if stats else 0
            total_delivered = stats.get('delivered', 0) if stats else 0
            total_read = stats.get('read', 0) if stats else 0
            total_failed = stats.get('failed', 0) if stats else 0
            total_messages = stats.get('total', 0) if stats else 0
            pending = total_messages - total_sent - total_failed
            
            # Datos para la tabla
            data = [
                ("Total de Contactos", str(contact_count)),
                ("Total de Campañas", str(len(campaigns))),
                ("Mensajes Enviados", str(total_sent)),
                ("Mensajes Entregados", str(total_delivered)),
                ("Mensajes Leídos", str(total_read)),
                ("Mensajes Fallidos", str(total_failed)),
                ("Mensajes Pendientes", str(max(0, pending)))
            ]
            
            self.details_table.setRowCount(len(data))
            
            for row, (metric, value) in enumerate(data):
                self.details_table.setItem(row, 0, QTableWidgetItem(metric))
                self.details_table.setItem(row, 1, QTableWidgetItem(value))
                
                # Alinear valores a la derecha
                value_item = self.details_table.item(row, 1)
                if value_item:
                    value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
        except Exception as e:
            logger.error(f"Error cargando resumen general: {e}")
            self.details_table.setRowCount(0)
    
    def load_campaign_report(self):
        """Cargar reporte por campaña"""
        try:
            # Configurar tabla
            self.details_table.setColumnCount(8)
            self.details_table.setHorizontalHeaderLabels([
                "Campaña", "Fecha", "Total", "Enviados", "Entregados", 
                "Leídos", "Fallidos", "Tasa Éxito"
            ])
            
            # Configurar anchos de columna
            header = self.details_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            for i in range(1, 8):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
            header.setStretchLastSection(True)
            
            self.details_table.setColumnWidth(0, 250)  # Campaña
            self.details_table.setColumnWidth(1, 150)  # Fecha
            self.details_table.setColumnWidth(2, 80)   # Total
            self.details_table.setColumnWidth(3, 80)   # Enviados
            self.details_table.setColumnWidth(4, 90)   # Entregados
            self.details_table.setColumnWidth(5, 80)   # Leídos
            self.details_table.setColumnWidth(6, 80)   # Fallidos
            self.details_table.setColumnWidth(7, 100)  # Tasa Éxito
            
            # Obtener datos
            campaigns = self.campaign_model.get_campaign_stats()
            self.details_table.setRowCount(len(campaigns))
            
            for row, campaign in enumerate(campaigns):
                self.details_table.setItem(row, 0, QTableWidgetItem(campaign['name']))
                self.details_table.setItem(row, 1, QTableWidgetItem(
                    campaign['created_at'].strftime('%Y-%m-%d %H:%M') 
                    if campaign['created_at'] else ''
                ))
                
                # Números alineados a la derecha
                for col, value in enumerate([
                    campaign['total_contacts'],
                    campaign['sent_messages'],
                    campaign['delivered'],
                    campaign['read'],
                    campaign['failed']
                ], start=2):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    self.details_table.setItem(row, col, item)
                
                # Calcular tasa de éxito
                if campaign['sent_messages'] > 0:
                    success_rate = (campaign['delivered'] / campaign['sent_messages']) * 100
                    rate_item = QTableWidgetItem(f"{success_rate:.1f}%")
                else:
                    rate_item = QTableWidgetItem("0%")
                
                rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.details_table.setItem(row, 7, rate_item)
            
        except Exception as e:
            logger.error(f"Error cargando reporte por campaña: {e}")
    
    def load_status_report(self):
        """Cargar reporte por estado"""
        try:
            # Configurar tabla
            self.details_table.setColumnCount(3)
            self.details_table.setHorizontalHeaderLabels(["Estado", "Cantidad", "Porcentaje"])
            
            # Configurar anchos
            header = self.details_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setStretchLastSection(True)
            
            self.details_table.setColumnWidth(0, 200)
            self.details_table.setColumnWidth(1, 100)
            self.details_table.setColumnWidth(2, 100)
            
            # Obtener estadísticas
            stats = self.message_model.get_message_stats()
            
            if stats:
                total = stats.get('total', 0) or 0
                sent = stats.get('sent', 0) or 0
                delivered = stats.get('delivered', 0) or 0
                read = stats.get('read', 0) or 0
                failed = stats.get('failed', 0) or 0
                pending = max(0, total - sent - failed)
            else:
                total = sent = delivered = read = failed = pending = 0
            
            # Estados y sus valores
            statuses = [
                ("Pendientes", pending),
                ("Enviados", sent),
                ("Entregados", delivered),
                ("Leídos", read),
                ("Fallidos", failed)
            ]
            
            self.details_table.setRowCount(len(statuses))
            
            for row, (status, count) in enumerate(statuses):
                self.details_table.setItem(row, 0, QTableWidgetItem(status))
                
                # Cantidad alineada a la derecha
                count_item = QTableWidgetItem(str(count))
                count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.details_table.setItem(row, 1, count_item)
                
                # Calcular porcentaje
                if total > 0:
                    percentage = (count / total) * 100
                    perc_item = QTableWidgetItem(f"{percentage:.1f}%")
                else:
                    perc_item = QTableWidgetItem("0%")
                
                perc_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.details_table.setItem(row, 2, perc_item)
            
        except Exception as e:
            logger.error(f"Error cargando reporte por estado: {e}")
            self.details_table.setRowCount(0)
    
    def load_activity_report(self):
        """Cargar reporte de actividad de usuarios"""
        try:
            # Configurar tabla
            self.details_table.setColumnCount(4)
            self.details_table.setHorizontalHeaderLabels([
                "Usuario", "Acción", "Detalles", "Fecha"
            ])
            
            # Configurar anchos
            header = self.details_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setStretchLastSection(True)
            
            self.details_table.setColumnWidth(0, 100)
            self.details_table.setColumnWidth(1, 150)
            self.details_table.setColumnWidth(2, 350)
            self.details_table.setColumnWidth(3, 150)
            
            # Obtener actividades recientes
            user = auth_manager.get_current_user()
            activities = self.activity_log_model.get_recent_activities(limit=100)
            
            self.details_table.setRowCount(len(activities))
            
            for row, activity in enumerate(activities):
                # Usuario
                user_id = activity.get('user_id', '')
                self.details_table.setItem(row, 0, QTableWidgetItem(f"Usuario {user_id}"))
                
                # Acción
                self.details_table.setItem(row, 1, QTableWidgetItem(activity.get('action', '')))
                
                # Detalles
                details = activity.get('details', '')
                if details:
                    try:
                        import json
                        details_dict = json.loads(details)
                        details = str(details_dict)
                    except:
                        pass
                self.details_table.setItem(row, 2, QTableWidgetItem(str(details)))
                
                # Fecha
                created_at = activity.get('created_at')
                if created_at:
                    self.details_table.setItem(row, 3, QTableWidgetItem(
                        created_at.strftime('%Y-%m-%d %H:%M:%S')
                    ))
            
        except Exception as e:
            logger.error(f"Error cargando reporte de actividad: {e}")
    
    def export_report(self):
        """Exportar reporte actual a Excel"""
        try:
            # Obtener datos de la tabla
            rows = self.details_table.rowCount()
            cols = self.details_table.columnCount()
            
            if rows == 0:
                QMessageBox.warning(self, "Aviso", "No hay datos para exportar")
                return
            
            # Crear DataFrame
            data = []
            headers = []
            
            # Obtener headers
            for col in range(cols):
                header = self.details_table.horizontalHeaderItem(col)
                headers.append(header.text() if header else f"Columna {col + 1}")
            
            # Obtener datos
            for row in range(rows):
                row_data = []
                for col in range(cols):
                    item = self.details_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            df = pd.DataFrame(data, columns=headers)
            
            # Solicitar ubicación para guardar
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Reporte",
                f"reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                # Exportar a Excel con formato
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Reporte')
                    
                    # Obtener worksheet
                    worksheet = writer.sheets['Reporte']
                    
                    # Ajustar anchos de columna
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
                
                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Reporte exportado exitosamente a:\n{file_path}"
                )
                
        except Exception as e:
            logger.error(f"Error exportando reporte: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando reporte: {str(e)}")
    
    def refresh_data(self):
        """Actualizar datos (llamado desde otras ventanas)"""
        self.load_summary()

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTextEdit, QComboBox, QLabel, QCheckBox,
                             QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor
import os
from config import Config
import logging

logger = logging.getLogger(__name__)

class LogsViewer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visor de Logs")
        self.setMinimumSize(800, 600)
        self.log_file_path = Config.LOG_FILE
        self.auto_scroll = True
        self.init_ui()
        self.load_logs()
        
        # Timer para actualización automática
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.refresh_logs)
        self.update_timer.start(2000)  # Actualizar cada 2 segundos
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        # Filtro de nivel
        toolbar_layout.addWidget(QLabel("Nivel:"))
        self.level_filter = QComboBox()
        self.level_filter.addItems(["TODOS", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_filter.setCurrentText("INFO")
        self.level_filter.currentTextChanged.connect(self.apply_filter)
        toolbar_layout.addWidget(self.level_filter)
        
        # Auto-scroll
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll")
        self.auto_scroll_checkbox.setChecked(True)
        self.auto_scroll_checkbox.toggled.connect(self.toggle_auto_scroll)
        toolbar_layout.addWidget(self.auto_scroll_checkbox)
        
        toolbar_layout.addStretch()
        
        # Botones
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.load_logs)
        toolbar_layout.addWidget(refresh_btn)
        
        clear_btn = QPushButton("🗑️ Limpiar Logs")
        clear_btn.clicked.connect(self.clear_logs)
        toolbar_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("📤 Exportar")
        export_btn.clicked.connect(self.export_logs)
        toolbar_layout.addWidget(export_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Área de texto para logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
            }
        """)
        layout.addWidget(self.log_text)
        
        # Información
        self.info_label = QLabel("Logs cargados: 0 líneas")
        self.info_label.setStyleSheet("padding: 5px; background-color: #f8f9fa;")
        layout.addWidget(self.info_label)
        
        self.setLayout(layout)
    
    def load_logs(self):
        """Cargar logs desde archivo"""
        try:
            if not os.path.exists(self.log_file_path):
                self.log_text.setPlainText("No se encontró archivo de logs.")
                return
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Aplicar filtro si es necesario
            if self.level_filter.currentText() != "TODOS":
                filtered_lines = []
                for line in content.split('\n'):
                    if self.level_filter.currentText() in line:
                        filtered_lines.append(line)
                content = '\n'.join(filtered_lines)
            
            # Aplicar colores según nivel
            self.display_colored_logs(content)
            
            # Actualizar información
            line_count = len(content.split('\n'))
            self.info_label.setText(f"Logs cargados: {line_count} líneas")
            
            # Auto-scroll al final
            if self.auto_scroll:
                cursor = self.log_text.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.log_text.setTextCursor(cursor)
                
        except Exception as e:
            logger.error(f"Error cargando logs: {e}")
            self.log_text.setPlainText(f"Error cargando logs: {str(e)}")
    
    def display_colored_logs(self, content):
        """Mostrar logs con colores según nivel"""
        self.log_text.clear()
        
        # Definir colores para cada nivel
        colors = {
            'DEBUG': '#808080',
            'INFO': '#00ff00',
            'WARNING': '#ffff00',
            'ERROR': '#ff0000',
            'CRITICAL': '#ff00ff'
        }
        
        for line in content.split('\n'):
            color = '#d4d4d4'  # Color por defecto
            
            # Buscar nivel en la línea
            for level, level_color in colors.items():
                if f' - {level} - ' in line:
                    color = level_color
                    break
            
            # Agregar línea con color
            self.log_text.append(f'<span style="color: {color};">{line}</span>')
    
    def apply_filter(self):
        """Aplicar filtro de nivel"""
        self.load_logs()
    
    def toggle_auto_scroll(self, checked):
        """Activar/desactivar auto-scroll"""
        self.auto_scroll = checked
    
    def refresh_logs(self):
        """Actualizar logs automáticamente"""
        if self.isVisible():
            # Guardar posición actual
            current_position = self.log_text.verticalScrollBar().value()
            
            # Recargar logs
            self.load_logs()
            
            # Restaurar posición si auto-scroll está desactivado
            if not self.auto_scroll:
                self.log_text.verticalScrollBar().setValue(current_position)
    
    def clear_logs(self):
        """Limpiar archivo de logs"""
        reply = QMessageBox.question(
            self,
            "Confirmar Limpieza",
            "¿Está seguro de que desea limpiar todos los logs?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Crear backup antes de limpiar
                import shutil
                from datetime import datetime
                
                backup_name = f"app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                backup_path = os.path.join(Config.LOG_FOLDER, backup_name)
                shutil.copy2(self.log_file_path, backup_path)
                
                # Limpiar archivo
                with open(self.log_file_path, 'w') as f:
                    f.write(f"=== Logs limpiados el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                
                logger.info("Logs limpiados por el usuario")
                
                self.load_logs()
                
                QMessageBox.information(
                    self,
                    "Logs Limpiados",
                    f"Los logs han sido limpiados.\n"
                    f"Se creó un backup en: {backup_name}"
                )
                
            except Exception as e:
                logger.error(f"Error limpiando logs: {e}")
                QMessageBox.critical(self, "Error", f"Error limpiando logs: {str(e)}")
    
    def export_logs(self):
        """Exportar logs a archivo"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar Logs",
                f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt)"
            )
            
            if file_path:
                # Obtener contenido actual (con filtros aplicados)
                content = self.log_text.toPlainText()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                QMessageBox.information(
                    self,
                    "Exportación Exitosa",
                    f"Logs exportados exitosamente a:\n{file_path}"
                )
                
        except Exception as e:
            logger.error(f"Error exportando logs: {e}")
            QMessageBox.critical(self, "Error", f"Error exportando logs: {str(e)}")
    
    def closeEvent(self, event):
        """Manejar cierre de ventana"""
        # Detener timer
        self.update_timer.stop()
        event.accept()

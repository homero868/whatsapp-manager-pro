from PyQt6.QtCore import Qt, QObject, QEvent, QTimer
from PyQt6.QtWidgets import (QPushButton, QCheckBox, QRadioButton, 
                            QComboBox, QToolButton, QLabel, QApplication,
                            QTabBar, QMenuBar, QMenu, QWidget,
                            QMainWindow, QDialog)
from PyQt6.QtGui import QAction

class GlobalCursorChanger(QObject):
    """Cambiador global de cursores para elementos clickeables"""
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.processed_widgets = set()
        
        # Instalar el filtro de eventos en la aplicación
        self.app.installEventFilter(self)
        
        # Timer para procesar widgets nuevos
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_all_widgets)
        self.timer.start(500)  # Verificar cada 500ms
    
    def process_all_widgets(self):
        """Procesar todos los widgets de todas las ventanas"""
        for window in self.app.topLevelWidgets():
            if isinstance(window, (QMainWindow, QDialog)):
                self.apply_cursors_to_widget(window)
    
    def apply_cursors_to_widget(self, widget):
        """Aplicar cursores recursivamente a un widget y sus hijos"""
        if widget in self.processed_widgets:
            return
            
        # Marcar como procesado
        self.processed_widgets.add(widget)
        
        # Aplicar cursor si es necesario
        if self.should_have_pointer_cursor(widget):
            widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Casos especiales
        if hasattr(widget, 'tabBar') and callable(widget.tabBar):
            try:
                tab_bar = widget.tabBar()
                if tab_bar:
                    tab_bar.setCursor(Qt.CursorShape.PointingHandCursor)
            except:
                pass
        
        if hasattr(widget, 'menuBar') and callable(widget.menuBar):
            try:
                menu_bar = widget.menuBar()
                if menu_bar:
                    menu_bar.setCursor(Qt.CursorShape.PointingHandCursor)
                    # Procesar acciones del menú
                    for action in menu_bar.actions():
                        if action.menu():
                            action.menu().setCursor(Qt.CursorShape.PointingHandCursor)
            except:
                pass
        
        # Procesar hijos
        for child in widget.findChildren(QWidget):
            if child not in self.processed_widgets:
                self.apply_cursors_to_widget(child)
    
    def should_have_pointer_cursor(self, widget):
        """Determinar si un widget debe tener cursor pointer"""
        clickable_types = (
            QPushButton,
            QCheckBox,
            QRadioButton,
            QComboBox,
            QToolButton,
            QTabBar,
            QMenuBar,
            QMenu
        )
        
        if isinstance(widget, clickable_types):
            return True
            
        # Para QLabel con links
        if isinstance(widget, QLabel):
            if widget.textInteractionFlags() & Qt.TextInteractionFlag.LinksAccessibleByMouse:
                return True
        
        return False
    
    def eventFilter(self, obj, event):
        """Filtrar eventos para procesar widgets nuevos"""
        if event.type() == QEvent.Type.Show and isinstance(obj, QWidget):
            # Cuando se muestra un nuevo widget, procesarlo
            QTimer.singleShot(100, lambda: self.apply_cursors_to_widget(obj))
        
        return super().eventFilter(obj, event)

def setup_global_cursors(app):
    """Configurar cursores globalmente en la aplicación"""
    # Crear e instalar el cambiador de cursores
    cursor_changer = GlobalCursorChanger(app)
    
    # No usar CSS para cursores ya que PyQt6 no lo soporta bien
    # El GlobalCursorChanger se encarga de todo programáticamente
    
    return cursor_changer

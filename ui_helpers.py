from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QPushButton, QCheckBox, QRadioButton, 
                            QComboBox, QToolButton, QWidget)

def apply_pointer_cursor(widget):
    """Aplicar cursor pointer a elementos clickeables y sus hijos"""
    # Lista de clases que deben tener cursor pointer
    clickable_types = (
        QPushButton,
        QCheckBox,
        QRadioButton,
        QComboBox,
        QToolButton
    )
    
    # Si el widget es clickeable, aplicar cursor
    if isinstance(widget, clickable_types):
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
    
    # Aplicar a labels con links
    if hasattr(widget, 'openExternalLinks'):
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
    
    # Recursivamente aplicar a todos los hijos
    for child in widget.findChildren(QWidget):
        if isinstance(child, clickable_types):
            child.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Para QLabel con links
        if hasattr(child, 'linkActivated'):
            child.setCursor(Qt.CursorShape.PointingHandCursor)

def style_button(button, style_type="primary"):
    """Aplicar estilos y cursor a botones"""
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    if style_type == "primary":
        button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #1AAE52;
            }
        """)
    elif style_type == "danger":
        button.setStyleSheet("""
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
    elif style_type == "secondary":
        button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
    elif style_type == "info":
        button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

def apply_hover_effects(widget):
    """Aplicar efectos hover a widgets"""
    widget.setStyleSheet(widget.styleSheet() + """
        QListWidget::item:hover {
            background-color: rgba(37, 211, 102, 0.1);
        }
        
        QTableWidget::item:hover {
            background-color: rgba(37, 211, 102, 0.1);
        }
        
        QToolButton:hover {
            background-color: rgba(37, 211, 102, 0.2);
        }
    """)

class ThemeManager:
    """Gestor de temas para la aplicación"""
    
    LIGHT_THEME = """
    /* Tema Claro */
    * {
        background-color: transparent;
    }
    
    QMainWindow, QDialog {
        background-color: #f5f5f5;
    }
    
    QWidget {
        color: #333333;
    }
    
    /* Panel central y contenedores principales */
    QWidget#centralwidget, QFrame {
        background-color: #ffffff;
        color: #333333;
    }
    
    QTabWidget::pane {
        border: 1px solid #ddd;
        background-color: white;
    }
    
    QTabWidget > QWidget {
        background-color: white;
    }
    
    QTabBar::tab {
        padding: 10px 20px;
        margin-right: 5px;
        background-color: #f0f0f0;
        color: #333333;
    }
    
    QTabBar::tab:selected {
        background-color: #25D366;
        color: white;
    }
    
    QTabBar::tab:hover {
        background-color: #e0e0e0;
    }
    
    QPushButton {
        background-color: #25D366;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 500;
    }
    
    QPushButton:hover {
        background-color: #20BD5A;
    }
    
    QPushButton:pressed {
        background-color: #1AAE52;
    }
    
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit, QDateTimeEdit {
        background-color: #ffffff;
        color: #333333;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 8px;
    }
    
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        border-color: #25D366;
    }
    
    QTableWidget {
        background-color: #ffffff;
        alternate-background-color: #f9f9f9;
        border: 1px solid #ddd;
        gridline-color: #e0e0e0;
        color: #333333;
    }
    
    QTableWidget::item {
        padding: 8px;
        border: none;
        color: #333333;
        background-color: transparent;
    }
    
    QTableWidget::item:selected {
        background-color: #25D366;
        color: white;
    }
    
    QHeaderView::section {
        background-color: #f8f9fa;
        color: #333333;
        padding: 10px;
        border: none;
        font-weight: 600;
    }
    
    QListWidget {
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 4px;
        color: #333333;
    }
    
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid #f0f0f0;
        color: #333333;
    }
    
    QListWidget::item:selected {
        background-color: #25D366;
        color: white;
    }
    
    QListWidget::item:hover {
        background-color: #f0f0f0;
    }
    
    QGroupBox {
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-top: 10px;
        padding-top: 10px;
        font-weight: bold;
        background-color: #ffffff;
        color: #333333;
    }
    
    QGroupBox::title {
        color: #333333;
        background-color: transparent;
    }
    
    QLabel {
        color: #333333;
        background-color: transparent;
    }
    
    QStatusBar {
        background-color: #e0e0e0;
        color: #333333;
        border-top: 1px solid #ccc;
    }
    
    QMenuBar {
        background-color: #f8f9fa;
        color: #333333;
    }
    
    QMenuBar::item:selected {
        background-color: #25D366;
        color: white;
    }
    
    QMenu {
        background-color: #ffffff;
        border: 1px solid #ddd;
        color: #333333;
    }
    
    QMenu::item:selected {
        background-color: #25D366;
        color: white;
    }
    
    QToolBar {
        background-color: #f8f9fa;
        border-bottom: 1px solid #dee2e6;
        spacing: 5px;
        padding: 5px;
    }
    
    QScrollBar:vertical {
        background-color: #f0f0f0;
        width: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #c0c0c0;
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #a0a0a0;
    }
    
    QCheckBox {
        color: #333333;
        background-color: transparent;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #ddd;
        border-radius: 3px;
        background-color: #ffffff;
    }
    
    QCheckBox::indicator:checked {
        background-color: #25D366;
        border-color: #25D366;
    }
    """
    
    DARK_THEME = """
    /* Tema Oscuro */
    * {
        background-color: transparent;
    }
    
    QMainWindow, QDialog {
        background-color: #1e1e1e;
    }
    
    QWidget {
        color: #ffffff;
    }
    
    /* Panel central y contenedores principales */
    QWidget#centralwidget, QFrame {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    QTabWidget::pane {
        border: 1px solid #3d3d3d;
        background-color: #2d2d2d;
    }
    
    QTabWidget > QWidget {
        background-color: #2d2d2d;
    }
    
    QTabBar::tab {
        padding: 10px 20px;
        margin-right: 5px;
        background-color: #3d3d3d;
        color: #ffffff;
    }
    
    QTabBar::tab:selected {
        background-color: #25D366;
        color: white;
    }
    
    QTabBar::tab:hover {
        background-color: #4d4d4d;
    }
    
    QPushButton {
        background-color: #25D366;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: 500;
    }
    
    QPushButton:hover {
        background-color: #20BD5A;
    }
    
    QPushButton:pressed {
        background-color: #1AAE52;
    }
    
    QPushButton[class="secondary"] {
        background-color: #4d4d4d;
    }
    
    QPushButton[class="secondary"]:hover {
        background-color: #5d5d5d;
    }
    
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit, QDateTimeEdit {
        background-color: #3d3d3d;
        color: #ffffff;
        border: 1px solid #4d4d4d;
        border-radius: 4px;
        padding: 8px;
    }
    
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
        border-color: #25D366;
    }
    
    QComboBox::drop-down {
        background-color: #3d3d3d;
        border: none;
    }
    
    QComboBox QAbstractItemView {
        background-color: #3d3d3d;
        color: #ffffff;
        selection-background-color: #25D366;
    }
    
    QTableWidget {
        background-color: #2d2d2d;
        alternate-background-color: #323232;
        border: 1px solid #3d3d3d;
        gridline-color: #3d3d3d;
        color: #ffffff;
    }
    
    QTableWidget::item {
        padding: 8px;
        border: none;
        color: #ffffff;
        background-color: transparent;
    }
    
    QTableWidget::item:selected {
        background-color: #25D366;
        color: white;
    }
    
    QTableWidget QTableCornerButton::section {
        background-color: #3d3d3d;
    }
    
    QHeaderView::section {
        background-color: #3d3d3d;
        color: #ffffff;
        padding: 10px;
        border: none;
        font-weight: 600;
    }
    
    QListWidget {
        background-color: #2d2d2d;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        color: #ffffff;
    }
    
    QListWidget::item {
        padding: 8px;
        border-bottom: 1px solid #3d3d3d;
        color: #ffffff;
        background-color: transparent;
    }
    
    QListWidget::item:selected {
        background-color: #25D366;
        color: white;
    }
    
    QListWidget::item:hover {
        background-color: #3d3d3d;
    }
    
    QGroupBox {
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        margin-top: 10px;
        padding-top: 10px;
        font-weight: bold;
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    QGroupBox::title {
        color: #ffffff;
        background-color: #2d2d2d;
        padding: 0 5px;
    }
    
    QLabel {
        color: #ffffff;
        background-color: transparent;
    }
    
    QStatusBar {
        background-color: #3d3d3d;
        color: #ffffff;
        border-top: 1px solid #4d4d4d;
    }
    
    QMenuBar {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    QMenuBar::item:selected {
        background-color: #25D366;
        color: white;
    }
    
    QMenu {
        background-color: #2d2d2d;
        border: 1px solid #3d3d3d;
        color: #ffffff;
    }
    
    QMenu::item:selected {
        background-color: #25D366;
        color: white;
    }
    
    QToolBar {
        background-color: #2d2d2d;
        border-bottom: 1px solid #3d3d3d;
        spacing: 5px;
        padding: 5px;
    }
    
    QToolBar QToolButton {
        background-color: #3d3d3d;
        border: 1px solid #4d4d4d;
        border-radius: 3px;
        padding: 5px 10px;
        color: #ffffff;
    }
    
    QToolBar QToolButton:hover {
        background-color: #4d4d4d;
    }
    
    QScrollBar:vertical {
        background-color: #2d2d2d;
        width: 12px;
        border-radius: 6px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #5d5d5d;
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #6d6d6d;
    }
    
    QCheckBox {
        color: #ffffff;
        background-color: transparent;
    }
    
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border: 2px solid #4d4d4d;
        border-radius: 3px;
        background-color: #3d3d3d;
    }
    
    QCheckBox::indicator:checked {
        background-color: #25D366;
        border-color: #25D366;
    }
    
    /* Forzar colores en todos los widgets hijos */
    QWidget QWidget {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    /* Asegurar que los labels tengan el color correcto */
    QLabel {
        color: #ffffff !important;
        background-color: transparent !important;
    }
    """
    
    def __init__(self):
        self.current_theme = "light"
    
    def toggle_theme(self):
        """Alternar entre tema claro y oscuro"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        return self.get_current_theme()
    
    def get_current_theme(self):
        """Obtener el tema actual"""
        return self.DARK_THEME if self.current_theme == "dark" else self.LIGHT_THEME
    
    def get_theme_name(self):
        """Obtener el nombre del tema actual"""
        return self.current_theme
    
    def set_theme(self, theme_name):
        """Establecer un tema específico"""
        if theme_name in ["light", "dark"]:
            self.current_theme = theme_name
            return self.get_current_theme()
        return None

# Instancia global del gestor de temas
theme_manager = ThemeManager()

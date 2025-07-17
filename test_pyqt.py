import sys

print("Probando importaciones de PyQt6...")
print(f"Python version: {sys.version}")
print(f"Python ejecutable: {sys.executable}")

try:
    print("\n1. Importando QtCore...")
    from PyQt6 import QtCore
    print("   ✓ QtCore importado correctamente")
    
    print("\n2. Importando QtWidgets...")
    from PyQt6 import QtWidgets
    print("   ✓ QtWidgets importado correctamente")
    
    print("\n3. Importando QtGui...")
    from PyQt6 import QtGui
    print("   ✓ QtGui importado correctamente")
    
    print("\n4. Creando QApplication...")
    app = QtWidgets.QApplication(sys.argv)
    print("   ✓ QApplication creada correctamente")
    
    print("\n5. Información de Qt:")
    print(f"   - Qt version: {QtCore.QT_VERSION_STR}")
    print(f"   - PyQt version: {QtCore.PYQT_VERSION_STR}")
    
    print("\n✅ PyQt6 está funcionando correctamente!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPosibles soluciones:")
    print("1. Instala Visual C++ Redistributable 2019-2022")
    print("2. Reinstala PyQt6: pip uninstall PyQt6 -y && pip install PyQt6")
    print("3. Verifica que Python sea de 64 bits")
    
    # Información adicional del sistema
    import platform
    print(f"\nInformación del sistema:")
    print(f"- Sistema: {platform.system()}")
    print(f"- Versión: {platform.version()}")
    print(f"- Arquitectura: {platform.machine()}")
    print(f"- Python: {platform.python_version()}")
    print(f"- Arquitectura Python: {platform.architecture()[0]}")
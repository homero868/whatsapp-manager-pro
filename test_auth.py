import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import auth_manager
from database import UserModel
import mysql.connector
from config import Config

print("=== Test de Autenticación ===\n")

# Test 1: Conexión a base de datos
print("1. Probando conexión a base de datos...")
try:
    conn = mysql.connector.connect(**Config.get_db_config())
    print("   ✓ Conexión exitosa")
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    print(f"   ✓ Usuarios en la base de datos: {count}")
    
    # Verificar usuario admin
    cursor.execute("SELECT username, password_hash, is_active FROM users WHERE username = 'admin'")
    result = cursor.fetchone()
    if result:
        print(f"   ✓ Usuario admin encontrado")
        print(f"     - Username: {result[0]}")
        print(f"     - Hash length: {len(result[1])}")
        print(f"     - Is active: {result[2]}")
        print(f"     - Hash: {result[1][:50]}...")
    else:
        print("   ✗ Usuario admin NO encontrado")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Crear usuario admin si no existe
print("\n2. Verificando/Creando usuario admin...")
try:
    user_model = UserModel()
    existing_user = user_model.get_user_by_username('admin')
    
    if not existing_user:
        print("   - Usuario admin no existe, creándolo...")
        # Hashear password
        password_hash = auth_manager.hash_password('admin123')
        print(f"   - Hash generado: {password_hash[:50]}...")
        
        # Crear usuario
        user_id = user_model.create_user('admin', password_hash, 'admin@example.com')
        print(f"   ✓ Usuario admin creado con ID: {user_id}")
    else:
        print("   - Usuario admin ya existe, actualizando password...")
        # Generar nuevo hash
        new_hash = auth_manager.hash_password('admin123')
        
        # Actualizar directamente en la base de datos
        conn = mysql.connector.connect(**Config.get_db_config())
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE username = 'admin'",
            (new_hash,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        print("   ✓ Password actualizado")
        
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Probar login
print("\n3. Probando login con admin/admin123...")
try:
    result = auth_manager.login('admin', 'admin123')
    if result:
        print("   ✓ Login exitoso!")
        print(f"   - Usuario: {result}")
    else:
        print("   ✗ Login falló")
        
        # Intentar debug
        print("\n   Debugging...")
        user = user_model.get_user_by_username('admin')
        if user:
            print(f"   - Usuario encontrado: {user['username']}")
            print(f"   - Verificando password...")
            
            # Probar verificación directa
            try:
                is_valid = auth_manager.verify_password(user['password_hash'], 'admin123')
                print(f"   - Password válido: {is_valid}")
            except Exception as e:
                print(f"   - Error verificando password: {e}")
                print("   - Generando nuevo hash...")
                new_hash = auth_manager.hash_password('admin123')
                print(f"   - Nuevo hash: {new_hash[:50]}...")
                
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Probar registro
print("\n4. Probando registro de nuevo usuario...")
try:
    import random
    test_username = f"test_user_{random.randint(1000, 9999)}"
    
    result = auth_manager.register(test_username, 'test123', 'test@example.com')
    if result:
        print(f"   ✓ Registro exitoso: {test_username}")
        
        # Probar login con el nuevo usuario
        login_result = auth_manager.login(test_username, 'test123')
        if login_result:
            print(f"   ✓ Login con nuevo usuario exitoso")
        else:
            print(f"   ✗ No se pudo hacer login con el nuevo usuario")
    else:
        print("   ✗ Registro falló")
        
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n=== Fin de pruebas ===")
print("\nSi el login sigue fallando, ejecuta este comando SQL:")
print("UPDATE users SET is_active = 1 WHERE username = 'admin';")

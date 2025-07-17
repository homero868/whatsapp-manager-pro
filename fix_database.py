import mysql.connector
from config import Config
import json

print("=== Arreglando base de datos ===\n")

try:
    # Conectar a la base de datos
    conn = mysql.connector.connect(**Config.get_db_config())
    cursor = conn.cursor()
    print("✓ Conectado a la base de datos")
    
    # 1. Limpiar la tabla activity_logs
    print("\n1. Limpiando tabla activity_logs...")
    cursor.execute("DELETE FROM activity_logs WHERE details IS NULL OR details = ''")
    deleted = cursor.rowcount
    conn.commit()
    print(f"   ✓ Eliminados {deleted} registros problemáticos")
    
    # 2. Actualizar registros existentes con JSON válido
    print("\n2. Actualizando registros existentes...")
    cursor.execute("SELECT id, details FROM activity_logs WHERE details NOT LIKE '{%'")
    rows = cursor.fetchall()
    
    for row_id, details in rows:
        # Convertir a JSON válido
        json_details = json.dumps({"message": details if details else ""})
        cursor.execute(
            "UPDATE activity_logs SET details = %s WHERE id = %s",
            (json_details, row_id)
        )
    
    updated = len(rows)
    conn.commit()
    print(f"   ✓ Actualizados {updated} registros")
    
    # 3. Modificar la columna para que acepte NULL o tenga un default JSON
    print("\n3. Modificando estructura de la tabla...")
    try:
        cursor.execute("""
            ALTER TABLE activity_logs 
            MODIFY COLUMN details JSON DEFAULT NULL
        """)
        conn.commit()
        print("   ✓ Columna 'details' modificada")
    except mysql.connector.Error as e:
        if e.errno == 1060:  # Duplicate column
            print("   - La columna ya tiene el formato correcto")
        else:
            print(f"   ! Error modificando columna: {e}")
    
    # 4. Verificar que todo esté bien
    print("\n4. Verificando integridad...")
    cursor.execute("SELECT COUNT(*) FROM activity_logs")
    total = cursor.fetchone()[0]
    print(f"   ✓ Total de registros: {total}")
    
    cursor.close()
    conn.close()
    
    print("\n✅ Base de datos arreglada")
    print("\nAhora puedes ejecutar: python main.py")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

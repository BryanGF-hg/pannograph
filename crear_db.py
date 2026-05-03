import sqlite3
import os

def crear_base_datos():
    # Eliminar base de datos existente si existe
    if os.path.exists('notas_corte.db'):
        os.remove('notas_corte.db')
        print("Base de datos anterior eliminada")
    
    # Crear nueva base de datos
    conn = sqlite3.connect('notas_corte.db')
    cursor = conn.cursor()
    
    # Leer y ejecutar el esquema
    print("Creando tablas...")
    with open('schema.sql', 'r', encoding='utf-8') as f:
        schema_sql = f.read()
        cursor.executescript(schema_sql)
    
    # Insertar datos iniciales
    print("Insertando datos iniciales...")
    with open('seed_data.sql', 'r', encoding='utf-8') as f:
        seed_sql = f.read()
        cursor.executescript(seed_sql)
    
    conn.commit()
    
    # Verificar la creación
    cursor.execute("SELECT COUNT(*) FROM grados")
    num_ramas = cursor.fetchone()[0]
    print(f"Ramas creadas: {num_ramas}")
    
    cursor.execute("SELECT COUNT(*) FROM titulos")
    num_titulos = cursor.fetchone()[0]
    print(f"Títulos creados: {num_titulos}")
    
    # Mostrar resumen
    cursor.execute("""
        SELECT g.rama, COUNT(t.id) as total
        FROM grados g
        LEFT JOIN titulos t ON g.id = t.rama_id
        GROUP BY g.rama
    """)
    
    print("\nResumen por rama:")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} títulos")
    
    conn.close()
    print("\nBase de datos creada exitosamente!")

if __name__ == "__main__":
    crear_base_datos()

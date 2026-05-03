import re
from database import SessionLocal, init_db
from models import Grado, Titulo
from scraper import extraer_y_poblar, RAMAS_KEYWORDS

def generar_sql_desde_pdf():
    """
    Genera instrucciones SQL INSERT a partir de los datos del PDF
    """
    db = SessionLocal()
    
    try:
        # Ejecutar el scraper para obtener los datos
        extraer_y_poblar(db)
        
        # Obtener todos los títulos ordenados por rama
        titulos = db.query(Titulo).join(Grado).order_by(Grado.rama, Titulo.titulo).all()
        
        sql_lines = []
        sql_lines.append("-- Datos extraídos del PDF de Notas de Corte 2025-2026")
        sql_lines.append("-- Fecha de generación: " + str(db.query(Titulo).count()) + " títulos\n")
        
        # Generar INSERTs
        sql_lines.append("-- Insertar títulos por rama")
        rama_actual = None
        
        for titulo in titulos:
            if titulo.grado.rama != rama_actual:
                rama_actual = titulo.grado.rama
                sql_lines.append(f"\n-- {rama_actual}")
                sql_lines.append(f"-- Rama ID: {titulo.grado.id}")
            
            # Escapar comillas simples en el título
            titulo_escape = titulo.titulo.replace("'", "''")
            
            sql = f"INSERT INTO titulos (titulo, nota_corte_general, sitio_web, rama_id) VALUES ('{titulo_escape}', '{titulo.nota_corte_general}', '{titulo.sitio_web or ''}', {titulo.rama_id});"
            sql_lines.append(sql)
        
        # Guardar en archivo
        with open('datos_pdf.sql', 'w', encoding='utf-8') as f:
            f.write('\n'.join(sql_lines))
        
        print(f"SQL generado: {len(titulos)} títulos exportados a datos_pdf.sql")
        
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    generar_sql_desde_pdf()

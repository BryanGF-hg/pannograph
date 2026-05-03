import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from sqlalchemy.orm import Session
from models import Grado, Titulo
import pdfplumber
import io

PDF_URL = "https://universitats.gva.es/documents/389338055/389340603/NOTAS+CORTE+2025-2026.pdf/7e7191c9-116b-2b19-849d-ac021fe51669"

# ============================================
# CONFIGURACIÓN DE RAMAS
# ============================================
RAMAS_KEYWORDS = {
    "Ingeniería y Arquitectura": [
        "ingeniería", "arquitect", "industrial", "informática", "robótica",
        "telecomunicación", "aeroespacial", "diseño industrial", "edificación",
        "multimedia", "tecnología digital", "interactivas", "inteligencia artificial",
        "geomática", "topografía", "energía", "organización industrial",
        "mecánica", "electrónica", "química", "civil", "forestal", "agroalimentaria",
        "ambiental", "biomédica", "sistemas de telecomunicación",
        "grado en tecnología", "grado en informática", "grado en ingeniería"
    ],
    "Ciencias de la Salud": [
        "medicina", "enfermería", "farmacia", "fisioterapia", "odontología",
        "podología", "logopedia", "nutrición", "terapia ocupacional", "biotecnología",
        "bioquímica", "biología", "ciencias biomédicas", "óptica y optometría",
        "psicología"
    ],
    "Empresariales": [
        "administración y dirección de empresas", "ade", "economía",
        "marketing", "finanzas", "contabilidad", "negocios internacionales",
        "turismo", "dirección de empresas", "digital business",
        "comercial y marketing", "gestión y administración pública",
        "inteligencia y analítica de negocios", "bia"
    ],
    "Ciencias Sociales y Jurídicas": [
        "derecho", "criminología", "relaciones laborales", "periodismo",
        "comunicación audiovisual", "traducción", "educación social",
        "pedagogía", "historia", "geografía", "sociología",
        "ciencias políticas", "humanidades", "relaciones internacionales",
        "seguridad pública", "ciencias de la actividad física",
        "maestro en educación", "maestro/a en educación", "estudios ingleses",
        "estudios hispánicos", "lenguas modernas", "filología"
    ],
    "Ciencias": [
        "matemáticas", "física", "química", "ciencias ambientales",
        "geología", "ciencias del mar", "estadística", "óptica",
        "biotecnología", "ciencia de datos", "bioquímica",
        "ciencia y tecnología de los alimentos"
    ],
    "Artes y Humanidades": [
        "bellas artes", "diseño y tecnologías creativas", "conservación",
        "filología", "estudios ingleses", "lenguas", "historia del arte",
        "traducción e interpretación", "comunicación y relaciones públicas",
        "diseño arquitectónico de interiores"
    ]
}

# ============================================
# MAPEO DE UNIVERSIDADES
# ============================================
UNIVERSIDADES_MAPEO = {
    "Universitat Politècnica de València": [
        "politècnica de valència", "politécnica de valencia"
    ],
    "Universitat de València": [
        "universitat de valència", "valència (estudi general)", "estudi general"
    ],
    "Universidad de Alicante": [
        "universidad de alicante", "universitat d'alacant", "alicante", "d'alacant"
    ],
    "Universidad Miguel Hernández de Elche": [
        "miguel hernández", "miguel hernandez", "elche"
    ],
    "Universitat Jaume I de Castelló": [
        "jaume i", "castelló", "castellón", "castello"
    ]
}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def asignar_rama(titulo: str) -> str:
    """Asigna una rama basada en palabras clave del título"""
    titulo_lower = titulo.lower()
    mejor_rama = "Otras"
    mejor_puntuacion = 0
    
    for rama, keywords in RAMAS_KEYWORDS.items():
        puntuacion = sum(len(kw) for kw in keywords if kw in titulo_lower)
        if puntuacion > mejor_puntuacion:
            mejor_puntuacion = puntuacion
            mejor_rama = rama
    
    return mejor_rama

def extraer_universidad(titulo: str) -> str:
    """Extrae el nombre de la universidad del título"""
    titulo_lower = titulo.lower()
    
    for nombre_uni, keywords in UNIVERSIDADES_MAPEO.items():
        for kw in keywords:
            if kw in titulo_lower:
                return nombre_uni
    
    return ""

def limpiar_titulo(titulo: str) -> str:
    """Limpia el título (quita códigos numéricos)"""
    titulo = re.sub(r'\s*,\s*\d{3,4}\b', '', titulo)
    return titulo.strip()

def es_grado_valido(titulo: str) -> bool:
    """Filtra solo grados simples (no dobles grados ni PARS)"""
    titulo_lower = titulo.lower()
    
    # Excluir estos tipos
    excluir = ["doble grado", "pars en", "programa académico con recorrido"]
    for p in excluir:
        if p in titulo_lower:
            return False
    
    # Solo aceptar "Grado en ..."
    return titulo_lower.startswith("grado en")

# ============================================
# EXTRACCIÓN DEL PDF
# ============================================

def extraer_texto_pdf(pdf_content: bytes) -> str:
    """Extrae texto del PDF con pdfplumber"""
    textos = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            print(f"  Páginas: {len(pdf.pages)}")
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    textos.append(texto)
        return "\n".join(textos)
    except Exception as e:
        print(f"  Error pdfplumber: {e}")
        return ""

def extraer_texto_selenium(url: str) -> str:
    """Extrae texto con Selenium (plan B)"""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    try:
        driver = webdriver.Chrome(options=opts)
        driver.get(url)
        time.sleep(10)
        texto = driver.execute_script("return document.body.innerText")
        driver.quit()
        return texto
    except Exception as e:
        print(f"  Error Selenium: {e}")
        return ""

def parsear_titulos(texto: str) -> list:
    """Parsea títulos y notas de corte del texto extraído"""
    titulos = []
    vistos = set()
    
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    print(f"  Líneas a procesar: {len(lineas)}")
    
    patron_titulo = re.compile(r'^(Grado en .+?)(?:\s*,\s*\d{3,4})?(?:\s*\(.*?\))?$')
    patron_nota = re.compile(r'^(\d{1,2}[,.]?\d{1,3})\s*(?:\(.*?\))?$')
    
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        match = patron_titulo.match(linea)
        
        if match:
            titulo_base = match.group(1).strip()
            
            # Verificar si el título continúa en la siguiente línea
            if i + 1 < len(lineas):
                sig = lineas[i + 1]
                if (sig.startswith(('por la', '(', 'Escuela', 'Facultad', 'Centro'))
                    and not patron_nota.match(sig)):
                    titulo_base = f"{titulo_base} {sig}"
                    i += 1
            
            # Filtrar solo grados válidos
            if not es_grado_valido(titulo_base):
                i += 1
                continue
            
            titulo_limpio = limpiar_titulo(titulo_base)
            
            # Evitar duplicados
            clave = titulo_limpio.lower()[:120]
            if clave in vistos:
                i += 1
                continue
            
            vistos.add(clave)
            
            # Buscar nota de corte
            nota = None
            for j in range(i + 1, min(i + 20, len(lineas))):
                m = patron_nota.match(lineas[j])
                if m:
                    nota = m.group(1)
                    break
            
            if nota:
                titulos.append((titulo_limpio, nota))
        
        i += 1
    
    return titulos

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def extraer_y_poblar(db: Session):
    """Extrae datos del PDF y los guarda en la base de datos"""
    print("\n" + "="*60)
    print("  EXTRACCIÓN DE NOTAS DE CORTE 2025-2026")
    print("="*60)
    
    # 1. Descargar PDF
    print("\n[1/6] Descargando PDF...")
    try:
        resp = requests.get(PDF_URL, timeout=30)
        resp.raise_for_status()
        pdf_content = resp.content
        print(f"  ✓ Descargado: {len(pdf_content):,} bytes")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return
    
    # 2. Extraer texto
    print("\n[2/6] Extrayendo texto del PDF...")
    texto = extraer_texto_pdf(pdf_content)
    
    if not texto or len(texto) < 500:
        print("  Probando con Selenium...")
        texto = extraer_texto_selenium(PDF_URL)
    
    if not texto:
        print("  ✗ No se pudo extraer texto")
        return
    
    print(f"  ✓ {len(texto):,} caracteres")
    
    # 3. Parsear títulos
    print("\n[3/6] Analizando títulos y notas...")
    titulos_parseados = parsear_titulos(texto)
    print(f"  ✓ {len(titulos_parseados)} grados simples encontrados")
    
    if not titulos_parseados:
        print("  ✗ No se encontraron títulos")
        return
    
    # 4. Limpiar BD
    print("\n[4/6] Limpiando base de datos...")
    try:
        num_t = db.query(Titulo).delete()
        num_g = db.query(Grado).delete()
        db.commit()
        print(f"  ✓ Eliminados {num_t} títulos y {num_g} ramas")
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error: {e}")
        return
    
    # 5. Crear ramas e insertar títulos
    print("\n[5/6] Guardando datos...")
    ramas_dict = {}
    insertados = 0
    duplicados = 0
    
    for idx, (titulo, nota) in enumerate(titulos_parseados, 1):
        rama = asignar_rama(titulo)
        universidad = extraer_universidad(titulo)
        
        # Crear rama si no existe
        if rama not in ramas_dict:
            grado = Grado(rama=rama, nota_promedia=0.0)
            db.add(grado)
            db.flush()
            ramas_dict[rama] = grado.id
        
        # Verificar duplicado
        existe = db.query(Titulo).filter(Titulo.titulo == titulo).first()
        if existe:
            duplicados += 1
            continue
        
        # Insertar título
        nuevo = Titulo(
            titulo=titulo,
            nota_corte_general=nota,
            universidad=universidad,
            rama_id=ramas_dict[rama]
        )
        db.add(nuevo)
        insertados += 1
        
        # Mostrar progreso
        if idx % 20 == 0:
            db.flush()
            print(f"  {idx}/{len(titulos_parseados)}...")
    
    db.commit()
    print(f"  ✓ {insertados} títulos insertados")
    print(f"  ✓ {len(ramas_dict)} ramas creadas")
    if duplicados:
        print(f"  ⚠ {duplicados} duplicados omitidos")
    
    # 6. Calcular promedios
    print("\n[6/6] Calculando promedios por rama...")
    for grado in db.query(Grado).all():
        notas = []
        for t in grado.titulos:
            try:
                n = float(t.nota_corte_general.replace(",", "."))
                if 0 < n <= 14:
                    notas.append(n)
            except:
                pass
        
        grado.nota_promedia = sum(notas)/len(notas) if notas else 0.0
    
    db.commit()
    
    # Resumen final
    con_uni = db.query(Titulo).filter(Titulo.universidad != "").count()
    
    print("\n" + "="*60)
    print("  ✅ EXTRACCIÓN COMPLETADA")
    print("="*60)
    print(f"  📈 Títulos: {insertados}")
    print(f"  🏛️  Con universidad: {con_uni}/{insertados}")
    print(f"  📚 Ramas: {len(ramas_dict)}")
    print("="*60 + "\n")


# ============================================
# EJECUCIÓN DIRECTA
# ============================================
if __name__ == "__main__":
    from database import SessionLocal, engine, Base
    
    print("\n🔧 Preparando base de datos...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("✓ Tablas listas\n")
    
    db = SessionLocal()
    
    try:
        extraer_y_poblar(db)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

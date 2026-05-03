import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from sqlalchemy.orm import Session
from sqlalchemy import text, delete
from models import Grado, Titulo
import pdfplumber
import io
from urllib.parse import quote
import sys

PDF_URL = "https://universitats.gva.es/documents/389338055/389340603/NOTAS+CORTE+2025-2026.pdf/7e7191c9-116b-2b19-849d-ac021fe51669"

# ============================================
# CONFIGURACIÓN
# ============================================

RAMAS_KEYWORDS = {
    "Ingeniería y Arquitectura": [
        "ingeniería", "arquitect", "industrial", "informática", "robótica",
        "telecomunicación", "aeroespacial", "diseño industrial", "edificación",
        "multimedia", "tecnología digital", "interactivas", "inteligencia artificial",
        "física", "geomática", "topografía", "energía", "organización industrial",
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

UNIVERSIDADES_MAPEO = {
    "Universitat Politècnica de València": {
        "keywords": ["politècnica de valència", "politécnica de valencia"],
        "dominio": "upv.es"
    },
    "Universitat de València": {
        "keywords": ["universitat de valència", "valència (estudi general)", "estudi general"],
        "dominio": "uv.es"
    },
    "Universidad de Alicante": {
        "keywords": ["universidad de alicante", "universitat d'alacant", "alicante", "d'alacant"],
        "dominio": "ua.es"
    },
    "Universidad Miguel Hernández de Elche": {
        "keywords": ["miguel hernández", "miguel hernandez", "elche"],
        "dominio": "umh.es"
    },
    "Universitat Jaume I de Castelló": {
        "keywords": ["jaume i", "castelló", "castellón", "castello"],
        "dominio": "uji.es"
    }
}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def asignar_rama(titulo: str) -> str:
    """Asigna una rama basada en palabras clave"""
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
    
    for nombre_uni, data in UNIVERSIDADES_MAPEO.items():
        for kw in data["keywords"]:
            if kw in titulo_lower:
                return nombre_uni
    
    return ""

def extraer_dominio(universidad: str) -> str:
    """Obtiene el dominio de la universidad"""
    if universidad in UNIVERSIDADES_MAPEO:
        return UNIVERSIDADES_MAPEO[universidad]["dominio"]
    return ""

def limpiar_titulo(titulo: str) -> str:
    """Limpia el título completo"""
    # Quitar código numérico (ej: , 519)
    titulo = re.sub(r'\s*,\s*\d{3,4}\b', '', titulo)
    return titulo.strip()

def limpiar_para_busqueda(titulo: str) -> str:
    """Limpia para búsqueda en Google"""
    titulo = limpiar_titulo(titulo)
    titulo = re.sub(r'\s+por la (?:Universidad|Universitat).*$', '', titulo)
    titulo = re.sub(r'\s*\(.*?(?:Facultad|Escuela|Instituto|Centro).*?\)', '', titulo)
    return titulo.strip()

def es_grado_valido(titulo: str) -> bool:
    """Filtra solo grados simples"""
    titulo_lower = titulo.lower()
    
    excluir = ["doble grado", "pars en", "programa académico con recorrido"]
    for p in excluir:
        if p in titulo_lower:
            return False
    
    return titulo_lower.startswith("grado en")

# ============================================
# EXTRACCIÓN DEL PDF
# ============================================

def extraer_texto_pdf(pdf_content):
    """Extrae texto del PDF con pdfplumber"""
    textos = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                texto = page.extract_text()
                if texto:
                    textos.append(texto)
        return "\n".join(textos)
    except Exception as e:
        print(f"Error pdfplumber: {e}")
        return ""

def extraer_texto_selenium(url):
    """Extrae texto con Selenium (fallback)"""
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
        print(f"Error Selenium: {e}")
        return ""

def parsear_titulos(texto):
    """Parsea títulos y notas"""
    titulos = []
    vistos = set()
    
    lineas = [l.strip() for l in texto.split("\n") if l.strip()]
    
    patron_titulo = re.compile(r'^(Grado en .+?)(?:\s*,\s*\d{3,4})?(?:\s*\(.*?\))?$')
    patron_nota = re.compile(r'^(\d{1,2}[,.]?\d{1,3})\s*(?:\(.*?\))?$')
    
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        match = patron_titulo.match(linea)
        
        if match:
            titulo_base = match.group(1).strip()
            
            # Continuación en siguiente línea
            if i + 1 < len(lineas):
                sig = lineas[i + 1]
                if (sig.startswith(('por la', '(', 'Escuela', 'Facultad', 'Centro'))
                    and not patron_nota.match(sig)):
                    titulo_base = f"{titulo_base} {sig}"
                    i += 1
            
            # Validar
            if not es_grado_valido(titulo_base):
                i += 1
                continue
            
            titulo_limpio = limpiar_titulo(titulo_base)
            
            # Detectar duplicados
            clave = titulo_limpio.lower()[:120]
            if clave in vistos:
                i += 1
                continue
            
            vistos.add(clave)
            
            # Buscar nota
            nota = None
            for j in range(i + 1, min(i + 20, len(lineas))):
                m = patron_nota.match(lineas[j])
                if m:
                    nota = m.group(1)
                    break
            
            if nota:
                titulos.append((titulo_limpio, nota))
                print(f"  ✓ [{len(titulos)}] {titulo_limpio}... → {nota}")
        
        i += 1
    
    print(f"\n  📊 Total grados simples encontrados: {len(titulos)}")
    return titulos

# ============================================
# BÚSQUEDA DE WEBS
# ============================================

def buscar_web_grado(driver, titulo: str, universidad: str) -> str:
    """Busca el sitio web del grado"""
    dominio = extraer_dominio(universidad)
    if not dominio:
        return ""
    
    titulo_busq = limpiar_para_busqueda(titulo)
    
    try:
        # Estrategia 1: site:dominio
        query = f'"{titulo_busq}" site:{dominio}'
        driver.get(f'https://www.google.com/search?q={quote(query)}&hl=es&num=5')
        time.sleep(1.5)
        
        enlaces = driver.find_elements(By.CSS_SELECTOR, 'a[href^="http"]')
        for enlace in enlaces[:10]:
            href = enlace.get_attribute('href')
            if href and dominio in href and 'google' not in href:
                if any(t in href.lower() for t in ['grado', 'estudio', 'grau', 'titulacion']):
                    print(f"    ✓ {href[:80]}")
                    return href
        
        # Estrategia 2: sin site
        query2 = f'"{titulo_busq}" {universidad}'
        driver.get(f'https://www.google.com/search?q={quote(query2)}&hl=es&num=5')
        time.sleep(1)
        
        enlaces = driver.find_elements(By.CSS_SELECTOR, 'a[href^="http"]')
        for enlace in enlaces[:10]:
            href = enlace.get_attribute('href')
            if href and dominio in href and 'google' not in href:
                print(f"    ✓ {href[:80]}")
                return href
        
    except Exception as e:
        print(f"    ✗ Error: {e}")
    
    return ""

def buscar_webs(db: Session, titulos_lista: list):
    """Busca webs para títulos sin web"""
    sin_web = [(t, u) for t, u in titulos_lista if not t.sitio_web]
    
    if not sin_web:
        print("✓ Todos los títulos tienen web")
        return 0
    
    print(f"\n{'='*50}")
    print(f"🔍 BUSCANDO WEBS PARA {len(sin_web)} TÍTULOS")
    print(f"{'='*50}\n")
    
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("user-agent=Mozilla/5.0")
    opts.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    driver = webdriver.Chrome(options=opts)
    encontradas = 0
    
    try:
        for idx, (titulo_obj, uni) in enumerate(sin_web, 1):
            print(f"[{idx}/{len(sin_web)}] {titulo_obj.titulo}...")
            
            if not uni:
                uni = extraer_universidad(titulo_obj.titulo)
                if uni:
                    titulo_obj.universidad = uni
            
            if uni:
                web = buscar_web_grado(driver, titulo_obj.titulo, uni)
                if web:
                    titulo_obj.sitio_web = web
                    encontradas += 1
                    
                    if encontradas % 10 == 0:
                        db.commit()
                        print(f"    💾 Guardado ({encontradas} webs)")
            else:
                print(f"    ✗ Universidad no identificada")
            
            time.sleep(1)
    
    finally:
        db.commit()
        driver.quit()
    
    print(f"\n✅ Webs encontradas: {encontradas}/{len(sin_web)}")
    return encontradas

# ============================================
# FUNCIÓN PRINCIPAL
# ============================================

def extraer_y_poblar(db: Session, hacer_busqueda_webs: bool = True):
    """Función principal de extracción"""
    print("\n" + "="*60)
    print("🚀 EXTRACCIÓN DE NOTAS DE CORTE 2025-2026")
    print("="*60)
    
    # 1. Descargar PDF
    print("\n📥 Descargando PDF...")
    try:
        resp = requests.get(PDF_URL, timeout=30)
        resp.raise_for_status()
        pdf_content = resp.content
        print(f"✓ Descargado: {len(pdf_content)} bytes")
    except Exception as e:
        print(f"✗ Error descargando: {e}")
        return
    
    # 2. Extraer texto
    print("\n📄 Extrayendo texto del PDF...")
    texto = extraer_texto_pdf(pdf_content)
    
    if not texto or len(texto) < 500:
        print("  pdfplumber no obtuvo suficiente texto, probando Selenium...")
        texto = extraer_texto_selenium(PDF_URL)
    
    if not texto:
        print("✗ No se pudo extraer texto del PDF")
        return
    
    print(f"✓ {len(texto)} caracteres extraídos")
    
    # 3. Parsear títulos
    print("\n🔍 Analizando títulos y notas de corte...")
    titulos_parseados = parsear_titulos(texto)
    
    if not titulos_parseados:
        print("✗ No se encontraron títulos válidos")
        return
    
    # 4. Limpiar base de datos
    print("\n🧹 Limpiando base de datos existente...")
    try:
        # Eliminar en orden: primero títulos, luego grados
        num_titulos_eliminados = db.query(Titulo).delete()
        num_grados_eliminados = db.query(Grado).delete()
        db.commit()
        print(f"✓ Eliminados {num_titulos_eliminados} títulos y {num_grados_eliminados} ramas")
    except Exception as e:
        db.rollback()
        print(f"✗ Error limpiando BD: {e}")
        return
    
    # 5. Crear ramas
    print("\n📚 Creando ramas de conocimiento...")
    ramas_dict = {}
    
    for titulo, _ in titulos_parseados:
        rama = asignar_rama(titulo)
        if rama not in ramas_dict:
            grado = Grado(rama=rama, nota_promedia=0.0)
            db.add(grado)
            db.flush()
            ramas_dict[rama] = grado.id
            print(f"  ✓ {rama}")
    
    db.commit()
    print(f"  Total: {len(ramas_dict)} ramas")
    
    # 6. Insertar títulos
    print(f"\n💾 Insertando {len(titulos_parseados)} títulos...")
    titulos_insertados = []
    errores = 0
    
    for idx, (titulo, nota) in enumerate(titulos_parseados, 1):
        rama = asignar_rama(titulo)
        universidad = extraer_universidad(titulo)
        
        # Verificar duplicado
        existente = db.query(Titulo).filter(Titulo.titulo == titulo).first()
        if existente:
            print(f"  [SKIP] Duplicado: {titulo}...")
            errores += 1
            continue
        
        nuevo = Titulo(
            titulo=titulo,
            nota_corte_general=nota,
            sitio_web="",
            universidad=universidad,
            rama_id=ramas_dict.get(rama, list(ramas_dict.values())[0])
        )
        db.add(nuevo)
        titulos_insertados.append((nuevo, universidad))
        
        if idx % 25 == 0:
            db.flush()
            print(f"  {idx}/{len(titulos_parseados)}...")
    
    try:
        db.commit()
        print(f"✓ {len(titulos_insertados)} títulos insertados correctamente")
        if errores > 0:
            print(f"  ({errores} duplicados omitidos)")
    except Exception as e:
        db.rollback()
        print(f"✗ Error en commit: {e}")
        return
    
    # 7. Calcular promedios por rama
    print("\n📊 Calculando notas promedio...")
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
        if notas:
            print(f"  {grado.rama}: {len(notas)} títulos, prom: {grado.nota_promedia:.2f}")
    
    db.commit()
    
    # 8. Buscar sitios web
    if hacer_busqueda_webs:
        encontradas = buscar_webs(db, titulos_insertados)
    
    # 9. Resumen final
    total = len(titulos_insertados)
    con_web = db.query(Titulo).filter(Titulo.sitio_web != "").count()
    con_uni = db.query(Titulo).filter(Titulo.universidad != "").count()
    
    print("\n" + "="*60)
    print("✅ EXTRACCIÓN COMPLETADA")
    print("="*60)
    print(f"📈 Títulos totales: {total}")
    print(f"🏛️  Con universidad: {con_uni}/{total}")
    print(f"🌐 Con sitio web: {con_web}/{total}")
    print(f"📚 Ramas: {len(ramas_dict)}")
    print("="*60 + "\n")


# ============================================
# EJECUCIÓN
# ============================================
if __name__ == "__main__":
    from database import SessionLocal, init_db, engine, Base
    
    print("Inicializando base de datos...")
    
    # Recrear tablas desde cero para evitar problemas de schema
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("✓ Tablas recreadas")
    
    db = SessionLocal()
    
    try:
        extraer_y_poblar(db, hacer_busqueda_webs=True)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n🔒 Conexión cerrada")

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import Grado, Titulo
from scraper import extraer_y_poblar
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI()

# Inicializar BD al arrancar
init_db()

# Servir archivos estáticos (frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependencia de sesión
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Esquemas Pydantic
class TituloCreate(BaseModel):
    titulo: str
    nota_corte_general: str
    sitio_web: Optional[str] = ""
    rama_id: int

class TituloUpdate(BaseModel):
    titulo: Optional[str] = None
    nota_corte_general: Optional[str] = None
    sitio_web: Optional[str] = None

# Endpoints ramas
@app.get("/api/ramas")
def listar_ramas(db: Session = Depends(get_db)):
    return db.query(Grado).all()

# CRUD títulos
@app.get("/api/titulos")
def listar_titulos(
    rama_id: Optional[int] = Query(None),
    search: Optional[str] = Query(""),
    db: Session = Depends(get_db)
):
    q = db.query(Titulo)
    if rama_id:
        q = q.filter(Titulo.rama_id == rama_id)
    if search:
        q = q.filter(Titulo.titulo.ilike(f"%{search}%"))
    return q.all()

@app.post("/api/titulos")
def crear_titulo(data: TituloCreate, db: Session = Depends(get_db)):
    grado = db.query(Grado).filter(Grado.id == data.rama_id).first()
    if not grado:
        raise HTTPException(status_code=404, detail="Rama no encontrada")
    nuevo = Titulo(**data.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@app.put("/api/titulos/{id}")
def actualizar_titulo(id: int, data: TituloUpdate, db: Session = Depends(get_db)):
    titulo = db.query(Titulo).filter(Titulo.id == id).first()
    if not titulo:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    if data.titulo is not None:
        titulo.titulo = data.titulo
    if data.nota_corte_general is not None:
        titulo.nota_corte_general = data.nota_corte_general
    if data.sitio_web is not None:
        titulo.sitio_web = data.sitio_web
    db.commit()
    return titulo

@app.delete("/api/titulos/{id}")
def eliminar_titulo(id: int, db: Session = Depends(get_db)):
    titulo = db.query(Titulo).filter(Titulo.id == id).first()
    if not titulo:
        raise HTTPException(status_code=404, detail="Título no encontrado")
    db.delete(titulo)
    db.commit()
    return {"ok": True}

# Endpoint para ejecutar el scraper (protegido o manual)
@app.post("/api/scrape")
def ejecutar_scraping(db: Session = Depends(get_db)):
    extraer_y_poblar(db)
    return {"status": "Scraping completado"}

# Ruta raíz -> redirige al panel
@app.get("/")
def root():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

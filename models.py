from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Grado(Base):
    __tablename__ = "grados"
    
    id = Column(Integer, primary_key=True, index=True)
    rama = Column(String, unique=True, index=True)
    ambito = Column(String, nullable=True)
    nota_promedia = Column(Float, default=0.0)
    
    titulos = relationship("Titulo", back_populates="grado")

class Titulo(Base):
    __tablename__ = "titulos"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, unique=True)  # UNIQUE evita duplicados
    titulo_limpio = Column(String, nullable=True)
    nota_corte_general = Column(String)
    sitio_web = Column(String, nullable=True)
    universidad = Column(String, nullable=True)
    facultad_escuela = Column(String, nullable=True)
    rama_id = Column(Integer, ForeignKey("grados.id"))
    codigo_grado = Column(String, nullable=True)
    
    grado = relationship("Grado", back_populates="titulos")

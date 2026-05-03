-- Crear la base de datos (si usas MySQL/PostgreSQL)
-- Para SQLite se crea automáticamente
sudo mysql -u root -p
CREATE DATABASE pannograph;

-- Tabla de Ramas (Grados)
CREATE TABLE IF NOT EXISTS grados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rama VARCHAR(255) NOT NULL UNIQUE,
    ambito VARCHAR(255),
    nota_promedia FLOAT DEFAULT 0.0
);

-- Tabla de Títulos
CREATE TABLE IF NOT EXISTS titulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    nota_corte_general VARCHAR(50),
    sitio_web TEXT,
    rama_id INTEGER,
    FOREIGN KEY (rama_id) REFERENCES grados(id) ON DELETE CASCADE
);

-- Índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_titulos_rama ON titulos(rama_id);
CREATE INDEX IF NOT EXISTS idx_titulos_titulo ON titulos(titulo);
CREATE INDEX IF NOT EXISTS idx_grados_rama ON grados(rama);

-- Insertar ramas principales
INSERT OR IGNORE INTO grados (rama, ambito, nota_promedia) VALUES 
('Ingeniería y Arquitectura', 'Ingeniería', 0.0),
('Ciencias de la Salud', 'Salud', 0.0),
('Empresariales', 'Negocios', 0.0),
('Ciencias Sociales y Jurídicas', 'Sociales', 0.0),
('Ciencias', 'Ciencias', 0.0),
('Artes y Humanidades', 'Humanidades', 0.0),
('Otras', 'General', 0.0);

-- Ejemplo de inserción de títulos (datos reales del PDF)
INSERT OR IGNORE INTO titulos (titulo, nota_corte_general, sitio_web, rama_id) VALUES 
-- Ingeniería y Arquitectura
('Grado en Ingeniería Informática por la Universitat Politècnica de València', '9,772', 'https://www.upv.es/', 1),
('Grado en Ingeniería Aeroespacial por la Universitat Politècnica de València', '13,176', 'https://www.upv.es/', 1),
('Grado en Ingeniería en Tecnologías Industriales por la Universitat Politècnica de València', '11,184', 'https://www.upv.es/', 1),

-- Ciencias de la Salud
('Grado en Medicina por la Universitat de València', '13,202', 'https://www.uv.es/', 2),
('Grado en Enfermería por la Universidad de Alicante', '11,968', 'https://www.ua.es/', 2),
('Grado en Farmacia por la Universidad Miguel Hernández de Elche', '11,398', 'https://www.umh.es/', 2),

-- Empresariales
('Grado en Administración y Dirección de Empresas por la Universitat de València', '9,552', 'https://www.uv.es/', 3),
('Grado en Economía por la Universitat de València', '9,644', 'https://www.uv.es/', 3),
('Grado en Marketing por la Universidad de Alicante', '9,599', 'https://www.ua.es/', 3),

-- Ciencias Sociales y Jurídicas
('Grado en Derecho por la Universitat de València', '9,986', 'https://www.uv.es/', 4),
('Grado en Psicología por la Universitat de València', '10,808', 'https://www.uv.es/', 4),
('Grado en Criminología por la Universidad de Alicante', '9,224', 'https://www.ua.es/', 4),

-- Ciencias
('Grado en Matemáticas por la Universitat de València', '12,38', 'https://www.uv.es/', 5),
('Grado en Física por la Universitat de València', '13,001', 'https://www.uv.es/', 5),
('Grado en Química por la Universidad de Alicante', '10,808', 'https://www.ua.es/', 5),

-- Artes y Humanidades
('Grado en Bellas Artes por la Universitat Politècnica de València', '9,946', 'https://www.upv.es/', 6),
('Grado en Traducción e Interpretación por la Universidad de Alicante', '11,034', 'https://www.ua.es/', 6),
('Grado en Estudios Ingleses por la Universitat de València', '9,736', 'https://www.uv.es/', 6);

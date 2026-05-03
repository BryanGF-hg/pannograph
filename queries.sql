-- ==========================================
-- CONSULTAS PARA EL PANEL DE ADMINISTRACIÓN
-- ==========================================

-- 1. Obtener todas las ramas con su nota promedio
SELECT 
    id,
    rama,
    ambito,
    nota_promedia,
    (SELECT COUNT(*) FROM titulos WHERE titulos.rama_id = grados.id) as total_titulos
FROM grados
ORDER BY rama;

-- 2. Obtener títulos por rama
SELECT 
    t.id,
    t.titulo,
    t.nota_corte_general,
    t.sitio_web,
    g.rama
FROM titulos t
INNER JOIN grados g ON t.rama_id = g.id
WHERE g.id = ? -- ID de la rama
ORDER BY t.titulo;

-- 3. Buscar títulos por texto
SELECT 
    t.id,
    t.titulo,
    t.nota_corte_general,
    t.sitio_web,
    g.rama
FROM titulos t
INNER JOIN grados g ON t.rama_id = g.id
WHERE t.titulo LIKE '%' || ? || '%' -- Texto a buscar
ORDER BY g.rama, t.titulo;

-- 4. Obtener top 10 notas más altas
SELECT 
    t.titulo,
    t.nota_corte_general,
    g.rama
FROM titulos t
INNER JOIN grados g ON t.rama_id = g.id
WHERE t.nota_corte_general != '5'
ORDER BY CAST(REPLACE(t.nota_corte_general, ',', '.') AS FLOAT) DESC
LIMIT 10;

-- 5. Estadísticas por rama
SELECT 
    g.rama,
    COUNT(t.id) as total_titulos,
    ROUND(AVG(CAST(REPLACE(t.nota_corte_general, ',', '.') AS FLOAT)), 2) as nota_promedio,
    MIN(CAST(REPLACE(t.nota_corte_general, ',', '.') AS FLOAT)) as nota_minima,
    MAX(CAST(REPLACE(t.nota_corte_general, ',', '.') AS FLOAT)) as nota_maxima
FROM grados g
LEFT JOIN titulos t ON g.id = t.rama_id
WHERE t.nota_corte_general != '5'
GROUP BY g.rama
ORDER BY nota_promedio DESC;

-- 6. Títulos con nota de corte más alta por universidad
SELECT 
    t.titulo,
    t.nota_corte_general,
    g.rama
FROM titulos t
INNER JOIN grados g ON t.rama_id = g.id
WHERE t.nota_corte_general != '5'
ORDER BY CAST(REPLACE(t.nota_corte_general, ',', '.') AS FLOAT) DESC
LIMIT 20;

-- 7. Actualizar nota promedio de todas las ramas
UPDATE grados
SET nota_promedia = (
    SELECT AVG(CAST(REPLACE(titulos.nota_corte_general, ',', '.') AS FLOAT))
    FROM titulos
    WHERE titulos.rama_id = grados.id
    AND titulos.nota_corte_general != '5'
);

-- 8. Contar títulos por universidad (extraer del título)
SELECT 
    CASE 
        WHEN t.titulo LIKE '%Universitat Politècnica de València%' THEN 'UPV'
        WHEN t.titulo LIKE '%Universitat de València%' THEN 'UV'
        WHEN t.titulo LIKE '%Universidad de Alicante%' THEN 'UA'
        WHEN t.titulo LIKE '%Universidad Miguel Hernández%' THEN 'UMH'
        WHEN t.titulo LIKE '%Universidad Jaume I%' THEN 'UJI'
        ELSE 'Otras'
    END as universidad,
    COUNT(*) as cantidad_titulos,
    ROUND(AVG(CAST(REPLACE(t.nota_corte_general, ',', '.') AS FLOAT)), 2) as nota_promedio
FROM titulos t
WHERE t.nota_corte_general != '5'
GROUP BY universidad
ORDER BY cantidad_titulos DESC;

-- 9. Títulos sin sitio web asignado
SELECT 
    t.id,
    t.titulo,
    g.rama
FROM titulos t
INNER JOIN grados g ON t.rama_id = g.id
WHERE t.sitio_web IS NULL OR t.sitio_web = '';

-- 10. Eliminar títulos duplicados (mantener el primero)
DELETE FROM titulos 
WHERE id NOT IN (
    SELECT MIN(id)
    FROM titulos
    GROUP BY titulo
);

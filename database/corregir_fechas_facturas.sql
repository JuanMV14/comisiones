-- Script para corregir fechas mal interpretadas en la tabla comisiones
-- Este script identifica y corrige fechas que pueden estar en formato incorrecto
-- Ejecutar este script en Supabase SQL Editor

-- IMPORTANTE: Revisar los resultados antes de ejecutar los UPDATEs
-- Este script primero muestra qué fechas se van a corregir

-- 1. Ver fechas que pueden estar mal (mes > 12 o día > 31 cuando se interpreta como YYYY-MM-DD)
-- Si una fecha está guardada como "2026-09-02" pero debería ser "2026-02-09" (9 de febrero),
-- necesitamos identificarla y corregirla manualmente o con lógica específica

-- 2. Verificar fechas sospechosas (años futuros muy lejanos o fechas inválidas)
SELECT 
    id,
    factura,
    fecha_factura,
    CASE 
        WHEN fecha_factura::text LIKE '%-09-%' OR fecha_factura::text LIKE '%-10-%' OR 
             fecha_factura::text LIKE '%-11-%' OR fecha_factura::text LIKE '%-12-%'
        THEN 'Posible fecha mal interpretada (mes > 8)'
        ELSE 'OK'
    END as observacion
FROM comisiones
WHERE fecha_factura IS NOT NULL
ORDER BY fecha_factura DESC
LIMIT 100;

-- 3. Si necesitas corregir fechas específicas, usa este formato:
-- UPDATE comisiones 
-- SET fecha_factura = '2026-02-09'::date  -- Formato correcto: YYYY-MM-DD
-- WHERE id = [ID_DE_LA_FACTURA];

-- NOTA: Este script es solo para revisión. 
-- Las correcciones deben hacerse manualmente o con un script Python que analice el contexto.

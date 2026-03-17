-- Script para agregar campo presupuesto_marcas_total a la tabla metas_mensuales
-- Ejecutar este script en Supabase SQL Editor

-- Agregar columna presupuesto_marcas_total
ALTER TABLE metas_mensuales 
ADD COLUMN IF NOT EXISTS presupuesto_marcas_total NUMERIC(15,2) DEFAULT 0;

-- Agregar comentario
COMMENT ON COLUMN metas_mensuales.presupuesto_marcas_total IS 'Presupuesto total para las 4 marcas combinadas (EFFIX, MOTEK USA, KBS, TOYAMA)';

-- Crear índice para búsquedas rápidas (opcional)
CREATE INDEX IF NOT EXISTS idx_metas_presupuesto_marcas_total 
ON metas_mensuales(presupuesto_marcas_total);

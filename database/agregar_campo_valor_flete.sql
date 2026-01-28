-- Script para agregar campo valor_flete a la tabla comisiones
-- Ejecutar este script en Supabase SQL Editor
-- Este script agrega: valor_flete, ciudad_destino, recogida_local

-- 1. Agregar columna valor_flete
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS valor_flete NUMERIC(15,2) DEFAULT 0;

-- Agregar comentario
COMMENT ON COLUMN comisiones.valor_flete IS 'Valor del flete cobrado en la factura';

-- 2. Agregar columna ciudad_destino (si no existe)
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS ciudad_destino TEXT DEFAULT 'Resto';

-- Agregar comentario
COMMENT ON COLUMN comisiones.ciudad_destino IS 'Ciudad de destino: Medellín, Bogotá, Resto, etc.';

-- 3. Agregar columna recogida_local (si no existe)
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS recogida_local BOOLEAN DEFAULT FALSE;

-- Agregar comentario
COMMENT ON COLUMN comisiones.recogida_local IS 'TRUE si el cliente recoge localmente';

-- 4. Crear índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_comisiones_ciudad_destino 
ON comisiones(ciudad_destino);

CREATE INDEX IF NOT EXISTS idx_comisiones_valor_flete 
ON comisiones(valor_flete);

-- 5. Actualizar registros existentes
-- Si valor_flete es NULL, establecerlo en 0
UPDATE comisiones 
SET valor_flete = 0 
WHERE valor_flete IS NULL;

-- Si ciudad_destino está vacío o es NULL, establecerlo en 'Resto'
UPDATE comisiones 
SET ciudad_destino = 'Resto' 
WHERE ciudad_destino IS NULL OR ciudad_destino = '';

-- Si recogida_local es NULL, establecerlo en FALSE
UPDATE comisiones 
SET recogida_local = FALSE 
WHERE recogida_local IS NULL;

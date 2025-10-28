-- Agregar campos para control de flete
-- Ejecutar en Supabase SQL Editor

-- 1. Agregar campo ciudad_destino
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS ciudad_destino TEXT DEFAULT 'Resto';

-- 2. Agregar campo recogida_local
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS recogida_local BOOLEAN DEFAULT FALSE;

-- 3. Agregar comentarios
COMMENT ON COLUMN comisiones.ciudad_destino IS 'Ciudad de destino del envío: Medellín, Bogotá, Resto';
COMMENT ON COLUMN comisiones.recogida_local IS 'Indica si el cliente recoge el pedido localmente (solo aplica para Medellín)';

-- 4. Crear índice para búsquedas
CREATE INDEX IF NOT EXISTS idx_comisiones_ciudad_destino ON comisiones(ciudad_destino);


-- Agregar campos para control de flete
-- Ejecutar en Supabase SQL Editor

-- 1. Agregar campo ciudad_destino
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS ciudad_destino TEXT DEFAULT 'Resto';

-- 2. Agregar campo recogida_local
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS recogida_local BOOLEAN DEFAULT FALSE;

-- 3. Agregar campo valor_flete
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS valor_flete NUMERIC DEFAULT 0;

-- 4. Agregar comentarios
COMMENT ON COLUMN comisiones.ciudad_destino IS 'Ciudad de destino del envío: Medellín, Bogotá, Resto';
COMMENT ON COLUMN comisiones.recogida_local IS 'Indica si el cliente recoge el pedido localmente (solo aplica para Medellín)';
COMMENT ON COLUMN comisiones.valor_flete IS 'Valor del flete cobrado al cliente (NO afecta la base de comisión)';

-- 5. Crear índice para búsquedas
CREATE INDEX IF NOT EXISTS idx_comisiones_ciudad_destino ON comisiones(ciudad_destino);


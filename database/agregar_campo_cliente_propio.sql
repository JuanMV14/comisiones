-- Script para agregar campos faltantes a la tabla clientes_b2b
-- Ejecutar este script en Supabase SQL Editor
-- Este script agrega: contacto y cliente_propio

-- 1. Agregar columna contacto
ALTER TABLE clientes_b2b 
ADD COLUMN IF NOT EXISTS contacto VARCHAR(255) DEFAULT '';

-- Agregar comentario
COMMENT ON COLUMN clientes_b2b.contacto IS 'Nombre de contacto del cliente';

-- 2. Agregar columna cliente_propio
ALTER TABLE clientes_b2b 
ADD COLUMN IF NOT EXISTS cliente_propio BOOLEAN DEFAULT TRUE;

-- Agregar comentario
COMMENT ON COLUMN clientes_b2b.cliente_propio IS 'TRUE = Cliente propio (comisiones 2.5%/1.5%), FALSE = Cliente externo (comisiones 1.0%/0.5%)';

-- 3. Crear índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_clientes_cliente_propio 
ON clientes_b2b(cliente_propio);

CREATE INDEX IF NOT EXISTS idx_clientes_contacto 
ON clientes_b2b(contacto);

-- 4. Actualizar clientes existentes
-- Por defecto todos son propios
UPDATE clientes_b2b 
SET cliente_propio = TRUE 
WHERE cliente_propio IS NULL;

-- Si contacto está vacío, usar el nombre como contacto
UPDATE clientes_b2b 
SET contacto = nombre 
WHERE contacto IS NULL OR contacto = '';

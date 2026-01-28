# DOCUMENTACIÓN DE BASE DE DATOS

## ÍNDICE
1. [Tablas Principales](#tablas-principales)
2. [Tablas B2B](#tablas-b2b)
3. [Políticas de Seguridad (RLS)](#políticas-de-seguridad-rls)
4. [Índices](#índices)
5. [Relaciones](#relaciones)
6. [Vistas](#vistas)
7. [Migraciones y Cambios](#migraciones-y-cambios)

---

## TABLAS PRINCIPALES

### 1. Tabla `comisiones`
**Descripción**: Almacena todas las facturas/comisiones de ventas.

#### Campos Principales:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGSERIAL | Primary Key (auto-incremental) |
| `pedido` | VARCHAR | Número de pedido |
| `cliente` | VARCHAR | Nombre del cliente |
| `factura` | VARCHAR | Número de factura |
| `fecha_factura` | TIMESTAMP | Fecha de la factura |
| `valor` | NUMERIC(15,2) | Valor total (incluye IVA y flete) |
| `valor_neto` | NUMERIC(15,2) | Valor sin IVA |
| `iva` | NUMERIC(15,2) | Valor del IVA (19%) |
| `valor_flete` | NUMERIC(15,2) | Valor del flete cobrado |
| `comision` | NUMERIC(15,2) | Comisión calculada |
| `base_comision` | NUMERIC(15,2) | Base para cálculo de comisión |
| `cliente_propio` | BOOLEAN | TRUE = Cliente propio, FALSE = Cliente externo |
| `descuento_pie_factura` | BOOLEAN | TRUE si hay descuento a pie en factura |
| `descuento_adicional` | NUMERIC(5,2) | Porcentaje de descuento adicional |
| `condicion_especial` | BOOLEAN | TRUE si tiene condición especial de pago |
| `ciudad_destino` | TEXT | Ciudad destino: Medellín, Bogotá, Resto |
| `recogida_local` | BOOLEAN | TRUE si cliente recoge localmente |
| `fecha_pago_max` | DATE | Fecha límite de pago |
| `pagado` | BOOLEAN | TRUE si está pagado |
| `fecha_pago_real` | DATE | Fecha real de pago |
| `dias_pago_real` | INTEGER | Días transcurridos hasta el pago |
| `comision_perdida` | BOOLEAN | TRUE si perdió comisión (pago > 80 días) |
| `compra_cliente_id` | BIGINT | ID de compra relacionada en compras_clientes |
| `sincronizado_compras` | BOOLEAN | TRUE si está sincronizado con compras |

#### Lógica de Cálculo:
- **valor** = valor_neto + iva + valor_flete
- **base_comision**:
  - Si `descuento_pie_factura` = TRUE → base_comision = valor_neto
  - Si `descuento_pie_factura` = FALSE → base_comision = valor_neto * 0.85
- **comision**: Calculada según porcentaje basado en cliente_propio y descuentos

---

### 2. Tabla `devoluciones`
**Descripción**: Registra las devoluciones de facturas.

#### Campos Principales:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGSERIAL | Primary Key |
| `factura_id` | BIGINT | Foreign Key → comisiones(id) |
| `valor_devuelto` | NUMERIC(15,2) | Valor devuelto (incluye IVA) |
| `fecha_devolucion` | DATE | Fecha de la devolución |
| `motivo` | TEXT | Motivo de la devolución |
| `afecta_comision` | BOOLEAN | TRUE si afecta el cálculo de comisión |

#### Relaciones:
- **Foreign Key**: `factura_id` → `comisiones(id)`
- Cuando se crea una devolución con `afecta_comision = TRUE`, se recalcula automáticamente la comisión de la factura relacionada.

---

### 3. Tabla `metas_mensuales`
**Descripción**: Define las metas de ventas mensuales.

#### Campos Principales:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGSERIAL | Primary Key |
| `mes` | VARCHAR(7) | Formato: YYYY-MM (ej: 2025-01) |
| `meta_ventas` | NUMERIC(15,2) | Meta de ventas en valor neto |
| `meta_clientes_nuevos` | INTEGER | Meta de clientes nuevos |
| `meta_comisiones` | NUMERIC(15,2) | Meta de comisiones |

---

### 4. Tabla `catalogo_productos`
**Descripción**: Catálogo de productos disponibles.

#### Campos Principales:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGSERIAL | Primary Key |
| `codigo` | VARCHAR | Código único del producto |
| `descripcion` | TEXT | Descripción del producto |
| `precio` | NUMERIC(12,2) | Precio unitario |
| `categoria` | VARCHAR | Categoría del producto |
| `marca` | VARCHAR | Marca del producto |
| `activo` | BOOLEAN | TRUE si está disponible |
| `fecha_actualizacion` | TIMESTAMP | Última actualización |

---

## TABLAS B2B

### 5. Tabla `clientes_b2b`
**Descripción**: Gestión de clientes B2B con información de crédito.

#### Campos Principales:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGSERIAL | Primary Key |
| `nombre` | VARCHAR(255) | Nombre del cliente (NOT NULL) |
| `nit` | VARCHAR(50) | NIT del cliente (UNIQUE, NOT NULL) |
| `cupo_total` | NUMERIC(15,2) | Cupo de crédito total asignado |
| `cupo_utilizado` | NUMERIC(15,2) | Cupo actualmente utilizado |
| `cupo_disponible` | NUMERIC(15,2) | Calculado: cupo_total - cupo_utilizado |
| `plazo_pago` | INTEGER | Días de plazo para pago (default: 30) |
| `descuento_predeterminado` | NUMERIC(5,2) | Descuento predeterminado del cliente (%) |
| `ciudad` | VARCHAR(100) | Ciudad del cliente |
| `direccion` | TEXT | Dirección completa |
| `telefono` | VARCHAR(50) | Teléfono de contacto |
| `email` | VARCHAR(255) | Email de contacto |
| `vendedor` | VARCHAR(100) | Nombre del vendedor asignado |
| `cliente_propio` | BOOLEAN | TRUE = Cliente propio (comisiones 2.5%/1.5%), FALSE = Cliente externo (comisiones 1.0%/0.5%) (default: TRUE) |
| `activo` | BOOLEAN | TRUE si el cliente está activo (default: TRUE) |
| `fecha_registro` | TIMESTAMP | Fecha de registro (default: NOW()) |
| `fecha_actualizacion` | TIMESTAMP | Fecha de última actualización (default: NOW()) |

#### Índices:
- `idx_clientes_nit` → Búsqueda rápida por NIT
- `idx_clientes_nombre` → Búsqueda rápida por nombre
- `idx_clientes_ciudad` → Filtrado por ciudad
- `idx_clientes_activo` → Filtrado por estado activo

#### Restricciones:
- **UNIQUE**: `nit` (no puede haber dos clientes con el mismo NIT)

---

### 6. Tabla `compras_clientes`
**Descripción**: Historial detallado de compras de clientes B2B (producto por producto).

#### Campos Principales:
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | BIGSERIAL | Primary Key |
| `cliente_id` | BIGINT | Foreign Key → clientes_b2b(id) |
| `nit_cliente` | VARCHAR(50) | NIT del cliente (NOT NULL) |
| `fuente` | VARCHAR(20) | Tipo de documento (FE=Factura Electrónica, DV=Devolución) |
| `num_documento` | VARCHAR(50) | Número del documento/factura |
| `fecha` | TIMESTAMP | Fecha de la compra |
| `cod_articulo` | VARCHAR(50) | Código del artículo/producto |
| `detalle` | TEXT | Descripción del producto |
| `cantidad` | INTEGER | Cantidad comprada |
| `valor_unitario` | NUMERIC(12,2) | Precio unitario |
| `descuento` | NUMERIC(5,2) | Porcentaje de descuento aplicado |
| `total` | NUMERIC(15,2) | Total del item (cantidad * valor_unitario - descuento) |
| `familia` | VARCHAR(100) | Familia/categoría del producto |
| `marca` | VARCHAR(100) | Marca del producto |
| `subgrupo` | VARCHAR(100) | Subgrupo del producto |
| `grupo` | VARCHAR(100) | Grupo del producto |
| `es_devolucion` | BOOLEAN | TRUE si es devolución (DV), FALSE si es compra (FE) |
| `factura_id` | BIGINT | Foreign Key → comisiones(id) (si está sincronizado) |
| `sincronizado` | BOOLEAN | TRUE si está sincronizado con una factura |
| `fecha_sincronizacion` | TIMESTAMP | Fecha de sincronización |
| `fecha_carga` | TIMESTAMP | Fecha de carga al sistema (default: NOW()) |

#### Índices:
- `idx_compras_cliente` → Búsqueda por cliente_id
- `idx_compras_nit` → Búsqueda por NIT
- `idx_compras_fecha` → Filtrado por fecha
- `idx_compras_articulo` → Búsqueda por código de artículo
- `idx_compras_marca` → Filtrado por marca
- `idx_compras_grupo` → Filtrado por grupo
- `idx_compras_documento` → Búsqueda por número de documento
- `idx_compras_es_devolucion` → Filtrado por tipo (compra/devolución)
- `idx_compras_factura_id` → Búsqueda por factura relacionada
- `idx_compras_sincronizado` → Filtrado por estado de sincronización

#### Restricciones:
- **UNIQUE INDEX**: `(nit_cliente, num_documento, cod_articulo)` → Evita duplicados
- **Foreign Key**: `cliente_id` → `clientes_b2b(id)`
- **Foreign Key**: `factura_id` → `comisiones(id)`

#### Lógica:
- **Sincronización**: Los productos de una compra se pueden sincronizar automáticamente con una factura en `comisiones` cuando hay coincidencia por número de documento, cliente, fecha y monto.
- **Devoluciones**: Si `es_devolucion = TRUE`, se resta del historial de compras del cliente.

---

## POLÍTICAS DE SEGURIDAD (RLS)

### Row Level Security (RLS)
Todas las tablas B2B tienen RLS habilitado para control de acceso a nivel de fila.

### Tabla `clientes_b2b`
```sql
-- Habilitar RLS
ALTER TABLE clientes_b2b ENABLE ROW LEVEL SECURITY;

-- Políticas
CREATE POLICY "Permitir lectura clientes" 
ON clientes_b2b FOR SELECT USING (true);

CREATE POLICY "Permitir inserción clientes" 
ON clientes_b2b FOR INSERT WITH CHECK (true);

CREATE POLICY "Permitir actualización clientes" 
ON clientes_b2b FOR UPDATE USING (true);
```

**Efecto**: Permite lectura, inserción y actualización sin restricciones. Se puede modificar en el futuro para restringir acceso según roles de usuario.

### Tabla `compras_clientes`
```sql
-- Habilitar RLS
ALTER TABLE compras_clientes ENABLE ROW LEVEL SECURITY;

-- Políticas
CREATE POLICY "Permitir lectura compras" 
ON compras_clientes FOR SELECT USING (true);

CREATE POLICY "Permitir inserción compras" 
ON compras_clientes FOR INSERT WITH CHECK (true);

CREATE POLICY "Permitir actualización compras" 
ON compras_clientes FOR UPDATE USING (true);
```

**Efecto**: Mismas políticas que clientes_b2b - acceso completo. Ideal para modificar en producción para control por vendedor o región.

---

## ÍNDICES

### Índices de Rendimiento

#### Tabla `comisiones`:
- `idx_comisiones_ciudad_destino` → Filtrado por ciudad
- `idx_comisiones_compra_cliente_id` → Búsqueda por compra relacionada
- `idx_comisiones_sincronizado_compras` → Filtrado por sincronización

#### Tabla `clientes_b2b`:
- `idx_clientes_nit` → Búsqueda rápida por NIT (único)
- `idx_clientes_nombre` → Búsqueda por nombre
- `idx_clientes_ciudad` → Filtrado por ciudad
- `idx_clientes_activo` → Filtrado por estado

#### Tabla `compras_clientes`:
- `idx_compras_cliente` → Join rápido con clientes_b2b
- `idx_compras_nit` → Búsqueda por NIT
- `idx_compras_fecha` → Filtrado y ordenamiento por fecha
- `idx_compras_articulo` → Búsqueda por producto
- `idx_compras_marca` → Filtrado por marca
- `idx_compras_grupo` → Filtrado por grupo
- `idx_compras_documento` → Búsqueda por número de documento
- `idx_compras_es_devolucion` → Filtrado compras vs devoluciones
- `idx_compras_factura_id` → Join rápido con comisiones
- `idx_compras_sincronizado` → Filtrado por estado de sincronización

**Nota**: Los índices mejoran significativamente el rendimiento de búsquedas y filtros, especialmente con grandes volúmenes de datos.

---

## RELACIONES

### Diagrama de Relaciones:

```
clientes_b2b (1) ──< (N) compras_clientes
    │                        │
    │                        ├──> (N) comisiones (factura_id)
    │                        └──> (N) comisiones (compra_cliente_id)
    │
comisiones (1) ──< (N) devoluciones (factura_id)
```

### Relaciones Detalladas:

1. **clientes_b2b ← compras_clientes**
   - Relación: 1 a N (Un cliente tiene muchas compras)
   - Foreign Key: `compras_clientes.cliente_id` → `clientes_b2b.id`
   - También relacionado por: `compras_clientes.nit_cliente` = `clientes_b2b.nit`

2. **compras_clientes → comisiones**
   - Relación: N a 1 (Muchos productos de compra pertenecen a una factura)
   - Foreign Key: `compras_clientes.factura_id` → `comisiones.id`
   - También: `comisiones.compra_cliente_id` → `compras_clientes.id` (primera compra del documento)

3. **comisiones ← devoluciones**
   - Relación: 1 a N (Una factura puede tener muchas devoluciones)
   - Foreign Key: `devoluciones.factura_id` → `comisiones.id`
   - Cuando se crea una devolución, se recalcula automáticamente la comisión

---

## VISTAS

### Vista `vista_clientes_resumen`
**Descripción**: Vista agregada que muestra resumen de clientes con totales de compras.

#### Campos:
- `id`, `nombre`, `nit`
- `cupo_total`, `cupo_utilizado`, `cupo_disponible` (calculado)
- `plazo_pago`, `ciudad`
- `total_transacciones` → COUNT de documentos únicos
- `total_compras` → SUM de totales
- `ultima_compra` → MAX fecha de compra

#### SQL:
```sql
CREATE OR REPLACE VIEW vista_clientes_resumen AS
SELECT 
    c.id,
    c.nombre,
    c.nit,
    c.cupo_total,
    c.cupo_utilizado,
    c.cupo_total - c.cupo_utilizado AS cupo_disponible,
    c.plazo_pago,
    c.ciudad,
    COUNT(DISTINCT cp.num_documento) AS total_transacciones,
    COALESCE(SUM(cp.total), 0) AS total_compras,
    MAX(cp.fecha) AS ultima_compra
FROM clientes_b2b c
LEFT JOIN compras_clientes cp ON c.nit = cp.nit_cliente
WHERE c.activo = true
GROUP BY c.id, c.nombre, c.nit, c.cupo_total, c.cupo_utilizado, c.plazo_pago, c.ciudad;
```

---

## MIGRACIONES Y CAMBIOS

### Scripts de Migración (Orden de Ejecución):

#### 1. Tablas Base de Clientes B2B
**Archivo**: `crear_tablas_clientes_compras.sql`
- Crea tablas: `clientes_b2b`, `compras_clientes`
- Crea índices principales
- Configura políticas RLS
- Crea vista `vista_clientes_resumen`

#### 2. Campo de Devolución
**Archivo**: `agregar_campo_devolucion.sql`
```sql
ALTER TABLE compras_clientes 
ADD COLUMN IF NOT EXISTS es_devolucion BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_compras_es_devolucion 
ON compras_clientes(es_devolucion);
```

#### 3. Campo de Descuento
**Archivo**: `agregar_campo_descuento_cliente.sql`
```sql
ALTER TABLE clientes_b2b 
ADD COLUMN IF NOT EXISTS descuento_predeterminado NUMERIC(5, 2) DEFAULT 0.0;
```

#### 4. Campos de Flete
**Archivo**: `agregar_campos_flete.sql`
```sql
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS ciudad_destino TEXT DEFAULT 'Resto',
ADD COLUMN IF NOT EXISTS recogida_local BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS valor_flete NUMERIC DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_comisiones_ciudad_destino 
ON comisiones(ciudad_destino);
```

#### 5. Campos de Sincronización
**Archivo**: `agregar_campos_sincronizacion.sql`
```sql
-- En compras_clientes
ALTER TABLE compras_clientes 
ADD COLUMN IF NOT EXISTS factura_id BIGINT REFERENCES comisiones(id),
ADD COLUMN IF NOT EXISTS sincronizado BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS fecha_sincronizacion TIMESTAMP;

-- En comisiones
ALTER TABLE comisiones 
ADD COLUMN IF NOT EXISTS compra_cliente_id BIGINT,
ADD COLUMN IF NOT EXISTS sincronizado_compras BOOLEAN DEFAULT FALSE;

-- Índices
CREATE INDEX IF NOT EXISTS idx_compras_factura_id ON compras_clientes(factura_id);
CREATE INDEX IF NOT EXISTS idx_compras_sincronizado ON compras_clientes(sincronizado);
CREATE INDEX IF NOT EXISTS idx_comisiones_compra_cliente_id ON comisiones(compra_cliente_id);
CREATE INDEX IF NOT EXISTS idx_comisiones_sincronizado_compras ON comisiones(sincronizado_compras);
```

#### 6. Campo Cliente Propio
**Archivo**: `agregar_campo_cliente_propio.sql`
```sql
-- Agregar columna cliente_propio a clientes_b2b
ALTER TABLE clientes_b2b 
ADD COLUMN IF NOT EXISTS cliente_propio BOOLEAN DEFAULT TRUE;

-- Comentario
COMMENT ON COLUMN clientes_b2b.cliente_propio IS 'TRUE = Cliente propio (comisiones 2.5%/1.5%), FALSE = Cliente externo (comisiones 1.0%/0.5%)';

-- Índice
CREATE INDEX IF NOT EXISTS idx_clientes_cliente_propio 
ON clientes_b2b(cliente_propio);

-- Actualizar clientes existentes
UPDATE clientes_b2b 
SET cliente_propio = TRUE 
WHERE cliente_propio IS NULL;
```

---

## NOTAS IMPORTANTES

### Convenciones de Nomenclatura:
- **Tablas**: snake_case (ej: `comisiones`, `clientes_b2b`)
- **Campos**: snake_case (ej: `valor_neto`, `fecha_factura`)
- **Índices**: `idx_` + `tabla` + `campo` (ej: `idx_compras_nit`)
- **Foreign Keys**: `tabla_campo` (ej: `factura_id`, `cliente_id`)

### Validaciones Automáticas:
- **Consistencia de valores**: `valor = valor_neto + iva + valor_flete`
- **Cálculo automático**: IVA = 19% de valor_neto
- **Base comisión**: Se calcula según descuento_pie_factura
- **Duplicados**: Prevenidos por índice único en compras_clientes

### Mejores Prácticas:
1. **Usar índices** para campos de búsqueda frecuente
2. **Foreign Keys** para mantener integridad referencial
3. **RLS habilitado** en tablas sensibles
4. **Comentarios en columnas** para documentación
5. **Timestamps automáticos** para auditoría

---

**Última actualización**: Enero 2025  
**Versión**: 1.0  
**Base de Datos**: PostgreSQL (Supabase)

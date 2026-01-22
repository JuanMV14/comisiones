# PROPUESTA DE REORGANIZACIÓN DEL CRM

## FILOSOFÍA DE LA REORGANIZACIÓN

Separar claramente dos experiencias de usuario:
1. **ASISTENTE INTELIGENTE PARA VENDEDORES** - Herramientas operativas diarias
2. **PANEL ESTRATÉGICO PARA GERENCIA** - Análisis y toma de decisiones

---

## ESTRUCTURA PROPUESTA (15 PESTAÑAS)

### ============================================
### ZONA 1: ASISTENTE PARA VENDEDORES (6 pestañas)
### ============================================

#### 1. **PANEL DEL VENDEDOR** (NUEVO - Principal para vendedores)
**Objetivo**: Vista consolidada del día a día del vendedor

**Secciones:**
- **Alertas del Día**
  - Facturas vencidas de mis clientes
  - Recordatorios de pago automáticos
  - Clientes inactivos que necesitan contacto
  
- **Mis Mejores Clientes**
  - Top 10 por facturación, recurrencia y margen
  - Frecuencia de compra de cada uno
  - Días desde última compra
  
- **Cliente Rápido** (Buscar/Seleccionar cliente)
  - Buscador rápido por NIT o nombre
  - Al seleccionar cliente:
    * Resumen ejecutivo (crédito, comportamiento de pago)
    * Historial de compras recientes
    * Recomendaciones inteligentes de productos
    * Facturas pendientes y próximas a vencer
    * Botones rápidos: WhatsApp, Email, Nueva Venta

- **Productos Nuevos en Importación**
  - Lista de productos nuevos detectados
  - Recomendaciones automáticas: "Ofrecer a X clientes"
  - Botón para ver detalle del producto

**Funcionalidades:**
- Conexión directa WhatsApp/Email
- Acceso rápido a funciones frecuentes
- Recordatorios automáticos configurables

---

#### 2. **CLIENTES - VISTA VENDEDOR** (REORGANIZADO)
**Objetivo**: Gestión completa de clientes para vendedores

**Secciones:**
- **Buscador y Filtros**
  - Buscar por NIT, nombre, ciudad, vendedor
  - Filtros: Activos/Inactivos, Con crédito/Crédito disponible
  
- **Lista de Clientes con Métricas Clave**
  - Nombre, Ciudad, Vendedor
  - Cupo total / Utilizado / Disponible (%)
  - Total compras, Última compra (días)
  - Estado: Activo, Inactivo (>60 días), Riesgo
  
- **Al Seleccionar Cliente - Vista Detallada:**
  
  **Pestaña 1: Resumen General**
  - Información básica (NIT, contacto, crédito)
  - Comportamiento de pago (promedio días, puntualidad)
  - Métricas: Total facturado, ticket promedio, frecuencia
  
  **Pestaña 2: Historial de Compras**
  - Tabla de todas las facturas
  - Agrupado por fecha, monto, estado de pago
  - Ver detalle de productos comprados por factura
  - Botón: Cargar comprobante de pago
  
  **Pestaña 3: Productos Frecuentes**
  - Segmentado por: Marca, Grupo, Subgrupo, Referencia específica
  - Gráficos de frecuencia y valor
  - Última vez que compró cada producto
  
  **Pestaña 4: Recomendaciones Inteligentes**
  - Productos que podría comprar
  - Productos abandonados (compraba antes, ya no)
  - Productos complementarios
  - Productos nuevos de marcas que le gustan
  
  **Pestaña 5: Facturas y Pagos**
  - Facturas pendientes de pago
  - Facturas vencidas
  - Historial de pagos con comprobantes
  - Botones: Enviar recordatorio WhatsApp/Email
  
  **Pestaña 6: Crédito y Finanzas**
  - Estado actual del crédito
  - Historial de uso de cupo
  - Facturas pendientes que afectan el cupo
  - Alertas de límite

**Funcionalidades:**
- Acciones rápidas desde cada vista
- Exportar información del cliente
- Historial completo y navegable

---

#### 3. **NUEVA VENTA SIMPLE** (MEJORAR)
**Objetivo**: Crear ventas de forma rápida y eficiente

**Mejoras propuestas:**
- **Selector de Cliente Mejorado**
  - Búsqueda inteligente (por nombre, NIT, ciudad)
  - Mostrar crédito disponible al seleccionar
  - Mostrar último pedido y frecuencia
  
- **Asistente de Productos**
  - Si el cliente tiene historial, sugerir productos frecuentes
  - Buscador de productos del catálogo
  - Validación de stock (si aplica)
  
- **Preview Inteligente**
  - Mostrar comisión calculada
  - Alertar si excede crédito disponible
  - Sugerir productos complementarios

**Mantener:**
- Cálculos automáticos
- Validación de datos
- Integración con compras_clientes

---

#### 4. **CATÁLOGO INTELIGENTE** (MEJORAR)
**Objetivo**: Gestión y exploración de productos

**Secciones:**
- **Buscar Productos**
  - Buscador avanzado (por código, referencia, marca, línea)
  - Filtros: Marca, Grupo, Subgrupo, Precio
  
- **Productos Nuevos**
  - Lista de productos nuevos detectados en última importación
  - Fecha de llegada
  - Para cada producto nuevo:
    * Recomendaciones: "Ofrecer a X clientes"
    * Botón: Ver clientes sugeridos
    * Botón: Agregar a lista de ofertas
  
- **Referencias Quietas** (Para vendedores)
  - Productos sin rotación en últimos 90 días
  - Lista de clientes que compraron antes
  - Sugerencia: "Contactar estos clientes"
  
- **Importar Catálogo**
  - Cargar Excel de importación
  - Detectar automáticamente productos nuevos
  - Actualizar precios y disponibilidad

**Funcionalidades:**
- Comparar productos
- Ver historial de ventas por producto
- Generar reportes de rotación

---

#### 5. **MENSAJERÍA Y COMUNICACIÓN** (MEJORAR)
**Objetivo**: Centralizar comunicación con clientes

**Secciones:**
- **Recordatorios Automáticos**
  - Configurar triggers:
    * Factura vencida (X días)
    * Factura por vencer (X días antes)
    * Cliente inactivo (X días sin comprar)
    * Productos nuevos disponibles
  - Configurar plantillas personalizadas
  
- **Envíos Manuales**
  - Seleccionar cliente(s)
  - Elegir plantilla o escribir mensaje
  - Enviar por WhatsApp o Email
  - Ver historial de envíos
  
- **Radicación de Facturas**
  - Ver facturas pendientes de radicación
  - Buscar cliente y enviar mensaje
  - Cargar comprobante de radicación

**Funcionalidades:**
- Integración WhatsApp (Twilio/API)
- Integración Email (SMTP)
- Historial de comunicaciones
- Plantillas personalizables

---

#### 6. **COMISIONES - VISTA VENDEDOR** (SIMPLIFICAR)
**Objetivo**: Ver comisiones del vendedor de forma clara

**Secciones:**
- **Resumen del Mes**
  - Comisiones ganadas
  - Comisiones perdidas (pagos >80 días)
  - Proyección fin de mes
  
- **Mis Facturas**
  - Filtrar por cliente asignado
  - Ver estado de pago
  - Ver detalle de cálculo de comisión
  
- **Historial**
  - Comisiones por mes
  - Gráfico de tendencia

**Simplificar:**
- Enfocado solo en lo relevante para el vendedor
- Sin edición (eso es para administradores)

---

### ============================================
### ZONA 2: PANEL ESTRATÉGICO PARA GERENCIA (9 pestañas)
### ============================================

#### 7. **DASHBOARD EJECUTIVO** (MANTENER Y MEJORAR)
**Objetivo**: Visión 360° del negocio

**Mejoras:**
- **Análisis Geográfico Integrado**
  - Mapa de Colombia con clientes
  - Análisis por ciudad: aporte por asesor, aporte total
  - Identificar zonas de potencial
  
- **KPIs Mejorados**
  - Ventas por zona geográfica
  - Efectividad de vendedores por zona
  - Concentración de ventas (diversificación)

**Mantener:**
- KPIs financieros y operacionales actuales
- Proyecciones y tendencias

---

#### 8. **ANÁLISIS GEOGRÁFICO** (NUEVO - Expandido)
**Objetivo**: Análisis profundo de distribución geográfica

**Secciones:**
- **Mapa Interactivo de Colombia**
  - Clientes ubicados en mapa
  - Tamaño de burbuja = volumen de compras
  - Color = porcentaje de uso de crédito
  
- **Análisis por Ciudad**
  - Tabla comparativa:
    * Total clientes
    * Total facturado
    * Aporte por asesor (desglose)
    * Aporte al presupuesto general
    * Potencial estimado
  
- **Análisis por Zona/Región**
  - Agrupación por regiones (Caribe, Andina, Pacífico, etc.)
  - Comparativa entre zonas
  - Identificación de zonas con potencial
  
- **Análisis por Asesor**
  - Qué ciudades atiende cada asesor
  - Aporte de cada ciudad al total del asesor
  - Efectividad por zona

**Funcionalidades:**
- Filtros por período, vendedor, tipo de cliente
- Exportar análisis geográfico
- Identificar oportunidades de expansión

---

#### 9. **ANÁLISIS COMERCIAL AVANZADO** (NUEVO)
**Objetivo**: Análisis profundo de productos y clientes

**Secciones:**
- **Referencias Quietas**
  - Productos sin rotación (configurable: 60/90/120 días)
  - Para cada producto:
    * Última venta y a qué cliente
    * Historial de ventas
    * Clientes que compraron antes (lista completa)
    * Sugerencia: "Contactar estos X clientes"
  
- **Análisis de Rotación**
  - Productos más vendidos (top 50)
  - Productos menos vendidos (bottom 50)
  - Tendencias de rotación por marca/grupo
  
- **Oportunidades de Negociación**
  - Clientes candidatos para:
    * Descuentos por volumen
    * Negociaciones especiales
    * Campañas promocionales
  - Criterios:
    * Alto volumen de compras
    * Buena historia de pagos
    * Frecuencia constante
    * Interés en línea/producto específico
  
- **Segmentación de Clientes**
  - Clientes VIP (top 20%)
  - Clientes recurrentes
  - Clientes en crecimiento
  - Clientes en riesgo (inactivos)

**Funcionalidades:**
- Generar listas de clientes para campañas
- Exportar análisis
- Configurar alertas automáticas

---

#### 10. **COMISIONES - VISTA ADMINISTRACIÓN** (ACTUAL - Mantener)
**Objetivo**: Gestión completa de comisiones

**Mantener todo lo actual:**
- Tabla completa de comisiones
- Edición de facturas
- Filtros avanzados
- Cálculo y recálculo de comisiones
- Gestión de pagos y comprobantes

**Mejoras menores:**
- Mejor visualización de comisiones perdidas
- Análisis de tendencias de comisiones perdidas

---

#### 11. **GESTIÓN DE CLIENTES B2B** (MEJORAR)
**Objetivo**: Administración completa de clientes

**Secciones:**
- **Lista Completa de Clientes**
  - Tabla con todas las métricas
  - Acciones: Editar, Ver detalle, Desactivar
  
- **Registrar Nuevo Cliente**
  - Formulario completo
  - Validación de NIT único
  - Asignación de cupo y vendedor
  
- **Edición Masiva**
  - Actualizar cupos
  - Cambiar vendedor asignado
  - Activar/Desactivar clientes
  
- **Análisis de Portafolio**
  - Distribución de clientes por vendedor
  - Distribución por ciudad
  - Análisis de concentración

**Funcionalidades:**
- CRUD completo
- Validaciones de negocio
- Historial de cambios

---

#### 12. **ANÁLISIS DE COMPRAS Y COMPORTAMIENTO** (NUEVO)
**Objetivo**: Análisis profundo de patrones de compra

**Secciones:**
- **Análisis de Historial de Compras**
  - Tendencias por cliente
  - Tendencias por producto/marca
  - Análisis estacional
  
- **Productos por Cliente**
  - Qué compra cada cliente (análisis detallado)
  - Segmentado por: Marca, Grupo, Subgrupo, Referencia
  - Frecuencia y valor de cada segmento
  
- **Clientes Inactivos**
  - Lista de clientes que han dejado de comprar
  - Días desde última compra
  - Último pedido y monto
  - Acción sugerida: Contactar
  
- **Clientes por Producto**
  - Para cada producto: quiénes lo compran
  - Frecuencia de compra
  - Última compra

**Funcionalidades:**
- Exportar análisis
- Generar reportes personalizados
- Configurar alertas de inactividad

---

#### 13. **DEVOLUCIONES** (MANTENER)
**Objetivo**: Gestión de devoluciones

**Sin cambios mayores:**
- Sistema actual funciona bien
- Solo mejoras menores de UI

---

#### 14. **IMPORTACIONES Y STOCK** (NUEVO)
**Objetivo**: Gestión de importaciones y detección de productos nuevos

**Secciones:**
- **Cargar Importación**
  - Subir Excel de importación
  - Procesar y detectar productos nuevos
  - Comparar con catálogo actual
  
- **Productos Nuevos Detectados**
  - Lista de productos nuevos
  - Información completa del producto
  - Recomendaciones automáticas:
    * "Ofrecer a X clientes que compran marcas similares"
    * Ver lista de clientes sugeridos
  
- **Actualización de Precios**
  - Productos con precio actualizado
  - Comparativa precio anterior vs nuevo
  - Confirmar actualizaciones
  
- **Control de Stock** (si aplica)
  - Cantidades disponibles
  - Alertas de stock bajo
  - Rotación de inventario

**Funcionalidades:**
- Procesamiento automático de Excel
- Detección inteligente de nuevos productos
- Integración con recomendaciones

---

#### 15. **REPORTES Y EXPORTACIÓN** (NUEVO)
**Objetivo**: Generar reportes personalizados

**Secciones:**
- **Reportes Predefinidos**
  - Ventas por período
  - Comisiones por vendedor
  - Productos más vendidos
  - Clientes por ciudad
  - Análisis de crédito
  
- **Exportación de Datos**
  - Exportar a Excel/CSV
  - Configurar columnas
  - Aplicar filtros antes de exportar
  
- **Reportes Programados** (Futuro)
  - Configurar reportes automáticos
  - Envío por email semanal/mensual

---

## RESUMEN DE CAMBIOS

### Pestañas Nuevas (4):
1. **Panel del Vendedor** - Vista consolidada para vendedores
2. **Análisis Geográfico** - Análisis profundo geográfico
3. **Análisis Comercial Avanzado** - Referencias quietas, negociaciones
4. **Análisis de Compras y Comportamiento** - Patrones detallados
5. **Importaciones y Stock** - Gestión de importaciones
6. **Reportes y Exportación** - Generación de reportes

### Pestañas Mejoradas (5):
1. **Clientes - Vista Vendedor** - Reorganizado con pestañas internas
2. **Nueva Venta Simple** - Mejor asistente de productos
3. **Catálogo Inteligente** - Productos nuevos y referencias quietas
4. **Mensajería y Comunicación** - WhatsApp/Email integrado
5. **Gestión de Clientes B2B** - Administración completa

### Pestañas que se Mantienen (6):
1. **Dashboard Ejecutivo** - Con mejoras menores
2. **Comisiones - Vista Administración** - Sin cambios
3. **Devoluciones** - Sin cambios
4. **Comisiones Mensuales** - Sin cambios
5. **Nueva Venta** (formulario completo) - Sin cambios
6. **Analytics Clientes** - Mejorar integración

---

## PRIORIDADES DE IMPLEMENTACIÓN

### FASE 1 (Crítico - Semana 1-2):
1. **Panel del Vendedor** - Es la entrada principal para vendedores
2. **Clientes - Vista Vendedor** - Reorganizar y mejorar
3. **Mensajería y Comunicación** - Integrar WhatsApp/Email

### FASE 2 (Importante - Semana 3-4):
4. **Análisis Geográfico** - Expandir funcionalidad actual
5. **Análisis Comercial Avanzado** - Referencias quietas y negociaciones
6. **Importaciones y Stock** - Detección de productos nuevos

### FASE 3 (Mejoras - Semana 5-6):
7. **Catálogo Inteligente** - Mejoras y nuevos productos
8. **Nueva Venta Simple** - Mejor asistente
9. **Análisis de Compras y Comportamiento** - Análisis profundo

### FASE 4 (Completar - Semana 7-8):
10. **Reportes y Exportación** - Sistema de reportes
11. **Mejoras generales** - Pulir todas las pestañas
12. **Testing y ajustes** - Pruebas y correcciones

---

## NOTAS IMPORTANTES

### Separación de Roles:
- **Vendedores** verán principalmente las primeras 6 pestañas
- **Gerencia** verá todas, pero enfocadas en las últimas 9
- Podemos implementar un sistema de roles en el futuro

### Funcionalidades Transversales:
- **Buscador Global**: Buscar clientes, productos, facturas desde cualquier pestaña
- **Notificaciones**: Sistema de alertas unificado
- **Historial**: Acceso rápido a acciones recientes

### Integraciones Necesarias:
- WhatsApp API (Twilio o similar)
- Email SMTP (ya parcialmente implementado)
- Mapas (Plotly/Leaflet para visualización geográfica)

---

**Esta propuesta reorganiza el CRM en 15 pestañas, separando claramente las herramientas operativas de vendedores del panel estratégico de gerencia.**

¿Quieres que ajuste algo específico antes de comenzar la implementación?

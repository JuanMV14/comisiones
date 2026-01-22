# MANEJO DE LA APLICACIÓN Y CÓDIGO

## ÍNDICE
1. [Estructura del Proyecto](#estructura-del-proyecto)
2. [Archivos Principales](#archivos-principales)
3. [Arquitectura de la Aplicación](#arquitectura-de-la-aplicación)
4. [Cómo Funciona Cada Módulo](#cómo-funciona-cada-módulo)
5. [Flujo de Datos](#flujo-de-datos)
6. [Guía de Uso para Desarrolladores](#guía-de-uso-para-desarrolladores)

---

## ESTRUCTURA DEL PROYECTO

```
comisiones/
├── app.py                          # Aplicación principal Streamlit
├── requirements.txt                # Dependencias Python
├── .env                           # Variables de entorno (no en git)
│
├── business/                      # Lógica de negocio
│   ├── calculations.py            # Cálculos de comisiones
│   ├── executive_dashboard.py     # Dashboard ejecutivo
│   ├── client_analytics.py        # Analytics de clientes
│   ├── client_classification.py   # Clasificación ML de clientes
│   ├── client_product_recommendations.py  # Recomendaciones productos
│   ├── monthly_commission_calculator.py   # Calculadora mensual
│   ├── ml_analytics.py            # Machine Learning
│   ├── notification_system.py     # Sistema de notificaciones
│   ├── sales_pipeline.py          # Pipeline de ventas Kanban
│   ├── guides_analyzer.py         # Análisis de guías
│   ├── invoice_alerts.py          # Alertas de facturas
│   ├── invoice_radication.py      # Radicación de facturas
│   ├── ai_recommendations.py      # Recomendaciones IA
│   ├── product_recommendations.py # Recomendaciones de productos
│   └── freight_validator.py       # Validación de flete
│
├── database/                      # Gestión de base de datos
│   ├── queries.py                 # Operaciones CRUD principales
│   ├── client_purchases_manager.py # Gestión compras clientes
│   ├── catalog_manager.py         # Gestión catálogo productos
│   └── sync_manager.py            # Sincronización compras-facturas
│
├── ui/                            # Interfaz de usuario
│   ├── tabs.py                    # Renderizador de pestañas principal
│   ├── components.py              # Componentes reutilizables
│   ├── executive_components.py    # Componentes dashboard ejecutivo
│   ├── modern_components.py       # Componentes UI modernos
│   ├── kanban_components.py       # Componentes Kanban
│   ├── ml_components.py           # Componentes ML/Analytics
│   ├── notification_components.py # Componentes notificaciones
│   ├── client_analytics_components.py  # Componentes analytics clientes
│   ├── client_analysis_components.py   # Componentes análisis clientes
│   ├── client_recommendations_components.py  # Componentes recomendaciones
│   ├── catalog_store_components.py     # Componentes catálogo
│   ├── guides_components.py       # Componentes guías
│   ├── theme_manager.py           # Sistema de temas (Dark/Light)
│   └── sync_components.py         # Componentes sincronización
│
├── utils/                         # Utilidades
│   ├── formatting.py              # Formateo de datos y helpers
│   ├── discount_parser.py         # Parser de descuentos
│   └── streamlit_helpers.py       # Helpers Streamlit
│
└── config/                        # Configuración
    └── settings.py                # Settings centralizados
```

---

## ARCHIVOS PRINCIPALES

### 1. `app.py` - Aplicación Principal

**¿Qué hace?**
- Punto de entrada de la aplicación Streamlit
- Inicializa todos los sistemas (Database, UI, Business Logic)
- Configura el tema y estilos CSS
- Define las pestañas principales
- Maneja el routing de pestañas

**Estructura:**
```python
def main():
    # 1. Inicializar sistemas
    systems = initialize_systems()
    
    # 2. Configurar UI (sidebar, tema, filtros)
    configurar_sidebar(systems)
    
    # 3. Cargar CSS y estilos
    load_css()
    
    # 4. Definir y renderizar tabs
    tabs = st.tabs([...])
    with tabs[X]:
        systems["tab_renderer"].render_xxx()
```

**Pestañas Principales:**
1. Dashboard Ejecutivo
2. Dashboard General
3. Comisiones
4. Nueva Venta
5. Nueva Venta Simple
6. Devoluciones
7. Mensajes (Radicación)
8. Clientes
9. Comisiones Mensuales
10. Catálogo
11. Análisis B2B
12. Analytics Clientes

---

### 2. `database/queries.py` - Gestor de Base de Datos

**¿Qué hace?**
- Clase `DatabaseManager` que centraliza TODAS las operaciones de base de datos
- Operaciones CRUD para comisiones, devoluciones, metas
- Cálculos automáticos de campos derivados (valor_neto, IVA, base_comision)
- Validación y corrección automática de inconsistencias

**Métodos Principales:**

#### Comisiones:
```python
def cargar_datos()              # Carga todas las comisiones con cache
def insertar_factura()          # Inserta nueva factura
def actualizar_factura()        # Actualiza factura existente
def obtener_factura_por_id()    # Obtiene factura específica
```

#### Devoluciones:
```python
def cargar_devoluciones()       # Carga devoluciones con info de factura
def insertar_devolucion()       # Crea devolución y recalcula comisión
def _actualizar_comision_por_devolucion()  # Recalcula comisión automáticamente
```

#### Metas:
```python
def obtener_meta_mes_actual()   # Obtiene meta del mes actual
def actualizar_meta()           # Actualiza o crea meta mensual
```

**Lógica Importante:**
- **Cálculo Automático**: `valor_neto` = `(valor - valor_flete) / 1.19`
- **Validación**: Corrige automáticamente si `valor ≠ valor_neto + IVA + flete`
- **Cache**: Usa `@st.cache_data(ttl=300)` para optimizar carga

---

### 3. `business/calculations.py` - Lógica de Negocio

**¿Qué hace?**
- `ComisionCalculator`: Calcula comisiones según reglas de negocio
- `MetricsCalculator`: Calcula métricas y estadísticas

**Clases:**

#### `ComisionCalculator`:
```python
def calcular_comision_inteligente():
    # Lógica simplificada:
    # - Si descuento_pie: base = valor_neto
    # - Si NO descuento_pie: base = valor_neto * 0.85
    # - Porcentaje según cliente_propio y descuentos
    #   * Cliente propio: 2.5% (sin desc) o 1.5% (con desc)
    #   * Cliente externo: 1.0% (sin desc) o 0.5% (con desc)
```

#### `MetricsCalculator`:
```python
def calcular_progreso_meta()        # Progreso hacia meta mensual
def calcular_metricas_separadas()   # Métricas clientes propios vs externos
def calcular_prediccion_meta()      # Predicción de cumplimiento meta
def calcular_tendencia_comisiones() # Tendencias de comisiones
def identificar_clientes_riesgo()    # Clientes en riesgo
```

---

### 4. `ui/tabs.py` - Renderizador de Pestañas

**¿Qué hace?**
- Clase `TabRenderer` que renderiza TODAS las pestañas
- Integra Database, Business Logic y UI Components
- Maneja formularios, validaciones y procesamiento de datos

**Métodos Principales:**

```python
def render_executive_dashboard()    # Dashboard ejecutivo con KPIs
def render_dashboard()              # Dashboard general
def render_comisiones()             # Tabla de comisiones con filtros
def render_nueva_venta()            # Formulario completa de venta
def render_nueva_venta_simple()    # Formulario simplificado
def render_devoluciones()           # Gestión de devoluciones
def render_clientes()               # Lista de clientes
def render_catalog_store()          # Catálogo de productos
def render_ia_alertas()             # IA y alertas
def render_radicacion_facturas()    # Radicación de facturas
```

**Método Clave: `_procesar_nueva_venta()`**
```python
def _procesar_nueva_venta(self, pedido, cliente, factura, ...):
    # 1. Validar datos
    # 2. Calcular campos derivados (valor_neto, IVA, base_comision)
    # 3. Calcular comisión usando ComisionCalculator
    # 4. Insertar factura en BD
    # 5. Si hay productos, guardarlos en compras_clientes
    # 6. Sincronizar si hay cliente B2B
```

---

### 5. `ui/components.py` - Componentes UI Reutilizables

**¿Qué hace?**
- Clase `UIComponents` con componentes reutilizables
- Modales, formularios, tablas, etc.

**Componentes:**
```python
def render_modal_pago()             # Modal para registrar pago
def render_modal_edicion_factura()  # Modal para editar factura
def render_modal_nueva_devolucion() # Modal nueva devolución
def render_filtros_comisiones()     # Filtros para comisiones
```

---

### 6. `business/executive_dashboard.py` - Dashboard Ejecutivo

**¿Qué hace?**
- Clase `ExecutiveDashboard` que calcula todos los KPIs ejecutivos
- Métricas financieras y operacionales
- Proyecciones y tendencias

**Métodos:**
```python
def calcular_kpis_completos()       # Todos los KPIs
def _calcular_kpis_financieros()    # KPIs financieros
def _calcular_kpis_operacionales()  # KPIs operacionales
def _calcular_tendencias()          # Tendencias 6 meses
def _calcular_proyecciones()        # Proyecciones fin de mes
```

---

## ARQUITECTURA DE LA APLICACIÓN

### Patrón: MVC Adaptado

```
┌─────────────────┐
│   UI Layer      │  ← Streamlit Components
│  (ui/tabs.py)   │     (ui/*_components.py)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Business Layer  │  ← Lógica de Negocio
│ (business/*.py) │     (Cálculos, Validaciones)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Database Layer │  ← Operaciones BD
│ (database/*.py) │     (Supabase Queries)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Supabase      │  ← Base de Datos PostgreSQL
│   (Cloud DB)    │
└─────────────────┘
```

### Flujo de Datos Típico:

1. **Usuario interactúa** → `ui/tabs.py` → `TabRenderer.render_xxx()`
2. **TabRenderer llama** → `business/xxx.py` → Lógica de negocio
3. **Business llama** → `database/queries.py` → Operaciones BD
4. **DatabaseManager** → Supabase → PostgreSQL
5. **Respuesta** → DataFrame → Business → UI → Usuario

---

## CÓMO FUNCIONA CADA MÓDULO

### Módulo: Nueva Venta

**Flujo Completo:**

1. **Usuario ingresa datos** en `render_nueva_venta_simple()`:
   - Pedido, Cliente, Factura, Valor Total, Flete, etc.

2. **Cálculo en tiempo real** (preview):
   ```python
   valor_productos_con_iva = valor_total - valor_flete
   valor_neto_calculado = valor_productos_con_iva / 1.19
   iva_calculado = valor_productos_con_iva - valor_neto_calculado
   
   # Calcular comisión
   calc = ComisionCalculator.calcular_comision_inteligente(
       valor_total=valor_productos_con_iva,
       cliente_propio=cliente_propio,
       tiene_descuento=descuento_adicional > 0,
       descuento_pie=descuento_pie_factura
   )
   ```

3. **Usuario confirma** → Llama `_procesar_nueva_venta()`

4. **Procesamiento**:
   - Validar datos
   - Obtener/crear cliente B2B
   - Calcular campos finales
   - Insertar en `comisiones` table
   - Si hay productos, insertar en `compras_clientes`
   - Sincronizar si corresponde

5. **Resultado**: Factura creada, comisión calculada automáticamente

---

### Módulo: Sincronización Compras-Facturas

**Flujo:**

1. **Análisis**: `SyncManager.analizar_sincronizacion()`
   - Carga compras sin sincronizar
   - Busca facturas que coincidan por:
     * Número de documento
     * Cliente (NIT/nombre)
     * Fecha cercana (±7 días)
     * Monto similar (±10%)
   - Calcula score de coincidencia (0-1)

2. **Sincronización**: `SyncManager.sincronizar_automaticas()`
   - Para cada coincidencia con score ≥ 0.8:
     * Busca TODOS los productos del documento
     * Vincula todos a la factura (`factura_id`)
     * Marca como sincronizado
   - Actualiza factura con `compra_cliente_id`

3. **Resultado**: Compras vinculadas a facturas, productos relacionados

---

### Módulo: Cálculo de Comisiones

**Lógica Completa:**

```python
# 1. Calcular base
if descuento_pie_factura:
    base = valor_neto
else:
    base = valor_neto * 0.85  # Descuento estándar del 15%

# 2. Restar devoluciones (si aplica)
base_final = base - (valor_devuelto / 1.19)

# 3. Determinar porcentaje
tiene_descuento = descuento_adicional > 0
if cliente_propio:
    porcentaje = 1.5 if tiene_descuento else 2.5
else:
    porcentaje = 0.5 if tiene_descuento else 1.0

# 4. Verificar pérdida por pago tardío
if dias_pago > 80:
    comision = 0  # Pierde comisión
else:
    comision = base_final * (porcentaje / 100)
```

**Reglas Especiales:**
- **Condición especial**: Límite 60 días (vs 45 normal) para aplicar 15% descuento
- **Pago tardío**: Si paga después de 80 días → comisión = 0

---

### Módulo: Dashboard Ejecutivo

**KPIs Calculados:**

#### Financieros:
- Total Facturado (Propios + Externos)
- Total Comisiones Generadas
- Facturas Pendientes
- Facturas Vencidas
- Riesgo Financiero (Score 0-100)

#### Operacionales:
- Total Facturas (Propios + Externos)
- Facturas Pagadas vs Pendientes
- Ticket Promedio
- Comisión Promedio
- Tasa de Conversión

#### Proyecciones:
- Proyección Fin de Mes (3 escenarios: Conservador, Realista, Optimista)
- Tendencias 6 meses
- Comparativas MoM (Month over Month)

---

## FLUJO DE DATOS

### Ejemplo: Crear Nueva Venta

```
Usuario
  ↓
[Formulario Nueva Venta] → ui/tabs.py:render_nueva_venta_simple()
  ↓
[Validación] → Verifica campos requeridos
  ↓
[Calcular Preview] → business/calculations.py:calcular_comision_inteligente()
  ↓
[Usuario Confirma] → ui/tabs.py:_procesar_nueva_venta()
  ↓
[Obtener Cliente] → database/client_purchases_manager.py:obtener_cliente()
  ↓
[Insertar Factura] → database/queries.py:insertar_factura()
  ↓
[Si hay productos] → database/client_purchases_manager.py:cargar_compras_cliente()
  ↓
[Insertar Compras] → database/queries.py:insertar_factura() → compras_clientes
  ↓
[Actualizar UI] → st.success("Venta registrada")
  ↓
[Limpiar Cache] → st.cache_data.clear()
```

---

### Ejemplo: Calcular Dashboard

```
Usuario abre Dashboard
  ↓
[Renderizar Tab] → ui/tabs.py:render_executive_dashboard()
  ↓
[Cargar Datos] → database/queries.py:cargar_datos() [CACHE]
  ↓
[Calcular KPIs] → business/executive_dashboard.py:calcular_kpis_completos()
  ↓
  ├─→ _calcular_kpis_financieros() → Sumas, promedios, filtros
  ├─→ _calcular_kpis_operacionales() → Conteos, ratios
  └─→ _calcular_proyecciones() → Cálculos predictivos
  ↓
[Renderizar Componentes] → ui/executive_components.py
  ↓
[Mostrar al Usuario] → Streamlit UI
```

---

## GUÍA DE USO PARA DESARROLLADORES

### Agregar Nueva Funcionalidad

#### 1. Nueva Pestaña

**Paso 1**: Crear método en `ui/tabs.py`
```python
def render_mi_nueva_tab(self):
    st.header("Mi Nueva Tab")
    # Tu código aquí
```

**Paso 2**: Agregar en `app.py`
```python
tabs = st.tabs([..., "Mi Nueva Tab"])
with tabs[X]:
    render_tab_safe(X, systems["tab_renderer"].render_mi_nueva_tab)
```

#### 2. Nueva Operación de Base de Datos

**En `database/queries.py`:**
```python
def mi_nueva_operacion(self, param1: str, param2: int) -> pd.DataFrame:
    """Descripción de la operación"""
    try:
        response = self.supabase.table("mi_tabla").select("*").eq("campo", param1).execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return pd.DataFrame()
```

#### 3. Nueva Lógica de Negocio

**En `business/calculations.py` o nuevo archivo:**
```python
class MiCalculadora:
    @staticmethod
    def calcular_algo(df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula algo"""
        resultado = {
            "total": df["valor"].sum(),
            "promedio": df["valor"].mean()
        }
        return resultado
```

#### 4. Nuevo Componente UI

**En `ui/components.py` o nuevo archivo:**
```python
class MiComponenteUI:
    def render_mi_componente(self, data: Dict):
        """Renderiza mi componente"""
        st.markdown("### Mi Componente")
        st.write(f"Total: {data['total']}")
```

---

### Mejores Prácticas

1. **Cache para Operaciones Costosas**:
   ```python
   @st.cache_data(ttl=300)  # 5 minutos
   def cargar_datos_costosos(_self):
       # Operación costosa
       return datos
   ```

2. **Manejo de Errores**:
   ```python
   try:
       # Operación
   except Exception as e:
       st.error(f"Error: {str(e)}")
       return None  # o valor por defecto
   ```

3. **Validación de Datos**:
   ```python
   from utils.formatting import DataValidator
   errors = DataValidator.validate_venta_data(data)
   if errors:
       for error in errors:
           st.error(error)
   ```

4. **Type Hints**:
   ```python
   def mi_funcion(param1: str, param2: int) -> Dict[str, Any]:
       # Código
   ```

5. **Docstrings**:
   ```python
   def mi_funcion(param1: str) -> pd.DataFrame:
       """
       Descripción de qué hace la función.
       
       Args:
           param1: Descripción del parámetro
       
       Returns:
           DataFrame con los resultados
       """
   ```

---

## FUNCIONES HELPER IMPORTANTES

### `utils/formatting.py`

```python
# Formateo
format_currency(value)           # "$1,234,567"
format_percentage(value)         # "12.5%"
format_date(date_value)          # "01/01/2025"

# Conversiones seguras
safe_float_conversion(value)     # Convierte a float de forma segura
safe_int_conversion(value)       # Convierte a int de forma segura

# Validaciones
DataValidator.validate_venta_data(data)     # Valida datos de venta
DataValidator.validate_cliente_data(data)   # Valida datos de cliente

# Cálculos
CalculationHelpers.calcular_valor_neto_desde_total(valor, flete)
CalculationHelpers.calcular_iva_desde_total(valor, flete)
CalculationHelpers.validar_consistencia_valores(valor, neto, iva, flete)
```

---

## DEBUGGING Y TROUBLESHOOTING

### Problemas Comunes

1. **Datos no se cargan**:
   - Verificar `SUPABASE_URL` y `SUPABASE_KEY` en `.env`
   - Limpiar cache: `st.cache_data.clear()`

2. **Cálculos incorrectos**:
   - Verificar lógica en `business/calculations.py`
   - Revisar validaciones en `database/queries.py:_calcular_campos_derivados()`

3. **Errores de UI**:
   - Verificar que las claves (`key=`) sean únicas
   - Revisar estados de sesión: `st.session_state`

4. **Performance lento**:
   - Agregar `@st.cache_data` donde sea posible
   - Optimizar queries de base de datos
   - Reducir cantidad de datos cargados

---

## REFERENCIAS RÁPIDAS

### Tablas Principales:
- `comisiones` → Facturas/comisiones
- `devoluciones` → Devoluciones de facturas
- `metas_mensuales` → Metas mensuales
- `clientes_b2b` → Clientes B2B
- `compras_clientes` → Historial de compras
- `catalogo_productos` → Catálogo de productos

### Clases Principales:
- `DatabaseManager` → Todas las operaciones BD
- `ComisionCalculator` → Cálculos de comisiones
- `TabRenderer` → Renderizado de pestañas
- `UIComponents` → Componentes UI
- `ExecutiveDashboard` → KPIs ejecutivos

---

**Última actualización**: Enero 2025  
**Versión**: 1.0  
**Desarrollado con**: Streamlit, Python, Supabase

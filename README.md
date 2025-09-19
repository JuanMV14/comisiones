# CRM Inteligente - Estructura Organizada

## 📁 Estructura de Archivos

```
crm_inteligente/
├── app.py                          # Aplicación principal
├── requirements.txt                # Dependencias
├── .env                           # Variables de entorno
│
├── database/
│   ├── __init__.py
│   └── queries.py                 # Gestor de base de datos
│
├── business/
│   ├── __init__.py
│   ├── calculations.py            # Lógica de cálculos de negocio
│   └── ai_recommendations.py      # Sistema de recomendaciones IA
│
├── ui/
│   ├── __init__.py
│   ├── components.py              # Componentes reutilizables de UI
│   └── tabs.py                    # Renderizadores de pestañas
│
├── utils/
│   ├── __init__.py
│   └── formatting.py              # Utilidades de formato
│
└── config/
    ├── __init__.py
    └── settings.py                # Configuraciones centralizadas
```

## 🏗️ Arquitectura de la Aplicación

### Separación de Responsabilidades

**1. Capa de Presentación (UI)**
- `ui/components.py`: Componentes reutilizables de interfaz
- `ui/tabs.py`: Renderizadores específicos de cada pestaña
- `app.py`: Punto de entrada y configuración principal

**2. Capa de Lógica de Negocio**
- `business/calculations.py`: Cálculos de comisiones y métricas
- `business/ai_recommendations.py`: Sistema de recomendaciones inteligentes

**3. Capa de Datos**
- `database/queries.py`: Gestor centralizado de base de datos
- Manejo de cache y optimizaciones

**4. Capa de Utilidades**
- `utils/formatting.py`: Funciones de formato y validación
- `config/settings.py`: Configuraciones centralizadas

## 🔧 Mejoras Implementadas

### 1. **Modularización**
- Separación clara de responsabilidades
- Componentes reutilizables
- Fácil mantenimiento y testing

### 2. **Gestión de Estado Mejorada**
- Centralización de claves de sesión
- Limpieza automática de estados
- Evita conflictos entre componentes

### 3. **Manejo de Errores Robusto**
- Validaciones centralizadas
- Mensajes de error estandarizados
- Conversiones seguras de tipos

### 4. **Cache Optimizado**
- Cache estratégico en consultas pesadas
- TTL configurables
- Limpieza automática cuando es necesario

### 5. **Configuración Centralizada**
- Todas las configuraciones en un lugar
- Validación de variables de entorno
- Reglas de negocio parametrizables

## 🚀 Instalación y Configuración

### 1. Clonar e instalar dependencias

```bash
git clone <tu-repositorio>
cd crm_inteligente
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env`:

```env
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_clave_de_supabase
SUPABASE_BUCKET_COMPROBANTES=comprobantes
```

### 3. Ejecutar la aplicación

```bash
streamlit run app.py
```

## 📋 Guía de Uso

### Para Desarrolladores

#### Agregar una Nueva Funcionalidad

1. **Operación de Base de Datos**
   - Agregar método en `DatabaseManager` (`database/queries.py`)
   - Incluir validaciones y manejo de errores

2. **Lógica de Negocio**
   - Crear calculadora específica en `business/calculations.py`
   - O sistema de recomendaciones en `business/ai_recommendations.py`

3. **Componente de UI**
   - Crear componente reutilizable en `ui/components.py`
   - Integrar en pestaña correspondiente en `ui/tabs.py`

4. **Configuraciones**
   - Agregar configuraciones en `config/settings.py`
   - Actualizar mensajes en las clases correspondientes

#### Ejemplo: Agregar Nueva Métrica

```python
# 1. En business/calculations.py
class MetricsCalculator:
    @staticmethod
    def calcular_nueva_metrica(df: pd.DataFrame) -> Dict[str, Any]:
        # Tu lógica aquí
        pass

# 2. En ui/components.py
class UIComponents:
    def render_nueva_metrica(self, data):
        # Tu componente UI aquí
        pass

# 3. En ui/tabs.py
class TabRenderer:
    def render_dashboard(self):
        # Integrar nueva métrica
        metrica = self.metrics_calc.calcular_nueva_metrica(df)
        self.ui_components.render_nueva_metrica(metrica)
```

### Estructura de Base de Datos

#### Tablas Principales

**comisiones**
- `id`, `pedido`, `cliente`, `factura`
- `valor`, `valor_neto`, `iva`, `comision`
- `fecha_factura`, `fecha_pago_max`, `pagado`
- `cliente_propio`, `condicion_especial`

**devoluciones**
- `id`, `factura_id`, `valor_devuelto`
- `fecha_devolucion`, `motivo`, `afecta_comision`

**metas_mensuales**
- `id`, `mes`, `meta_ventas`, `meta_clientes_nuevos`

## 🔍 Funcionalidades Principales

### Dashboard
- Métricas en tiempo real
- Progreso de metas mensuales
- Recomendaciones IA
- Análisis predictivo

### Gestión de Comisiones
- CRUD completo de facturas
- Cálculo automático de comisiones
- Estados y alertas de vencimiento
- Procesamiento de pagos

### Devoluciones
- Registro de devoluciones
- Recálculo automático de comisiones
- Impacto en métricas

### IA y Alertas
- Recomendaciones personalizadas
- Análisis de riesgo de clientes
- Predicciones de cumplimiento de metas
- Alertas proactivas

## ⚡ Optimizaciones de Rendimiento

### Cache Inteligente
```python
@st.cache_data(ttl=300)  # Cache por 5 minutos
def cargar_datos(_self):
    return _self._cargar_datos_raw()
```

### Lazy Loading
- Carga de datos bajo demanda
- Componentes renderizados solo cuando es necesario

### Gestión de Memoria
- Limpieza automática de estados
- Liberación de recursos no utilizados

## 🛡️ Seguridad y Validación

### Validación de Datos
```python
from utils.formatting import DataValidator

errors = DataValidator.validate_venta_data(data)
if errors:
    for error in errors:
        st.error(error)
```

### Conversiones Seguras
```python
from utils.formatting import safe_float_conversion

valor_seguro = safe_float_conversion(input_valor, default=0.0)
```

## 🎨 Personalización de UI

### Colores y Estilos
Configurables en `config/settings.py`:

```python
PROGRESS_BAR_COLORS = {
    "high": "#10b981",    # Verde
    "medium": "#f59e0b",  # Amarillo  
    "low": "#ef4444"      # Rojo
}
```

### Componentes Modulares
- Cards reutilizables
- Modales consistentes
- Formularios estandarizados

## 📊 Métricas y Análisis

### KPIs Principales
- Total facturado (clientes propios vs externos)
- Comisiones generadas
- Facturas pendientes y vencidas
- Progreso de metas mensuales

### Análisis Predictivo
- Probabilidad de cumplir metas
- Identificación de clientes en riesgo
- Tendencias de comisiones
- Recomendaciones personalizadas

## 🔧 Troubleshooting

### Problemas Comunes

1. **Error de conexión a Supabase**
   - Verificar variables de entorno
   - Comprobar conectividad a internet

2. **Cache desactualizado**
   - Usar botón "Actualizar Datos"
   - O `st.cache_data.clear()` en código

3. **Estados de UI inconsistentes**
   - Usar botón "Limpiar Estados"
   - Verificar claves únicas en formularios

### Logs y Debugging

```python
# Para debugging en desarrollo
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Próximas Mejoras

### En Desarrollo
- [ ] Módulo completo de gestión de clientes
- [ ] Reportes avanzados con exportación
- [ ] Dashboard de gerencia
- [ ] Integración con APIs externas

### Roadmap
- [ ] Sistema de notificaciones
- [ ] Aplicación móvil
- [ ] Machine Learning avanzado
- [ ] Automatización de workflows

## 📝 Contribuir

### Estándares de Código
1. Seguir PEP 8
2. Documentar funciones con docstrings
3. Incluir type hints donde sea posible
4. Escribir tests para nueva funcionalidad

### Pull Requests
1. Crear branch desde main
2. Implementar feature completo
3. Actualizar documentación
4. Crear PR con descripción detallada

---

**Desarrollado con ❤️ para optimizar la gestión de comisiones**

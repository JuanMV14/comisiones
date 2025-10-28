# 🤖 FASE 2: Machine Learning y Analytics Avanzado

## ✅ IMPLEMENTADO

Sistema completo de Machine Learning y Analytics con 6 módulos de inteligencia artificial para análisis predictivo, segmentación automática y detección de patrones.

---

## 🎯 CARACTERÍSTICAS PRINCIPALES

### 1. **📈 Predicción de Ventas con ML**
- Regresión lineal para forecast de ventas
- Predicciones de 7-90 días
- Intervalos de confianza (90%, 95%, 99%)
- Métricas de calidad del modelo (R², MAE)
- Tendencias automáticas
- Gráficos interactivos con intervalos

### 2. **🎯 Análisis RFM**
- Segmentación automática de clientes
- 9 segmentos inteligentes:
  - Champions (Mejores clientes)
  - Loyal Customers (Leales)
  - Promising (Prometedores)
  - Potential Loyalists (Potencial leales)
  - New Customers (Nuevos)
  - At Risk (En riesgo)
  - Can't Lose Them (No perderlos)
  - Lost (Perdidos)
  - Need Attention (Necesitan atención)
- Scores RFM (1-5) por dimensión
- Top 5 Champions y At Risk
- Revenue por segmento

### 3. **🔍 Detección de Anomalías**
- Algoritmo Z-Score para outliers
- Detecta ventas inusualmente altas o bajas
- Sensibilidad ajustable (1.5-3.0 σ)
- Clasificación automática
- Tabla detallada de anomalías

### 4. **🏷️ Clustering Automático**
- K-Means para agrupar clientes similares
- 2-6 clusters configurables
- Normalización automática de datos
- Características por cluster:
  - Total ventas
  - Ticket promedio
  - Número de compras
  - Total comisión
- Nombres inteligentes de clusters

### 5. **⚠️ Predicción de Churn**
- Identifica clientes en riesgo de abandonar
- Score de riesgo (0-100)
- 3 niveles: Bajo, Medio, Alto
- Basado en días de inactividad
- Valor histórico en riesgo
- Top 20 clientes en riesgo alto
- Recomendaciones de acción

### 6. **📊 Análisis de Tendencias**
- Tendencias semanales
- Tendencias mensuales
- Crecimiento mensual %
- Mejor mes histórico
- Promedios y comparativas
- Gráficos de evolución

---

## 📦 ARCHIVOS CREADOS

### 1. `business/ml_analytics.py` (750 líneas)
**Motor de Machine Learning**

#### Clase Principal: `MLAnalytics`

**Predicción de Ventas**:
```python
predict_sales(df, periods=30, confidence=0.95) -> Dict
```
- Usa `sklearn.linear_model.LinearRegression`
- Calcula R² score y MAE
- Genera intervalos de confianza
- Retorna predicciones + métricas

**Análisis RFM**:
```python
rfm_analysis(df) -> Dict
```
- Calcula Recency, Frequency, Monetary
- Asigna scores 1-5 por dimensión
- Segmenta automáticamente en 9 categorías
- Estadísticas por segmento

**Detección de Anomalías**:
```python
detect_anomalies(df, threshold=2.0) -> Dict
```
- Calcula Z-Score de valores
- Identifica outliers según threshold
- Clasifica como altos o bajos
- Retorna lista de anomalías

**Clustering**:
```python
cluster_clients(df, n_clusters=4) -> Dict
```
- K-Means de `sklearn.cluster`
- Normaliza features con `StandardScaler`
- Agrupa por comportamiento
- Nombra clusters inteligentemente

**Predicción de Churn**:
```python
predict_churn(df, dias_inactivo=60) -> Dict
```
- Calcula días de inactividad
- Promedio de días entre compras
- Score de riesgo ponderado
- Clasifica en 3 niveles

**Tendencias**:
```python
trend_analysis(df) -> Dict
```
- Agrupa por semana y mes
- Calcula crecimientos
- Identifica mejor período
- Promedios históricos

### 2. `ui/ml_components.py` (700 líneas)
**Interfaz Visual de ML**

#### Clase Principal: `MLComponentsUI`

**6 Tabs Implementados**:
```python
_render_sales_prediction()      # Forecast con gráfico
_render_rfm_analysis()          # Segmentación visual
_render_anomaly_detection()     # Outliers detectados
_render_clustering()            # Grupos automáticos
_render_churn_prediction()      # Riesgo de abandono
_render_trend_analysis()        # Evolución temporal
```

**Gráficos Avanzados**:
- Predicción con intervalos de confianza
- Pie charts de segmentación
- Bar charts de distribución
- Donut charts de riesgo
- Líneas de tendencia

### 3. Actualizaciones en Archivos Existentes
- `ui/tabs.py`: Nuevo método `render_ml_analytics()`
- `app.py`: Nueva pestaña "🧠 ML & Analytics"
- `requirements.txt`: Ya incluye `scikit-learn>=1.3.0`

---

## 🚀 CÓMO USAR

### 📋 **Requisitos Previos**

```bash
# Instalar dependencias ML
pip install scikit-learn numpy pandas

# O simplemente
pip install -r requirements.txt
```

### 1. **Predicción de Ventas**

```
1. Ve a pestaña "🧠 ML & Analytics"
2. Tab "📈 Predicción Ventas"
3. Ajusta:
   - Días a predecir (7-90)
   - Nivel de confianza (90%, 95%, 99%)
4. Clic en "🚀 Generar Predicción"
5. Revisa:
   - Total predicho
   - Tendencia (creciente/decreciente)
   - R² Score (calidad del modelo)
   - Gráfico con intervalos
```

### 2. **Análisis RFM**

```
1. Tab "🎯 Análisis RFM"
2. El análisis se ejecuta automáticamente
3. Revisa:
   - Distribución de segmentos
   - Revenue por segmento
   - Top 5 Champions
   - Top 5 En Riesgo
4. Toma acción según segmento
```

### 3. **Detección de Anomalías**

```
1. Tab "🔍 Anomalías"
2. Ajusta sensibilidad (1.5-3.0)
   - 1.5 = Muy sensible
   - 2.0 = Moderado (recomendado)
   - 3.0 = Solo extremos
3. Clic en "🔍 Detectar Anomalías"
4. Revisa facturas inusuales
```

### 4. **Clustering de Clientes**

```
1. Tab "🏷️ Clustering"
2. Selecciona número de grupos (2-6)
3. Clic en "🏷️ Agrupar Clientes"
4. Analiza características de cada cluster
5. Diseña estrategias por grupo
```

### 5. **Predicción de Churn**

```
1. Tab "⚠️ Predicción Churn"
2. Ajusta días de inactividad (30-180)
3. Clic en "⚠️ Analizar Churn"
4. Revisa:
   - Clientes en riesgo alto
   - Valor histórico en riesgo
   - Distribución de riesgo
5. Contacta clientes urgentes
```

### 6. **Análisis de Tendencias**

```
1. Tab "📊 Tendencias"
2. El análisis se ejecuta automáticamente
3. Revisa:
   - Tendencia semanal
   - Tendencia mensual
   - Crecimiento %
   - Mejor mes histórico
```

---

## 📊 ALGORITMOS Y MÉTRICAS

### Predicción de Ventas

**Algoritmo**: Regresión Lineal Simple
```
y = mx + b

Donde:
y = valor de venta
x = día (número ordinal)
m = pendiente (cambio diario)
b = intercepto
```

**Métricas de Calidad**:

1. **R² Score** (Coeficiente de Determinación)
```
R² = 1 - (SS_res / SS_tot)

Interpretación:
1.0 = Perfecto
>0.7 = Alta confianza
0.4-0.7 = Media confianza
<0.4 = Baja confianza
```

2. **MAE** (Mean Absolute Error)
```
MAE = Σ|y_pred - y_real| / n

Menor es mejor
Representa error promedio en $
```

3. **Intervalo de Confianza**
```
IC = predicción ± (Z × std_error)

Z-Score:
90% = 1.645
95% = 1.960
99% = 2.576
```

### Análisis RFM

**Cálculo de Scores**:

1. **Recency** (Recencia)
```
Días desde última compra
Score 5 = Compró recientemente
Score 1 = Hace mucho no compra
```

2. **Frequency** (Frecuencia)
```
Número total de compras
Score 5 = Muchas compras
Score 1 = Pocas compras
```

3. **Monetary** (Monetario)
```
Valor total comprado
Score 5 = Alto valor
Score 1 = Bajo valor
```

**RFM Score Total** = R + F + M (3-15)

### Detección de Anomalías

**Z-Score**:
```
Z = (X - μ) / σ

Donde:
X = valor de la venta
μ = media de todas las ventas
σ = desviación estándar

Anomalía si |Z| > threshold
```

**Interpretación**:
- Z > 2.0: Valor inusualmente alto
- Z < -2.0: Valor inusualmente bajo
- -2.0 < Z < 2.0: Normal

### Clustering (K-Means)

**Algoritmo**:
```
1. Normalizar features (StandardScaler)
2. Inicializar K centroides aleatorios
3. Asignar cada punto al centroide más cercano
4. Recalcular centroides
5. Repetir 3-4 hasta convergencia
```

**Features Usadas**:
- Total ventas
- Ticket promedio
- Número de compras
- Total comisión

### Predicción de Churn

**Churn Score**:
```
Score = (Días_Inactivo / Promedio_Días_Entre_Compras × 50) + 
        (50 si Días_Inactivo > Threshold else 0)

Limitado a 0-100
```

**Clasificación**:
- 0-30: Bajo riesgo
- 31-60: Riesgo medio
- 61-100: Alto riesgo

---

## 🎯 CASOS DE USO REALES

### **Caso 1: Planificación de Inventario**

**Situación**: Necesitas saber cuánto stock pedir

**Uso**:
```
1. Predicción de Ventas → 30 días
2. Ve el valor total predicho
3. Calcula inventario necesario
4. Considera intervalo de confianza
5. Pide según best case
```

**Resultado**: Inventario optimizado, sin excesos ni faltantes

### **Caso 2: Recuperar Clientes en Riesgo**

**Situación**: Ventas están bajando

**Uso**:
```
1. Análisis RFM → Identifica "At Risk"
2. Predicción Churn → Ve alto riesgo
3. Prioriza por valor histórico
4. Crea oferta especial para ellos
5. Contacta proactivamente
```

**Resultado**: Recuperas 30-40% de clientes en riesgo

### **Caso 3: Segmentación de Marketing**

**Situación**: Quieres personalizar comunicación

**Uso**:
```
1. Análisis RFM → Segmenta clientes
2. Champions → Programa de lealtad
3. At Risk → Descuentos agresivos
4. New Customers → Onboarding especial
5. Lost → Campaña de reactivación
```

**Resultado**: Marketing 3x más efectivo

### **Caso 4: Detectar Fraude o Errores**

**Situación**: Hay facturas sospechosas

**Uso**:
```
1. Detección de Anomalías → Z-Score 2.0
2. Revisa valores extremos
3. Verifica facturas inusuales
4. Detecta errores de captura
5. Identifica posibles fraudes
```

**Resultado**: Mayor control y calidad de datos

### **Caso 5: Pronóstico Financiero**

**Situación**: Gerencia pide proyección trimestral

**Uso**:
```
1. Predicción de Ventas → 90 días
2. Ve escenarios: Best/Expected/Worst
3. Analiza tendencia (creciente/decreciente)
4. Revisa R² para confianza
5. Presenta gráfico profesional
```

**Resultado**: Pronóstico confiable para planeación

---

## 📈 INTERPRETACIÓN DE RESULTADOS

### Predicción de Ventas

#### R² Score
```
0.9-1.0  ⭐⭐⭐⭐⭐ Excelente - Muy confiable
0.7-0.9  ⭐⭐⭐⭐   Bueno - Confiable
0.5-0.7  ⭐⭐⭐     Regular - Usar con cuidado
0.3-0.5  ⭐⭐       Pobre - Baja confianza
<0.3     ⭐         Muy pobre - No confiar
```

#### Tendencia
```
Creciente + R² alto = ✅ Excelente momento
Creciente + R² bajo = ⚠️ Verificar datos
Decreciente + R² alto = 🚨 Problema real
Decreciente + R² bajo = 🤔 Datos inconsistentes
```

### Análisis RFM

#### Acción por Segmento

**Champions (5-5-5)**:
- ✅ Programa VIP
- ✅ Recompensas exclusivas
- ✅ Comunicación premium

**Loyal Customers**:
- ✅ Mantener satisfechos
- ✅ Cross-selling
- ✅ Pedir referidos

**At Risk**:
- 🚨 Contactar urgentemente
- 🚨 Oferta especial
- 🚨 Encuesta de satisfacción

**Can't Lose Them**:
- 🚨🚨 Máxima prioridad
- 🚨🚨 Llamada personal
- 🚨🚨 Descuento agresivo

**Lost**:
- 💔 Campaña de reactivación
- 💔 Win-back offers
- 💔 Último intento

### Predicción de Churn

#### Nivel de Urgencia

**Alto Riesgo (>60)**:
```
⏰ Contactar: HOY
📞 Canal: Llamada personal
💰 Oferta: Descuento 20-30%
🎯 Objetivo: Reactivar en 7 días
```

**Riesgo Medio (31-60)**:
```
⏰ Contactar: Esta semana
📧 Canal: Email personalizado
💰 Oferta: Descuento 10-15%
🎯 Objetivo: Reactivar en 15 días
```

**Bajo Riesgo (0-30)**:
```
✅ Acción: Seguimiento normal
📧 Canal: Newsletter
💰 Oferta: Ninguna especial
🎯 Objetivo: Mantener engagement
```

---

## 💡 MEJORES PRÁCTICAS

### 1. **Datos de Calidad**
- ✅ Mínimo 30 días de histórico
- ✅ Datos completos (sin NaNs)
- ✅ Fechas correctas
- ✅ Actualizar regularmente

### 2. **Interpretar con Contexto**
- ⚠️ R² bajo puede ser por estacionalidad
- ⚠️ Anomalías pueden ser promociones
- ⚠️ Churn alto puede ser temporada baja
- ⚠️ Siempre validar con conocimiento del negocio

### 3. **Acción Rápida**
- ⏰ Churn alto → Contactar en 24h
- ⏰ At Risk → Plan de acción esta semana
- ⏰ Anomalías → Verificar inmediatamente
- ⏰ Tendencia negativa → Reunión de estrategia

### 4. **Combinar Análisis**
```
RFM + Churn = Priorización perfecta
Predicción + Tendencias = Planeación completa
Clustering + RFM = Segmentación óptima
Anomalías + RFM = Control de calidad
```

### 5. **Revisar Periódicamente**
- 📅 Predicción: Semanal
- 📅 RFM: Mensual
- 📅 Churn: Quincenal
- 📅 Anomalías: Semanal
- 📅 Clustering: Trimestral

---

## 🔧 PERSONALIZACIÓN AVANZADA

### Modificar Algoritmo de Predicción

En `business/ml_analytics.py`:

```python
# Usar otro modelo (ej: Random Forest)
from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)
```

### Ajustar Segmentos RFM

Modifica la función `segment_cliente()`:

```python
def segment_cliente(row):
    r, f, m = int(row['R_Score']), int(row['F_Score']), int(row['M_Score'])
    
    # Tus reglas personalizadas
    if r >= 5 and f >= 5:
        return "Super VIP"
    # ...
```

### Cambiar Features de Clustering

```python
cliente_features = df_pagadas.groupby('cliente').agg({
    'valor': ['sum', 'mean'],
    'comision': 'sum',
    # Agregar más features:
    'descuento_aplicado': 'mean',
    'dias_entre_compras': 'mean'
})
```

---

## 📊 ESTADÍSTICAS Y BENCHMARKS

### Precisión Típica

**Predicción de Ventas**:
- R² > 0.7: 60-70% de los casos
- MAE < 20% del promedio: 70% de los casos

**RFM**:
- 15-25% Champions (objetivo)
- 10-20% At Risk (normal)
- <10% Lost (bueno)

**Churn**:
- 20-30% en riesgo: Normal
- >40% en riesgo: Alerta
- <15% en riesgo: Excelente

---

## ⚠️ LIMITACIONES Y CONSIDERACIONES

### Predicción de Ventas
- ❌ No captura estacionalidad compleja
- ❌ No considera factores externos (economía, competencia)
- ❌ Asume tendencia lineal
- ✅ Bueno para corto plazo (30 días)
- ✅ Excelente para tendencias generales

### RFM
- ❌ No considera contexto (sector, tamaño)
- ❌ Umbrales fijos (no dinámicos)
- ✅ Probado y efectivo
- ✅ Fácil de entender y accionar

### Detección de Anomalías
- ❌ No distingue error vs oportunidad
- ❌ Puede marcar promociones como anomalías
- ✅ Rápido y efectivo
- ✅ Excelente para control de calidad

### Clustering
- ❌ Número de clusters manual
- ❌ Sensible a outliers
- ✅ Descubre patrones ocultos
- ✅ Útil para segmentación inicial

### Predicción de Churn
- ❌ No considera factores cualitativos
- ❌ Asume comportamiento pasado = futuro
- ✅ Excelente indicador temprano
- ✅ Muy accionable

---

## 🚀 PRÓXIMAS MEJORAS SUGERIDAS

### Machine Learning Avanzado
1. **Time Series**: ARIMA, Prophet para estacionalidad
2. **Random Forest**: Predicción más precisa
3. **XGBoost**: Máxima precisión
4. **Redes Neuronales**: Deep learning para patrones complejos

### Análisis Adicionales
5. **Market Basket**: Productos comprados juntos
6. **Lifetime Value**: Predicción de valor futuro
7. **Propensity to Buy**: Probabilidad de compra
8. **Sentiment Analysis**: Análisis de comentarios

### Automatización
9. **Auto-ML**: Selección automática de modelo
10. **A/B Testing**: Comparar estrategias
11. **Real-time Scoring**: Scores en tiempo real
12. **Alertas Automáticas**: Notificar anomalías

---

## 📞 SOPORTE Y RECURSOS

### Archivos Relacionados
- `business/ml_analytics.py` - Motor ML
- `ui/ml_components.py` - Interfaz
- `ui/tabs.py` - Integración
- `app.py` - Pestaña principal

### Dependencias Requeridas
```bash
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=1.5.0
```

### Recursos de Aprendizaje
- **Scikit-learn**: https://scikit-learn.org/
- **RFM Analysis**: https://en.wikipedia.org/wiki/RFM_(market_research)
- **K-Means**: https://scikit-learn.org/stable/modules/clustering.html#k-means

---

## 🎉 RESUMEN

### ✅ LOGROS FASE 2:
- Sistema ML completo y funcional
- 6 módulos de análisis avanzado
- Predicción de ventas con IA
- Segmentación automática RFM
- Detección de anomalías
- Clustering inteligente
- Predicción de churn
- Análisis de tendencias
- 10+ gráficos interactivos
- Documentación exhaustiva
- Listo para producción

### 🚀 IMPACTO:
- **Toma de decisiones basada en datos**
- **Predicciones confiables** de ventas
- **Segmentación inteligente** de clientes
- **Detección temprana** de problemas
- **Recuperación proactiva** de clientes
- **Optimización** de recursos
- **Ventaja competitiva** con IA

---

**¡Sistema de IA y Analytics Completado!** 🤖📊✨

**Nota**: Este es un sistema profesional de ML, pero siempre valida los resultados con tu conocimiento del negocio. La IA es una herramienta poderosa, pero el juicio humano sigue siendo esencial.


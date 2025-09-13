import os
from datetime import date, timedelta, datetime
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Importar módulos (manteniendo tu estructura)
from queries_mejoradas import *
from utils_mejoradas import *

# ========================
# Configuración (igual que antes)
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Configuración de página mejorada
# ========================
st.set_page_config(
    page_title="CRM Inteligente", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧠"
)

# CSS personalizado para mejorar la apariencia
st.markdown("""
<style>
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .alert-high { border-left: 4px solid #ef4444; background: #fef2f2; }
    .alert-medium { border-left: 4px solid #f59e0b; background: #fffbeb; }
    .alert-low { border-left: 4px solid #10b981; background: #f0fdf4; }
    .recomendacion-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# Sidebar - Configuración Global
# ========================
with st.sidebar:
    st.title("🧠 CRM Inteligente")
    st.markdown("---")
    
    # Filtro de mes mejorado
    df_tmp = cargar_datos_completos(supabase)
    meses_disponibles = ["Todos"] + (sorted(df_tmp["mes_factura"].dropna().unique().tolist()) if not df_tmp.empty else [])
    
    mes_seleccionado = st.selectbox(
        "📅 Filtrar por mes",
        meses_disponibles,
        index=0
    )
    
    st.markdown("---")
    
    # Meta del mes actual
    mes_actual = datetime.now().strftime("%Y-%m")
    meta_actual = obtener_meta_mes(supabase, mes_actual)
    
    if meta_actual:
        st.markdown(f"🎯 **Meta {mes_actual}**")
        st.metric("Ventas", f"${meta_actual['meta_ventas']:,.0f}")
        st.metric("Clientes Nuevos", meta_actual['meta_clientes_nuevos'])
        
        progreso = (meta_actual['ventas_actuales'] / meta_actual['meta_ventas']) * 100
        st.progress(min(progreso/100, 1.0))
        st.caption(f"Progreso: {progreso:.1f}%")
    else:
        if st.button("⚙️ Configurar Meta Mensual"):
            st.session_state.show_meta_config = True

# ========================
# Funciones de cálculo mejoradas
# ========================

def calcular_comision_real(factura_data):
    """Calcula comisión según tu lógica exacta"""
    valor_neto = factura_data.get('valor_neto', 0)
    cliente_propio = factura_data.get('cliente_propio', False)
    descuento_pie_factura = factura_data.get('descuento_pie_factura', False)
    descuento_adicional = factura_data.get('descuento_adicional', 0)
    dias_pago = factura_data.get('dias_pago_real')
    condicion_especial = factura_data.get('condicion_especial', False)
    valor_devuelto = factura_data.get('valor_devuelto', 0)
    
    # 1. Calcular base inicial
    if descuento_pie_factura:
        base = valor_neto  # Ya tiene descuento aplicado
    else:
        # Verificar si mantiene el 15% de descuento según días
        limite_dias = 60 if condicion_especial else 45
        if not dias_pago or dias_pago <= limite_dias:
            base = valor_neto * 0.85  # Aplica descuento 15%
        else:
            base = valor_neto  # Pierde descuento por pago tardío
    
    # 2. Restar devoluciones
    base_final = base - valor_devuelto
    
    # 3. Determinar porcentaje según cliente y descuento
    tiene_descuento_adicional = descuento_adicional > 15
    
    if cliente_propio:
        porcentaje = 1.5 if tiene_descuento_adicional else 2.5
    else:
        porcentaje = 0.5 if tiene_descuento_adicional else 1.0
    
    # 4. Verificar pérdida por +80 días
    if dias_pago and dias_pago > 80:
        return {
            'comision': 0,
            'base_inicial': base,
            'base_final': 0,
            'porcentaje': 0,
            'perdida': True,
            'razon_perdida': 'mas_80_dias'
        }
    
    comision = base_final * (porcentaje / 100)
    
    return {
        'comision': comision,
        'base_inicial': base,
        'base_final': base_final,
        'porcentaje': porcentaje,
        'perdida': False
    }

def generar_recomendaciones_ia(supabase, meta_actual, dias_restantes):
    """Genera recomendaciones inteligentes para cumplir meta"""
    clientes = cargar_clientes(supabase)
    recomendaciones = []
    
    for cliente in clientes:
        # Calcular días desde última compra
        if cliente.get('ultima_compra'):
            dias_sin_compra = (datetime.now().date() - cliente['ultima_compra']).days
            frecuencia_normal = cliente.get('frecuencia_compra', 60)
            
            # Cliente en ventana de compra
            if dias_sin_compra >= frecuencia_normal * 0.8:
                probabilidad = min(90, (dias_sin_compra / frecuencia_normal) * 100)
                ticket_estimado = cliente.get('ticket_promedio', 500000)
                
                # Calcular comisión estimada
                comision_estimada = calcular_comision_real({
                    'valor_neto': ticket_estimado / 1.19,
                    'cliente_propio': cliente.get('es_propio', False),
                    'descuento_pie_factura': False,
                    'descuento_adicional': cliente.get('descuento_habitual', 0)
                })['comision']
                
                accion = "Llamar HOY" if dias_sin_compra > frecuencia_normal else "Contactar esta semana"
                prioridad = "alta" if probabilidad > 70 else "media"
                
                recomendaciones.append({
                    'cliente': cliente['nombre'],
                    'accion': accion,
                    'probabilidad': int(probabilidad),
                    'impacto_comision': comision_estimada,
                    'razon': f"Patrón de compra cada {frecuencia_normal} días - Último: hace {dias_sin_compra} días",
                    'prioridad': prioridad,
                    'tipo': 'patron_compra'
                })
    
    # Ordenar por impacto en comisiones
    recomendaciones.sort(key=lambda x: x['impacto_comision'], reverse=True)
    return recomendaciones[:5]  # Top 5 recomendaciones

# ========================
# Layout principal con tabs mejoradas
# ========================
tabs = st.tabs([
    "🎯 Dashboard",
    "💰 Comisiones", 
    "👥 Clientes",
    "📦 Productos",
    "🧠 IA Analytics",
    "🚨 Alertas",
    "⚙️ Configuración"
])

# ========================
# TAB 1 - DASHBOARD INTELIGENTE
# ========================
with tabs[0]:
    st.header("🎯 Dashboard Inteligente")
    
    # Cargar datos
    df = cargar_datos_completos(supabase)
    if mes_seleccionado != "Todos":
        df = df[df["mes_factura"] == mes_seleccionado]
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    total_facturado = df["valor_neto"].sum()
    total_comisiones = df["comision"].sum()
    comisiones_perdidas = df[df["comision_perdida"] == True]["comision"].sum()
    facturas_riesgo = len(df[(df["pagado"] == False) & (df["dias_vencimiento"] <= 5)])
    
    with col1:
        st.metric(
            "💵 Total Facturado",
            f"${total_facturado:,.0f}",
            delta=f"{((total_facturado/8500000-1)*100):+.1f}%" if total_facturado > 0 else None
        )
    
    with col2:
        st.metric(
            "💰 Comisiones Mes",
            f"${total_comisiones:,.0f}",
            delta=f"{((total_comisiones/170000-1)*100):+.1f}%" if total_comisiones > 0 else None
        )
    
    with col3:
        st.metric(
            "⚠️ Comisiones Perdidas", 
            f"${comisiones_perdidas:,.0f}",
            delta=None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "🚨 Facturas en Riesgo",
            facturas_riesgo,
            delta=None,
            delta_color="inverse"
        )
    
    # Meta del mes y recomendaciones IA
    if meta_actual:
        st.markdown("---")
        
        # Progreso de meta visual
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎯 Progreso Meta Mensual")
            
            progreso = meta_actual['ventas_actuales'] / meta_actual['meta_ventas']
            faltante = meta_actual['meta_ventas'] - meta_actual['ventas_actuales']
            dias_restantes = 30 - datetime.now().day
            
            # Gráfico de progreso
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = progreso * 100,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "% Cumplimiento Meta"},
                delta = {'reference': 100, 'position': "top"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "green" if progreso > 0.8 else "orange" if progreso > 0.5 else "red"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"},
                        {'range': [80, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': 100
                    }
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            # Información adicional
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("💰 Faltante", f"${faltante:,.0f}")
            with col_b:
                st.metric("📅 Días Restantes", dias_restantes)
            with col_c:
                velocidad = faltante / max(dias_restantes, 1)
                st.metric("🚀 Necesitas/día", f"${velocidad:,.0f}")
        
        with col2:
            st.markdown("### 🧠 Recomendaciones IA")
            
            recomendaciones = generar_recomendaciones_ia(supabase, meta_actual, dias_restantes)
            
            for rec in recomendaciones[:3]:
                with st.container():
                    st.markdown(f"""
                    <div class="recomendacion-card">
                        <h4>{rec['cliente']}</h4>
                        <p><strong>{rec['accion']}</strong> ({rec['probabilidad']}% prob.)</p>
                        <p>💰 +${rec['impacto_comision']:,.0f} comisión</p>
                        <small>{rec['razon']}</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    # Gráficos de tendencias
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Evolución Comisiones")
        if not df.empty:
            df_mes = df.groupby('mes_factura').agg({
                'comision': 'sum',
                'valor_neto': 'sum'
            }).reset_index()
            
            fig = px.line(df_mes, x='mes_factura', y='comision',
                         title="Comisiones por Mes",
                         labels={'comision': 'Comisiones ($)', 'mes_factura': 'Mes'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 👥 Distribución Clientes")
        clientes_data = cargar_clientes(supabase)
        if clientes_data:
            df_clientes = pd.DataFrame(clientes_data)
            
            # Crear distribución
            dist = df_clientes.groupby(['categoria', 'es_propio']).size().reset_index(name='count')
            dist['tipo'] = dist.apply(lambda x: f"{'Propios' if x['es_propio'] else 'Externos'} (Cat {x['categoria']})", axis=1)
            
            fig = px.pie(dist, values='count', names='tipo',
                        title="Distribución de Clientes")
            st.plotly_chart(fig, use_container_width=True)

# ========================
# TAB 2 - COMISIONES MEJORADAS
# ========================
with tabs[1]:
    st.header("💰 Gestión de Comisiones")
    
    # Botón para nueva venta
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Nueva Venta", type="primary", use_container_width=True):
            st.session_state.show_nueva_venta = True
    
    # Filtros avanzados
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        estado_filter = st.selectbox("Estado", ["Todos", "Pendiente", "Pagado", "Vencido", "Perdido"])
    with col2:
        cliente_filter = st.selectbox("Tipo Cliente", ["Todos", "Propios", "Externos"])
    with col3:
        riesgo_filter = st.selectbox("Riesgo", ["Todos", "Sin Riesgo", "En Riesgo", "Crítico"])
    with col4:
        st.write("")  # Espaciador
        export_btn = st.button("📥 Exportar Excel")
    
    # Aplicar filtros
    df_filtrado = df.copy()
    if estado_filter != "Todos":
        estado_map = {"Pendiente": False, "Pagado": True, "Vencido": "vencido", "Perdido": "perdido"}
        if estado_filter in ["Pendiente", "Pagado"]:
            df_filtrado = df_filtrado[df_filtrado["pagado"] == estado_map[estado_filter]]
    
    # Mostrar resumen
    st.markdown("### 📊 Resumen Comisiones")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_periodo = df_filtrado["comision"].sum()
        st.metric("Total Período", f"${total_periodo:,.0f}")
    
    with col2:
        pendientes = df_filtrado[df_filtrado["pagado"] == False]["comision"].sum()
        st.metric("Pendientes", f"${pendientes:,.0f}")
    
    with col3:
        pagadas = df_filtrado[df_filtrado["pagado"] == True]["comision"].sum()
        st.metric("Pagadas", f"${pagadas:,.0f}")
    
    with col4:
        perdidas = df_filtrado[df_filtrado["comision_perdida"] == True]["comision"].sum()
        st.metric("Perdidas", f"${perdidas:,.0f}", delta_color="inverse")
    
    # Tabla de facturas con acciones
    st.markdown("### 📋 Facturas Detalladas")
    
    if not df_filtrado.empty:
        for idx, factura in df_filtrado.iterrows():
            with st.expander(f"🧾 {factura.get('pedido', 'N/A')} - {factura.get('cliente', 'N/A')} - ${factura.get('valor_neto', 0):,.0f}"):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Cliente:** {factura.get('cliente', 'N/A')}")
                    st.write(f"**Factura:** {factura.get('factura', 'N/A')}")
                    st.write(f"**Valor Neto:** ${factura.get('valor_neto', 0):,.0f}")
                    st.write(f"**Fecha Factura:** {factura.get('fecha_factura', 'N/A')}")
                    
                    # Indicadores especiales
                    if factura.get('cliente_propio'):
                        st.success("✅ Cliente Propio")
                    if factura.get('descuento_adicional', 0) > 15:
                        st.warning(f"⚠️ Descuento Adicional: {factura.get('descuento_adicional')}%")
                
                with col2:
                    st.write(f"**Base Comisión:** ${factura.get('base_comision', 0):,.0f}")
                    st.write(f"**Porcentaje:** {factura.get('porcentaje', 0)}%")
                    st.write(f"**Comisión:** ${factura.get('comision', 0):,.0f}")
                    
                    if factura.get('valor_devuelto', 0) > 0:
                        st.error(f"🔄 Devolución: ${factura.get('valor_devuelto'):,.0f}")
                    
                    if factura.get('comision_perdida'):
                        st.error("❌ Comisión Perdida")
                
                with col3:
                    st.write("**Acciones:**")
                    
                    if st.button(f"✏️ Editar", key=f"edit_{factura.get('id')}"):
                        st.session_state.edit_factura = factura
                        st.session_state.show_edit_modal = True
                    
                    if factura.get('pagado') and not factura.get('comision_perdida'):
                        if st.button(f"🔄 Devolución", key=f"dev_{factura.get('id')}"):
                            st.session_state.devolucion_factura = factura
                            st.session_state.show_devolucion_modal = True
                    
                    if not factura.get('pagado') and not factura.get('comision_perdida'):
                        if st.button(f"✅ Marcar Pagado", key=f"pay_{factura.get('id')}"):
                            # Aquí iría la lógica para marcar como pagado
                            st.success("Función por implementar")
    else:
        st.info("No hay facturas que coincidan con los filtros seleccionados.")

# Modales (estos irían en la parte inferior del archivo)
# Modal Nueva Venta
if st.session_state.get('show_nueva_venta', False):
    with st.form("nueva_venta_form"):
        st.markdown("### ➕ Registrar Nueva Venta")
        
        col1, col2 = st.columns(2)
        with col1:
            pedido = st.text_input("Número de Pedido")
            cliente = st.text_input("Cliente")
            factura = st.text_input("Número de Factura")
        
        with col2:
            valor_total = st.number_input("Valor Total (con IVA)", min_value=0.0, step=1000.0)
            fecha_factura = st.date_input("Fecha de Factura", value=date.today())
        
        col1, col2 = st.columns(2)
        with col1:
            cliente_propio = st.checkbox("Cliente Propio", help="2.5% vs 1% de comisión")
            descuento_pie_factura = st.checkbox("Descuento a Pie de Factura")
        
        with col2:
            descuento_adicional = st.number_input("Descuento Adicional (%)", min_value=0.0, max_value=100.0, step=0.5)
            condicion_especial = st.checkbox("Condición Especial (60 días)")
        
        # Preview de cálculos
        if valor_total > 0:
            valor_neto = valor_total / 1.19
            iva = valor_total - valor_neto
            
            st.markdown("---")
            st.markdown("### 🧮 Preview Comisión")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Valor Neto", f"${valor_neto:,.0f}")
            with col2:
                st.metric("IVA", f"${iva:,.0f}")
            
            # Calcular comisión preview
            comision_data = calcular_comision_real({
                'valor_neto': valor_neto,
                'cliente_propio': cliente_propio,
                'descuento_pie_factura': descuento_pie_factura,
                'descuento_adicional': descuento_adicional
            })
            
            with col3:
                st.metric("Comisión Estimada", f"${comision_data['comision']:,.0f}")
            
            st.info(f"Base: ${comision_data['base_final']:,.0f} × {comision_data['porcentaje']}% = ${comision_data['comision']:,.0f}")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Registrar Venta", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if submit:
            if pedido and cliente and valor_total > 0:
                # Calcular días de pago estimados
                dias_pago = 60 if condicion_especial else 35
                dias_max = 60 if condicion_especial else 45
                fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
                fecha_pago_max = fecha_factura + timedelta(days=dias_max)
                
                # Calcular valores
                valor_neto = valor_total / 1.19
                iva = valor_total - valor_neto
                comision_data = calcular_comision_real({
                    'valor_neto': valor_neto,
                    'cliente_propio': cliente_propio,
                    'descuento_pie_factura': descuento_pie_factura,
                    'descuento_adicional': descuento_adicional
                })
                
                # Preparar datos para inserción
                data = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "factura": factura,
                    "valor": valor_total,  # Mantener compatibilidad
                    "valor_neto": valor_neto,
                    "iva": iva,
                    "cliente_propio": cliente_propio,
                    "descuento_pie_factura": descuento_pie_factura,
                    "descuento_adicional": descuento_adicional,
                    "condicion_especial": condicion_especial,
                    "fecha_factura": fecha_factura.isoformat(),
                    "fecha_pago_est": fecha_pago_est.isoformat(),
                    "fecha_pago_max": fecha_pago_max.isoformat(),
                    "base_comision": comision_data['base_final'],
                    "comision": comision_data['comision'],
                    "porcentaje": comision_data['porcentaje'],
                    "pagado": False,
                    "comision_perdida": False
                }
                
                if insertar_venta_completa(supabase, data):
                    st.success("✅ Venta registrada correctamente")
                    st.session_state.show_nueva_venta = False
                    st.rerun()
                else:
                    st.error("❌ Error al registrar la venta")
            else:
                st.error("Por favor completa todos los campos obligatorios")
        
        if cancel:
            st.session_state.show_nueva_venta = False
            st.rerun()

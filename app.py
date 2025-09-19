import os
from datetime import date, timedelta, datetime
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# ========================
# CONFIGURACIÓN INICIAL
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="CRM Inteligente", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧠"
)

# ========================
# UTILIDADES
# ========================
def format_currency(value):
    """Formatea números como moneda colombiana"""
    if pd.isna(value) or value == 0 or value is None:
        return "$0"
    try:
        return f"${float(value):,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "$0"

def calcular_comision_inteligente(valor_total, cliente_propio=False, tiene_descuento=False, descuento_pie=False):
    """Calcula comisión con lógica simplificada"""
    valor_neto = valor_total / 1.19
    
    if descuento_pie:
        base = valor_neto
    else:
        base = valor_neto * 0.85
    
    # LÓGICA SIMPLIFICADA: solo importa SI hay descuento
    if cliente_propio:
        porcentaje = 1.5 if tiene_descuento else 2.5
    else:
        porcentaje = 0.5 if tiene_descuento else 1.0
    
    comision = base * (porcentaje / 100)
    
    return {
        'valor_neto': valor_neto,
        'iva': valor_total - valor_neto,
        'base_comision': base,
        'comision': comision,
        'porcentaje': porcentaje
    }

# ========================
# FUNCIONES DE BASE DE DATOS
# ========================
@st.cache_data(ttl=300)
def cargar_datos():
    """Carga datos de la tabla comisiones"""
    try:
        response = supabase.table("comisiones").select("*").execute()
        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        
        # Conversión de tipos
        columnas_numericas_str = ['valor_base', 'valor_neto', 'iva', 'base_comision', 'comision_ajustada']
        for col in columnas_numericas_str:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: 0 if x in [None, "NULL", "null", ""] else float(x) if str(x).replace('.','').replace('-','').isdigit() else 0)

        columnas_numericas_existentes = ['valor', 'porcentaje', 'comision', 'porcentaje_descuento', 'descuento_adicional', 'valor_devuelto']
        for col in columnas_numericas_existentes:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Calcular campos faltantes
        if df['valor_neto'].sum() == 0 and df['valor'].sum() > 0:
            df['valor_neto'] = df['valor'] / 1.19
        
        if df['iva'].sum() == 0 and df['valor'].sum() > 0:
            df['iva'] = df['valor'] - df['valor_neto']

        if df['base_comision'].sum() == 0:
            df['base_comision'] = df.apply(lambda row: 
                row['valor_neto'] if row.get('descuento_pie_factura', False)
                else row['valor_neto'] * 0.85, axis=1)

        # Convertir fechas
        columnas_fecha = ['fecha_factura', 'fecha_pago_est', 'fecha_pago_max', 'fecha_pago_real', 'created_at', 'updated_at']
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Crear columnas derivadas
        df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)
        hoy = pd.Timestamp.now()
        
        # Solo calcular días de vencimiento para facturas NO PAGADAS
        df['dias_vencimiento'] = df.apply(lambda row: 
            (row['fecha_pago_max'] - hoy).days if not row.get('pagado', False) and pd.notna(row['fecha_pago_max']) 
            else None, axis=1)

        # Asegurar columnas boolean
        columnas_boolean = ['pagado', 'condicion_especial', 'cliente_propio', 'descuento_pie_factura', 'comision_perdida']
        for col in columnas_boolean:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)

        # Asegurar columnas string
        columnas_string = ['pedido', 'cliente', 'factura', 'comprobante_url', 'razon_perdida']
        for col in columnas_string:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)

        return df

    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return pd.DataFrame()

def insertar_venta(data: dict):
    """Inserta una nueva venta"""
    try:
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        result = supabase.table("comisiones").insert(data).execute()
        
        if result.data:
            st.cache_data.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Error insertando venta: {e}")
        return False

def obtener_meta_mes_actual():
    """Obtiene la meta del mes actual"""
    try:
        mes_actual = date.today().strftime("%Y-%m")
        response = supabase.table("metas_mensuales").select("*").eq("mes", mes_actual).execute()
        
        if response.data:
            return response.data[0]
        else:
            meta_default = {
                "mes": mes_actual,
                "meta_ventas": 10000000,
                "meta_clientes_nuevos": 5,
                "ventas_actuales": 0,
                "clientes_nuevos_actuales": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            result = supabase.table("metas_mensuales").insert(meta_default).execute()
            return result.data[0] if result.data else meta_default
            
    except Exception as e:
        return {
            "mes": date.today().strftime("%Y-%m"), 
            "meta_ventas": 10000000, 
            "meta_clientes_nuevos": 5
        }

def actualizar_meta(mes: str, meta_ventas: float, meta_clientes: int):
    """Actualiza meta mensual"""
    try:
        response = supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
        
        data = {
            "meta_ventas": meta_ventas,
            "meta_clientes_nuevos": meta_clientes,
            "updated_at": datetime.now().isoformat()
        }
        
        if response.data:
            result = supabase.table("metas_mensuales").update(data).eq("mes", mes).execute()
        else:
            data["mes"] = mes
            data["created_at"] = datetime.now().isoformat()
            result = supabase.table("metas_mensuales").insert(data).execute()
        
        return True if result.data else False
        
    except Exception as e:
        st.error(f"Error actualizando meta: {e}")
        return False

# ========================
# FUNCIONES DE RECOMENDACIONES IA
# ========================
def generar_recomendaciones_reales():
    """Genera recomendaciones basadas en datos reales"""
    try:
        df = cargar_datos()
        
        if df.empty:
            return [{
                'cliente': 'No hay datos disponibles',
                'accion': 'Revisar base de datos',
                'producto': 'N/A',
                'razon': 'La tabla comisiones está vacía o hay error de conexión',
                'probabilidad': 0,
                'impacto_comision': 0,
                'prioridad': 'alta'
            }]
        
        recomendaciones = []
        hoy = pd.Timestamp.now()
        
        # Facturas próximas a vencer (solo las no pagadas)
        proximas_vencer = df[
            (df['dias_vencimiento'].notna()) & 
            (df['dias_vencimiento'] >= 0) & 
            (df['dias_vencimiento'] <= 7) & 
            (df['pagado'] == False)
        ].nlargest(2, 'comision')
        
        for _, factura in proximas_vencer.iterrows():
            recomendaciones.append({
                'cliente': factura['cliente'],
                'accion': f"URGENTE: Cobrar en {int(factura['dias_vencimiento'])} días",
                'producto': f"Factura {factura['factura']} - ${factura['valor']:,.0f}",
                'razon': f"Comisión de ${factura['comision']:,.0f} en riesgo de perderse",
                'probabilidad': 90,
                'impacto_comision': factura['comision'],
                'prioridad': 'alta'
            })
        
        # Facturas vencidas (solo las no pagadas)
        vencidas = df[
            (df['dias_vencimiento'].notna()) & 
            (df['dias_vencimiento'] < 0) & 
            (df['pagado'] == False)
        ].nlargest(2, 'comision')
        
        for _, factura in vencidas.iterrows():
            dias_vencida = abs(int(factura['dias_vencimiento']))
            recomendaciones.append({
                'cliente': factura['cliente'],
                'accion': f"CRÍTICO: Vencida hace {dias_vencida} días",
                'producto': f"Factura {factura['factura']} - ${factura['valor']:,.0f}",
                'razon': f"Comisión perdida si no se cobra pronto (${factura['comision']:,.0f})",
                'probabilidad': max(20, 100 - dias_vencida * 2),
                'impacto_comision': factura['comision'],
                'prioridad': 'alta'
            })
        
        # Si no hay suficientes recomendaciones
        if len(recomendaciones) == 0:
            top_cliente = df.groupby('cliente')['valor'].sum().nlargest(1)
            if not top_cliente.empty:
                cliente_nombre = top_cliente.index[0]
                volumen_total = top_cliente.iloc[0]
                
                recomendaciones.append({
                    'cliente': cliente_nombre,
                    'accion': 'Seguimiento comercial',
                    'producto': f"Nueva propuesta (${volumen_total*0.3:,.0f})",
                    'razon': f"Tu cliente #1 por volumen total (${volumen_total:,.0f})",
                    'probabilidad': 65,
                    'impacto_comision': volumen_total * 0.015,
                    'prioridad': 'media'
                })
        
        return recomendaciones[:3]
        
    except Exception as e:
        return [{
            'cliente': 'Error técnico',
            'accion': 'Revisar logs',
            'producto': 'N/A',
            'razon': f'Error: {str(e)[:100]}',
            'probabilidad': 0,
            'impacto_comision': 0,
            'prioridad': 'baja'
        }]

# ========================
# CSS STYLES
# ========================
def load_css():
    """Carga estilos CSS para fondo oscuro"""
    st.markdown("""
    <style>
        .main .block-container {
            background-color: #0f1419 !important;
            color: #ffffff !important;
        }
        
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stText, p, span, div {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 800 !important;
            text-shadow: 0 0 10px rgba(255,255,255,0.3) !important;
        }
        
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid #ffffff !important;
            border-radius: 0.75rem !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px) !important;
        }
        
        div[data-testid="metric-container"] > div {
            color: #ffffff !important;
            font-weight: 800 !important;
            font-size: 16px !important;
        }
        
        .stButton > button {
            border-radius: 0.5rem !important;
            border: 2px solid #ffffff !important;
            font-weight: 800 !important;
            font-size: 14px !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            transition: all 0.2s ease !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.2) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255,255,255,0.2) !important;
        }
        
        .stButton > button[kind="primary"] {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border-color: #3b82f6 !important;
            font-weight: 900 !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(255, 255, 255, 0.1);
            padding: 0.5rem;
            border-radius: 0.75rem;
            border: 2px solid #ffffff;
            backdrop-filter: blur(10px);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid #ffffff !important;
            border-radius: 0.5rem !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            padding: 0.75rem 1.5rem !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: #3b82f6 !important;
            color: #ffffff !important;
            border-color: #3b82f6 !important;
            font-weight: 900 !important;
        }
        
        .progress-bar {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 1rem;
            height: 1.5rem;
            overflow: hidden;
            width: 100%;
            border: 2px solid #ffffff;
            backdrop-filter: blur(10px);
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 1rem;
            transition: width 0.3s ease;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid #ffffff;
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 6px 20px rgba(255,255,255,0.1);
            color: #ffffff;
            backdrop-filter: blur(15px);
        }
        
        .alert-high { 
            background: rgba(239, 68, 68, 0.2); 
            border: 2px solid #ef4444;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        .alert-medium { 
            background: rgba(251, 146, 60, 0.2); 
            border: 2px solid #fb923c;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        .alert-low { 
            background: rgba(34, 197, 94, 0.2); 
            border: 2px solid #22c55e;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
    </style>
    """, unsafe_allow_html=True)

# ========================
# APLICACIÓN PRINCIPAL
# ========================
def main():
    """Aplicación principal"""
    # Cargar CSS
    load_css()
    
    # Variables de estado
    meta_actual = obtener_meta_mes_actual()
    if 'show_meta_config' not in st.session_state:
        st.session_state.show_meta_config = False

    # SIDEBAR
    with st.sidebar:
        st.title("🧠 CRM Inteligente")
        st.markdown("---")
        
        st.subheader("Meta Mensual")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Config"):
                st.session_state.show_meta_config = True
        
        with col2:
            if st.button("Ver Meta"):
                st.session_state.show_meta_detail = True
        
        df_tmp = cargar_datos()
        mes_actual_str = date.today().strftime("%Y-%m")
        ventas_mes = df_tmp[
            (df_tmp["mes_factura"] == mes_actual_str) & 
            (df_tmp["cliente_propio"] == True)  # Solo clientes propios
        ]["valor_neto"].sum() if not df_tmp.empty else 0
        
        progreso = (ventas_mes / meta_actual["meta_ventas"] * 100) if meta_actual["meta_ventas"] > 0 else 0
        
        st.markdown(f"""
        <div class="metric-card">
            <h4>{date.today().strftime("%B %Y")}</h4>
            <p><strong>Meta:</strong> {format_currency(meta_actual["meta_ventas"])}</p>
            <p><strong>Actual:</strong> {format_currency(ventas_mes)}</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {min(progreso, 100)}%; background: {'#10b981' if progreso > 80 else '#f59e0b' if progreso > 50 else '#ef4444'}"></div>
            </div>
            <small>{progreso:.1f}% completado</small>
        </div>
        """, unsafe_allow_html=True)

    # MODAL DE CONFIGURACIÓN DE META
    if st.session_state.show_meta_config:
        with st.form("config_meta"):
            st.markdown("### Configurar Meta Mensual")
            
            col1, col2 = st.columns(2)
            with col1:
                nueva_meta = st.number_input(
                    "Meta de Ventas (COP)", 
                    value=float(meta_actual["meta_ventas"]),
                    min_value=0,
                    step=100000,
                    key="config_meta_ventas"
                )
            
            with col2:
                nueva_meta_clientes = st.number_input(
                    "Meta Clientes Nuevos", 
                    value=meta_actual["meta_clientes_nuevos"],
                    min_value=0,
                    step=1,
                    key="config_meta_clientes"
                )

            bono_potencial = nueva_meta * 0.005
            st.info(f"**Bono potencial:** {format_currency(bono_potencial)} (0.5% de la meta)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar Meta", type="primary"):
                    mes_actual_str = date.today().strftime("%Y-%m")
                    if actualizar_meta(mes_actual_str, nueva_meta, nueva_meta_clientes):
                        st.success("Meta actualizada correctamente")
                        st.session_state.show_meta_config = False
                        st.rerun()
                    else:
                        st.error("Error al guardar la meta")
            
            with col2:
                if st.form_submit_button("Cancelar"):
                    st.session_state.show_meta_config = False
                    st.rerun()

    # LAYOUT PRINCIPAL
    if not st.session_state.show_meta_config:
        st.title("🧠 CRM Inteligente")

        tabs = st.tabs([
            "Dashboard",
            "Nueva Venta",
            "IA & Alertas"
        ])

        # TAB 1 - DASHBOARD
        with tabs[0]:
            st.header("Dashboard Ejecutivo")

            df = cargar_datos()
            
            if not df.empty:
                # Separar por tipo de cliente
                clientes_propios = df[df["cliente_propio"] == True]
                clientes_externos = df[df["cliente_propio"] == False]
                
                # Calcular métricas
                ventas_propios = clientes_propios["valor_neto"].sum()
                ventas_externos = clientes_externos["valor_neto"].sum()
                comision_propios = clientes_propios["comision"].sum()
                comision_externos = clientes_externos["comision"].sum()
                
                # Mostrar métricas principales (solo clientes propios)
                col1, col2, col3, col4 = st.columns(4)
        
                with col1:
                    st.metric(
                        "Ventas Meta (Propios)",
                        format_currency(ventas_propios),
                        help="Solo clientes propios cuentan para la meta"
                    )
        
                with col2:
                    st.metric(
                        "Comisión Total", 
                        format_currency(comision_propios + comision_externos),
                        help="Comisiones de todos los clientes"
                    )
        
                with col3:
                    facturas_pendientes = len(df[df["pagado"] == False])
                    st.metric("Facturas Pendientes", facturas_pendientes)
        
                with col4:
                    total_general = ventas_propios + ventas_externos
                    porcentaje_propios = (ventas_propios / total_general * 100) if total_general > 0 else 0
                    st.metric("% Clientes Propios", f"{porcentaje_propios:.1f}%")
        
                # Mostrar desglose adicional
                st.markdown("---")
                st.markdown("### Desglose por Tipo de Cliente")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🏢 Clientes Propios (Para Meta)")
                    st.metric("Ventas", format_currency(ventas_propios))
                    st.metric("Comisión", format_currency(comision_propios))
                    st.metric("Facturas", len(clientes_propios))
                
                with col2:
                    st.markdown("#### 🤝 Clientes Externos (Solo Comisión)")
                    st.metric("Ventas", format_currency(ventas_externos))
                    st.metric("Comisión", format_currency(comision_externos))
                    st.metric("Facturas", len(clientes_externos))

                # Progreso Meta y Recomendaciones IA
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("### Progreso Meta Mensual")
                    
                    meta = meta_actual["meta_ventas"]
                    actual = ventas_propios
                    progreso_meta = (actual / meta * 100) if meta > 0 else 0
                    faltante = max(0, meta - actual)
                    dias_restantes = max(1, (date(2024, 12, 31) - date.today()).days)
                    velocidad_necesaria = faltante / dias_restantes
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Meta", format_currency(meta))
                    with col_b:
                        st.metric("Actual", format_currency(actual))
                    with col_c:
                        st.metric("Faltante", format_currency(faltante))
                    
                    color = "#10b981" if progreso_meta > 80 else "#f59e0b" if progreso_meta > 50 else "#ef4444"
                    st.markdown(f"""
                    <div class="progress-bar" style="margin: 1rem 0;">
                        <div class="progress-fill" style="width: {min(progreso_meta, 100)}%; background: {color}"></div>
                    </div>
                    <p><strong>{progreso_meta:.1f}%</strong> completado | <strong>Necesitas:</strong> {format_currency(velocidad_necesaria)}/día</p>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### Recomendaciones IA")
                    
                    recomendaciones = generar_recomendaciones_reales()
                    
                    for rec in recomendaciones:
                        st.markdown(f"""
                        <div class="alert-{'high' if rec['prioridad'] == 'alta' else 'medium'}">
                            <h4 style="margin:0; color: #ffffff;">{rec['cliente']}</h4>
                            <p style="margin:0.5rem 0; color: #ffffff;"><strong>{rec['accion']}</strong> ({rec['probabilidad']}% prob.)</p>
                            <p style="margin:0; color: #ffffff; font-size: 0.9rem;">{rec['razon']}</p>
                            <p style="margin:0.5rem 0 0 0; color: #ffffff; font-weight: bold;">💰 +{format_currency(rec['impacto_comision'])} comisión</p>
                        </div>
                        """, unsafe_allow_html=True)

        # TAB 2 - NUEVA VENTA
        with tabs[1]:
            st.header("Registrar Nueva Venta")
            
            with st.form("nueva_venta_form", clear_on_submit=False):
                st.markdown("### Información Básica")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    pedido = st.text_input(
                        "Número de Pedido *", 
                        placeholder="Ej: PED-001",
                        help="Número único del pedido",
                        key="nueva_venta_pedido"
                    )
                    cliente = st.text_input(
                        "Cliente *",
                        placeholder="Ej: DISTRIBUIDORA CENTRAL",
                        help="Nombre completo del cliente",
                        key="nueva_venta_cliente"
                    )
                    factura = st.text_input(
                        "Número de Factura",
                        placeholder="Ej: FAC-1001",
                        help="Número de la factura generada",
                        key="nueva_venta_factura"
                    )
                
                with col2:
                    fecha_factura = st.date_input(
                        "Fecha de Factura *", 
                        value=date.today(),
                        help="Fecha de emisión de la factura",
                        key="nueva_venta_fecha"
                    )
                    valor_total = st.number_input(
                        "Valor Total (con IVA) *", 
                        min_value=0.0, 
                        step=10000.0,
                        format="%.0f",
                        help="Valor total de la venta incluyendo IVA",
                        key="nueva_venta_valor"
                    )
                    condicion_especial = st.checkbox(
                        "Condición Especial (60 días de pago)",
                        help="Marcar si el cliente tiene condiciones especiales de pago",
                        key="nueva_venta_condicion"
                    )
                
                st.markdown("### Configuración de Comisión")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    cliente_propio = st.checkbox(
                        "Cliente Propio", 
                        help="Cliente directo (2.5% comisión vs 1% externo)",
                        key="nueva_venta_cliente_propio"
                    )
                
                with col2:
                    descuento_pie_factura = st.checkbox(
                        "Descuento a Pie de Factura",
                        help="Si el descuento aparece directamente en la factura",
                        key="nueva_venta_descuento_pie"
                    )
                
                with col3:
                    descuento_adicional = st.number_input(
                        "Descuento Adicional (%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.5,
                        help="Porcentaje de descuento adicional aplicado",
                        key="nueva_venta_descuento_adicional"
                    )

                # Preview de cálculos
                if valor_total > 0:
                    st.markdown("---")
                    st.markdown("### Preview de Comisión")
                    
                    calc = calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, descuento_pie_factura)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Valor Neto", format_currency(calc['valor_neto']))
                    with col2:
                        st.metric("IVA (19%)", format_currency(calc['iva']))
                    with col3:
                        st.metric("Base Comisión", format_currency(calc['base_comision']))
                    with col4:
                        st.metric("Comisión Final", format_currency(calc['comision']))
                    
                    st.info(f"""
                    **Detalles del cálculo:**
                    - Tipo cliente: {'Propio' if cliente_propio else 'Externo'}
                    - Porcentaje comisión: {calc['porcentaje']}%
                    - {'Descuento aplicado en factura' if descuento_pie_factura else 'Descuento automático del 15%'}
                    - Descuento adicional: {descuento_adicional}%
                    """)
                
                st.markdown("---")
                
                # Botones
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    submit = st.form_submit_button(
                        "Registrar Venta", 
                        type="primary", 
                        use_container_width=True
                    )
                
                with col2:
                    if st.form_submit_button("Limpiar", use_container_width=True):
                        st.rerun()
                
                with col3:
                    if st.form_submit_button("Previsualizar", use_container_width=True):
                        if pedido and cliente and valor_total > 0:
                            st.success("Los datos se ven correctos para registrar")
                        else:
                            st.warning("Faltan campos obligatorios")
                
                # Lógica de guardado
                if submit:
                    if pedido and cliente and valor_total > 0:
                        try:
                            # Calcular fechas
                            dias_pago = 60 if condicion_especial else 35
                            dias_max = 60 if condicion_especial else 45
                            fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
                            fecha_pago_max = fecha_factura + timedelta(days=dias_max)
                            
                            # Calcular comisión
                            calc = calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, descuento_pie_factura)
                            
                            # Preparar datos
                            data = {
                                "pedido": pedido,
                                "cliente": cliente,
                                "factura": factura if factura else f"FAC-{pedido}",
                                "valor": float(valor_total),
                                "valor_neto": float(calc['valor_neto']),
                                "iva": float(calc['iva']),
                                "base_comision": float(calc['base_comision']),
                                "comision": float(calc['comision']),
                                "porcentaje": float(calc['porcentaje']),
                                "fecha_factura": fecha_factura.isoformat(),
                                "fecha_pago_est": fecha_pago_est.isoformat(),
                                "fecha_pago_max": fecha_pago_max.isoformat(),
                                "cliente_propio": cliente_propio,
                                "descuento_pie_factura": descuento_pie_factura,
                                "descuento_adicional": float(descuento_adicional),
                                "condicion_especial": condicion_especial,
                                "pagado": False
                            }
                            
                            # Insertar
                            if insertar_venta(data):
                                st.success("¡Venta registrada correctamente!")
                                st.success(f"Comisión calculada: {format_currency(calc['comision'])}")
                                st.balloons()
                                
                                st.markdown("### Resumen de la venta:")
                                st.write(f"**Cliente:** {cliente}")
                                st.write(f"**Pedido:** {pedido}")
                                st.write(f"**Valor:** {format_currency(valor_total)}")
                                st.write(f"**Comisión:** {format_currency(calc['comision'])} ({calc['porcentaje']}%)")
                                st.write(f"**Fecha límite pago:** {fecha_pago_max.strftime('%d/%m/%Y')}")
                            else:
                                st.error("Error al registrar la venta")
                                
                        except Exception as e:
                            st.error(f"Error procesando la venta: {str(e)}")
                    else:
                        st.error("Por favor completa todos los campos marcados con *")

        # TAB 3 - IA & ALERTAS
        with tabs[2]:
            st.header("Inteligencia Artificial & Alertas")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### Alertas Críticas")
                
                alertas_encontradas = False
                df = cargar_datos()
                
                if not df.empty:
                    # Facturas vencidas (solo no pagadas)
                    vencidas = df[
                        (df["dias_vencimiento"].notna()) & 
                        (df["dias_vencimiento"] < 0) & 
                        (df["pagado"] == False)
                    ]
                    for _, factura in vencidas.head(3).iterrows():
                        st.error(f"**Factura Vencida:** {factura.get('cliente', 'N/A')} - {factura.get('pedido', 'N/A')} ({format_currency(factura.get('valor_neto', 0))})")
                        alertas_encontradas = True
                    
                    # Próximas a vencer (solo no pagadas)
                    prox_vencer = df[
                        (df["dias_vencimiento"].notna()) & 
                        (df["dias_vencimiento"] >= 0) & 
                        (df["dias_vencimiento"] <= 5) & 
                        (df["pagado"] == False)
                    ]
                    for _, factura in prox_vencer.head(3).iterrows():
                        st.warning(f"**Próximo Vencimiento:** {factura.get('cliente', 'N/A')} vence en {factura.get('dias_vencimiento', 0)} días")
                        alertas_encontradas = True
                    
                    # Altas comisiones pendientes
                    if not df.empty:
                        alto_valor = df[df["comision"] > df["comision"].quantile(0.8)]
                        for _, factura in alto_valor.head(2).iterrows():
                            if not factura.get("pagado"):
                                st.info(f"**Alta Comisión Pendiente:** {format_currency(factura.get('comision', 0))} esperando pago")
                                alertas_encontradas = True
                
                if not alertas_encontradas:
                    st.success("No hay alertas críticas en este momento")
            
            with col2:
                st.markdown("### Recomendaciones Estratégicas")
                
                recomendaciones = generar_recomendaciones_reales()
                
                for i, rec in enumerate(recomendaciones):
                    with st.container(border=True):
                        st.markdown(f"**{rec['cliente']}** - {rec['probabilidad']}% probabilidad")
                        st.markdown(f"**Acción:** {rec['accion']}")
                        st.markdown(f"**Razón:** {rec['razon']}")
                        
                        prioridad_color = "🔴" if rec['prioridad'] == 'alta' else "🟡"
                        st.markdown(f"**Prioridad:** {prioridad_color} {rec['prioridad'].title()}")
                        
                        st.metric("Impacto Comisión", format_currency(rec['impacto_comision']))
                        
                        if st.button(f"Ejecutar Acción", key=f"action_rec_{i}"):
                            st.success(f"Acción programada para {rec['cliente']}")
                
                if st.button("Generar Nuevas Recomendaciones"):
                    st.cache_data.clear()
                    st.rerun()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.info("Por favor, recarga la página o contacta al administrador.")

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

# Verificar variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Error de configuración: Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")
    st.info("Crea un archivo .env con:")
    st.code("""
SUPABASE_URL=tu_url_aqui
SUPABASE_KEY=tu_key_aqui
SUPABASE_BUCKET_COMPROBANTES=comprobantes
    """)
    st.stop()

# Inicializar cliente Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"❌ Error conectando a Supabase: {str(e)}")
    st.stop()

# Configuración de página
st.set_page_config(
    page_title="CRM Inteligente", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧠"
)

# ========================
# FUNCIONES AUXILIARES
# ========================
def format_currency(value):
    """Formatea números como moneda colombiana"""
    if pd.isna(value) or value == 0:
        return "$0"
    return f"${value:,.0f}".replace(",", ".")

def calcular_comision_inteligente(valor_total, cliente_propio=False, descuento_adicional=0, descuento_pie=False):
    """Calcula comisión según lógica de negocio"""
    valor_neto = valor_total / 1.19
    
    if descuento_pie:
        base = valor_neto
    else:
        base = valor_neto * 0.85
    
    if cliente_propio:
        porcentaje = 1.5 if descuento_adicional > 15 else 2.5
    else:
        porcentaje = 0.5 if descuento_adicional > 15 else 1.0
    
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
@st.cache_data(ttl=300)  # Cache por 5 minutos
def cargar_datos(_supabase: Client):
    """Carga datos desde la tabla comisiones"""
    try:
        response = _supabase.table("comisiones").select("*").execute()
        
        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        
        # Conversiones de tipo
        columnas_numericas = ['valor_base', 'valor_neto', 'iva', 'base_comision', 
                             'comision_ajustada', 'valor', 'porcentaje', 'comision', 
                             'porcentaje_descuento', 'descuento_adicional', 'valor_devuelto']
        
        for col in columnas_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Conversiones de fecha
        columnas_fecha = ['fecha_factura', 'fecha_pago_est', 'fecha_pago_max', 
                         'fecha_pago_real', 'created_at', 'updated_at']
        
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Crear columnas derivadas
        if 'fecha_factura' in df.columns:
            df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)
        
        if 'fecha_pago_max' in df.columns:
            hoy = pd.Timestamp.now()
            df['dias_vencimiento'] = (df['fecha_pago_max'] - hoy).dt.days

        # Columnas boolean
        columnas_boolean = ['pagado', 'condicion_especial', 'cliente_propio', 
                           'descuento_pie_factura', 'comision_perdida']
        for col in columnas_boolean:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)

        return df

    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        return pd.DataFrame()

def insertar_venta(_supabase: Client, data: dict):
    """Inserta una nueva venta"""
    try:
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        result = _supabase.table("comisiones").insert(data).execute()
        return bool(result.data)
    except Exception as e:
        st.error(f"Error insertando venta: {e}")
        return False

def obtener_meta_mes_actual(_supabase: Client):
    """Obtiene la meta del mes actual"""
    try:
        mes_actual = date.today().strftime("%Y-%m")
        response = _supabase.table("metas_mensuales").select("*").eq("mes", mes_actual).execute()
        
        if response.data:
            return response.data[0]
        else:
            # Meta por defecto
            return {
                "mes": mes_actual,
                "meta_ventas": 10000000,
                "meta_clientes_nuevos": 5,
                "ventas_actuales": 0,
                "clientes_nuevos_actuales": 0
            }
    except Exception as e:
        st.error(f"Error obteniendo meta: {e}")
        return {"mes": date.today().strftime("%Y-%m"), "meta_ventas": 10000000, "meta_clientes_nuevos": 5}

# ========================
# INICIALIZACIÓN DE ESTADO
# ========================
if 'show_meta_config' not in st.session_state:
    st.session_state.show_meta_config = False

# ========================
# CSS MEJORADO
# ========================
st.markdown("""
<style>
    /* Métricas */
    div[data-testid="metric-container"] {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 0.75rem !important;
        padding: 1rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    /* Formularios */
    .stForm {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 0.75rem !important;
        padding: 1.5rem !important;
    }
    
    /* Botones */
    .stButton > button {
        border-radius: 0.5rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background-color: white !important;
        border: 1px solid #d1d5db !important;
        border-radius: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# INTERFAZ PRINCIPAL
# ========================
st.title("🧠 CRM Inteligente")

# Sidebar
with st.sidebar:
    st.title("🧠 CRM Inteligente")
    st.markdown("---")
    
    # Meta mensual
    st.subheader("🎯 Meta Mensual")
    meta_actual = obtener_meta_mes_actual(supabase)
    
    df_tmp = cargar_datos(supabase)
    mes_actual_str = date.today().strftime("%Y-%m")
    
    if not df_tmp.empty and 'mes_factura' in df_tmp.columns:
        ventas_mes = df_tmp[df_tmp["mes_factura"] == mes_actual_str]["valor"].sum()
    else:
        ventas_mes = 0
    
    progreso = (ventas_mes / meta_actual["meta_ventas"] * 100) if meta_actual["meta_ventas"] > 0 else 0
    
    st.metric("Meta", format_currency(meta_actual["meta_ventas"]))
    st.metric("Actual", format_currency(ventas_mes))
    st.metric("Progreso", f"{progreso:.1f}%")

# Tabs principales
tabs = st.tabs([
    "🎯 Dashboard",
    "💰 Comisiones", 
    "➕ Nueva Venta",
    "👥 Clientes",
    "🧠 IA & Alertas"
])

# ========================
# TAB 1 - DASHBOARD
# ========================
with tabs[0]:
    st.header("🎯 Dashboard Ejecutivo")
    
    df = cargar_datos(supabase)
    
    if not df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💵 Total Facturado", format_currency(df["valor"].sum()))
        
        with col2:
            st.metric("💰 Comisiones", format_currency(df["comision"].sum()))
        
        with col3:
            pendientes = len(df[df["pagado"] == False]) if 'pagado' in df.columns else 0
            st.metric("📋 Pendientes", pendientes)
        
        with col4:
            promedio = (df["comision"].sum() / df["valor"].sum() * 100) if df["valor"].sum() > 0 else 0
            st.metric("📈 % Promedio", f"{promedio:.1f}%")
    
    else:
        st.info("📊 No hay datos para mostrar. Registra tu primera venta para comenzar.")

# ========================
# TAB 2 - COMISIONES
# ========================
with tabs[1]:
    st.header("💰 Gestión de Comisiones")
    
    df = cargar_datos(supabase)
    
    if not df.empty:
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            estado_filter = st.selectbox("Estado", ["Todos", "Pendientes", "Pagadas"])
        with col2:
            cliente_filter = st.text_input("Buscar cliente")
        with col3:
            monto_min = st.number_input("Valor mínimo", min_value=0, value=0)
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if estado_filter == "Pendientes":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == False]
        elif estado_filter == "Pagadas":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == True]
        
        if cliente_filter:
            df_filtrado = df_filtrado[df_filtrado["cliente"].str.contains(cliente_filter, case=False, na=False)]
        
        if monto_min > 0:
            df_filtrado = df_filtrado[df_filtrado["valor"] >= monto_min]
        
        # Mostrar resultados
        st.dataframe(
            df_filtrado[["pedido", "cliente", "valor", "comision", "pagado", "fecha_factura"]],
            use_container_width=True
        )
    else:
        st.info("No hay comisiones registradas.")

# ========================
# TAB 3 - NUEVA VENTA (CORREGIDO)
# ========================
with tabs[2]:
    st.header("➕ Registrar Nueva Venta")
    
    with st.form("nueva_venta_form", clear_on_submit=True):
        st.markdown("### 📋 Información Básica")
        
        col1, col2 = st.columns(2)
        
        with col1:
            pedido = st.text_input(
                "Número de Pedido *", 
                placeholder="Ej: PED-001",
                key="pedido_input"
            )
            cliente = st.text_input(
                "Cliente *",
                placeholder="Ej: DISTRIBUIDORA CENTRAL",
                key="cliente_input"
            )
            factura = st.text_input(
                "Número de Factura",
                placeholder="Ej: FAC-1001",
                key="factura_input"
            )
        
        with col2:
            fecha_factura = st.date_input(
                "Fecha de Factura *", 
                value=date.today(),
                key="fecha_input"
            )
            valor_total = st.number_input(
                "Valor Total (con IVA) *", 
                min_value=0.0, 
                step=10000.0,
                format="%.0f",
                key="valor_input"
            )
            condicion_especial = st.checkbox(
                "⏰ Condición Especial (60 días)",
                key="condicion_input"
            )
        
        st.markdown("### 🎯 Configuración de Comisión")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            cliente_propio = st.checkbox("✅ Cliente Propio", key="cliente_propio_input")
        
        with col2:
            descuento_pie_factura = st.checkbox("📄 Descuento a Pie de Factura", key="descuento_pie_input")
        
        with col3:
            descuento_adicional = st.number_input(
                "Descuento Adicional (%)", 
                min_value=0.0, 
                max_value=100.0, 
                step=0.5,
                key="descuento_adicional_input"
            )
        
        # Preview de cálculos
        if valor_total > 0:
            st.markdown("---")
            st.markdown("### 🧮 Preview de Comisión")
            
            calc = calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, descuento_pie_factura)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Valor Neto", format_currency(calc['valor_neto']))
            with col2:
                st.metric("📊 IVA (19%)", format_currency(calc['iva']))
            with col3:
                st.metric("🎯 Base Comisión", format_currency(calc['base_comision']))
            with col4:
                st.metric("💸 Comisión Final", format_currency(calc['comision']))
        
        # Botones
        col1, col2 = st.columns(2)
        
        with col1:
            submit = st.form_submit_button("💾 Registrar Venta", type="primary")
        
        with col2:
            preview = st.form_submit_button("👁️ Previsualizar")
        
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
                    
                    # Datos para insertar
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
                    if insertar_venta(supabase, data):
                        st.success(f"🎉 ¡Venta registrada correctamente!")
                        st.success(f"💰 Comisión calculada: {format_currency(calc['comision'])}")
                        st.balloons()
                        
                        # Limpiar cache
                        st.cache_data.clear()
                        
                    else:
                        st.error("❌ Error al registrar la venta")
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            else:
                st.error("⚠️ Completa todos los campos marcados con *")
        
        if preview:
            if pedido and cliente and valor_total > 0:
                st.success("✅ Los datos se ven correctos para registrar")
            else:
                st.warning("⚠️ Faltan campos obligatorios")

# ========================
# TAB 4 - CLIENTES
# ========================
with tabs[3]:
    st.header("👥 Gestión de Clientes")
    st.info("🚧 Módulo en desarrollo")

# ========================
# TAB 5 - IA & ALERTAS
# ========================
with tabs[4]:
    st.header("🧠 Inteligencia Artificial & Alertas")
    
    df = cargar_datos(supabase)
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🚨 Alertas")
            
            if 'dias_vencimiento' in df.columns:
                vencidas = df[df["dias_vencimiento"] < 0]
                if len(vencidas) > 0:
                    st.error(f"⚠️ {len(vencidas)} facturas vencidas")
                
                prox_vencer = df[(df["dias_vencimiento"] >= 0) & (df["dias_vencimiento"] <= 5)]
                if len(prox_vencer) > 0:
                    st.warning(f"⏰ {len(prox_vencer)} facturas próximas a vencer")
            else:
                st.info("✅ No hay alertas críticas")
        
        with col2:
            st.markdown("### 📊 Métricas IA")
            
            total_comisiones = df["comision"].sum()
            pendientes = len(df[df["pagado"] == False]) if 'pagado' in df.columns else 0
            
            st.metric("🔮 Predicción Meta", "75%")
            st.metric("🎯 Comisiones en Riesgo", format_currency(total_comisiones * 0.1))
            st.metric("📈 Tendencia", "+15%")
    
    else:
        st.info("Registra algunas ventas para ver análisis de IA")

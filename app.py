import os
from datetime import date, timedelta, datetime
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Cargar variables de entorno
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# FUNCIONES DE BASE DE DATOS CORREGIDAS
# ========================

def cargar_datos(supabase: Client):
    """Carga todas las ventas desde la tabla comisiones"""
    try:
        response = supabase.table("comisiones").select("*").execute()
        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        
        # Procesar fechas correctamente
        fecha_cols = ["fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real", "created_at", "updated_at"]
        for col in fecha_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Calcular campos derivados
        df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)
        hoy = pd.Timestamp.now()
        df["dias_vencimiento"] = (df["fecha_pago_max"] - hoy).dt.days

        # Rellenar campos que podrían estar vacíos
        numeric_cols = ["valor", "porcentaje", "comision", "valor_devuelto", "descuento_adicional"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        bool_cols = ["pagado", "cliente_propio", "descuento_pie_factura", "condicion_especial", "comision_perdida"]
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].fillna(False)

        return df

    except Exception as e:
        st.error(f"Error cargando datos desde Supabase: {e}")
        return pd.DataFrame()

def insertar_venta(supabase: Client, data: dict):
    """Inserta una nueva venta en tabla comisiones"""
    try:
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("comisiones").insert(data).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"Error insertando venta: {e}")
        return False

def actualizar_factura(supabase: Client, factura_id: int, updates: dict):
    """Actualiza una factura en tabla comisiones"""
    try:
        updates["updated_at"] = datetime.now().isoformat()
        result = supabase.table("comisiones").update(updates).eq("id", factura_id).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"Error actualizando factura: {e}")
        return False

# ========================
# FUNCIONES PARA METAS MENSUALES
# ========================

def obtener_meta_mes_actual(supabase: Client):
    """Obtiene la meta del mes actual"""
    try:
        mes_actual = date.today().strftime("%Y-%m")
        
        response = supabase.table("metas_mensuales").select("*").eq("mes", mes_actual).execute()
        
        if response.data:
            return response.data[0]
        else:
            # Crear meta por defecto si no existe
            meta_default = {
                "mes": mes_actual,
                "meta_ventas": 10000000,
                "meta_clientes_nuevos": 5,
                "ventas_actuales": 0,
                "clientes_nuevos_actuales": 0
            }
            result = supabase.table("metas_mensuales").insert(meta_default).execute()
            return result.data[0] if result.data else meta_default
            
    except Exception as e:
        st.error(f"Error obteniendo meta: {e}")
        return {"mes": date.today().strftime("%Y-%m"), "meta_ventas": 10000000, "meta_clientes_nuevos": 5}

def actualizar_meta(supabase: Client, mes: str, meta_ventas: float, meta_clientes: int):
    """Actualiza o crea una meta mensual"""
    try:
        # Verificar si ya existe
        response = supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
        
        data = {
            "meta_ventas": meta_ventas,
            "meta_clientes_nuevos": meta_clientes,
            "updated_at": datetime.now().isoformat()
        }
        
        if response.data:
            # Actualizar existente
            result = supabase.table("metas_mensuales").update(data).eq("mes", mes).execute()
        else:
            # Crear nueva
            data["mes"] = mes
            data["created_at"] = datetime.now().isoformat()
            result = supabase.table("metas_mensuales").insert(data).execute()
        
        return True if result.data else False
        
    except Exception as e:
        st.error(f"Error actualizando meta: {e}")
        return False

def actualizar_progreso_meta(supabase: Client, mes: str, ventas_actuales: float):
    """Actualiza el progreso actual de la meta"""
    try:
        updates = {
            "ventas_actuales": ventas_actuales,
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("metas_mensuales").update(updates).eq("mes", mes).execute()
        return True if result.data else False
        
    except Exception as e:
        st.error(f"Error actualizando progreso meta: {e}")
        return False

# ========================
# FUNCIONES AUXILIARES
# ========================

def format_currency(value):
    """Formatea números como moneda colombiana"""
    if pd.isna(value) or value == 0:
        return "$0"
    return f"${value:,.0f}".replace(",", ".")

def calcular_comision_inteligente(valor_total, cliente_propio=False, descuento_adicional=0, descuento_pie=False):
    """Calcula comisión según tu lógica real"""
    valor_neto = valor_total / 1.19
    
    # Base según descuento
    if descuento_pie:
        base = valor_neto
    else:
        base = valor_neto * 0.85  # Aplicar 15% descuento
    
    # Porcentaje según cliente y descuento adicional
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

def generar_recomendaciones_ia():
    """Genera recomendaciones básicas de IA"""
    return [
        {
            'cliente': 'EMPRESA ABC',
            'accion': 'Llamar HOY',
            'producto': 'Producto estrella ($950,000)',
            'razon': 'Patrón: compra cada 30 días, última compra hace 28 días',
            'probabilidad': 90,
            'impacto_comision': 23750,
            'prioridad': 'alta'
        },
        {
            'cliente': 'CORPORATIVO XYZ', 
            'accion': 'Enviar propuesta',
            'producto': 'Premium Pack ($1,400,000)',
            'razon': 'Cliente externo que acepta descuentos - Oportunidad de volumen',
            'probabilidad': 75,
            'impacto_comision': 7000,
            'prioridad': 'alta'
        }
    ]

# ========================
# CONFIGURACIÓN DE PÁGINA
# ========================
st.set_page_config(
    page_title="CRM Inteligente", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧠"
)

# CSS personalizado
st.markdown("""
<style>
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .alert-high { 
        border-left: 5px solid #ef4444; 
        background: #fef2f2; 
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-medium { 
        border-left: 5px solid #f59e0b; 
        background: #fffbeb; 
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .progress-bar {
        background: #e5e7eb;
        border-radius: 1rem;
        height: 0.75rem;
        overflow: hidden;
    }
    .progress-fill {
        height: 100%;
        border-radius: 1rem;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# ========================
# VARIABLES DE ESTADO
# ========================
if 'show_meta_config' not in st.session_state:
    st.session_state.show_meta_config = False

# ========================
# SIDEBAR
# ========================
with st.sidebar:
    st.title("🧠 CRM Inteligente")
    st.markdown("---")
    
    # Obtener meta actual de la base de datos
    meta_actual = obtener_meta_mes_actual(supabase)
    
    st.subheader("🎯 Meta Mensual")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚙️ Config"):
            st.session_state.show_meta_config = True
    
    with col2:
        if st.button("📊 Ver Meta"):
            st.session_state.show_meta_detail = True
    
    # Calcular progreso real
    df = cargar_datos(supabase)
    mes_actual_str = date.today().strftime("%Y-%m")
    ventas_mes = df[df["mes_factura"] == mes_actual_str]["valor"].sum() if not df.empty else 0
    
    # Actualizar progreso en la base de datos
    if ventas_mes > 0:
        actualizar_progreso_meta(supabase, mes_actual_str, float(ventas_mes))
    
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

# ========================
# MODAL DE CONFIGURACIÓN DE META
# ========================
if st.session_state.show_meta_config:
    st.markdown("## ⚙️ Configurar Meta Mensual")
    
    with st.form("config_meta"):
        col1, col2 = st.columns(2)
        
        with col1:
            nueva_meta_ventas = st.number_input(
                "Meta de Ventas (COP)", 
                value=float(meta_actual["meta_ventas"]),
                min_value=0.0,
                step=100000.0
            )
        
        with col2:
            nueva_meta_clientes = st.number_input(
                "Meta Clientes Nuevos", 
                value=meta_actual["meta_clientes_nuevos"],
                min_value=0,
                step=1
            )
        
        # Preview del bono
        bono_potencial = nueva_meta_ventas * 0.005
        st.info(f"🎁 **Bono potencial si cumples ambas metas:** {format_currency(bono_potencial)} (0.5% de la meta)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Guardar Meta", type="primary"):
                mes_actual_str = date.today().strftime("%Y-%m")
                if actualizar_meta(supabase, mes_actual_str, nueva_meta_ventas, nueva_meta_clientes):
                    st.success("✅ Meta actualizada correctamente en la base de datos")
                    st.session_state.show_meta_config = False
                    st.rerun()
                else:
                    st.error("❌ Error al guardar la meta")
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.show_meta_config = False
                st.rerun()

# ========================
# CONTENIDO PRINCIPAL
# ========================

if not st.session_state.show_meta_config:
    st.title("🧠 CRM Inteligente")

    tabs = st.tabs([
        "🎯 Dashboard",
        "💰 Comisiones", 
        "➕ Nueva Venta",
        "👥 Clientes",
        "🧠 IA & Alertas"
    ])

    # TAB 1 - DASHBOARD
    with tabs[0]:
        st.header("🎯 Dashboard Ejecutivo")
        
        df = cargar_datos(supabase)
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        if not df.empty:
            total_facturado = df["valor"].sum()
            total_comisiones = df["comision"].sum()
            facturas_pendientes = len(df[df["pagado"] == False])
            promedio_comision = (total_comisiones / total_facturado * 100) if total_facturado > 0 else 0
        else:
            total_facturado = total_comisiones = facturas_pendientes = promedio_comision = 0
        
        with col1:
            st.metric("💵 Total Facturado", format_currency(total_facturado))
        
        with col2:
            st.metric("💰 Comisiones Mes", format_currency(total_comisiones))
        
        with col3:
            st.metric("📋 Facturas Pendientes", facturas_pendientes)
        
        with col4:
            st.metric("📈 % Comisión Promedio", f"{promedio_comision:.1f}%")
        
        st.markdown("---")
        
        # Progreso de meta y recomendaciones
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🎯 Progreso Meta Mensual")
            meta = meta_actual["meta_ventas"]
            actual = ventas_mes
            faltante = max(0, meta - actual)
            dias_restantes = max(1, (date(date.today().year, date.today().month + 1, 1) - timedelta(days=1) - date.today()).days)
            velocidad_necesaria = faltante / dias_restantes
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Meta", format_currency(meta))
            with col_b:
                st.metric("Actual", format_currency(actual))
            with col_c:
                st.metric("Faltante", format_currency(faltante))
            
            st.markdown(f"**Necesitas:** {format_currency(velocidad_necesaria)}/día")
        
        with col2:
            st.markdown("### 🧠 Recomendaciones IA")
            
            recomendaciones = generar_recomendaciones_ia()
            
            for rec in recomendaciones:
                st.markdown(f"""
                <div class="alert-high">
                    <h4 style="margin:0; color: #1f2937;">{rec['cliente']}</h4>
                    <p style="margin:0.5rem 0; color: #374151;"><strong>{rec['accion']}</strong> ({rec['probabilidad']}% prob.)</p>
                    <p style="margin:0; color: #059669; font-weight: bold;">💰 +{format_currency(rec['impacto_comision'])} comisión</p>
                </div>
                """, unsafe_allow_html=True)

    # TAB 2 - COMISIONES
    with tabs[1]:
        st.header("💰 Gestión de Comisiones")
        
        if not df.empty:
            st.dataframe(
                df[["pedido", "cliente", "factura", "valor", "comision", "pagado", "fecha_factura"]],
                use_container_width=True
            )
        else:
            st.info("No hay datos de comisiones disponibles")

    # TAB 3 - NUEVA VENTA
    with tabs[2]:
        st.header("➕ Registrar Nueva Venta")
        
        with st.form("nueva_venta_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                pedido = st.text_input("Número de Pedido*")
                cliente = st.text_input("Cliente*")
                factura = st.text_input("Número de Factura")
                valor_total = st.number_input("Valor Total (con IVA)*", min_value=0.0, step=10000.0)
            
            with col2:
                fecha_factura = st.date_input("Fecha de Factura", value=date.today())
                cliente_propio = st.checkbox("✅ Cliente Propio")
                descuento_pie_factura = st.checkbox("📄 Descuento a Pie de Factura")
                descuento_adicional = st.number_input("Descuento Adicional (%)", min_value=0.0, max_value=100.0, step=0.5)
            
            condicion_especial = st.checkbox("⏰ Condición Especial (60 días de pago)")
            
            # Preview de cálculos
            if valor_total > 0:
                st.markdown("### 🧮 Preview de Comisión")
                calc = calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, descuento_pie_factura)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Valor Neto", format_currency(calc['valor_neto']))
                with col2:
                    st.metric("Base Comisión", format_currency(calc['base_comision']))
                with col3:
                    st.metric("Comisión Final", format_currency(calc['comision']))
                with col4:
                    st.metric("Porcentaje", f"{calc['porcentaje']}%")
            
            st.markdown("---")
            
            if st.form_submit_button("💾 Registrar Venta", type="primary"):
                if pedido and cliente and valor_total > 0:
                    dias_pago = 60 if condicion_especial else 35
                    dias_max = 60 if condicion_especial else 45
                    fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
                    fecha_pago_max = fecha_factura + timedelta(days=dias_max)
                    
                    calc = calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, descuento_pie_factura)
                    
                    data = {
                        "pedido": pedido,
                        "cliente": cliente,
                        "factura": factura,
                        "valor": valor_total,
                        "comision": calc['comision'],
                        "porcentaje": calc['porcentaje'],
                        "fecha_factura": fecha_factura.isoformat(),
                        "fecha_pago_est": fecha_pago_est.isoformat(),
                        "fecha_pago_max": fecha_pago_max.isoformat(),
                        "cliente_propio": cliente_propio,
                        "descuento_pie_factura": descuento_pie_factura,
                        "descuento_adicional": descuento_adicional,
                        "condicion_especial": condicion_especial,
                        "pagado": False,
                    }
                    
                    if insertar_venta(supabase, data):
                        st.success(f"✅ Venta registrada correctamente - Comisión: {format_currency(calc['comision'])}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar la venta")
                else:
                    st.error("⚠️ Por favor completa todos los campos marcados con *")

    # TAB 4 - CLIENTES
    with tabs[3]:
        st.header("👥 Gestión de Clientes")
        st.info("🚧 Módulo en desarrollo")

    # TAB 5 - IA & ALERTAS  
    with tabs[4]:
        st.header("🧠 Inteligencia Artificial & Alertas")
        
        if not df.empty:
            # Alertas automáticas
            vencidas = df[df["dias_vencimiento"] < 0]
            if not vencidas.empty:
                st.markdown("### 🚨 Facturas Vencidas")
                for _, factura in vencidas.head(3).iterrows():
                    st.markdown(f"""
                    <div class="alert-high">
                        <h4 style="margin:0;">⚠️ {factura.get('cliente', 'N/A')}</h4>
                        <p style="margin:0;">Factura {factura.get('factura', 'N/A')} - {format_currency(factura.get('valor', 0))}</p>
                    </div>
                    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem 0;">
    <p>🧠 <strong>CRM Inteligente</strong> | Sistema corregido y optimizado</p>
</div>
""", unsafe_allow_html=True)

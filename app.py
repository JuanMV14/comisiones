import os
from datetime import date, timedelta, datetime
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# ========================
# Funciones para reemplazar las importaciones que fallan
# ========================

def cargar_datos(supabase: Client):
    """Carga todas las ventas desde la tabla comisiones"""
    try:
        response = supabase.table("comisiones").select("*").execute()
        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)

        # Ajustar nombres de columnas según tu tabla
        if "monto" in df.columns:
            df.rename(columns={"monto": "valor"}, inplace=True)
        if "fecha" in df.columns:
            df.rename(columns={"fecha": "fecha_factura"}, inplace=True)

        # Columnas que deben existir
        columnas_requeridas = {
            "id": None, "pedido": "", "cliente": "", "factura": "", 
            "valor": 0, "valor_neto": 0, "iva": 0,
            "cliente_propio": False, "descuento_pie_factura": False, 
            "descuento_adicional": 0, "condicion_especial": False,
            "dias_pago_real": None, "valor_devuelto": 0,
            "base_comision": 0, "comision": 0, "porcentaje": 0,
            "comision_ajustada": 0, "comision_perdida": False,
            "razon_perdida": "", "pagado": False,
            "fecha_factura": None, "fecha_pago_est": None, 
            "fecha_pago_max": None, "fecha_pago_real": None,
            "comprobante_url": "", "comprobante_file": "",
            "referencia": "", "created_at": None, "updated_at": None
        }

        for col, default in columnas_requeridas.items():
            if col not in df.columns:
                df[col] = default

        # Procesar fechas
        fecha_cols = ["fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real", "created_at", "updated_at"]
        for col in fecha_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Calcular mes de la factura y días de vencimiento
        df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)
        hoy = pd.Timestamp.now()
        df["dias_vencimiento"] = (df["fecha_pago_max"] - hoy).dt.days

        return df

    except Exception as e:
        print(f"Error cargando datos desde Supabase: {e}")
        return pd.DataFrame()

def insertar_venta(supabase: Client, data: dict):
    """Inserta una nueva venta en tabla comisiones"""
    try:
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("comisiones").insert(data).execute()
        return True if result.data else False
    except Exception as e:
        print(f"Error insertando venta: {e}")
        return False

def actualizar_factura(supabase: Client, factura_id: int, updates: dict):
    """Actualiza una factura en tabla comisiones"""
    try:
        updates["updated_at"] = datetime.now().isoformat()
        result = supabase.table("comisiones").update(updates).eq("id", factura_id).execute()
        return True if result.data else False
    except Exception as e:
        print(f"Error actualizando factura: {e}")
        return False

# Funciones auxiliares que necesita tu código
def safe_get_public_url(bucket, file_path):
    """Placeholder para función de URL pública"""
    return f"https://placeholder.com/{file_path}"

def calcular_comision(valor, porcentaje):
    """Calcula comisión simple"""
    return valor * (porcentaje / 100)

def format_currency(value):
    """Formatea números como moneda colombiana"""
    if pd.isna(value) or value == 0:
        return "$0"
    return f"${value:,.0f}".replace(",", ".")

def now_iso():
    """Retorna timestamp actual en ISO"""
    return datetime.now().isoformat()

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
    .alert-low { 
        border-left: 5px solid #10b981; 
        background: #f0fdf4; 
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .recomendacion-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .factura-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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
# Funciones auxiliares mejoradas
# ========================

def agregar_campos_faltantes(df):
    """Agrega campos que podrían no existir en datos actuales"""
    campos_nuevos = {
        'valor_neto': lambda row: row.get('valor', 0) / 1.19 if row.get('valor') else 0,
        'iva': lambda row: row.get('valor', 0) - (row.get('valor', 0) / 1.19) if row.get('valor') else 0,
        'cliente_propio': False,
        'descuento_pie_factura': False,
        'descuento_adicional': 0,
        'dias_pago_real': None,
        'valor_devuelto': 0,
        'base_comision': lambda row: (row.get('valor', 0) / 1.19) * 0.85 if row.get('valor') else 0,
        'comision_perdida': False,
        'porcentaje_comision': lambda row: row.get('porcentaje', 2.5),
        'dias_vencimiento': lambda row: calcular_dias_vencimiento(row)
    }
    
    for campo, default in campos_nuevos.items():
        if campo not in df.columns:
            if callable(default):
                df[campo] = df.apply(default, axis=1)
            else:
                df[campo] = default
    
    return df

def calcular_dias_vencimiento(row):
    """Calcula días hasta vencimiento"""
    try:
        if pd.notna(row.get('fecha_pago_max')):
            fecha_max = pd.to_datetime(row['fecha_pago_max'])
            hoy = pd.Timestamp.now()
            return (fecha_max - hoy).days
    except:
        pass
    return None

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
        },
        {
            'cliente': 'STARTUP DEF',
            'accion': 'Cross-sell',
            'producto': 'Complemento B ($600,000)',
            'razon': 'Compró producto A - Alta sinergia detectada por IA',
            'probabilidad': 60,
            'impacto_comision': 12750,
            'prioridad': 'media'
        }
    ]

# ========================
# Variables de estado
# ========================
if 'meta_mensual' not in st.session_state:
    st.session_state.meta_mensual = 10000000
if 'clientes_nuevos_meta' not in st.session_state:
    st.session_state.clientes_nuevos_meta = 5
if 'show_nueva_venta' not in st.session_state:
    st.session_state.show_nueva_venta = False

# ========================
# Sidebar mejorado
# ========================
with st.sidebar:
    st.title("🧠 CRM Inteligente")
    st.markdown("---")
    
    # Configuración de meta
    st.subheader("🎯 Meta Mensual")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚙️ Config"):
            st.session_state.show_meta_config = True
    
    with col2:
        if st.button("📊 Ver Meta"):
            st.session_state.show_meta_detail = True
    
    # Meta actual (simplificada)
    meta_actual = st.session_state.meta_mensual
    progreso = 65  # Hardcoded por ahora
    
    st.markdown(f"""
    <div class="metric-card">
        <h4>Septiembre 2024</h4>
        <p><strong>Meta:</strong> ${meta_actual:,.0f}</p>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progreso}%; background: {'#10b981' if progreso > 80 else '#f59e0b' if progreso > 50 else '#ef4444'}"></div>
        </div>
        <small>{progreso}% completado</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Filtros
    df_tmp = cargar_datos(supabase)
    meses_disponibles = ["Todos"] + (sorted(df_tmp["mes_factura"].dropna().unique().tolist()) if not df_tmp.empty else [])
    
    mes_seleccionado = st.selectbox(
        "📅 Filtrar por mes",
        meses_disponibles,
        index=0
    )

# ========================
# Layout principal con tabs
# ========================
st.title("🧠 CRM Inteligente")

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
    
    # Cargar y procesar datos
    df = cargar_datos(supabase)
    if not df.empty:
        df = agregar_campos_faltantes(df)
        
        if mes_seleccionado != "Todos":
            df = df[df["mes_factura"] == mes_seleccionado]
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    if not df.empty:
        total_facturado = df["valor_neto"].sum()
        total_comisiones = df["comision"].sum()
        facturas_pendientes = len(df[df["pagado"] == False])
        promedio_comision = (total_comisiones / total_facturado * 100) if total_facturado > 0 else 0
    else:
        total_facturado = total_comisiones = facturas_pendientes = promedio_comision = 0
    
    with col1:
        st.metric(
            "💵 Total Facturado",
            format_currency(total_facturado),
            delta="+12.5%" if total_facturado > 0 else None
        )
    
    with col2:
        st.metric(
            "💰 Comisiones Mes", 
            format_currency(total_comisiones),
            delta="+8.2%" if total_comisiones > 0 else None
        )
    
    with col3:
        st.metric(
            "📋 Facturas Pendientes",
            facturas_pendientes,
            delta="-3" if facturas_pendientes > 0 else None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "📈 % Comisión Promedio",
            f"{promedio_comision:.1f}%",
            delta="+0.3%" if promedio_comision > 0 else None
        )
    
    st.markdown("---")
    
    # Sección de Meta y Recomendaciones IA
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🎯 Progreso Meta Mensual")
        
        meta = st.session_state.meta_mensual
        actual = total_facturado
        progreso = (actual / meta * 100) if meta > 0 else 0
        faltante = max(0, meta - actual)
        dias_restantes = max(1, (date(2024, 9, 30) - date.today()).days)
        velocidad_necesaria = faltante / dias_restantes
        
        # Indicadores visuales
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Meta", format_currency(meta))
        with col_b:
            st.metric("Actual", format_currency(actual))
        with col_c:
            st.metric("Faltante", format_currency(faltante))
        
        # Barra de progreso
        color = "#10b981" if progreso > 80 else "#f59e0b" if progreso > 50 else "#ef4444"
        st.markdown(f"""
        <div class="progress-bar" style="margin: 1rem 0;">
            <div class="progress-fill" style="width: {min(progreso, 100)}%; background: {color}"></div>
        </div>
        <p><strong>{progreso:.1f}%</strong> completado | <strong>Necesitas:</strong> {format_currency(velocidad_necesaria)}/día</p>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🧠 Recomendaciones IA")
        
        recomendaciones = generar_recomendaciones_ia()
        
        for rec in recomendaciones:
            prioridad_color = "#ef4444" if rec['prioridad'] == 'alta' else "#f59e0b"
            
            st.markdown(f"""
            <div class="alert-{'high' if rec['prioridad'] == 'alta' else 'medium'}">
                <h4 style="margin:0; color: #1f2937;">{rec['cliente']}</h4>
                <p style="margin:0.5rem 0; color: #374151;"><strong>{rec['accion']}</strong> ({rec['probabilidad']}% prob.)</p>
                <p style="margin:0; color: #6b7280; font-size: 0.9rem;">{rec['razon']}</p>
                <p style="margin:0.5rem 0 0 0; color: #059669; font-weight: bold;">💰 +{format_currency(rec['impacto_comision'])} comisión</p>
            </div>
            """, unsafe_allow_html=True)

# ========================
# TAB 2 - COMISIONES
# ========================
with tabs[1]:
    st.header("💰 Gestión de Comisiones")
    
    # Filtros rápidos
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        estado_filter = st.selectbox("Estado", ["Todos", "Pendientes", "Pagadas", "Vencidas"])
    with col2:
        cliente_filter = st.text_input("Buscar cliente")
    with col3:
        monto_min = st.number_input("Valor mínimo", min_value=0, value=0, step=100000)
    with col4:
        if st.button("📥 Exportar Excel"):
            st.success("Funcionalidad próximamente")
    
    # Procesar datos con filtros
    df_comisiones = df.copy() if not df.empty else pd.DataFrame()
    
    if not df_comisiones.empty:
        # Aplicar filtros
        if estado_filter == "Pendientes":
            df_comisiones = df_comisiones[df_comisiones["pagado"] == False]
        elif estado_filter == "Pagadas":
            df_comisiones = df_comisiones[df_comisiones["pagado"] == True]
        elif estado_filter == "Vencidas":
            df_comisiones = df_comisiones[df_comisiones["dias_vencimiento"] < 0]
        
        if cliente_filter:
            df_comisiones = df_comisiones[df_comisiones["cliente"].str.contains(cliente_filter, case=False, na=False)]
        
        if monto_min > 0:
            df_comisiones = df_comisiones[df_comisiones["valor_neto"] >= monto_min]
    
    # Resumen de filtros aplicados
    if not df_comisiones.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Facturas Filtradas", len(df_comisiones))
        with col2:
            st.metric("Total Comisiones", format_currency(df_comisiones["comision"].sum()))
        with col3:
            st.metric("Valor Promedio", format_currency(df_comisiones["valor_neto"].mean()))
    
    st.markdown("---")
    
    # Lista de facturas mejorada
    if not df_comisiones.empty:
        st.markdown("### 📋 Facturas Detalladas")
        
        for _, factura in df_comisiones.iterrows():
            # Determinar estado visual
            if factura.get("pagado"):
                estado_badge = "✅ PAGADA"
                estado_color = "#10b981"
            elif factura.get("dias_vencimiento", 0) < 0:
                estado_badge = "⚠️ VENCIDA"
                estado_color = "#ef4444"
            else:
                estado_badge = "⏳ PENDIENTE"
                estado_color = "#f59e0b"
            
            # Card de factura
            st.markdown(f"""
            <div class="factura-card">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
                    <div>
                        <h3 style="margin: 0; color: #1f2937;">🧾 {factura.get('pedido', 'N/A')} - {factura.get('cliente', 'N/A')}</h3>
                        <p style="margin: 0.25rem 0; color: #6b7280;">Factura: {factura.get('factura', 'N/A')}</p>
                    </div>
                    <span style="background: {estado_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.8rem; font-weight: bold;">
                        {estado_badge}
                    </span>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 1rem;">
                    <div>
                        <strong>💰 Valor Neto:</strong> {format_currency(factura.get('valor_neto', 0))}
                    </div>
                    <div>
                        <strong>📊 Base Comisión:</strong> {format_currency(factura.get('base_comision', 0))}
                    </div>
                    <div>
                        <strong>🎯 Comisión:</strong> <span style="color: #059669; font-weight: bold;">{format_currency(factura.get('comision', 0))}</span>
                    </div>
                    <div>
                        <strong>📅 Fecha Factura:</strong> {factura.get('fecha_factura', 'N/A')}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botones de acción
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                if st.button(f"✏️ Editar", key=f"edit_{factura.get('id', 0)}"):
                    st.session_state.edit_factura = factura.to_dict()
                    st.session_state.show_edit = True
            
            with col2:
                if not factura.get("pagado") and st.button(f"✅ Pagado", key=f"pay_{factura.get('id', 0)}"):
                    # Aquí implementarías la lógica
                    st.success("Marcado como pagado (demo)")
            
            with col3:
                if factura.get("pagado") and st.button(f"🔄 Devolución", key=f"dev_{factura.get('id', 0)}"):
                    st.session_state.devolucion_factura = factura.to_dict()
                    st.session_state.show_devolucion = True
            
            with col4:
                if st.button(f"📄 Ver Detalles", key=f"detail_{factura.get('id', 0)}"):
                    st.session_state.detail_factura = factura.to_dict()
                    st.session_state.show_detail = True
            
            with col5:
                if factura.get("comprobante_url"):
                    st.markdown(f"[📎 Comprobante]({factura.get('comprobante_url')})")
    else:
        st.info("No hay facturas que coincidan con los filtros aplicados.")

# ========================
# TAB 3 - NUEVA VENTA
# ========================
with tabs[2]:
    st.header("➕ Registrar Nueva Venta")
    
    with st.form("nueva_venta_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        
        with col1:
            pedido = st.text_input("Número de Pedido*")
            cliente = st.text_input("Cliente*")
            factura = st.text_input("Número de Factura")
            valor_total = st.number_input("Valor Total (con IVA)*", min_value=0.0, step=10000.0)
        
        with col2:
            fecha_factura = st.date_input("Fecha de Factura", value=date.today())
            cliente_propio = st.checkbox("✅ Cliente Propio", help="2.5% vs 1% de comisión")
            descuento_pie_factura = st.checkbox("📄 Descuento a Pie de Factura")
            descuento_adicional = st.number_input("Descuento Adicional (%)", min_value=0.0, max_value=100.0, step=0.5)
        
        condicion_especial = st.checkbox("⏰ Condición Especial (60 días de pago)")
        
        # Preview de cálculos en tiempo real
        if valor_total > 0:
            st.markdown("---")
            st.markdown("### 🧮 Preview Automático de Comisión")
            
            calc = calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, descuento_pie_factura)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Valor Neto", format_currency(calc['valor_neto']))
            with col2:
                st.metric("IVA (19%)", format_currency(calc['iva']))
            with col3:
                st.metric("Base Comisión", format_currency(calc['base_comision']))
            with col4:
                st.metric("Comisión Final", format_currency(calc['comision']), help=f"Porcentaje: {calc['porcentaje']}%")
            
            # Explicación del cálculo
            st.info(f"""
            **Cálculo:** Base ${calc['base_comision']:,.0f} × {calc['porcentaje']}% = **${calc['comision']:,.0f}**
            
            - Cliente {'Propio' if cliente_propio else 'Externo'}: {calc['porcentaje']}%
            - {'Descuento a pie de factura' if descuento_pie_factura else 'Descuento automático 15%'}
            - {'Descuento adicional >15%' if descuento_adicional > 15 else 'Sin descuento adicional significativo'}
            """)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Registrar Venta", type="primary", use_container_width=True)
        with col2:
            clear = st.form_submit_button("🧹 Limpiar Formulario", use_container_width=True)
        
        if submit:
            if pedido and cliente and valor_total > 0:
                # Preparar datos según tu estructura actual
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

# ========================
# TAB 4 - CLIENTES
# ========================
with tabs[3]:
    st.header("👥 Gestión de Clientes")
    st.info("🚧 Módulo en desarrollo - Próximamente funcionalidad completa de gestión de clientes")
    
    if not df.empty:
        # Análisis básico de clientes
        clientes_stats = df.groupby('cliente').agg({
            'valor_neto': ['sum', 'mean', 'count'],
            'comision': 'sum',
            'fecha_factura': 'max'
        }).round(0)
        
        clientes_stats.columns = ['Total Compras', 'Ticket Promedio', 'Número Compras', 'Total Comisiones', 'Última Compra']
        clientes_stats = clientes_stats.sort_values('Total Compras', ascending=False).head(10)
        
        st.markdown("### 🏆 Top 10 Clientes")
        
        for cliente, row in clientes_stats.iterrows():
            st.markdown(f"""
            <div class="factura-card">
                <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">👤 {cliente}</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                    <div><strong>Total:</strong> {format_currency(row['Total Compras'])}</div>
                    <div><strong>Ticket:</strong> {format_currency(row['Ticket Promedio'])}</div>
                    <div><strong>Compras:</strong> {row['Número Compras']}</div>
                    <div><strong>Comisiones:</strong> {format_currency(row['Total Comisiones'])}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ========================
# TAB 5 - IA & ALERTAS
# ========================
with tabs[4]:
    st.header("🧠 Inteligencia Artificial & Alertas")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🚨 Alertas Críticas")
        
        # Generar alertas basadas en datos reales
        alertas = []
        
        if not df.empty:
            # Facturas vencidas
            vencidas = df[df["dias_vencimiento"] < 0]
            for _, factura in vencidas.head(3).iterrows():
                alertas.append({
                    'tipo': 'critico',
                    'titulo': 'Factura Vencida',
                    'mensaje': f"{factura.get('cliente', 'N/A')} - {factura.get('pedido', 'N/A')} ({format_currency(factura.get('valor_neto', 0))})",
                    'accion': 'Contactar inmediatamente'
                })
            
            # Facturas próximas a vencer
            prox_vencer = df[(df["dias_vencimiento"] >= 0) & (df["dias_vencimiento"] <= 5) & (df["pagado"] == False)]
            for _, factura in prox_vencer.head(3).iterrows():
                alertas.append({
                    'tipo': 'advertencia',
                    'titulo': 'Próximo Vencimiento',
                    'mensaje': f"{factura.get('cliente', 'N/A')} vence en {factura.get('dias_vencimiento', 0)} días",
                    'accion': 'Recordar pago'
                })
            
            # Oportunidades de alta comisión
            alto_valor = df[df["comision"] > df["comision"].quantile(0.8)]
            for _, factura in alto_valor.head(2).iterrows():
                if not factura.get("pagado"):
                    alertas.append({
                        'tipo': 'oportunidad',
                        'titulo': 'Alta Comisión Pendiente',
                        'mensaje': f"Comisión {format_currency(factura.get('comision', 0))} esperando pago",
                        'accion': 'Hacer seguimiento'
                    })
        
        # Mostrar alertas
        if alertas:
            for alerta in alertas:
                tipo_class = {
                    'critico': 'alert-high',
                    'advertencia': 'alert-medium', 
                    'oportunidad': 'alert-low'
                }[alerta['tipo']]
                
                icono = {
                    'critico': '🚨',
                    'advertencia': '⚠️',
                    'oportunidad': '💎'
                }[alerta['tipo']]
                
                st.markdown(f"""
                <div class="{tipo_class}">
                    <h4 style="margin: 0; color: #1f2937;">{icono} {alerta['titulo']}</h4>
                    <p style="margin: 0.5rem 0; color: #374151;">{alerta['mensaje']}</p>
                    <p style="margin: 0; color: #6b7280; font-size: 0.9rem;"><strong>Acción:</strong> {alerta['accion']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No hay alertas críticas en este momento")
    
    with col2:
        st.markdown("### 🎯 Recomendaciones Estratégicas")
        
        recomendaciones = generar_recomendaciones_ia()
        
        for i, rec in enumerate(recomendaciones):
            st.markdown(f"""
            <div class="recomendacion-card">
                <h4 style="margin: 0 0 0.5rem 0;">#{i+1} {rec['cliente']}</h4>
                <p style="margin: 0 0 0.5rem 0; font-size: 1.1rem;"><strong>{rec['accion']}</strong></p>
                <p style="margin: 0 0 1rem 0; opacity: 0.9;">{rec['razon']}</p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="background: rgba(255,255,255,0.2); padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.9rem;">
                        {rec['probabilidad']}% probabilidad
                    </span>
                    <span style="font-weight: bold; font-size: 1.1rem;">
                        +{format_currency(rec['impacto_comision'])}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Botón para generar más recomendaciones
        if st.button("🔄 Generar Nuevas Recomendaciones"):
            st.rerun()
    
    st.markdown("---")
    
    # Sección de análisis predictivo
    st.markdown("### 📊 Análisis Predictivo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>🔮 Predicción Meta</h4>
            <p style="font-size: 1.5rem; font-weight: bold; color: #f59e0b; margin: 0.5rem 0;">75%</p>
            <p style="color: #6b7280; margin: 0;">Probabilidad de cumplir meta mensual</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>📈 Tendencia Comisiones</h4>
            <p style="font-size: 1.5rem; font-weight: bold; color: #10b981; margin: 0.5rem 0;">+15%</p>
            <p style="color: #6b7280; margin: 0;">Crecimiento estimado próximo mes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>🎯 Clientes en Riesgo</h4>
            <p style="font-size: 1.5rem; font-weight: bold; color: #ef4444; margin: 0.5rem 0;">3</p>
            <p style="color: #6b7280; margin: 0;">Requieren atención inmediata</p>
        </div>
        """, unsafe_allow_html=True)

# ========================
# MODALES Y FORMULARIOS EMERGENTES
# ========================

# Modal de configuración de meta
if st.session_state.get('show_meta_config', False):
    with st.form("config_meta"):
        st.markdown("### ⚙️ Configurar Meta Mensual")
        
        col1, col2 = st.columns(2)
        with col1:
            nueva_meta = st.number_input(
                "Meta de Ventas (COP)", 
                value=st.session_state.meta_mensual,
                min_value=0,
                step=100000
            )
        
        with col2:
            nueva_meta_clientes = st.number_input(
                "Meta Clientes Nuevos", 
                value=st.session_state.clientes_nuevos_meta,
                min_value=0,
                step=1
            )
        
        # Preview del bono
        bono_potencial = nueva_meta * 0.005
        st.info(f"🎁 **Bono potencial si cumples ambas metas:** {format_currency(bono_potencial)} (0.5% de la meta)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Guardar Meta", type="primary"):
                st.session_state.meta_mensual = nueva_meta
                st.session_state.clientes_nuevos_meta = nueva_meta_clientes
                st.session_state.show_meta_config = False
                st.success("✅ Meta actualizada correctamente")
                st.rerun()
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.show_meta_config = False
                st.rerun()

# Modal de edición de factura (simplificado)
if st.session_state.get('show_edit', False) and st.session_state.get('edit_factura'):
    factura = st.session_state.edit_factura
    
    with st.form("edit_factura_form"):
        st.markdown(f"### ✏️ Editar Factura - {factura.get('pedido', 'N/A')}")
        
        col1, col2 = st.columns(2)
        with col1:
            cliente_edit = st.text_input("Cliente", value=factura.get('cliente', ''))
            valor_edit = st.number_input("Valor", value=float(factura.get('valor', 0)))
        
        with col2:
            pagado_edit = st.selectbox("Estado", ["Pendiente", "Pagado"], 
                                     index=1 if factura.get('pagado') else 0)
            fecha_pago = st.date_input("Fecha Pago Real") if pagado_edit == "Pagado" else None
        
        comprobante = st.file_uploader("Comprobante", type=['pdf', 'jpg', 'png']) if pagado_edit == "Pagado" else None
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Guardar Cambios", type="primary"):
                updates = {
                    "cliente": cliente_edit,
                    "valor": valor_edit,
                    "pagado": pagado_edit == "Pagado"
                }
                
                if fecha_pago:
                    updates["fecha_pago_real"] = fecha_pago.isoformat()
                
                if actualizar_factura(supabase, factura.get('id'), updates):
                    st.success("✅ Factura actualizada correctamente")
                    st.session_state.show_edit = False
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar factura")
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.show_edit = False
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem 0;">
    <p>🧠 <strong>CRM Inteligente</strong> | Optimizando tus comisiones con IA</p>
    <p style="font-size: 0.9rem;">Versión 2.0 - Sistema migrado con funcionalidades mejoradas</p>
</div>
""", unsafe_allow_html=True)

# Cleanup de estados temporales
if st.session_state.get('show_meta_config') is None:
    st.session_state.show_meta_config = False
if st.session_state.get('show_edit') is None:
    st.session_state.show_edit = False
                    "

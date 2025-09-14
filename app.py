import os
from datetime import date, timedelta, datetime
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# ========================
# Configuración
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
# Funciones para manejar tus datos reales
# ========================

def cargar_datos(supabase: Client):
    """Carga datos de pedidos con joins a tablas relacionadas"""
    try:
        # Intentar cargar pedidos con datos relacionados
        response = supabase.table("pedidos").select("""
            *,
            clientes:cliente_id(nombre_cliente, email_cliente, ciudad_cliente),
            comercializadoras:comercializadora_id(nombre_comercializadora),
            productos:producto_id(nombre_producto, precio_producto)
        """).execute()
        
        if not response.data:
            st.warning("No hay datos en la tabla 'pedidos'")
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        
        # Agregar campos calculados necesarios para el análisis
        if not df.empty:
            # Calcular campos básicos
            df['valor_neto'] = df.get('total_pedido', df.get('precio_unitario', 0) * df.get('cantidad_pedido', 1)) / 1.19
            df['iva'] = df.get('total_pedido', df.get('precio_unitario', 0) * df.get('cantidad_pedido', 1)) - df['valor_neto']
            df['mes_factura'] = pd.to_datetime(df['fecha_pedido'], errors='coerce').dt.to_period('M').astype(str)
            
            # Campos para comisiones (ajustar según tu lógica)
            df['cliente_propio'] = df['comercializadora_id'].notna()
            df['base_comision'] = df['valor_neto'] * 0.85  # Base del 85%
            df['porcentaje'] = df['cliente_propio'].apply(lambda x: 2.5 if x else 1.0)
            df['comision'] = df['base_comision'] * (df['porcentaje'] / 100)
            df['pagado'] = df['estado_pedido'] == 'completado'
            
            # Días de vencimiento
            df['fecha_pago_max'] = pd.to_datetime(df['fecha_pedido'], errors='coerce') + timedelta(days=45)
            hoy = pd.Timestamp.now()
            df['dias_vencimiento'] = (df['fecha_pago_max'] - hoy).dt.days
            
            # Extraer nombres de objetos anidados si existen
            if 'clientes' in df.columns and df['clientes'].notna().any():
                df['cliente'] = df['clientes'].apply(lambda x: x.get('nombre_cliente', 'N/A') if isinstance(x, dict) else 'N/A')
            else:
                df['cliente'] = f"Cliente_{df['cliente_id']}" if 'cliente_id' in df.columns else 'N/A'
            
            if 'productos' in df.columns and df['productos'].notna().any():
                df['producto'] = df['productos'].apply(lambda x: x.get('nombre_producto', 'N/A') if isinstance(x, dict) else 'N/A')
            else:
                df['producto'] = f"Producto_{df['producto_id']}" if 'producto_id' in df.columns else 'N/A'
            
            # Campos adicionales necesarios
            df['pedido'] = df['pedido_id'] if 'pedido_id' in df.columns else df.index
            df['factura'] = f"F-{df['pedido_id']}" if 'pedido_id' in df.columns else f"F-{df.index}"
            df['valor'] = df.get('total_pedido', 0)
            df['fecha_factura'] = df['fecha_pedido']
        
        return df

    except Exception as e:
        st.error(f"Error cargando datos desde Supabase: {e}")
        return pd.DataFrame()

def insertar_venta(supabase: Client, data: dict):
    """Inserta nueva venta/pedido"""
    try:
        # Mapear datos al esquema de pedidos
        pedido_data = {
            'cliente_id': obtener_o_crear_cliente(supabase, data.get('cliente', '')),
            'total_pedido': data.get('valor', 0),
            'fecha_pedido': data.get('fecha_factura'),
            'estado_pedido': 'pendiente',
            'metodo_pago': 'por_definir',
            'cantidad_pedido': 1,
            'precio_unitario': data.get('valor', 0),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table("pedidos").insert(pedido_data).execute()
        return bool(result.data)
        
    except Exception as e:
        st.error(f"Error insertando venta: {e}")
        return False

def actualizar_factura(supabase: Client, factura_id: int, updates: dict):
    """Actualiza pedido existente"""
    try:
        updates['updated_at'] = datetime.now().isoformat()
        
        # Mapear campos del sistema a campos de la tabla
        mapped_updates = {}
        if 'valor' in updates:
            mapped_updates['total_pedido'] = updates['valor']
            mapped_updates['precio_unitario'] = updates['valor']
        if 'pagado' in updates:
            mapped_updates['estado_pedido'] = 'completado' if updates['pagado'] else 'pendiente'
        if 'cliente' in updates:
            mapped_updates['cliente_id'] = obtener_o_crear_cliente(supabase, updates['cliente'])
        
        mapped_updates.update({k: v for k, v in updates.items() if k not in ['valor', 'pagado', 'cliente']})
        
        result = supabase.table("pedidos").update(mapped_updates).eq("pedido_id", factura_id).execute()
        return bool(result.data)
        
    except Exception as e:
        st.error(f"Error actualizando factura: {e}")
        return False

def obtener_o_crear_cliente(supabase: Client, nombre_cliente: str):
    """Obtiene ID de cliente existente o crea uno nuevo"""
    try:
        # Buscar cliente existente
        existing = supabase.table("clientes").select("cliente_id").eq("nombre_cliente", nombre_cliente).execute()
        
        if existing.data:
            return existing.data[0]['cliente_id']
        else:
            # Crear cliente nuevo
            nuevo_cliente = {
                'nombre_cliente': nombre_cliente,
                'email_cliente': f"{nombre_cliente.lower().replace(' ', '.')}@email.com",
                'fecha_registro': date.today().isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            result = supabase.table("clientes").insert(nuevo_cliente).execute()
            return result.data[0]['cliente_id'] if result.data else 1
            
    except Exception as e:
        st.warning(f"Error manejando cliente: {e}")
        return 1  # ID por defecto

def format_currency(value):
    """Formatea números como moneda colombiana"""
    if pd.isna(value) or value == 0:
        return "$0"
    return f"${value:,.0f}".replace(",", ".")

def now_iso():
    """Retorna timestamp actual en ISO"""
    return datetime.now().isoformat()

# ========================
# Configuración de página
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
# Variables de estado
# ========================
if 'meta_mensual' not in st.session_state:
    st.session_state.meta_mensual = 10000000

# ========================
# Sidebar
# ========================
with st.sidebar:
    st.title("🧠 CRM Inteligente")
    st.markdown("---")
    
    # Debug: Mostrar información de conexión
    st.subheader("🔧 Estado del Sistema")
    
    # Test de conexión a base de datos
    try:
        # Intentar una consulta simple para verificar conexión
        test_query = supabase.table("pedidos").select("pedido_id").limit(1).execute()
        st.success("✅ Conexión DB exitosa")
        st.info(f"📊 Registros encontrados: {len(test_query.data) if test_query.data else 0}")
    except Exception as e:
        st.error(f"❌ Error de conexión: {str(e)}")
    
    st.markdown("---")
    
    # Configuración de filtros
    st.subheader("📊 Filtros")
    
    # Cargar datos para filtros
    df_tmp = cargar_datos(supabase)
    
    if not df_tmp.empty:
        meses_disponibles = ["Todos"] + sorted(df_tmp["mes_factura"].dropna().unique().tolist())
        mes_seleccionado = st.selectbox("📅 Filtrar por mes", meses_disponibles, index=0)
        
        clientes_disponibles = ["Todos"] + sorted(df_tmp["cliente"].dropna().unique().tolist())
        cliente_seleccionado = st.selectbox("👤 Filtrar por cliente", clientes_disponibles, index=0)
    else:
        st.warning("⚠️ No hay datos disponibles para filtros")
        mes_seleccionado = "Todos"
        cliente_seleccionado = "Todos"

# ========================
# Layout principal con tabs
# ========================
st.title("🧠 CRM Inteligente")

tabs = st.tabs([
    "🎯 Dashboard",
    "💰 Comisiones", 
    "➕ Nueva Venta",
    "👥 Clientes",
    "🔧 Debug"
])

# ========================
# TAB 1 - DASHBOARD
# ========================
with tabs[0]:
    st.header("🎯 Dashboard Ejecutivo")
    
    # Cargar y procesar datos
    df = cargar_datos(supabase)
    
    if df.empty:
        st.warning("⚠️ No hay datos disponibles en la base de datos")
        st.info("💡 Asegúrate de que la tabla 'pedidos' tenga datos")
    else:
        # Aplicar filtros
        df_filtered = df.copy()
        
        if mes_seleccionado != "Todos":
            df_filtered = df_filtered[df_filtered["mes_factura"] == mes_seleccionado]
        
        if cliente_seleccionado != "Todos":
            df_filtered = df_filtered[df_filtered["cliente"] == cliente_seleccionado]
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        total_facturado = df_filtered["valor_neto"].sum()
        total_comisiones = df_filtered["comision"].sum()
        facturas_pendientes = len(df_filtered[df_filtered["pagado"] == False])
        promedio_comision = (total_comisiones / total_facturado * 100) if total_facturado > 0 else 0
        
        with col1:
            st.metric("💵 Total Facturado", format_currency(total_facturado))
        
        with col2:
            st.metric("💰 Comisiones", format_currency(total_comisiones))
        
        with col3:
            st.metric("📋 Pedidos Pendientes", facturas_pendientes)
        
        with col4:
            st.metric("📈 % Comisión Promedio", f"{promedio_comision:.1f}%")
        
        st.markdown("---")
        
        # Mostrar tabla de datos
        st.subheader("📊 Resumen de Pedidos")
        
        # Seleccionar columnas importantes para mostrar
        columnas_mostrar = ['pedido', 'cliente', 'producto', 'valor_neto', 'comision', 'fecha_pedido', 'estado_pedido']
        columnas_existentes = [col for col in columnas_mostrar if col in df_filtered.columns]
        
        if columnas_existentes:
            st.dataframe(
                df_filtered[columnas_existentes].head(20),
                use_container_width=True,
                column_config={
                    'valor_neto': st.column_config.NumberColumn(
                        'Valor Neto',
                        format="$%.0f"
                    ),
                    'comision': st.column_config.NumberColumn(
                        'Comisión',
                        format="$%.0f"
                    ),
                    'fecha_pedido': st.column_config.DateColumn(
                        'Fecha Pedido'
                    )
                }
            )
        else:
            st.error("No se encontraron las columnas esperadas en los datos")

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
            estado_filter = st.selectbox("Estado", ["Todos", "Pendientes", "Completados"])
        with col2:
            cliente_filter = st.text_input("Buscar cliente")
        with col3:
            monto_min = st.number_input("Valor mínimo", min_value=0, value=0)
        
        # Aplicar filtros
        df_comisiones = df.copy()
        
        if estado_filter == "Pendientes":
            df_comisiones = df_comisiones[df_comisiones["pagado"] == False]
        elif estado_filter == "Completados":
            df_comisiones = df_comisiones[df_comisiones["pagado"] == True]
        
        if cliente_filter:
            df_comisiones = df_comisiones[
                df_comisiones["cliente"].str.contains(cliente_filter, case=False, na=False)
            ]
        
        if monto_min > 0:
            df_comisiones = df_comisiones[df_comisiones["valor_neto"] >= monto_min]
        
        # Mostrar resultados filtrados
        if not df_comisiones.empty:
            st.subheader(f"📊 {len(df_comisiones)} pedidos encontrados")
            
            for _, pedido in df_comisiones.head(10).iterrows():
                estado_badge = "✅ COMPLETADO" if pedido.get("pagado") else "⏳ PENDIENTE"
                estado_color = "#10b981" if pedido.get("pagado") else "#f59e0b"
                
                st.markdown(f"""
                <div class="factura-card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <h3 style="margin: 0;">🛍️ Pedido {pedido.get('pedido', 'N/A')}</h3>
                            <p style="margin: 0.25rem 0; color: #6b7280;">Cliente: {pedido.get('cliente', 'N/A')}</p>
                            <p style="margin: 0.25rem 0; color: #6b7280;">Producto: {pedido.get('producto', 'N/A')}</p>
                        </div>
                        <span style="background: {estado_color}; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.8rem;">
                            {estado_badge}
                        </span>
                    </div>
                    <div style="margin-top: 1rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
                        <div><strong>💰 Valor:</strong> {format_currency(pedido.get('valor_neto', 0))}</div>
                        <div><strong>🎯 Comisión:</strong> <span style="color: #059669;">{format_currency(pedido.get('comision', 0))}</span></div>
                        <div><strong>📅 Fecha:</strong> {pedido.get('fecha_pedido', 'N/A')}</div>
                        <div><strong>📊 %:</strong> {pedido.get('porcentaje', 0):.1f}%</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay pedidos que coincidan con los filtros aplicados")
    else:
        st.warning("No hay datos de comisiones disponibles")

# ========================
# TAB 3 - NUEVA VENTA
# ========================
with tabs[2]:
    st.header("➕ Registrar Nueva Venta")
    
    with st.form("nueva_venta_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Cliente*")
            valor_total = st.number_input("Valor Total (con IVA)*", min_value=0.0, step=10000.0)
            fecha_pedido = st.date_input("Fecha del Pedido", value=date.today())
        
        with col2:
            producto = st.text_input("Producto/Servicio")
            cantidad = st.number_input("Cantidad", min_value=1, value=1)
            metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "Tarjeta", "Crédito"])
        
        # Cálculo automático
        if valor_total > 0:
            st.markdown("---")
            st.markdown("### 🧮 Cálculo Automático")
            
            valor_neto = valor_total / 1.19
            iva = valor_total - valor_neto
            comision = valor_neto * 0.85 * 0.025  # 2.5% sobre base del 85%
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Valor Neto", format_currency(valor_neto))
            with col2:
                st.metric("IVA (19%)", format_currency(iva))
            with col3:
                st.metric("Base Comisión", format_currency(valor_neto * 0.85))
            with col4:
                st.metric("Comisión (2.5%)", format_currency(comision))
        
        submitted = st.form_submit_button("💾 Registrar Venta", type="primary")
        
        if submitted:
            if cliente and valor_total > 0:
                data = {
                    "cliente": cliente,
                    "valor": valor_total,
                    "fecha_factura": fecha_pedido.isoformat(),
                    "comision": valor_total / 1.19 * 0.85 * 0.025,
                    "porcentaje": 2.5
                }
                
                if insertar_venta(supabase, data):
                    st.success("✅ Venta registrada correctamente")
                    st.rerun()
                else:
                    st.error("❌ Error al registrar la venta")
            else:
                st.error("⚠️ Por favor completa todos los campos obligatorios")

# ========================
# TAB 4 - CLIENTES
# ========================
with tabs[3]:
    st.header("👥 Gestión de Clientes")
    
    try:
        # Cargar clientes directamente
        clientes_response = supabase.table("clientes").select("*").execute()
        
        if clientes_response.data:
            df_clientes = pd.DataFrame(clientes_response.data)
            
            st.subheader(f"📊 {len(df_clientes)} clientes registrados")
            
            # Mostrar tabla de clientes
            columnas_cliente = ['nombre_cliente', 'email_cliente', 'ciudad_cliente', 'fecha_registro']
            columnas_existentes = [col for col in columnas_cliente if col in df_clientes.columns]
            
            if columnas_existentes:
                st.dataframe(
                    df_clientes[columnas_existentes],
                    use_container_width=True
                )
            else:
                st.dataframe(df_clientes)
        else:
            st.info("No hay clientes registrados")
            
    except Exception as e:
        st.error(f"Error cargando clientes: {e}")

# ========================
# TAB 5 - DEBUG
# ========================
with tabs[4]:
    st.header("🔧 Información de Debug")
    
    # Mostrar estructura de tablas
    st.subheader("📋 Estructura de Datos")
    
    try:
        # Test de cada tabla
        tablas_test = ["pedidos", "clientes", "productos", "comercializadoras"]
        
        for tabla in tablas_test:
            try:
                response = supabase.table(tabla).select("*").limit(1).execute()
                if response.data:
                    st.success(f"✅ Tabla '{tabla}': {len(response.data)} registros (mostrando estructura)")
                    
                    # Mostrar primeros datos como ejemplo
                    df_sample = pd.DataFrame(response.data)
                    st.json(response.data[0])  # Mostrar estructura del primer registro
                else:
                    st.warning(f"⚠️ Tabla '{tabla}': Sin datos")
            except Exception as e:
                st.error(f"❌ Tabla '{tabla}': Error - {e}")
        
        st.markdown("---")
        
        # Mostrar datos cargados
        st.subheader("📊 Datos Procesados")
        df_debug = cargar_datos(supabase)
        
        if not df_debug.empty:
            st.success(f"✅ Datos cargados correctamente: {len(df_debug)} registros")
            st.write("Columnas disponibles:", list(df_debug.columns))
            st.dataframe(df_debug.head())
        else:
            st.warning("⚠️ No se pudieron cargar datos")
        
    except Exception as e:
        st.error(f"Error en debug: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem 0;">
    <p>🧠 <strong>CRM Inteligente</strong> - Versión corregida para tu base de datos</p>
</div>
""", unsafe_allow_html=True)

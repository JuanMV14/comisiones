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
# Funciones para manejar datos de la tabla COMISIONES
# ========================

def cargar_datos(supabase: Client):
    """Carga datos únicamente de la tabla comisiones"""
    try:
        response = supabase.table("comisiones").select("*").execute()
        
        if not response.data:
            st.warning("No hay datos en la tabla 'comisiones'")
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        
        # Procesar fechas si existen
        fecha_cols = [col for col in df.columns if 'fecha' in col.lower()]
        for col in fecha_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Agregar campos calculados básicos si no existen
        if not df.empty:
            # Crear mes_factura si hay alguna columna de fecha
            if fecha_cols:
                primera_fecha = fecha_cols[0]
                df['mes_factura'] = df[primera_fecha].dt.to_period('M').astype(str)
            
            # Asegurar que existen campos básicos para análisis
            campos_numericos = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
            
            # Si no existe 'valor_neto', usar el primer campo numérico grande
            if 'valor_neto' not in df.columns and campos_numericos:
                campo_valor = max(campos_numericos, key=lambda x: df[x].sum())
                df['valor_neto'] = df[campo_valor]
            
            # Si no existe 'comision', calcular como porcentaje del valor
            if 'comision' not in df.columns and 'valor_neto' in df.columns:
                df['comision'] = df['valor_neto'] * 0.025  # 2.5% por defecto
            
            # Campo pagado por defecto
            if 'pagado' not in df.columns:
                df['pagado'] = False
        
        return df

    except Exception as e:
        st.error(f"Error cargando datos de comisiones: {e}")
        return pd.DataFrame()

def insertar_venta(supabase: Client, data: dict):
    """Inserta nueva entrada en tabla comisiones"""
    try:
        # Agregar timestamps
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("comisiones").insert(data).execute()
        return bool(result.data)
        
    except Exception as e:
        st.error(f"Error insertando en comisiones: {e}")
        return False

def actualizar_factura(supabase: Client, registro_id: int, updates: dict):
    """Actualiza registro en tabla comisiones"""
    try:
        updates['updated_at'] = datetime.now().isoformat()
        
        result = supabase.table("comisiones").update(updates).eq("id", registro_id).execute()
        return bool(result.data)
        
    except Exception as e:
        st.error(f"Error actualizando comisión: {e}")
        return False

# Importar funciones auxiliares (manteniendo tus funciones originales)
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
# Configuración de página
# ========================
st.set_page_config(
    page_title="CRM Comisiones", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="💰"
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
    st.title("💰 Sistema de Comisiones")
    st.markdown("---")
    
    # Test de conexión a base de datos
    st.subheader("🔧 Estado del Sistema")
    
    try:
        test_query = supabase.table("comisiones").select("id").limit(1).execute()
        st.success("✅ Conexión DB exitosa")
        
        # Contar registros totales
        count_query = supabase.table("comisiones").select("id", count="exact").execute()
        total_registros = count_query.count if hasattr(count_query, 'count') else len(test_query.data) if test_query.data else 0
        st.info(f"📊 Total registros: {total_registros}")
        
    except Exception as e:
        st.error(f"❌ Error de conexión: {str(e)}")
    
    st.markdown("---")
    
    # Filtros basados en datos reales
    st.subheader("📊 Filtros")
    
    df_tmp = cargar_datos(supabase)
    
    if not df_tmp.empty:
        # Filtro por mes si existe
        if 'mes_factura' in df_tmp.columns:
            meses_disponibles = ["Todos"] + sorted(df_tmp["mes_factura"].dropna().unique().tolist())
            mes_seleccionado = st.selectbox("📅 Filtrar por mes", meses_disponibles, index=0)
        else:
            mes_seleccionado = "Todos"
        
        # Filtro por cualquier campo de texto que pueda ser cliente
        campos_texto = [col for col in df_tmp.columns if df_tmp[col].dtype == 'object' and col not in ['id', 'created_at', 'updated_at']]
        if campos_texto:
            campo_cliente = st.selectbox("Campo para filtrar", ["Ninguno"] + campos_texto)
            if campo_cliente != "Ninguno":
                valores_unicos = ["Todos"] + sorted(df_tmp[campo_cliente].dropna().unique().tolist())
                valor_seleccionado = st.selectbox(f"Filtrar por {campo_cliente}", valores_unicos, index=0)
            else:
                valor_seleccionado = "Todos"
        else:
            campo_cliente = "Ninguno"
            valor_seleccionado = "Todos"
    else:
        st.warning("⚠️ No hay datos para generar filtros")
        mes_seleccionado = "Todos"
        campo_cliente = "Ninguno"
        valor_seleccionado = "Todos"

# ========================
# Layout principal con tabs
# ========================
st.title("💰 Sistema de Comisiones")

tabs = st.tabs([
    "📊 Dashboard",
    "💰 Comisiones", 
    "➕ Nueva Comisión",
    "🔧 Estructura de Datos"
])

# ========================
# TAB 1 - DASHBOARD
# ========================
with tabs[0]:
    st.header("📊 Dashboard de Comisiones")
    
    df = cargar_datos(supabase)
    
    if df.empty:
        st.warning("⚠️ No hay datos disponibles en la tabla comisiones")
        st.info("💡 Ve al tab 'Nueva Comisión' para agregar datos")
    else:
        # Aplicar filtros
        df_filtered = df.copy()
        
        if mes_seleccionado != "Todos" and 'mes_factura' in df.columns:
            df_filtered = df_filtered[df_filtered["mes_factura"] == mes_seleccionado]
        
        if campo_cliente != "Ninguno" and valor_seleccionado != "Todos":
            df_filtered = df_filtered[df_filtered[campo_cliente] == valor_seleccionado]
        
        # Identificar campos numéricos para métricas
        campos_numericos = [col for col in df_filtered.columns if df_filtered[col].dtype in ['int64', 'float64']]
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        if campos_numericos:
            # Usar los campos numéricos más grandes como métricas principales
            campo_principal = max(campos_numericos, key=lambda x: df_filtered[x].sum())
            total_principal = df_filtered[campo_principal].sum()
            
            with col1:
                st.metric(f"💵 Total {campo_principal}", format_currency(total_principal))
            
            if len(campos_numericos) > 1:
                campo_secundario = [col for col in campos_numericos if col != campo_principal][0]
                total_secundario = df_filtered[campo_secundario].sum()
                with col2:
                    st.metric(f"💰 Total {campo_secundario}", format_currency(total_secundario))
            
            with col3:
                st.metric("📋 Total Registros", len(df_filtered))
            
            with col4:
                promedio = df_filtered[campo_principal].mean()
                st.metric(f"📈 Promedio {campo_principal}", format_currency(promedio))
        
        st.markdown("---")
        
        # Mostrar tabla de datos completa
        st.subheader(f"📋 Registros de Comisiones ({len(df_filtered)} total)")
        
        # Configurar columnas para mejor visualización
        column_config = {}
        for col in df_filtered.columns:
            if df_filtered[col].dtype in ['int64', 'float64']:
                column_config[col] = st.column_config.NumberColumn(
                    col,
                    format="$%.0f" if df_filtered[col].max() > 1000 else "%.2f"
                )
            elif 'fecha' in col.lower():
                column_config[col] = st.column_config.DatetimeColumn(col)
        
        st.dataframe(
            df_filtered,
            use_container_width=True,
            column_config=column_config
        )
        
        # Mostrar estadísticas adicionales
        if not df_filtered.empty:
            st.subheader("📊 Estadísticas")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Resumen numérico:**")
                st.dataframe(df_filtered.describe())
            
            with col2:
                st.write("**Información general:**")
                st.write(f"- Total de registros: {len(df_filtered)}")
                st.write(f"- Columnas disponibles: {len(df_filtered.columns)}")
                st.write(f"- Registros con datos faltantes: {df_filtered.isnull().sum().sum()}")

# ========================
# TAB 2 - COMISIONES DETALLADAS
# ========================
with tabs[1]:
    st.header("💰 Gestión Detallada de Comisiones")
    
    df = cargar_datos(supabase)
    
    if not df.empty:
        # Filtros específicos
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por campo numérico si existe
            campos_numericos = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
            if campos_numericos:
                campo_numerico = st.selectbox("Campo numérico", campos_numericos)
                valor_min = st.number_input(f"Valor mínimo {campo_numerico}", min_value=0.0, value=0.0)
            else:
                campo_numerico = None
                valor_min = 0
        
        with col2:
            # Filtro de texto general
            busqueda = st.text_input("Buscar en todos los campos")
        
        with col3:
            if st.button("📥 Exportar a CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="⬇️ Descargar CSV",
                    data=csv,
                    file_name=f"comisiones_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        # Aplicar filtros
        df_comisiones = df.copy()
        
        if campo_numerico and valor_min > 0:
            df_comisiones = df_comisiones[df_comisiones[campo_numerico] >= valor_min]
        
        if busqueda:
            # Buscar en todas las columnas de texto
            mask = False
            for col in df_comisiones.columns:
                if df_comisiones[col].dtype == 'object':
                    mask |= df_comisiones[col].astype(str).str.contains(busqueda, case=False, na=False)
            df_comisiones = df_comisiones[mask]
        
        # Mostrar resultados
        if not df_comisiones.empty:
            st.subheader(f"📊 {len(df_comisiones)} registros encontrados")
            
            # Mostrar cada registro como una tarjeta
            for _, registro in df_comisiones.head(20).iterrows():  # Limitar a 20 para rendimiento
                st.markdown(f"""
                <div class="factura-card">
                    <h3 style="margin: 0 0 1rem 0;">📄 Registro ID: {registro.get('id', 'N/A')}</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                """, unsafe_allow_html=True)
                
                # Mostrar todos los campos del registro
                for col, valor in registro.items():
                    if pd.notna(valor) and col not in ['id']:  # Excluir ID ya mostrado
                        valor_formateado = format_currency(valor) if isinstance(valor, (int, float)) and valor > 1000 else str(valor)
                        st.markdown(f"<div><strong>{col}:</strong> {valor_formateado}</div>", unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
                
                # Botones de acción
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"✏️ Editar", key=f"edit_{registro.get('id', 0)}"):
                        st.session_state[f'editing_{registro.get("id")}'] = True
                
                with col2:
                    if st.button(f"🗑️ Eliminar", key=f"delete_{registro.get('id', 0)}"):
                        if st.confirm(f"¿Eliminar registro {registro.get('id')}?"):
                            supabase.table("comisiones").delete().eq("id", registro.get('id')).execute()
                            st.rerun()
                
                # Formulario de edición inline
                if st.session_state.get(f'editing_{registro.get("id")}', False):
                    with st.form(f"edit_form_{registro.get('id')}"):
                        st.write("**Editar registro:**")
                        
                        updates = {}
                        for col, valor in registro.items():
                            if col not in ['id', 'created_at', 'updated_at']:
                                if isinstance(valor, (int, float)):
                                    updates[col] = st.number_input(f"{col}", value=float(valor), key=f"edit_{col}_{registro.get('id')}")
                                else:
                                    updates[col] = st.text_input(f"{col}", value=str(valor), key=f"edit_{col}_{registro.get('id')}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("💾 Guardar"):
                                if actualizar_factura(supabase, registro.get('id'), updates):
                                    st.success("✅ Registro actualizado")
                                    st.session_state[f'editing_{registro.get("id")}'] = False
                                    st.rerun()
                        with col2:
                            if st.form_submit_button("❌ Cancelar"):
                                st.session_state[f'editing_{registro.get("id")}'] = False
                                st.rerun()
        else:
            st.info("No hay registros que coincidan con los filtros aplicados")
    else:
        st.warning("No hay datos de comisiones disponibles")

# ========================
# TAB 3 - NUEVA COMISIÓN
# ========================
with tabs[2]:
    st.header("➕ Registrar Nueva Comisión")
    
    # Primero, mostrar la estructura actual para guiar al usuario
    df_muestra = cargar_datos(supabase)
    if not df_muestra.empty:
        st.subheader("📋 Campos disponibles en tu tabla:")
        cols_info = []
        for col in df_muestra.columns:
            tipo = str(df_muestra[col].dtype)
            ejemplo = df_muestra[col].dropna().iloc[0] if not df_muestra[col].dropna().empty else "N/A"
            cols_info.append({"Campo": col, "Tipo": tipo, "Ejemplo": str(ejemplo)})
        
        st.dataframe(pd.DataFrame(cols_info))
    
    st.markdown("---")
    
    with st.form("nueva_comision_form"):
        st.subheader("✍️ Datos de la nueva comisión")
        
        # Campos dinámicos basados en la estructura real
        if not df_muestra.empty:
            datos = {}
            
            # Crear campos de entrada para cada columna (excepto las automáticas)
            cols_auto = ['id', 'created_at', 'updated_at']
            
            col1, col2 = st.columns(2)
            
            for i, col in enumerate([c for c in df_muestra.columns if c not in cols_auto]):
                with col1 if i % 2 == 0 else col2:
                    if df_muestra[col].dtype in ['int64', 'float64']:
                        datos[col] = st.number_input(f"{col}", value=0.0, step=0.01)
                    elif 'fecha' in col.lower():
                        datos[col] = st.date_input(f"{col}", value=date.today())
                    elif df_muestra[col].dtype == 'bool':
                        datos[col] = st.checkbox(f"{col}")
                    else:
                        datos[col] = st.text_input(f"{col}")
        else:
            # Si no hay datos previos, campos básicos
            col1, col2 = st.columns(2)
            with col1:
                datos = {
                    "cliente": st.text_input("Cliente"),
                    "valor": st.number_input("Valor", min_value=0.0, step=1000.0),
                    "comision": st.number_input("Comisión", min_value=0.0, step=100.0)
                }
            with col2:
                datos.update({
                    "fecha": st.date_input("Fecha", value=date.today()),
                    "porcentaje": st.number_input("Porcentaje (%)", min_value=0.0, max_value=100.0, step=0.1),
                    "pagado": st.checkbox("Pagado")
                })
        
        submitted = st.form_submit_button("💾 Registrar Comisión", type="primary")
        
        if submitted:
            # Convertir fechas a string
            for key, value in datos.items():
                if isinstance(value, date):
                    datos[key] = value.isoformat()
            
            if any(datos.values()):  # Si al menos un campo tiene valor
                if insertar_venta(supabase, datos):
                    st.success("✅ Comisión registrada correctamente")
                    st.rerun()
                else:
                    st.error("❌ Error al registrar la comisión")
            else:
                st.error("⚠️ Por favor completa al menos un campo")

# ========================
# TAB 4 - ESTRUCTURA DE DATOS
# ========================
with tabs[3]:
    st.header("🔧 Análisis de Estructura de Datos")
    
    # Información sobre la tabla comisiones
    st.subheader("📋 Información de la tabla 'comisiones'")
    
    try:
        # Obtener muestra de datos
        sample_response = supabase.table("comisiones").select("*").limit(5).execute()
        
        if sample_response.data:
            df_sample = pd.DataFrame(sample_response.data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Estructura de la tabla:**")
                estructura = []
                for col in df_sample.columns:
                    tipo = str(df_sample[col].dtype)
                    nulos = df_sample[col].isnull().sum()
                    estructura.append({
                        "Columna": col,
                        "Tipo": tipo,
                        "Valores nulos": f"{nulos}/{len(df_sample)}"
                    })
                
                st.dataframe(pd.DataFrame(estructura))
            
            with col2:
                st.write("**Muestra de datos (primeros 5 registros):**")
                st.dataframe(df_sample)
            
            st.markdown("---")
            
            # Estadísticas generales
            st.subheader("📊 Estadísticas de la tabla completa")
            
            df_completo = cargar_datos(supabase)
            if not df_completo.empty:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total registros", len(df_completo))
                
                with col2:
                    st.metric("Total columnas", len(df_completo.columns))
                
                with col3:
                    valores_faltantes = df_completo.isnull().sum().sum()
                    st.metric("Valores faltantes", valores_faltantes)
                
                # Mostrar distribución de datos
                st.write("**Distribución por columnas:**")
                for col in df_completo.columns:
                    if df_completo[col].dtype in ['int64', 'float64']:
                        st.write(f"- **{col}**: Min: {df_completo[col].min():.2f}, Max: {df_completo[col].max():.2f}, Promedio: {df_completo[col].mean():.2f}")
                    elif df_completo[col].dtype == 'object':
                        valores_unicos = df_completo[col].nunique()
                        st.write(f"- **{col}**: {valores_unicos} valores únicos")
        
        else:
            st.warning("No hay datos en la tabla comisiones")
            
            # Sugerir estructura básica
            st.subheader("💡 Estructura sugerida para tabla de comisiones")
            estructura_sugerida = [
                {"Campo": "id", "Tipo": "SERIAL PRIMARY KEY", "Descripción": "ID único automático"},
                {"Campo": "cliente", "Tipo": "TEXT", "Descripción": "Nombre del cliente"},
                {"Campo": "valor", "Tipo": "NUMERIC", "Descripción": "Valor total de la venta"},
                {"Campo": "comision", "Tipo": "NUMERIC", "Descripción": "Comisión calculada"},
                {"Campo": "porcentaje", "Tipo": "NUMERIC", "Descripción": "Porcentaje de comisión"},
                {"Campo": "fecha", "Tipo": "DATE", "Descripción": "Fecha de la venta"},
                {"Campo": "pagado", "Tipo": "BOOLEAN", "Descripción": "Si está pagado o no"},
                {"Campo": "created_at", "Tipo": "TIMESTAMP", "Descripción": "Fecha de creación"},
                {"Campo": "updated_at", "Tipo": "TIMESTAMP", "Descripción": "Fecha de actualización"}
            ]
            
            st.dataframe(pd.DataFrame(estructura_sugerida))
    
    except Exception as e:
        st.error(f"Error analizando estructura: {e}")
    
    st.markdown("---")
    
    # Verificar otras tablas disponibles
    st.subheader("🔍 Otras tablas detectadas")
    tablas_detectadas = ["clientes", "productos"]  # Las que vi en tu imagen
    
    for tabla in tablas_detectadas:
        try:
            test = supabase.table(tabla).select("*").limit(1).execute()
            if test.data:
                st.success(f"✅ Tabla '{tabla}' encontrada - {len(test.data)} registro(s) de muestra")
                # Mostrar estructura básica
                if test.data:
                    columnas = list(test.data[0].keys())
                    st.write(f"Columnas: {', '.join(columnas)}")
            else:
                st.info(f"📋 Tabla '{tabla}' existe but vacía")
        except Exception as e:
            st.warning(f"⚠️ Tabla '{tabla}' no accesible: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 1rem 0;">
    <p>💰 <strong>Sistema de Comisiones</strong> - Trabajando únicamente con tu tabla 'comisiones'</p>
</div>
""", unsafe_allow_html=True)

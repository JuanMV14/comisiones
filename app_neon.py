#!/usr/bin/env python3
"""
Versión de la aplicación adaptada para usar Neon en lugar de Supabase
Autor: Asistente IA
Fecha: 2024
"""

import os
import psycopg2
from datetime import date, timedelta, datetime
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
from psycopg2.extras import RealDictCursor

# ========================
# CONFIGURACIÓN INICIAL
# ========================
load_dotenv()

# Configuración de Neon
NEON_HOST = os.getenv("NEON_HOST")
NEON_DATABASE = os.getenv("NEON_DATABASE")
NEON_USER = os.getenv("NEON_USER")
NEON_PASSWORD = os.getenv("NEON_PASSWORD")

if not all([NEON_HOST, NEON_DATABASE, NEON_USER, NEON_PASSWORD]):
    st.error("Faltan las variables de entorno de Neon (NEON_HOST, NEON_DATABASE, NEON_USER, NEON_PASSWORD).")
    st.stop()

# Función para obtener conexión a Neon
def get_neon_connection():
    """Obtiene una conexión a la base de datos Neon"""
    try:
        conn = psycopg2.connect(
            host=NEON_HOST,
            database=NEON_DATABASE,
            user=NEON_USER,
            password=NEON_PASSWORD,
            sslmode='require'
        )
        return conn
    except Exception as e:
        st.error(f"Error conectando a Neon: {e}")
        return None

st.set_page_config(
    page_title="CRM Inteligente - Neon",
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
    """Carga datos de la tabla comisiones desde Neon"""
    try:
        conn = get_neon_connection()
        if not conn:
            return pd.DataFrame()
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM comisiones ORDER BY created_at DESC")
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
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
    """Inserta una nueva venta en Neon"""
    try:
        conn = get_neon_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Preparar datos
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        insert_sql = """
        INSERT INTO comisiones (
            pedido, cliente, factura, valor, valor_neto, iva, base_comision,
            comision, porcentaje, fecha_factura, fecha_pago_est, fecha_pago_max,
            cliente_propio, descuento_pie_factura, descuento_adicional, condicion_especial,
            pagado, created_at, updated_at
        ) VALUES (
            %(pedido)s, %(cliente)s, %(factura)s, %(valor)s, %(valor_neto)s, %(iva)s, %(base_comision)s,
            %(comision)s, %(porcentaje)s, %(fecha_factura)s, %(fecha_pago_est)s, %(fecha_pago_max)s,
            %(cliente_propio)s, %(descuento_pie_factura)s, %(descuento_adicional)s, %(condicion_especial)s,
            %(pagado)s, %(created_at)s, %(updated_at)s
        )
        """
        
        cursor.execute(insert_sql, data)
        conn.commit()
        cursor.close()
        conn.close()
        
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"Error insertando venta: {e}")
        return False

def actualizar_factura(factura_id: int, updates: dict):
    """Actualiza una factura en Neon"""
    try:
        if not factura_id or factura_id == 0:
            st.error("ID de factura inválido")
            return False
        
        conn = get_neon_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Verificar existencia de la factura
        cursor.execute("SELECT id FROM comisiones WHERE id = %s", (factura_id,))
        if not cursor.fetchone():
            st.error("Factura no encontrada")
            cursor.close()
            conn.close()
            return False

        # Siempre agregar updated_at
        updates["updated_at"] = datetime.now().isoformat()
        
        # Construir query de actualización
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            values.append(value)
        
        values.append(factura_id)
        
        update_sql = f"UPDATE comisiones SET {', '.join(set_clauses)} WHERE id = %s"
        
        cursor.execute(update_sql, values)
        conn.commit()
        cursor.close()
        conn.close()
        
        st.cache_data.clear()
        return True
        
    except Exception as e:
        st.error(f"Error actualizando factura: {e}")
        return False

def obtener_meta_mes_actual():
    """Obtiene la meta del mes actual desde Neon"""
    try:
        conn = get_neon_connection()
        if not conn:
            return {
                "mes": date.today().strftime("%Y-%m"), 
                "meta_ventas": 10000000, 
                "meta_clientes_nuevos": 5
            }
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        mes_actual = date.today().strftime("%Y-%m")
        
        cursor.execute("SELECT * FROM metas_mensuales WHERE mes = %s", (mes_actual,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return dict(result)
        else:
            # Crear meta por defecto
            meta_default = {
                "mes": mes_actual,
                "meta_ventas": 10000000,
                "meta_clientes_nuevos": 5,
                "ventas_actuales": 0,
                "clientes_nuevos_actuales": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Insertar meta por defecto
            conn = get_neon_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO metas_mensuales (mes, meta_ventas, meta_clientes_nuevos, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (mes_actual, 10000000, 5, datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
                cursor.close()
                conn.close()
            
            return meta_default
            
    except Exception as e:
        return {
            "mes": date.today().strftime("%Y-%m"), 
            "meta_ventas": 10000000, 
            "meta_clientes_nuevos": 5
        }

def actualizar_meta(mes: str, meta_ventas: float, meta_clientes: int):
    """Actualiza meta mensual en Neon"""
    try:
        conn = get_neon_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute("SELECT id FROM metas_mensuales WHERE mes = %s", (mes,))
        exists = cursor.fetchone()
        
        if exists:
            # Actualizar
            cursor.execute("""
                UPDATE metas_mensuales 
                SET meta_ventas = %s, meta_clientes_nuevos = %s, updated_at = %s
                WHERE mes = %s
            """, (meta_ventas, meta_clientes, datetime.now().isoformat(), mes))
        else:
            # Insertar
            cursor.execute("""
                INSERT INTO metas_mensuales (mes, meta_ventas, meta_clientes_nuevos, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (mes, meta_ventas, meta_clientes, datetime.now().isoformat(), datetime.now().isoformat()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        st.error(f"Error actualizando meta: {e}")
        return False

# ========================
# FUNCIONES DE DEVOLUCIONES
# ========================
def cargar_devoluciones():
    """Carga datos de devoluciones desde Neon"""
    try:
        conn = get_neon_connection()
        if not conn:
            return pd.DataFrame()
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT d.*, c.pedido, c.cliente, c.factura, c.valor, c.comision
            FROM devoluciones d
            LEFT JOIN comisiones c ON d.factura_id = c.id
            ORDER BY d.created_at DESC
        """)
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Procesar tipos de datos
        df['valor_devuelto'] = pd.to_numeric(df['valor_devuelto'], errors='coerce').fillna(0)
        df['afecta_comision'] = df['afecta_comision'].fillna(True).astype(bool)
        
        # Convertir fechas
        for col in ['fecha_devolucion', 'created_at']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Campos string
        for col in ['motivo']:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)
        
        return df
        
    except Exception as e:
        st.error(f"Error cargando devoluciones: {str(e)}")
        return pd.DataFrame()

def insertar_devolucion(data: dict):
    """Inserta una nueva devolución en Neon"""
    try:
        conn = get_neon_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        data["created_at"] = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO devoluciones (factura_id, valor_devuelto, motivo, fecha_devolucion, afecta_comision, created_at)
            VALUES (%(factura_id)s, %(valor_devuelto)s, %(motivo)s, %(fecha_devolucion)s, %(afecta_comision)s, %(created_at)s)
        """, data)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Si la devolución afecta la comisión, actualizar la factura
        if data.get("afecta_comision", True):
            actualizar_comision_por_devolucion(data["factura_id"], data["valor_devuelto"])
        
        return True
        
    except Exception as e:
        st.error(f"Error insertando devolución: {e}")
        return False

def actualizar_comision_por_devolucion(factura_id: int, valor_devuelto: float):
    """Actualiza la comisión de una factura considerando devoluciones"""
    try:
        conn = get_neon_connection()
        if not conn:
            return False
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Obtener datos actuales de la factura
        cursor.execute("SELECT * FROM comisiones WHERE id = %s", (factura_id,))
        factura = cursor.fetchone()
        
        if not factura:
            cursor.close()
            conn.close()
            return False
        
        # Obtener total de devoluciones que afectan comisión para esta factura
        cursor.execute("""
            SELECT SUM(valor_devuelto) as total_devuelto 
            FROM devoluciones 
            WHERE factura_id = %s AND afecta_comision = TRUE
        """, (factura_id,))
        
        result = cursor.fetchone()
        total_devuelto = result['total_devuelto'] if result['total_devuelto'] else 0
        
        # Recalcular valores considerando devoluciones
        valor_original = factura['valor'] or 0
        valor_neto_original = factura['valor_neto'] or 0
        porcentaje = factura['porcentaje'] or 0
        
        # Nuevo valor después de devoluciones
        valor_neto_efectivo = valor_neto_original - (total_devuelto / 1.19)
        
        # Recalcular base comisión
        if factura.get('descuento_pie_factura', False):
            base_comision_efectiva = valor_neto_efectivo
        else:
            base_comision_efectiva = valor_neto_efectivo * 0.85
        
        # Nueva comisión
        comision_efectiva = base_comision_efectiva * (porcentaje / 100)
        
        # Actualizar factura
        cursor.execute("""
            UPDATE comisiones 
            SET valor_devuelto = %s, comision_ajustada = %s, updated_at = %s
            WHERE id = %s
        """, (total_devuelto, comision_efectiva, datetime.now().isoformat(), factura_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        st.error(f"Error actualizando comisión por devolución: {e}")
        return False

def obtener_facturas_para_devolucion():
    """Obtiene facturas disponibles para devoluciones desde Neon"""
    try:
        conn = get_neon_connection()
        if not conn:
            return pd.DataFrame()
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, pedido, cliente, factura, valor, comision, fecha_factura
            FROM comisiones 
            ORDER BY fecha_factura DESC
        """)
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if data:
            df = pd.DataFrame(data)
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
            return df
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"Error obteniendo facturas: {e}")
        return pd.DataFrame()

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
        
        # Clientes sin actividad reciente
        if len(recomendaciones) < 3:
            df['dias_desde_factura'] = (hoy - df['fecha_factura']).dt.days
            
            clientes_inactivos = df.groupby('cliente').agg({
                'dias_desde_factura': 'min',
                'valor': 'mean',
                'comision': 'mean'
            }).reset_index()
            
            oportunidades = clientes_inactivos[
                (clientes_inactivos['dias_desde_factura'] >= 30) & 
                (clientes_inactivos['dias_desde_factura'] <= 90)
            ].nlargest(1, 'valor')
            
            for _, cliente in oportunidades.iterrows():
                recomendaciones.append({
                    'cliente': cliente['cliente'],
                    'accion': 'Reactivar cliente',
                    'producto': f"Oferta personalizada (${cliente['valor']*0.8:,.0f})",
                    'razon': f"Sin compras {int(cliente['dias_desde_factura'])} días - Cliente valioso",
                    'probabilidad': max(30, 90 - int(cliente['dias_desde_factura'])),
                    'impacto_comision': cliente['comision'],
                    'prioridad': 'media'
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
# APLICACIÓN PRINCIPAL (Simplificada)
# ========================
def main():
    """Aplicación principal simplificada para demostración"""
    st.title("🧠 CRM Inteligente - Neon")
    st.info("🚀 Versión migrada a Neon - Base de datos optimizada")
    
    # Verificar conexión
    conn = get_neon_connection()
    if conn:
        st.success("✅ Conectado a Neon exitosamente")
        conn.close()
    else:
        st.error("❌ Error de conexión a Neon")
        return
    
    # Tabs principales
    tabs = st.tabs([
        "Dashboard",
        "Comisiones", 
        "Nueva Venta",
        "Devoluciones"
    ])
    
    # TAB 1 - DASHBOARD
    with tabs[0]:
        st.header("Dashboard Ejecutivo")
        
        df = cargar_datos()
        
        if not df.empty:
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Facturas", len(df))
            
            with col2:
                st.metric("Ventas Totales", format_currency(df["valor"].sum()))
            
            with col3:
                st.metric("Comisiones Totales", format_currency(df["comision"].sum()))
            
            with col4:
                pendientes = len(df[df["pagado"] == False])
                st.metric("Facturas Pendientes", pendientes)
            
            # Progreso de meta
            meta_actual = obtener_meta_mes_actual()
            mes_actual_str = date.today().strftime("%Y-%m")
            ventas_mes = df[
                (df["mes_factura"] == mes_actual_str) & 
                (df["cliente_propio"] == True)
            ]["valor_neto"].sum() if not df.empty else 0
            
            progreso = (ventas_mes / meta_actual["meta_ventas"] * 100) if meta_actual["meta_ventas"] > 0 else 0
            
            st.markdown("### Progreso Meta Mensual")
            st.progress(progreso / 100)
            st.write(f"**{progreso:.1f}%** completado - {format_currency(ventas_mes)} de {format_currency(meta_actual['meta_ventas'])}")
            
        else:
            st.warning("No hay datos disponibles")
    
    # TAB 2 - COMISIONES
    with tabs[1]:
        st.header("Gestión de Comisiones")
        
        df = cargar_datos()
        
        if not df.empty:
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                estado_filter = st.selectbox("Estado", ["Todos", "Pendientes", "Pagadas"])
            with col2:
                cliente_filter = st.text_input("Buscar cliente")
            
            # Aplicar filtros
            df_filtrado = df.copy()
            if estado_filter == "Pendientes":
                df_filtrado = df_filtrado[df_filtrado["pagado"] == False]
            elif estado_filter == "Pagadas":
                df_filtrado = df_filtrado[df_filtrado["pagado"] == True]
            
            if cliente_filter:
                df_filtrado = df_filtrado[df_filtrado["cliente"].str.contains(cliente_filter, case=False, na=False)]
            
            # Mostrar facturas
            for _, factura in df_filtrado.head(10).iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**{factura['cliente']}**")
                        st.write(f"Pedido: {factura['pedido']}")
                    
                    with col2:
                        st.write(f"Valor: {format_currency(factura['valor'])}")
                        st.write(f"Comisión: {format_currency(factura['comision'])}")
                    
                    with col3:
                        estado = "✅ Pagada" if factura['pagado'] else "⏳ Pendiente"
                        st.write(estado)
        else:
            st.warning("No hay comisiones registradas")
    
    # TAB 3 - NUEVA VENTA
    with tabs[2]:
        st.header("Registrar Nueva Venta")
        
        with st.form("nueva_venta_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                pedido = st.text_input("Número de Pedido *")
                cliente = st.text_input("Cliente *")
                valor_total = st.number_input("Valor Total (con IVA) *", min_value=0.0)
            
            with col2:
                fecha_factura = st.date_input("Fecha de Factura *", value=date.today())
                cliente_propio = st.checkbox("Cliente Propio")
                descuento_adicional = st.number_input("Descuento Adicional (%)", min_value=0.0, max_value=100.0)
            
            # Preview de comisión
            if valor_total > 0:
                calc = calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, False)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Valor Neto", format_currency(calc['valor_neto']))
                with col2:
                    st.metric("Base Comisión", format_currency(calc['base_comision']))
                with col3:
                    st.metric("Comisión Final", format_currency(calc['comision']))
            
            submit = st.form_submit_button("Registrar Venta", type="primary")
            
            if submit:
                if pedido and cliente and valor_total > 0:
                    try:
                        # Calcular fechas
                        dias_pago = 35
                        dias_max = 45
                        fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
                        fecha_pago_max = fecha_factura + timedelta(days=dias_max)
                        
                        # Calcular comisión
                        calc = calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, False)
                        
                        # Preparar datos
                        data = {
                            "pedido": pedido,
                            "cliente": cliente,
                            "factura": f"FAC-{pedido}",
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
                            "descuento_pie_factura": False,
                            "descuento_adicional": float(descuento_adicional),
                            "condicion_especial": False,
                            "pagado": False
                        }
                        
                        if insertar_venta(data):
                            st.success("¡Venta registrada correctamente!")
                            st.success(f"Comisión calculada: {format_currency(calc['comision'])}")
                        else:
                            st.error("Error al registrar la venta")
                            
                    except Exception as e:
                        st.error(f"Error procesando la venta: {str(e)}")
                else:
                    st.error("Por favor completa todos los campos marcados con *")
    
    # TAB 4 - DEVOLUCIONES
    with tabs[3]:
        st.header("Gestión de Devoluciones")
        
        df_devoluciones = cargar_devoluciones()
        
        if not df_devoluciones.empty:
            st.markdown("### Devoluciones Registradas")
            
            for _, devolucion in df_devoluciones.head(5).iterrows():
                with st.container(border=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Cliente:** {devolucion.get('cliente', 'N/A')}")
                        st.write(f"**Pedido:** {devolucion.get('pedido', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Valor Devuelto:** {format_currency(devolucion['valor_devuelto'])}")
                        st.write(f"**Fecha:** {devolucion['fecha_devolucion'].strftime('%d/%m/%Y') if pd.notna(devolucion['fecha_devolucion']) else 'N/A'}")
                    
                    with col3:
                        afecta = "❌ AFECTA COMISIÓN" if devolucion.get('afecta_comision', True) else "✅ NO AFECTA"
                        st.write(afecta)
        else:
            st.info("No hay devoluciones registradas")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.info("Por favor, recarga la página o contacta al administrador.")

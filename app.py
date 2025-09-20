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

def agregar_campos_faltantes(df):
    """Agrega campos que podrían no existir"""
    campos_nuevos = {
        'valor_neto': lambda row: row.get('valor', 0) / 1.19 if row.get('valor') else 0,
        'iva': lambda row: row.get('valor', 0) - (row.get('valor', 0) / 1.19) if row.get('valor') else 0,
        'base_comision': lambda row: (row.get('valor', 0) / 1.19) * 0.85 if row.get('valor') else 0,
    }
    
    for campo, default in campos_nuevos.items():
        if campo not in df.columns:
            if callable(default):
                df[campo] = df.apply(default, axis=1)
            else:
                df[campo] = default
    
    return df

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

def actualizar_factura(factura_id: int, updates: dict):
    """Actualiza una factura"""
    try:
        if not factura_id or factura_id == 0:
            st.error("ID de factura inválido")
            return False
            
        factura_id = int(factura_id)
        
        # Verificar existencia de la factura
        check_response = supabase.table("comisiones").select("id").eq("id", factura_id).execute()
        if not check_response.data:
            st.error("Factura no encontrada")
            return False

        # Siempre agregar updated_at
        updates["updated_at"] = datetime.now().isoformat()
        
        # Ejecutar actualización
        result = supabase.table("comisiones").update(updates).eq("id", factura_id).execute()
        
        if result.data:
            st.cache_data.clear()
            return True
        else:
            st.error("No se pudo actualizar la factura")
            return False
        
    except Exception as e:
        st.error(f"Error actualizando factura: {e}")
        return False

def subir_comprobante(file, factura_id: int):
    """Sube comprobante de pago"""
    try:
        if file is None:
            return None
            
        file_content = file.getvalue()
        original_extension = file.name.split('.')[-1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"comprobante_{factura_id}_{timestamp}.{original_extension}"
        
        result = supabase.storage.from_("comprobantes").upload(
            new_filename,
            file_content,
            file_options={
                "content-type": f"application/{original_extension}",
                "upsert": "true"
            }
        )
        
        if result:
            public_url = supabase.storage.from_("comprobantes").get_public_url(new_filename)
            return public_url
        return None
        
    except Exception as e:
        st.error(f"Error subiendo comprobante: {e}")
        return None

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
# FUNCIONES DE DEVOLUCIONES
# ========================
def cargar_devoluciones():
    """Carga datos de devoluciones"""
    try:
        response = supabase.table("devoluciones").select("""
            *,
            comisiones!devoluciones_factura_id_fkey(
                pedido,
                cliente,
                factura,
                valor,
                comision
            )
        """).execute()
        
        if not response.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(response.data)
        
        # Expandir datos de la factura relacionada
        if 'comisiones' in df.columns:
            factura_data = pd.json_normalize(df['comisiones'])
            factura_data.columns = ['factura_' + col for col in factura_data.columns]
            df = pd.concat([df.drop('comisiones', axis=1), factura_data], axis=1)
        
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
    """Inserta una nueva devolución"""
    try:
        data["created_at"] = datetime.now().isoformat()
        result = supabase.table("devoluciones").insert(data).execute()
        
        if result.data:
            # Si la devolución afecta la comisión, actualizar la factura
            if data.get("afecta_comision", True):
                actualizar_comision_por_devolucion(data["factura_id"], data["valor_devuelto"])
            
            return True
        return False
        
    except Exception as e:
        st.error(f"Error insertando devolución: {e}")
        return False

def actualizar_comision_por_devolucion(factura_id: int, valor_devuelto: float):
    """Actualiza la comisión de una factura considerando devoluciones"""
    try:
        # Obtener datos actuales de la factura
        factura_response = supabase.table("comisiones").select("*").eq("id", factura_id).execute()
        if not factura_response.data:
            return False
        
        factura = factura_response.data[0]
        
        # Obtener total de devoluciones que afectan comisión para esta factura
        devoluciones_response = supabase.table("devoluciones").select("valor_devuelto").eq("factura_id", factura_id).eq("afecta_comision", True).execute()
        
        total_devuelto = sum([d['valor_devuelto'] for d in devoluciones_response.data]) if devoluciones_response.data else 0
        
        # Recalcular valores considerando devoluciones
        valor_original = factura.get('valor', 0)
        valor_neto_original = factura.get('valor_neto', 0)
        porcentaje = factura.get('porcentaje', 0)
        
        # Nuevo valor después de devoluciones
        valor_neto_efectivo = valor_neto_original - (total_devuelto / 1.19)
        
        # Recalcular base comisión
        if factura.get('descuento_pie_factura', False):
            base_comision_efectiva = valor_neto_efectivo
        else:
            base_comision_efectiva = valor_neto_efectivo * 0.85
        
        # Nueva comisión
        comision_efectiva = base_comision_efectiva * (porcentaje / 100)
        
        updates = {
            "valor_devuelto": total_devuelto,
            "comision_ajustada": comision_efectiva,
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("comisiones").update(updates).eq("id", factura_id).execute()
        return True if result.data else False
        
    except Exception as e:
        st.error(f"Error actualizando comisión por devolución: {e}")
        return False

def obtener_facturas_para_devolucion():
    """Obtiene facturas disponibles para devoluciones"""
    try:
        response = supabase.table("comisiones").select(
            "id, pedido, cliente, factura, valor, comision, fecha_factura"
        ).order("fecha_factura", desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
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
# FUNCIONES DE UI
# ========================
def render_factura_card(factura, index):
    """Renderiza una card de factura"""
    estado_pagado = factura.get("pagado", False)
    
    if estado_pagado:
        estado_badge = "PAGADA"
        estado_color = "success"
        estado_icon = "✅"
    else:
        dias_venc = factura.get("dias_vencimiento")
        if dias_venc is not None and dias_venc < 0:
            estado_badge = f"VENCIDA ({abs(dias_venc)} días)"
            estado_color = "error"
            estado_icon = "🚨"
        elif dias_venc is not None and dias_venc <= 5:
            estado_badge = f"POR VENCER ({dias_venc} días)"
            estado_color = "warning"
            estado_icon = "⚠️"
        else:
            estado_badge = "PENDIENTE"
            estado_color = "info"
            estado_icon = "⏳"
    
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"## 🧾 {factura.get('pedido', 'N/A')} - {factura.get('cliente', 'N/A')}")
            st.caption(f"Factura: {factura.get('factura', 'N/A')}")
        
        with col2:
            if estado_color == "error":
                st.error(f"{estado_icon} {estado_badge}")
            elif estado_color == "success":
                st.success(f"{estado_icon} {estado_badge}")
            elif estado_color == "warning":
                st.warning(f"{estado_icon} {estado_badge}")
            else:
                st.info(f"{estado_icon} {estado_badge}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Valor Neto", format_currency(factura.get('valor_neto', 0)))
        with col2:
            st.metric("Base Comisión", format_currency(factura.get('base_comision', 0)))
        with col3:
            st.metric("Comisión", format_currency(factura.get('comision', 0)))
        with col4:
            fecha_factura = factura.get('fecha_factura')
            if pd.notna(fecha_factura):
                fecha_str = pd.to_datetime(fecha_factura).strftime('%d/%m/%Y')
            else:
                fecha_str = "N/A"
            st.metric("Fecha", fecha_str)

        # Mostrar información adicional solo para facturas NO PAGADAS
        if not estado_pagado:
            dias_venc = factura.get('dias_vencimiento')
            if dias_venc is not None:
                if dias_venc < 0:
                    st.error(f"⚠️ Vencida hace {abs(dias_venc)} días")
                elif dias_venc <= 5:
                    st.warning(f"⏰ Vence en {dias_venc} días")
        else:
            # Para facturas pagadas, mostrar información del pago
            fecha_pago = factura.get('fecha_pago_real')
            if pd.notna(fecha_pago):
                st.success(f"💰 Pagada el {pd.to_datetime(fecha_pago).strftime('%d/%m/%Y')}")

def mostrar_modal_editar(factura):
    """Modal de edición de factura"""
    factura_id = factura.get('id')
    if not factura_id:
        st.error("ERROR: Factura sin ID")
        return
    
    form_key = f"edit_form_{factura_id}"
    
    with st.form(form_key, clear_on_submit=False):
        st.markdown(f"### ✏️ Editar Factura - {factura.get('pedido', 'N/A')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nuevo_pedido = st.text_input("Pedido", value=str(factura.get('pedido', '')), key=f"edit_pedido_{factura_id}")
            nuevo_cliente = st.text_input("Cliente", value=str(factura.get('cliente', '')), key=f"edit_cliente_{factura_id}")
            nuevo_valor = st.number_input("Valor Total", value=float(factura.get('valor', 0)), min_value=0.0, key=f"edit_valor_{factura_id}")
        
        with col2:
            nueva_factura = st.text_input("Número Factura", value=str(factura.get('factura', '')), key=f"edit_factura_{factura_id}")
            cliente_propio = st.checkbox("Cliente Propio", value=bool(factura.get('cliente_propio', False)), key=f"edit_cliente_propio_{factura_id}")
            descuento_adicional = st.number_input("Descuento %", value=float(factura.get('descuento_adicional', 0)), key=f"edit_descuento_{factura_id}")
        
        nueva_fecha = st.date_input(
            "Fecha Factura", 
            value=pd.to_datetime(factura.get('fecha_factura', date.today())).date(),
            key=f"edit_fecha_{factura_id}"
        )
        
        st.markdown("#### Recálculo de Comisión")
        if nuevo_valor > 0:
            calc = calcular_comision_inteligente(
                nuevo_valor, 
                cliente_propio, 
                descuento_adicional, 
                factura.get('descuento_pie_factura', False)
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Nueva Comisión", format_currency(calc['comision']))
            with col2:
                st.metric("Porcentaje", f"{calc['porcentaje']}%")
            with col3:
                st.metric("Base", format_currency(calc['base_comision']))
        
        col1, col2 = st.columns(2)
        with col1:
            guardar = st.form_submit_button("💾 Guardar Cambios", type="primary")
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar")
        
        if cancelar:
            if f"show_edit_{factura_id}" in st.session_state:
                del st.session_state[f"show_edit_{factura_id}"]
            st.rerun()
        
        if guardar:
            if nuevo_pedido and nuevo_cliente and nuevo_valor > 0:
                try:
                    # Recalcular comisión
                    calc = calcular_comision_inteligente(
                        nuevo_valor, 
                        cliente_propio, 
                        descuento_adicional,
                        factura.get('descuento_pie_factura', False)
                    )
                    
                    # Recalcular fechas de pago
                    dias_pago = 60 if factura.get('condicion_especial', False) else 35
                    dias_max = 60 if factura.get('condicion_especial', False) else 45
                    fecha_pago_est = nueva_fecha + timedelta(days=dias_pago)
                    fecha_pago_max = nueva_fecha + timedelta(days=dias_max)
                    
                    updates = {
                        "pedido": nuevo_pedido,
                        "cliente": nuevo_cliente,
                        "factura": nueva_factura,
                        "valor": nuevo_valor,
                        "valor_neto": calc['valor_neto'],
                        "iva": calc['iva'],
                        "base_comision": calc['base_comision'],
                        "comision": calc['comision'],
                        "porcentaje": calc['porcentaje'],
                        "fecha_factura": nueva_fecha.isoformat(),
                        "fecha_pago_est": fecha_pago_est.isoformat(),
                        "fecha_pago_max": fecha_pago_max.isoformat(),
                        "cliente_propio": cliente_propio,
                        "descuento_adicional": descuento_adicional
                    }
                    
                    with st.spinner("Guardando cambios..."):
                        resultado = actualizar_factura(factura_id, updates)
                    
                    if resultado:
                        st.success("✅ Factura actualizada exitosamente!")
                        if f"show_edit_{factura_id}" in st.session_state:
                            del st.session_state[f"show_edit_{factura_id}"]
                        st.rerun()
                    else:
                        st.error("❌ Error actualizando la factura")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.error("Por favor completa todos los campos requeridos")

def mostrar_modal_pago_final(factura):
    """Modal de pago con información completa"""
    factura_id = factura.get('id')
    if not factura_id:
        st.error("ERROR: Factura sin ID")
        return
    
    if factura.get('pagado'):
        st.warning("⚠️ Esta factura ya está marcada como pagada")
        return
    
    form_key = f"pago_form_{factura_id}"
    
    with st.form(form_key, clear_on_submit=False):
        st.markdown(f"### 💳 Procesar Pago - {factura.get('pedido', 'N/A')}")
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_pago = st.date_input("Fecha de Pago", value=date.today(), key=f"pago_fecha_{factura_id}")
            metodo = st.selectbox("Método", ["Transferencia", "Efectivo", "Cheque", "Tarjeta"], key=f"pago_metodo_{factura_id}")
        with col2:
            referencia = st.text_input("Referencia", placeholder="Número de transacción", key=f"pago_referencia_{factura_id}")
            observaciones = st.text_area("Observaciones", placeholder="Notas del pago", key=f"pago_observaciones_{factura_id}")
        
        archivo = st.file_uploader(
            "Subir comprobante", 
            type=['pdf', 'jpg', 'jpeg', 'png'],
            key=f"archivo_pago_{factura_id}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            procesar = st.form_submit_button("✅ PROCESAR PAGO", type="primary")
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar")
        
        if cancelar:
            if f"show_pago_{factura_id}" in st.session_state:
                del st.session_state[f"show_pago_{factura_id}"]
            st.rerun()
        
        if procesar:
            with st.spinner("🔄 Procesando pago..."):
                try:
                    comprobante_url = None
                    if archivo:
                        comprobante_url = subir_comprobante(archivo, factura_id)
                    
                    # Calcular días de pago
                    fecha_factura = pd.to_datetime(factura.get('fecha_factura'))
                    dias = (pd.to_datetime(fecha_pago) - fecha_factura).days
                    
                    updates = {
                        "pagado": True,
                        "fecha_pago_real": fecha_pago.isoformat(),
                        "dias_pago_real": dias,
                        "metodo_pago": metodo,
                        "referencia": referencia,
                        "observaciones_pago": observaciones
                    }
                    
                    if comprobante_url:
                        updates["comprobante_url"] = comprobante_url
                    
                    # Verificar si la comisión se pierde por pago tardío
                    if dias > 80:
                        updates["comision_perdida"] = True
                        updates["razon_perdida"] = f"Pago tardío: {dias} días"
                        updates["comision_ajustada"] = 0
                    else:
                        updates["comision_perdida"] = False
                        updates["comision_ajustada"] = factura.get('comision', 0)
                    
                    resultado = actualizar_factura(factura_id, updates)
                    
                    if resultado:
                        st.success("🎉 PAGO PROCESADO EXITOSAMENTE!")
                        st.balloons()
                        
                        if dias > 80:
                            st.warning(f"⚠️ COMISIÓN PERDIDA: Pago realizado después de 80 días ({dias} días)")
                        
                        if f"show_pago_{factura_id}" in st.session_state:
                            del st.session_state[f"show_pago_{factura_id}"]
                        st.rerun()
                    else:
                        st.error("❌ Error procesando el pago")
                        
                except Exception as e:
                    st.error(f"Error procesando pago: {str(e)}")

def render_devolucion_card(devolucion, index):
    """Renderiza una card de devolución"""
    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            cliente = devolucion.get('factura_cliente', 'N/A')
            pedido = devolucion.get('factura_pedido', 'N/A')
            st.markdown(f"## 🔄 {pedido} - {cliente}")
            st.caption(f"Factura: {devolucion.get('factura_factura', 'N/A')}")
        
        with col2:
            if devolucion.get('afecta_comision', True):
                st.error("❌ AFECTA COMISIÓN")
            else:
                st.success("✅ NO AFECTA")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Valor Devuelto", format_currency(devolucion.get('valor_devuelto', 0)))
        
        with col2:
            valor_factura = devolucion.get('factura_valor', 0)
            porcentaje = (devolucion.get('valor_devuelto', 0) / valor_factura * 100) if valor_factura > 0 else 0
            st.metric("% de Factura", f"{porcentaje:.1f}%")
        
        with col3:
            if devolucion.get('afecta_comision', True):
                comision_original = devolucion.get('factura_comision', 0)
                comision_perdida = comision_original * (porcentaje / 100)
                st.metric("Comisión Perdida", format_currency(comision_perdida))
            else:
                st.metric("Comisión Perdida", format_currency(0))
        
        with col4:
            fecha_dev = devolucion.get('fecha_devolucion')
            if pd.notna(fecha_dev):
                fecha_str = pd.to_datetime(fecha_dev).strftime('%d/%m/%Y')
            else:
                fecha_str = "N/A"
            st.metric("Fecha", fecha_str)
        
        # Mostrar motivo si existe
        if devolucion.get('motivo'):
            st.markdown(f"**Motivo:** {devolucion.get('motivo')}")

def mostrar_modal_nueva_devolucion(facturas_df):
    """Modal para crear nueva devolución"""
    with st.form("nueva_devolucion_form", clear_on_submit=False):
        st.markdown("### Registrar Nueva Devolución")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not facturas_df.empty:
                opciones_factura = [f"{row['pedido']} - {row['cliente']} - {format_currency(row['valor'])}" 
                                   for _, row in facturas_df.iterrows()]
                
                factura_seleccionada = st.selectbox(
                    "Seleccionar Factura *",
                    options=range(len(opciones_factura)),
                    format_func=lambda x: opciones_factura[x] if x < len(opciones_factura) else "Seleccione...",
                    help="Factura sobre la cual se hará la devolución",
                    key="devolucion_factura_select"
                )
            else:
                st.error("No hay facturas disponibles")
                return
            
            valor_devuelto = st.number_input(
                "Valor a Devolver *",
                min_value=0.0,
                step=1000.0,
                format="%.0f",
                help="Valor total a devolver (incluye IVA si aplica)",
                key="devolucion_valor"
            )
        
        with col2:
            fecha_devolucion = st.date_input(
                "Fecha de Devolución *",
                value=date.today(),
                help="Fecha en que se procesa la devolución",
                key="devolucion_fecha"
            )
            
            afecta_comision = st.checkbox(
                "Afecta Comisión",
                value=True,
                help="Si esta devolución debe reducir la comisión calculada",
                key="devolucion_afecta"
            )
        
        motivo = st.text_area(
            "Motivo de la Devolución",
            placeholder="Ej: Producto defectuoso, Error en pedido, Cambio de especificación...",
            help="Descripción del motivo de la devolución",
            key="devolucion_motivo"
        )
        
        # Mostrar información de la factura seleccionada
        if factura_seleccionada is not None and factura_seleccionada < len(facturas_df):
            st.markdown("---")
            st.markdown("### Información de la Factura")
            
            factura_info = facturas_df.iloc[factura_seleccionada]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Valor Factura", format_currency(factura_info['valor']))
            with col2:
                st.metric("Comisión Original", format_currency(factura_info['comision']))
            with col3:
                if valor_devuelto > 0 and afecta_comision:
                    porcentaje_devuelto = valor_devuelto / factura_info['valor']
                    comision_perdida = factura_info['comision'] * porcentaje_devuelto
                    st.metric("Comisión Perdida", format_currency(comision_perdida))
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            registrar = st.form_submit_button(
                "Registrar Devolución",
                type="primary",
                use_container_width=True
            )
        
        with col2:
            cancelar = st.form_submit_button(
                "Cancelar",
                use_container_width=True
            )
        
        if cancelar:
            if 'show_nueva_devolucion' in st.session_state:
                del st.session_state['show_nueva_devolucion']
            st.rerun()
        
        if registrar:
            if factura_seleccionada is not None and valor_devuelto > 0:
                try:
                    factura_info = facturas_df.iloc[factura_seleccionada]
                    
                    # Validar que el valor no exceda el de la factura
                    if valor_devuelto > factura_info['valor']:
                        st.error("El valor a devolver no puede ser mayor al valor de la factura")
                        return
                    
                    data = {
                        "factura_id": int(factura_info['id']),
                        "valor_devuelto": float(valor_devuelto),
                        "motivo": motivo.strip(),
                        "fecha_devolucion": fecha_devolucion.isoformat(),
                        "afecta_comision": afecta_comision
                    }
                    
                    if insertar_devolucion(data):
                        st.success("Devolución registrada correctamente!")
                        
                        if afecta_comision:
                            st.warning("La comisión de la factura ha sido recalculada")
                        
                        st.balloons()
                        
                        # Mostrar resumen
                        st.markdown("### Resumen de la Devolución")
                        st.write(f"**Cliente:** {factura_info['cliente']}")
                        st.write(f"**Pedido:** {factura_info['pedido']}")
                        st.write(f"**Valor devuelto:** {format_currency(valor_devuelto)}")
                        st.write(f"**Fecha:** {fecha_devolucion.strftime('%d/%m/%Y')}")
                        if motivo:
                            st.write(f"**Motivo:** {motivo}")
                        
                        # Limpiar cache y estado
                        st.cache_data.clear()
                        if 'show_nueva_devolucion' in st.session_state:
                            del st.session_state['show_nueva_devolucion']
                        
                        st.rerun()
                    else:
                        st.error("Error registrando la devolución")
                        
                except Exception as e:
                    st.error(f"Error procesando devolución: {str(e)}")
            else:
                st.error("Por favor completa todos los campos obligatorios")

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
        
        st.markdown("---")
        
        # Filtros globales
        meses_disponibles = ["Todos"] + (sorted(df_tmp["mes_factura"].dropna().unique().tolist()) if not df_tmp.empty else [])
        
        mes_seleccionado = st.selectbox(
            "📅 Filtrar por mes",
            meses_disponibles,
            index=0
        )
        
        # Botón de limpieza de estado
        if st.button("🔄 Limpiar Estados"):
            keys_to_delete = [key for key in st.session_state.keys() if key.startswith('show_')]
            for key in keys_to_delete:
                del st.session_state[key]
            st.cache_data.clear()
            st.rerun()

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
            "Comisiones",
            "Nueva Venta",
            "Devoluciones",
            "Clientes",
            "IA & Alertas"
        ])

        # TAB 1 - DASHBOARD
        with tabs[0]:
            st.header("Dashboard Ejecutivo")

            df = cargar_datos()
            
            if not df.empty:
                df = agregar_campos_faltantes(df)
                
                if mes_seleccionado != "Todos":
                    df = df[df["mes_factura"] == mes_seleccionado]
                
                # Separar por tipo de cliente
                clientes_propios = df[df["cliente_propio"] == True]
                clientes_externos = df[df["cliente_propio"] == False]
                
                # Calcular métricas
                ventas_propios = clientes_propios["valor_neto"].sum()
                ventas_externos = clientes_externos["valor_neto"].sum()
                comision_propios = clientes_propios["comision"].sum()
                comision_externos = clientes_externos["comision"].sum()
                
                # Mostrar métricas principales
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

        # TAB 2 - COMISIONES
        with tabs[1]:
            st.header("Gestión de Comisiones")
            
            # Botón para limpiar cache
            col_refresh, col_empty = st.columns([1, 3])
            with col_refresh:
                if st.button("🔄 Actualizar Datos", type="secondary"):
                    st.cache_data.clear()
                    keys_to_delete = [key for key in st.session_state.keys() if key.startswith('show_')]
                    for key in keys_to_delete:
                        del st.session_state[key]
                    st.rerun()
            
            # Filtros
            with st.container():
                st.markdown("### Filtros")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    estado_filter = st.selectbox("Estado", ["Todos", "Pendientes", "Pagadas", "Vencidas"])
                with col2:
                    cliente_filter = st.text_input("Buscar cliente", key="comisiones_cliente_filter")
                with col3:
                    monto_min = st.number_input("Valor mínimo", min_value=0, value=0, step=100000)
                with col4:
                    aplicar_filtros = st.button("🔍 Aplicar Filtros")
            
            # Cargar y filtrar datos
            df = cargar_datos()
            
            if not df.empty:
                df = agregar_campos_faltantes(df)
                df_filtrado = df.copy()
                
                # Aplicar filtros
                if estado_filter == "Pendientes":
                    df_filtrado = df_filtrado[df_filtrado["pagado"] == False]
                elif estado_filter == "Pagadas":
                    df_filtrado = df_filtrado[df_filtrado["pagado"] == True]
                elif estado_filter == "Vencidas":
                    df_filtrado = df_filtrado[
                        (df_filtrado["dias_vencimiento"].notna()) & 
                        (df_filtrado["dias_vencimiento"] < 0) & 
                        (df_filtrado["pagado"] == False)
                    ]
                
                if cliente_filter:
                    df_filtrado = df_filtrado[df_filtrado["cliente"].str.contains(cliente_filter, case=False, na=False)]
                
                if monto_min > 0:
                    df_filtrado = df_filtrado[df_filtrado["valor"] >= monto_min]
            else:
                df_filtrado = pd.DataFrame()
            
            # Mostrar resumen
            if not df_filtrado.empty:
                st.markdown("### Resumen")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Facturas", len(df_filtrado))
                with col2:
                    st.metric("Total Comisiones", format_currency(df_filtrado["comision"].sum()))
                with col3:
                    st.metric("Valor Promedio", format_currency(df_filtrado["valor"].mean()))
                with col4:
                    pendientes = len(df_filtrado[df_filtrado["pagado"] == False])
                    st.metric("Pendientes", pendientes)
            
            st.markdown("---")
            
            # Mostrar facturas
            if not df_filtrado.empty:
                st.markdown("### Facturas Detalladas")
                
                # Ordenar por prioridad
                def calcular_prioridad(row):
                    if row['pagado']:
                        return 3
                    elif row.get('dias_vencimiento') is not None:
                        if row['dias_vencimiento'] < 0:
                            return 0
                        elif row['dias_vencimiento'] <= 5:
                            return 1
                        else:
                            return 2
                    return 2
                
                df_filtrado['prioridad'] = df_filtrado.apply(calcular_prioridad, axis=1)
                df_filtrado = df_filtrado.sort_values(['prioridad', 'fecha_factura'], ascending=[True, False])
                
                for index, (_, factura) in enumerate(df_filtrado.iterrows()):
                    factura_id = factura.get('id')
                    if not factura_id:
                        continue
                        
                    unique_key = f"{factura_id}_{index}_{int(datetime.now().timestamp() / 100)}"
                    
                    # Renderizar card de factura
                    render_factura_card(factura, index)
                    
                    # Botones de acción
                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                    
                    with col1:
                        if st.button("✏️ Editar", key=f"edit_{unique_key}"):
                            for key in list(st.session_state.keys()):
                                if key.startswith(f"show_") and str(factura_id) in key:
                                    del st.session_state[key]
                            st.session_state[f"show_edit_{factura_id}"] = True
                            st.rerun()
                    
                    with col2:
                        if not factura.get("pagado"):
                            if st.button("💳 Pagar", key=f"pay_{unique_key}"):
                                for key in list(st.session_state.keys()):
                                    if key.startswith(f"show_") and str(factura_id) in key:
                                        del st.session_state[key]
                                st.session_state[f"show_pago_{factura_id}"] = True
                                st.rerun()
                        else:
                            st.success("✅ Pagada")
                    
                    with col3:
                        if st.button("📊 Detalles", key=f"detail_{unique_key}"):
                            st.info(f"Detalles de {factura.get('pedido', 'N/A')}")
                    
                    with col4:
                        if factura.get("comprobante_url"):
                            st.success("📄 Tiene")
                        else:
                            st.caption("Sin comprobante")
                    
                    with col5:
                        if factura.get("pagado"):
                            dias_pago = factura.get("dias_pago_real", 0)
                            if dias_pago > 80:
                                st.error("⚠️ Sin comisión")
                            else:
                                st.success(f"✅ {dias_pago} días")
                        else:
                            dias_venc = factura.get("dias_vencimiento")
                            if dias_venc is not None:
                                if dias_venc < 0:
                                    st.error(f"🚨 -{abs(dias_venc)}d")
                                elif dias_venc <= 5:
                                    st.warning(f"⏰ {dias_venc}d")
                                else:
                                    st.info(f"📅 {dias_venc}d")
                    
                    with col6:
                        if factura.get("pagado"):
                            st.success("✅ COMPLETO")
                        else:
                            dias_venc = factura.get("dias_vencimiento")
                            if dias_venc is not None:
                                if dias_venc < 0:
                                    st.error("🚨 CRÍTICO")
                                elif dias_venc <= 5:
                                    st.warning("⚠️ ALTO")
                                else:
                                    st.info("📋 MEDIO")
                    
                    # Mostrar modales según el estado
                    if st.session_state.get(f"show_edit_{factura_id}", False):
                        with st.expander(f"✏️ Editando: {factura.get('pedido', 'N/A')}", expanded=True):
                            mostrar_modal_editar(factura)
                    
                    if st.session_state.get(f"show_pago_{factura_id}", False):
                        with st.expander(f"💳 Procesando Pago: {factura.get('pedido', 'N/A')}", expanded=True):
                            mostrar_modal_pago_final(factura)
                    
                    st.markdown("---")
            else:
                st.info("No hay facturas que coincidan con los filtros aplicados")
                
                if df.empty:
                    st.warning("No hay datos en la base de datos. Registra tu primera venta en la pestaña 'Nueva Venta'.")

        # TAB 3 - NUEVA VENTA
        with tabs[2]:
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

        # TAB 4 - DEVOLUCIONES
        with tabs[3]:
            st.header("Gestión de Devoluciones")
            
            # Botones de acción
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                if st.button("➕ Nueva Devolución", type="primary"):
                    st.session_state['show_nueva_devolucion'] = True
                    st.rerun()
            
            with col2:
                if st.button("🔄 Actualizar", type="secondary"):
                    st.cache_data.clear()
                    st.rerun()
            
            # Modal nueva devolución
            if st.session_state.get('show_nueva_devolucion', False):
                with st.expander("➕ Nueva Devolución", expanded=True):
                    facturas_df = obtener_facturas_para_devolucion()
                    mostrar_modal_nueva_devolucion(facturas_df)
            
            st.markdown("---")
            
            # Cargar devoluciones
            df_devoluciones = cargar_devoluciones()
            
            if not df_devoluciones.empty:
                # Resumen de devoluciones
                st.markdown("### Resumen")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Devoluciones", len(df_devoluciones))
                
                with col2:
                    total_devuelto = df_devoluciones['valor_devuelto'].sum()
                    st.metric("Valor Total Devuelto", format_currency(total_devuelto))
                
                with col3:
                    afectan_comision = len(df_devoluciones[df_devoluciones['afecta_comision'] == True])
                    st.metric("Afectan Comisión", afectan_comision)
                
                with col4:
                    valor_promedio = df_devoluciones['valor_devuelto'].mean()
                    st.metric("Valor Promedio", format_currency(valor_promedio))
                
                st.markdown("---")
                
                # Filtros
                st.markdown("### Filtros")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    afecta_filter = st.selectbox("Afecta Comisión", ["Todos", "Sí", "No"])
                
                with col2:
                    cliente_filter = st.text_input("Buscar cliente", key="devoluciones_cliente_filter")
                
                with col3:
                    fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=30))
                
                with col4:
                    fecha_hasta = st.date_input("Hasta", value=date.today())
                
                # Aplicar filtros
                df_filtrado = df_devoluciones.copy()
                
                if afecta_filter == "Sí":
                    df_filtrado = df_filtrado[df_filtrado['afecta_comision'] == True]
                elif afecta_filter == "No":
                    df_filtrado = df_filtrado[df_filtrado['afecta_comision'] == False]
                
                if cliente_filter:
                    df_filtrado = df_filtrado[df_filtrado['factura_cliente'].str.contains(cliente_filter, case=False, na=False)]
                
                # Filtro por fechas
                df_filtrado['fecha_devolucion'] = pd.to_datetime(df_filtrado['fecha_devolucion'])
                df_filtrado = df_filtrado[
                    (df_filtrado['fecha_devolucion'].dt.date >= fecha_desde) &
                    (df_filtrado['fecha_devolucion'].dt.date <= fecha_hasta)
                ]
                
                st.markdown("---")
                
                # Mostrar devoluciones
                if not df_filtrado.empty:
                    st.markdown("### Devoluciones Registradas")
                    
                    df_filtrado = df_filtrado.sort_values('fecha_devolucion', ascending=False)
                    
                    for index, (_, devolucion) in enumerate(df_filtrado.iterrows()):
                        render_devolucion_card(devolucion, index)
                        st.markdown("---")
                else:
                    st.info("No hay devoluciones que coincidan con los filtros aplicados")
            
            else:
                st.info("No hay devoluciones registradas")
                st.markdown("""
                **¿Cómo registrar una devolución?**
                1. Haz clic en "Nueva Devolución"
                2. Selecciona la factura correspondiente
                3. Ingresa el valor y motivo
                4. Indica si afecta la comisión
                5. Registra la devolución
                """)

        # TAB 5 - CLIENTES
        with tabs[4]:
            st.header("Gestión de Clientes")
            st.info("Módulo en desarrollo - Próximamente funcionalidad completa de gestión de clientes")
            
            df = cargar_datos()
            if not df.empty:
                clientes_stats = df.groupby('cliente').agg({
                    'valor_neto': ['sum', 'mean', 'count'],
                    'comision': 'sum',
                    'fecha_factura': 'max'
                }).round(0)
                
                clientes_stats.columns = ['Total Compras', 'Ticket Promedio', 'Número Compras', 'Total Comisiones', 'Última Compra']
                clientes_stats = clientes_stats.sort_values('Total Compras', ascending=False).head(10)
                
                st.markdown("### Top 10 Clientes")
                
                for cliente, row in clientes_stats.iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{cliente}**")
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total", format_currency(row['Total Compras']))
                        with col2:
                            st.metric("Ticket", format_currency(row['Ticket Promedio']))
                        with col3:
                            st.metric("Compras", int(row['Número Compras']))
                        with col4:
                            st.metric("Comisiones", format_currency(row['Total Comisiones']))
            else:
                st.warning("No hay datos de clientes disponibles")

        # TAB 6 - IA & ALERTAS
        with tabs[5]:
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

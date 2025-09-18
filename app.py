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
# FUNCIONES DE BASE DE DATOS - COMISIONES
# ========================
def cargar_datos(supabase: Client):
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

def insertar_venta(supabase: Client, data: dict):
    """Inserta una nueva venta"""
    try:
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        result = supabase.table("comisiones").insert(data).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"Error insertando venta: {e}")
        return False

def actualizar_factura(supabase: Client, factura_id: int, updates: dict):
    """Actualiza una factura - VERSIÓN QUE DETECTA COLUMNAS AUTOMÁTICAMENTE"""
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

        # OBTENER COLUMNAS EXISTENTES DE LA TABLA
        try:
            sample_query = supabase.table("comisiones").select("*").limit(1).execute()
            columnas_existentes = set(sample_query.data[0].keys()) if sample_query.data else set()
        except:
            # Columnas mínimas que deberían existir siempre
            columnas_existentes = {
                'id', 'pedido', 'cliente', 'factura', 'valor', 'pagado', 
                'fecha_factura', 'created_at', 'updated_at'
            }

        # FILTRAR SOLO UPDATES PARA COLUMNAS QUE EXISTEN
        safe_updates = {}
        
        for campo, valor in updates.items():
            # Solo procesar si la columna existe en la tabla
            if campo in columnas_existentes:
                try:
                    # Validación por tipo de campo
                    if campo in ['pedido', 'cliente', 'factura', 'referencia', 'observaciones_pago', 'razon_perdida', 'comprobante_url']:
                        safe_updates[campo] = str(valor) if valor is not None else ""
                    
                    elif campo in ['valor', 'valor_neto', 'iva', 'base_comision', 'comision', 'porcentaje', 'comision_ajustada', 'descuento_adicional']:
                        safe_updates[campo] = float(valor) if valor is not None else 0
                    
                    elif campo in ['dias_pago_real']:
                        # Campo INTEGER - convertir a entero
                        safe_updates[campo] = int(float(valor)) if valor is not None else 0
                    
                    elif campo in ['pagado', 'comision_perdida', 'cliente_propio', 'condicion_especial', 'descuento_pie_factura']:
                        safe_updates[campo] = bool(valor)
                    
                    elif campo in ['fecha_factura', 'fecha_pago_est', 'fecha_pago_max', 'fecha_pago_real']:
                        if isinstance(valor, str):
                            datetime.fromisoformat(valor.replace('Z', '+00:00'))
                            safe_updates[campo] = valor
                        elif hasattr(valor, 'isoformat'):
                            safe_updates[campo] = valor.isoformat()
                    
                    else:
                        # Para otros campos, intentar agregar como están
                        safe_updates[campo] = valor
                        
                except (ValueError, TypeError):
                    # Si hay error de conversión, omitir este campo
                    continue
        
        # Siempre agregar updated_at si existe la columna
        if 'updated_at' in columnas_existentes:
            safe_updates["updated_at"] = datetime.now().isoformat()
        
        if not safe_updates:
            st.warning("No hay campos válidos para actualizar")
            return False
        
        # Mostrar qué se va a actualizar (para debug)
        st.info(f"Actualizando campos: {list(safe_updates.keys())}")
        
        # Ejecutar actualización
        result = supabase.table("comisiones").update(safe_updates).eq("id", factura_id).execute()
        
        if result.data:
            st.cache_data.clear()
            return True
        else:
            st.error("No se pudo actualizar la factura")
            return False
        
    except Exception as e:
        st.error(f"Error actualizando factura: {e}")
        return False

# ========================
# FUNCIONES DE BASE DE DATOS - DEVOLUCIONES
# ========================
def cargar_devoluciones(supabase: Client):
    """Carga datos de devoluciones con información de factura"""
    try:
        # Query con JOIN para obtener información de la factura
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
        
        # Conversión de tipos
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

def insertar_devolucion(supabase: Client, data: dict):
    """Inserta una nueva devolución"""
    try:
        data["created_at"] = datetime.now().isoformat()
        result = supabase.table("devoluciones").insert(data).execute()
        
        if result.data:
            # Si la devolución afecta la comisión, actualizar la factura
            if data.get("afecta_comision", True):
                actualizar_comision_por_devolucion(supabase, data["factura_id"], data["valor_devuelto"])
            
            return True
        return False
        
    except Exception as e:
        st.error(f"Error insertando devolución: {e}")
        return False

def actualizar_comision_por_devolucion(supabase: Client, factura_id: int, valor_devuelto: float):
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
        valor_efectivo = valor_original - total_devuelto
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

def obtener_facturas_para_devolucion(supabase: Client):
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
# FUNCIONES AUXILIARES
# ========================
def subir_comprobante(supabase: Client, file, factura_id: int):
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

def obtener_meta_mes_actual(supabase: Client):
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

def actualizar_meta(supabase: Client, mes: str, meta_ventas: float, meta_clientes: int):
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
# FUNCIONES DE CÁLCULO
# ========================
def format_currency(value):
    """Formatea números como moneda colombiana"""
    if pd.isna(value) or value == 0:
        return "$0"
    return f"${value:,.0f}".replace(",", ".")

def calcular_comision_inteligente(valor_total, cliente_propio=False, descuento_adicional=0, descuento_pie=False):
    """Calcula comisión según lógica real"""
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
# FUNCIONES DE RECOMENDACIONES IA
# ========================
def generar_recomendaciones_reales(supabase: Client):
    """Genera recomendaciones basadas en datos reales"""
    try:
        df = cargar_datos(supabase)
        
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
# FUNCIONES DE UI - COMISIONES
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
            # AGREGAR keys únicos basados en factura_id
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
                        resultado = actualizar_factura(supabase, factura_id, updates)
                    
                    if resultado:
                        st.success("✅ Factura actualizada exitosamente!")
                        # Limpiar estado y recargar
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
        
        # ... código anterior ...
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_pago = st.date_input("Fecha de Pago", value=date.today(), key=f"pago_fecha_{factura_id}")
            metodo = st.selectbox("Método", ["Transferencia", "Efectivo", "Cheque", "Tarjeta"], key=f"pago_metodo_{factura_id}")
        with col2:
            referencia = st.text_input("Referencia", placeholder="Número de transacción", key=f"pago_referencia_{factura_id}")
            observaciones = st.text_area("Observaciones", placeholder="Notas del pago", key=f"pago_observaciones_{factura_id}")
        
        # archivo ya tiene key único
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
                        comprobante_url = subir_comprobante(supabase, archivo, factura_id)
                    
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
                    
                    resultado = actualizar_factura(supabase, factura_id, updates)
                    
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

def mostrar_comprobante(comprobante_url):
    """Muestra comprobante de pago"""
    if comprobante_url:
        if comprobante_url.lower().endswith('.pdf'):
            st.markdown(f"📄 [Ver Comprobante PDF]({comprobante_url})")
        else:
            try:
                st.image(comprobante_url, caption="Comprobante de Pago", width=300)
            except:
                st.markdown(f"[Ver Comprobante]({comprobante_url})")
    else:
        st.info("No hay comprobante subido")

def mostrar_detalles_completos(factura):
    """Muestra detalles completos de factura"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Información General")
        st.write(f"**Pedido:** {factura.get('pedido', 'N/A')}")
        st.write(f"**Cliente:** {factura.get('cliente', 'N/A')}")
        st.write(f"**Factura:** {factura.get('factura', 'N/A')}")
        st.write(f"**Cliente Propio:** {'Sí' if factura.get('cliente_propio') else 'No'}")
        
        fecha_factura = factura.get('fecha_factura')
        if pd.notna(fecha_factura):
            st.write(f"**Fecha Factura:** {pd.to_datetime(fecha_factura).strftime('%d/%m/%Y')}")
        
        fecha_pago_max = factura.get('fecha_pago_max')
        if pd.notna(fecha_pago_max):
            st.write(f"**Fecha Límite:** {pd.to_datetime(fecha_pago_max).strftime('%d/%m/%Y')}")
    
    with col2:
        st.markdown("#### Información Financiera")
        st.write(f"**Valor Total:** {format_currency(factura.get('valor', 0))}")
        st.write(f"**Valor Neto:** {format_currency(factura.get('valor_neto', 0))}")
        st.write(f"**IVA:** {format_currency(factura.get('iva', 0))}")
        st.write(f"**Base Comisión:** {format_currency(factura.get('base_comision', 0))}")
        st.write(f"**Comisión:** {format_currency(factura.get('comision', 0))} ({factura.get('porcentaje', 0)}%)")
        
        if factura.get('descuento_adicional', 0) > 0:
            st.write(f"**Descuento Adicional:** {factura.get('descuento_adicional', 0)}%")
    
    # Información de pago si existe
    if factura.get('pagado'):
        st.markdown("#### Información de Pago")
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_pago_real = factura.get('fecha_pago_real')
            if pd.notna(fecha_pago_real):
                st.write(f"**Fecha Pago:** {pd.to_datetime(fecha_pago_real).strftime('%d/%m/%Y')}")
            
            if factura.get('metodo_pago'):
                st.write(f"**Método:** {factura.get('metodo_pago')}")
            
            if factura.get('referencia'):
                st.write(f"**Referencia:** {factura.get('referencia')}")
        
        with col2:
            dias_pago = factura.get('dias_pago_real')
            if dias_pago is not None:
                st.write(f"**Días de Pago:** {dias_pago}")
            
            if factura.get('comision_perdida'):
                st.error("**Estado:** Comisión Perdida")
                if factura.get('razon_perdida'):
                    st.write(f"**Razón:** {factura.get('razon_perdida')}")
            else:
                st.success("**Estado:** Comisión Ganada")
    
    if factura.get('observaciones_pago'):
        st.markdown("#### Observaciones")
        st.write(factura.get('observaciones_pago'))

# ========================
# FUNCIONES DE UI - DEVOLUCIONES
# ========================
def mostrar_modal_nueva_devolucion(facturas_df):
    """Modal para crear nueva devolución"""
    with st.form("nueva_devolucion_form", clear_on_submit=False):
        st.markdown("### Registrar Nueva Devolución")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Selector de factura
            if not facturas_df.empty:
                opciones_factura = [f"{row['pedido']} - {row['cliente']} - {format_currency(row['valor'])}" 
                                   for _, row in facturas_df.iterrows()]
                
                factura_seleccionada = st.selectbox(
                    "Seleccionar Factura *",
                    options=range(len(opciones_factura)),
                    format_func=lambda x: opciones_factura[x] if x < len(opciones_factura) else "Seleccione...",
                    help="Factura sobre la cual se hará la devolución",
                    key="devolucion_factura_select"  # AGREGAR key único
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
                key="devolucion_valor"  # AGREGAR key único
            )
        
        with col2:
            fecha_devolucion = st.date_input(
                "Fecha de Devolución *",
                value=date.today(),
                help="Fecha en que se procesa la devolución",
                key="devolucion_fecha"  # AGREGAR key único
            )
            
            afecta_comision = st.checkbox(
                "Afecta Comisión",
                value=True,
                help="Si esta devolución debe reducir la comisión calculada",
                key="devolucion_afecta"  # AGREGAR key único
            )
        
        motivo = st.text_area(
            "Motivo de la Devolución",
            placeholder="Ej: Producto defectuoso, Error en pedido, Cambio de especificación...",
            help="Descripción del motivo de la devolución",
            key="devolucion_motivo"  # AGREGAR key único
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
                    # Calcular impacto en comisión
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
                    
                    if insertar_devolucion(supabase, data):
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

# ========================
# FUNCIONES DE TABS
# ========================
@st.cache_data(ttl=300)  # Cache por 5 minutos
def cargar_datos_cache(supabase_url, supabase_key):
    """Versión con cache de cargar_datos"""
    return cargar_datos(supabase)

def render_tab_comisiones():
    """Tab de gestión de comisiones"""
    st.header("Gestión de Comisiones")
    
    # Botón para limpiar cache y forzar recarga
    col_refresh, col_empty = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Actualizar Datos", type="secondary"):
            st.cache_data.clear()
            # Limpiar todos los estados de show_
            keys_to_delete = [key for key in st.session_state.keys() if key.startswith('show_')]
            for key in keys_to_delete:
                del st.session_state[key]
            st.rerun()
    
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
    
    # Cargar datos (con cache)
    df = cargar_datos_cache(SUPABASE_URL, SUPABASE_KEY)
    
    if not df.empty:
        df = agregar_campos_faltantes(df)
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
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
        
        # Ordenar por prioridad: vencidas, por vencer, pagadas
        def calcular_prioridad(row):
            if row['pagado']:
                return 3  # Menos prioridad
            elif row.get('dias_vencimiento') is not None:
                if row['dias_vencimiento'] < 0:
                    return 0  # Máxima prioridad - vencidas
                elif row['dias_vencimiento'] <= 5:
                    return 1  # Alta prioridad - por vencer
                else:
                    return 2  # Prioridad media
            return 2
        
        df_filtrado['prioridad'] = df_filtrado.apply(calcular_prioridad, axis=1)
        df_filtrado = df_filtrado.sort_values(['prioridad', 'fecha_factura'], ascending=[True, False])
        
        for index, (_, factura) in enumerate(df_filtrado.iterrows()):
            factura_id = factura.get('id')
            if not factura_id:
                continue
                
            unique_key = f"{factura_id}_{index}_{int(datetime.now().timestamp() / 100)}"
            
            # Renderizar card
            render_factura_card(factura, index)
            
            # Botones de acción
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                if st.button("✏️ Editar", key=f"edit_{unique_key}"):
                    # Limpiar otros estados de esta factura
                    for key in list(st.session_state.keys()):
                        if key.startswith(f"show_") and str(factura_id) in key:
                            del st.session_state[key]
                    st.session_state[f"show_edit_{factura_id}"] = True
                    st.rerun()
            
            with col2:
                if not factura.get("pagado"):
                    if st.button("💳 Pagar", key=f"pay_{unique_key}"):
                        # Limpiar otros estados de esta factura
                        for key in list(st.session_state.keys()):
                            if key.startswith(f"show_") and str(factura_id) in key:
                                del st.session_state[key]
                        st.session_state[f"show_pago_{factura_id}"] = True
                        st.rerun()
                else:
                    st.success("✅ Pagada")
            
            with col3:
                if st.button("📊 Detalles", key=f"detail_{unique_key}"):
                    # Limpiar otros estados de esta factura
                    for key in list(st.session_state.keys()):
                        if key.startswith(f"show_") and str(factura_id) in key:
                            del st.session_state[key]
                    st.session_state[f"show_detail_{factura_id}"] = True
                    st.rerun()
            
            with col4:
                if factura.get("comprobante_url"):
                    if st.button("📄 Comprobante", key=f"comp_{unique_key}"):
                        # Limpiar otros estados de esta factura
                        for key in list(st.session_state.keys()):
                            if key.startswith(f"show_") and str(factura_id) in key:
                                del st.session_state[key]
                        st.session_state[f"show_comprobante_{factura_id}"] = True
                        st.rerun()
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
            
            # Mostrar modales/expandibles basados en el estado
            if st.session_state.get(f"show_edit_{factura_id}", False):
                with st.expander(f"✏️ Editando: {factura.get('pedido', 'N/A')}", expanded=True):
                    mostrar_modal_editar(factura)
            
            if st.session_state.get(f"show_pago_{factura_id}", False):
                with st.expander(f"💳 Procesando Pago: {factura.get('pedido', 'N/A')}", expanded=True):
                    mostrar_modal_pago_final(factura)
            
            if st.session_state.get(f"show_comprobante_{factura_id}", False):
                with st.expander(f"📄 Comprobante: {factura.get('pedido', 'N/A')}", expanded=True):
                    mostrar_comprobante(factura.get("comprobante_url"))
                    if st.button("❌ Cerrar", key=f"close_comp_{unique_key}"):
                        del st.session_state[f"show_comprobante_{factura_id}"]
                        st.rerun()
            
            if st.session_state.get(f"show_detail_{factura_id}", False):
                with st.expander(f"📊 Detalles: {factura.get('pedido', 'N/A')}", expanded=True):
                    mostrar_detalles_completos(factura)
                    if st.button("❌ Cerrar", key=f"close_detail_{unique_key}"):
                        del st.session_state[f"show_detail_{factura_id}"]
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("No hay facturas que coincidan con los filtros aplicados")
        
        if df.empty:
            st.warning("No hay datos en la base de datos. Registra tu primera venta en la pestaña 'Nueva Venta'.")

def render_tab_devoluciones():
    """Tab de gestión de devoluciones"""
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
            facturas_df = obtener_facturas_para_devolucion(supabase)
            mostrar_modal_nueva_devolucion(facturas_df)
    
    st.markdown("---")
    
    # Cargar devoluciones
    df_devoluciones = cargar_devoluciones(supabase)
    
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
            
            # Ordenar por fecha más reciente
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
        
        .recomendacion-card {
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.3) 0%, rgba(124, 58, 237, 0.3) 100%);
            color: #ffffff;
            padding: 2rem;
            border-radius: 1rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(255,255,255,0.1);
            border: 2px solid #4f46e5;
            backdrop-filter: blur(20px);
        }
        
        /* Estilos para expandibles */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            border: 2px solid #ffffff !important;
        }
        
        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 2px solid #ffffff !important;
            border-top: none !important;
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
    meta_actual = obtener_meta_mes_actual(supabase)
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
        
        df_tmp = cargar_datos(supabase)
        mes_actual_str = date.today().strftime("%Y-%m")
        ventas_mes = df_tmp[df_tmp["mes_factura"] == mes_actual_str]["valor"].sum() if not df_tmp.empty else 0
        
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
        
        # Filtros
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
                    key="config_meta_ventas"  # AGREGAR key único
                )
            
            with col2:
                nueva_meta_clientes = st.number_input(
                    "Meta Clientes Nuevos", 
                    value=meta_actual["meta_clientes_nuevos"],
                    min_value=0,
                    step=1,
                    key="config_meta_clientes"  # AGREGAR key único
                )

            
            bono_potencial = nueva_meta * 0.005
            st.info(f"**Bono potencial:** {format_currency(bono_potencial)} (0.5% de la meta)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar Meta", type="primary"):
                    mes_actual_str = date.today().strftime("%Y-%m")
                    if actualizar_meta(supabase, mes_actual_str, nueva_meta, nueva_meta_clientes):
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
                    "Total Facturado",
                    format_currency(total_facturado),
                    delta="+12.5%" if total_facturado > 0 else None
                )
            
            with col2:
                st.metric(
                    "Comisiones Mes", 
                    format_currency(total_comisiones),
                    delta="+8.2%" if total_comisiones > 0 else None
                )
            
            with col3:
                st.metric(
                    "Facturas Pendientes",
                    facturas_pendientes,
                    delta="-3" if facturas_pendientes > 0 else None,
                    delta_color="inverse"
                )
            
            with col4:
                st.metric(
                    "% Comisión Promedio",
                    f"{promedio_comision:.1f}%",
                    delta="+0.3%" if promedio_comision > 0 else None
                )
            
            st.markdown("---")
            
            # Progreso Meta y Recomendaciones IA
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### Progreso Meta Mensual")
                
                meta = meta_actual["meta_ventas"]
                actual = total_facturado
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
                
                recomendaciones = generar_recomendaciones_reales(supabase)
                
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
            render_tab_comisiones()

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
                        key="nueva_venta_pedido"  # AGREGAR key único
                    )
                    cliente = st.text_input(
                        "Cliente *",
                        placeholder="Ej: DISTRIBUIDORA CENTRAL",
                        help="Nombre completo del cliente",
                        key="nueva_venta_cliente"  # AGREGAR key único
                    )
                    factura = st.text_input(
                        "Número de Factura",
                        placeholder="Ej: FAC-1001",
                        help="Número de la factura generada",
                        key="nueva_venta_factura"  # AGREGAR key único
                    )
                
                with col2:
                    fecha_factura = st.date_input(
                        "Fecha de Factura *", 
                        value=date.today(),
                        help="Fecha de emisión de la factura",
                        key="nueva_venta_fecha"  # AGREGAR key único
                    )
                    valor_total = st.number_input(
                        "Valor Total (con IVA) *", 
                        min_value=0.0, 
                        step=10000.0,
                        format="%.0f",
                        help="Valor total de la venta incluyendo IVA",
                        key="nueva_venta_valor"  # AGREGAR key único
                    )
                    condicion_especial = st.checkbox(
                        "Condición Especial (60 días de pago)",
                        help="Marcar si el cliente tiene condiciones especiales de pago",
                        key="nueva_venta_condicion"  # AGREGAR key único
                    )
                
                st.markdown("### Configuración de Comisión")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    cliente_propio = st.checkbox(
                        "Cliente Propio", 
                        help="Cliente directo (2.5% comisión vs 1% externo)",
                        key="nueva_venta_cliente_propio"  # AGREGAR key único
                    )
                
                with col2:
                    descuento_pie_factura = st.checkbox(
                        "Descuento a Pie de Factura",
                        help="Si el descuento aparece directamente en la factura",
                        key="nueva_venta_descuento_pie"  # AGREGAR key único
                    )
                
                with col3:
                    descuento_adicional = st.number_input(
                        "Descuento Adicional (%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.5,
                        help="Porcentaje de descuento adicional aplicado",
                        key="nueva_venta_descuento_adicional"  # AGREGAR key único
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
                            if insertar_venta(supabase, data):
                                st.success("¡Venta registrada correctamente!")
                                st.success(f"Comisión calculada: {format_currency(calc['comision'])}")
                                st.balloons()
                                
                                st.markdown("### Resumen de la venta:")
                                st.write(f"**Cliente:** {cliente}")
                                st.write(f"**Pedido:** {pedido}")
                                st.write(f"**Valor:** {format_currency(valor_total)}")
                                st.write(f"**Comisión:** {format_currency(calc['comision'])} ({calc['porcentaje']}%)")
                                st.write(f"**Fecha límite pago:** {fecha_pago_max.strftime('%d/%m/%Y')}")
                                
                                # Limpiar cache
                                st.cache_data.clear()
                            else:
                                st.error("Error al registrar la venta")
                                
                        except Exception as e:
                            st.error(f"Error procesando la venta: {str(e)}")
                    else:
                        st.error("Por favor completa todos los campos marcados con *")

        # TAB 4 - DEVOLUCIONES
        with tabs[3]:
            render_tab_devoluciones()

        # TAB 5 - CLIENTES
        with tabs[4]:
            st.header("Gestión de Clientes")
            st.info("Módulo en desarrollo - Próximamente funcionalidad completa de gestión de clientes")
            
            df = cargar_datos(supabase)
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
    
    # AGREGAR ANÁLISIS PREDICTIVO AQUÍ
    df = cargar_datos(supabase)
    render_analisis_predictivo_real(df, meta_actual)
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Alertas Críticas")
        
        alertas_encontradas = False
        
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
        
        recomendaciones = generar_recomendaciones_reales(supabase)
        
        for i, rec in enumerate(recomendaciones):
            with st.container(border=True):
                with st.expander(f"#{i+1} {rec['cliente']} - {rec['probabilidad']}% probabilidad", expanded=True):
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.markdown(f"**Acción:** {rec['accion']}")
                        st.markdown(f"**Producto:** {rec['producto']}")
                        st.markdown(f"**Razón:** {rec['razon']}")
                        
                        prioridad_color = "🔴" if rec['prioridad'] == 'alta' else "🟡"
                        st.markdown(f"**Prioridad:** {prioridad_color} {rec['prioridad'].title()}")
                    
                    with col_b:
                        st.metric(
                            label="Impacto Comisión",
                            value=format_currency(rec['impacto_comision']),
                            delta=f"+{rec['probabilidad']}%"
                        )
                    
                    if st.button(f"Ejecutar Acción", key=f"action_rec_{i}"):
                        st.success(f"Acción programada para {rec['cliente']}")
        
        if st.button("Generar Nuevas Recomendaciones"):
            st.rerun()
    
    st.markdown("---")
            
def calcular_prediccion_meta(df, meta_actual):
    """Calcula predicción real de cumplimiento de meta"""
    if df.empty:
        return {"probabilidad": 0, "tendencia": "Sin datos", "dias_necesarios": 0}
    
    # Obtener datos del mes actual
    mes_actual = date.today().strftime("%Y-%m")
    df_mes = df[df["mes_factura"] == mes_actual]
    
    if df_mes.empty:
        return {"probabilidad": 0, "tendencia": "Sin ventas este mes", "dias_necesarios": 0}
    
    # Calcular progreso actual
    ventas_actuales = df_mes["valor"].sum()
    meta_ventas = meta_actual.get("meta_ventas", 0)
    
    if meta_ventas == 0:
        return {"probabilidad": 0, "tendencia": "Meta no definida", "dias_necesarios": 0}
    
    # Calcular días transcurridos y restantes del mes
    hoy = date.today()
    primer_dia_mes = hoy.replace(day=1)
    dias_transcurridos = (hoy - primer_dia_mes).days + 1
    
    # Calcular último día del mes
    if hoy.month == 12:
        ultimo_dia_mes = hoy.replace(year=hoy.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        ultimo_dia_mes = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)
    
    dias_restantes = (ultimo_dia_mes - hoy).days + 1
    dias_totales_mes = dias_transcurridos + dias_restantes
    
    # Calcular velocidad actual y necesaria
    velocidad_actual = ventas_actuales / dias_transcurridos if dias_transcurridos > 0 else 0
    faltante = max(0, meta_ventas - ventas_actuales)
    velocidad_necesaria = faltante / dias_restantes if dias_restantes > 0 else float('inf')
    
    # Calcular probabilidad basada en velocidad
    if velocidad_actual == 0:
        probabilidad = 0
    elif velocidad_necesaria == 0:  # Ya cumplió la meta
        probabilidad = 100
    else:
        ratio_velocidad = velocidad_actual / velocidad_necesaria
        # Probabilidad basada en qué tan cerca está la velocidad actual de la necesaria
        if ratio_velocidad >= 1:
            probabilidad = min(95, 70 + (ratio_velocidad - 1) * 25)
        else:
            probabilidad = max(5, ratio_velocidad * 70)
    
    # Proyección lineal
    proyeccion_mes = velocidad_actual * dias_totales_mes
    porcentaje_meta = (proyeccion_mes / meta_ventas) * 100 if meta_ventas > 0 else 0
    
    return {
        "probabilidad": int(probabilidad),
        "tendencia": f"{porcentaje_meta:.0f}%",
        "dias_necesarios": dias_restantes,
        "velocidad_actual": velocidad_actual,
        "velocidad_necesaria": velocidad_necesaria,
        "proyeccion": proyeccion_mes
    }

def calcular_tendencia_comisiones(df):
    """Calcula tendencia real de comisiones"""
    if df.empty:
        return {"crecimiento": "0%", "delta": "Sin datos"}
    
    # Obtener datos de los últimos 2 meses
    hoy = date.today()
    mes_actual = hoy.strftime("%Y-%m")
    
    # Mes anterior
    if hoy.month == 1:
        mes_anterior = f"{hoy.year - 1}-12"
    else:
        mes_anterior = f"{hoy.year}-{hoy.month - 1:02d}"
    
    comisiones_actual = df[df["mes_factura"] == mes_actual]["comision"].sum()
    comisiones_anterior = df[df["mes_factura"] == mes_anterior]["comision"].sum()
    
    if comisiones_anterior == 0:
        if comisiones_actual > 0:
            return {"crecimiento": "+100%", "delta": "Primer mes"}
        else:
            return {"crecimiento": "0%", "delta": "Sin datos"}
    
    crecimiento = ((comisiones_actual - comisiones_anterior) / comisiones_anterior) * 100
    
    return {
        "crecimiento": f"{crecimiento:+.1f}%",
        "delta": f"{abs(crecimiento):.1f}%",
        "direccion": "normal" if crecimiento >= 0 else "inverse"
    }

def identificar_clientes_riesgo(df):
    """Identifica clientes que requieren atención"""
    if df.empty:
        return {"cantidad": 0, "delta": "Sin datos", "clientes": []}
    
    hoy = pd.Timestamp.now()
    clientes_riesgo = []
    
    # 1. Facturas vencidas (alto riesgo)
    vencidas = df[
        (df['dias_vencimiento'].notna()) & 
        (df['dias_vencimiento'] < -5) & 
        (df['pagado'] == False)
    ]
    
    for cliente in vencidas['cliente'].unique():
        cliente_vencidas = vencidas[vencidas['cliente'] == cliente]
        total_riesgo = cliente_vencidas['comision'].sum()
        if total_riesgo > 0:
            clientes_riesgo.append({
                'cliente': cliente,
                'razon': f"Facturas vencidas",
                'impacto': total_riesgo,
                'tipo': 'critico'
            })
    
    # 2. Clientes sin actividad reciente (riesgo medio)
    df['dias_ultima_factura'] = (hoy - df['fecha_factura']).dt.days
    
    clientes_inactivos = df.groupby('cliente').agg({
        'dias_ultima_factura': 'min',
        'comision': 'mean',
        'valor': 'sum'
    }).reset_index()
    
    # Clientes inactivos por más de 60 días pero que han comprado antes
    inactivos_riesgo = clientes_inactivos[
        (clientes_inactivos['dias_ultima_factura'] >= 60) & 
        (clientes_inactivos['valor'] > 0)
    ].nlargest(3, 'comision')
    
    for _, cliente in inactivos_riesgo.iterrows():
        if cliente['cliente'] not in [c['cliente'] for c in clientes_riesgo]:
            clientes_riesgo.append({
                'cliente': cliente['cliente'],
                'razon': f"Sin actividad {cliente['dias_ultima_factura']} días",
                'impacto': cliente['comision'],
                'tipo': 'medio'
            })
    
    # Calcular tendencia (comparar con mes anterior si hay datos)
    mes_actual = date.today().strftime("%Y-%m")
    if date.today().month == 1:
        mes_anterior = f"{date.today().year - 1}-12"
    else:
        mes_anterior = f"{date.today().year}-{date.today().month - 1:02d}"
    
    riesgo_actual = len([c for c in clientes_riesgo if c['tipo'] == 'critico'])
    
    # Buscar clientes en riesgo del mes anterior para comparar
    df_anterior = df[df["mes_factura"] == mes_anterior]
    if not df_anterior.empty:
        vencidas_anterior = df_anterior[
            (df_anterior['dias_vencimiento'].notna()) & 
            (df_anterior['dias_vencimiento'] < -5) & 
            (df_anterior['pagado'] == False)
        ]
        riesgo_anterior = len(vencidas_anterior['cliente'].unique())
        delta_riesgo = riesgo_actual - riesgo_anterior
        delta_str = f"{delta_riesgo:+d}" if riesgo_anterior > 0 else "Sin comparación"
    else:
        delta_str = "Sin datos previos"
    
    return {
        "cantidad": len(clientes_riesgo),
        "delta": delta_str,
        "clientes": clientes_riesgo[:5]  # Top 5
    }

st.write(f"Número de tabs creados: {len(tabs)}")
st.write(f"Tipo de tabs: {type(tabs)}")

# ========================
# EJECUTAR APLICACIÓN
# ========================
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.info("Por favor, recarga la página o contacta al administrador.")

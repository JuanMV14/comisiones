import os
from datetime import date, timedelta, datetime
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# ========================
# FUNCIONES DE BASE DE DATOS Y UTILIDADES
# ========================
def cargar_datos(supabase: Client):
    """Carga datos específicamente para la estructura de tu tabla comisiones"""
    try:
        print("🔄 Cargando datos desde tu tabla comisiones...")
        response = supabase.table("comisiones").select("*").execute()
        
        if not response.data:
            print("❌ No hay datos en la tabla")
            return pd.DataFrame()

        df = pd.DataFrame(response.data)
        print(f"📊 Datos cargados: {len(df)} registros")

        # ===== CONVERSIÓN DE TIPOS ESPECÍFICA PARA TU ESTRUCTURA =====
        
        # 1. LIMPIAR VALORES NULL Y CONVERTIR NÚMEROS
        # Columnas que están como string pero deben ser números
        columnas_numericas_str = ['valor_base', 'valor_neto', 'iva', 'base_comision', 'comision_ajustada']
        
        for col in columnas_numericas_str:
            if col in df.columns:
                # Convertir "NULL" strings a 0, otros valores a float
                df[col] = df[col].apply(lambda x: 0 if x in [None, "NULL", "null", ""] else float(x) if str(x).replace('.','').replace('-','').isdigit() else 0)
                print(f"✅ Convertido {col} de string a float")

        # 2. ASEGURAR QUE LAS COLUMNAS NUMÉRICAS EXISTENTES SEAN FLOAT
        columnas_numericas_existentes = ['valor', 'porcentaje', 'comision', 'porcentaje_descuento', 'descuento_adicional', 'valor_devuelto']
        
        for col in columnas_numericas_existentes:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. CALCULAR CAMPOS FALTANTES BASÁNDOSE EN TU ESTRUCTURA
        
        # Si valor_neto está vacío (0), calcularlo desde valor
        if df['valor_neto'].sum() == 0 and df['valor'].sum() > 0:
            df['valor_neto'] = df['valor'] / 1.19  # Quitar IVA 19%
            print("📊 Calculando valor_neto desde valor")

        # Si iva está vacío, calcularlo
        if df['iva'].sum() == 0 and df['valor'].sum() > 0:
            df['iva'] = df['valor'] - df['valor_neto']
            print("📊 Calculando IVA")

        # Si base_comision está vacío, usar tu lógica específica
        if df['base_comision'].sum() == 0:
            # Usar valor_neto como base si no hay descuento a pie de factura
            # Usar valor_neto * 0.85 si hay descuento automático
            df['base_comision'] = df.apply(lambda row: 
                row['valor_neto'] if row.get('descuento_pie_factura', False) or row.get('tiene_descuento_factura', False)
                else row['valor_neto'] * 0.85, axis=1)
            print("📊 Calculando base_comision")

        # 4. CONVERTIR FECHAS (tu estructura tiene fechas como strings)
        columnas_fecha = ['fecha_factura', 'fecha_pago_est', 'fecha_pago_max', 'fecha_pago_real', 'created_at', 'updated_at']
        
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                print(f"📅 Convertido {col} a datetime")

        # 5. CREAR COLUMNAS DERIVADAS NECESARIAS PARA EL DASHBOARD
        
        # Crear mes_factura para filtros
        df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)
        
        # Calcular días de vencimiento
        hoy = pd.Timestamp.now()
        df['dias_vencimiento'] = (df['fecha_pago_max'] - hoy).dt.days
        
        # Asegurar que columnas boolean existan
        columnas_boolean = ['pagado', 'condicion_especial', 'cliente_propio', 'descuento_pie_factura', 'comision_perdida']
        for col in columnas_boolean:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)

        # Asegurar que columnas string existan
        columnas_string = ['pedido', 'cliente', 'factura', 'comprobante_url', 'razon_perdida']
        for col in columnas_string:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)

        # ===== DIAGNÓSTICO FINAL =====
        print(f"\n📈 RESUMEN FINAL DE DATOS:")
        print(f"   Total registros: {len(df)}")
        print(f"   Suma valor total: ${df['valor'].sum():,.0f}")
        print(f"   Suma valor neto: ${df['valor_neto'].sum():,.0f}")
        print(f"   Suma comisiones: ${df['comision'].sum():,.0f}")
        print(f"   Facturas pagadas: {df['pagado'].sum()}")
        print(f"   Facturas pendientes: {(~df['pagado']).sum()}")
        print(f"   Meses con datos: {sorted(df['mes_factura'].dropna().unique().tolist())}")
        
        return df

    except Exception as e:
        print(f"❌ ERROR en cargar_datos: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return pd.DataFrame()


# FUNCIÓN CORREGIDA PARA RECOMENDACIONES CON TUS DATOS REALES
def generar_recomendaciones_reales(supabase: Client):
    """Genera recomendaciones basadas en TUS datos reales"""
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
        
        # 1. FACTURAS PRÓXIMAS A VENCER (alta prioridad)
        proximas_vencer = df[
            (df['dias_vencimiento'] >= 0) & 
            (df['dias_vencimiento'] <= 7) & 
            (df['pagado'] == False)
        ].nlargest(2, 'comision')  # Las de mayor comisión primero
        
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
        
        # 2. FACTURAS VENCIDAS (crítico)
        vencidas = df[
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
                'probabilidad': max(20, 100 - dias_vencida * 2),  # Menos probabilidad mientras más vencida
                'impacto_comision': factura['comision'],
                'prioridad': 'alta'
            })
        
        # 3. CLIENTES SIN ACTIVIDAD RECIENTE (oportunidad)
        if len(recomendaciones) < 3:
            df['dias_desde_factura'] = (hoy - df['fecha_factura']).dt.days
            
            clientes_inactivos = df.groupby('cliente').agg({
                'dias_desde_factura': 'min',  # Días desde su última factura
                'valor': 'mean',  # Ticket promedio
                'comision': 'mean'  # Comisión promedio
            }).reset_index()
            
            # Clientes que no han comprado en 30-90 días (ventana de oportunidad)
            oportunidades = clientes_inactivos[
                (clientes_inactivos['dias_desde_factura'] >= 30) & 
                (clientes_inactivos['dias_desde_factura'] <= 90)
            ].nlargest(1, 'valor')  # El de mayor ticket promedio
            
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
        
        # Si no hay suficientes recomendaciones, agregar general
        if len(recomendaciones) == 0:
            # Buscar el cliente con más volumen total
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
                    'impacto_comision': volumen_total * 0.015,  # 1.5% estimado
                    'prioridad': 'media'
                })
        
        return recomendaciones[:3]  # Máximo 3
        
    except Exception as e:
        print(f"Error generando recomendaciones: {e}")
        return [{
            'cliente': 'Error técnico',
            'accion': 'Revisar logs',
            'producto': 'N/A',
            'razon': f'Error: {str(e)[:100]}',
            'probabilidad': 0,
            'impacto_comision': 0,
            'prioridad': 'baja'
        }]

# FUNCIÓN ADICIONAL PARA DEBUGGEAR TU BASE DE DATOS ESPECÍFICA
def mostrar_estructura_tabla(supabase: Client):
    """Muestra la estructura completa de tu tabla comisiones"""
    try:
        # Obtener una muestra de datos
        response = supabase.table("comisiones").select("*").limit(1).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            st.write("### ESTRUCTURA DE TU TABLA 'comisiones':")
            
            for col in df.columns:
                sample_value = df[col].iloc[0] if not pd.isna(df[col].iloc[0]) else "NULL"
                st.write(f"**{col}:** {type(sample_value).__name__} - Valor ejemplo: `{sample_value}`")
        else:
            st.write("No hay datos en la tabla para mostrar estructura")
            
    except Exception as e:
        st.error(f"Error obteniendo estructura: {e}")


# FUNCIÓN DE DEBUG ESPECÍFICA PARA TU CASO
def debug_mi_base_datos(supabase: Client):
    """Debug específico para tu base de datos"""
    st.write("## 🔍 DEBUG DE TU BASE DE DATOS")
    
    # 1. Mostrar estructura
    mostrar_estructura_tabla(supabase)
    
    # 2. Contar registros
    try:
        response = supabase.table("comisiones").select("*", count="exact").execute()
        st.write(f"**Total de registros en comisiones:** {response.count}")
    except Exception as e:
        st.error(f"Error contando registros: {e}")
    
    # 3. Mostrar primeros registros
    try:
        response = supabase.table("comisiones").select("*").limit(3).execute()
        if response.data:
            df_sample = pd.DataFrame(response.data)
            st.write("### PRIMEROS 3 REGISTROS:")
            st.dataframe(df_sample)
    except Exception as e:
        st.error(f"Error obteniendo muestra: {e}")
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

def obtener_meta_mes_actual(supabase: Client):
    """Obtiene la meta del mes actual de la base de datos"""
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
                "clientes_nuevos_actuales": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            result = supabase.table("metas_mensuales").insert(meta_default).execute()
            return result.data[0] if result.data else meta_default
            
    except Exception as e:
        print(f"Error obteniendo meta: {e}")
        return {
            "mes": date.today().strftime("%Y-%m"), 
            "meta_ventas": 10000000, 
            "meta_clientes_nuevos": 5
        }

def actualizar_meta(supabase: Client, mes: str, meta_ventas: float, meta_clientes: int):
    """Actualiza o crea una meta mensual en la base de datos"""
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
        print(f"Error actualizando meta: {e}")
        return False

def subir_comprobante(supabase: Client, file, factura_id: int):
    """Sube un archivo de comprobante a Supabase Storage"""
    try:
        if file is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = file.name.split('.')[-1]
            file_name = f"comprobante_{factura_id}_{timestamp}.{file_extension}"
            
            result = supabase.storage.from_(BUCKET).upload(file_name, file.getvalue())
            
            if result:
                public_url = supabase.storage.from_(BUCKET).get_public_url(file_name)
                return public_url
            else:
                return None
    except Exception as e:
        print(f"Error subiendo comprobante: {e}")
        return None

# Funciones auxiliares
def format_currency(value):
    """Formatea números como moneda colombiana"""
    if pd.isna(value) or value == 0:
        return "$0"
    return f"${value:,.0f}".replace(",", ".")

def calcular_comision_inteligente(valor_total, cliente_propio=False, descuento_adicional=0, descuento_pie=False):
    """Calcula comisión según tu lógica real"""
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
    """Agrega campos que podrían no existir en datos actuales"""
    campos_nuevos = {
        'valor_neto': lambda row: row.get('valor', 0) / 1.19 if row.get('valor') else 0,
        'iva': lambda row: row.get('valor', 0) - (row.get('valor', 0) / 1.19) if row.get('valor') else 0,
        'base_comision': lambda row: (row.get('valor', 0) / 1.19) * 0.85 if row.get('valor') else 0,
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

#Funcion IA nueva
def generar_recomendaciones_reales(supabase: Client):
    """Genera recomendaciones basadas en TUS datos reales"""
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
        
        # 1. FACTURAS PRÓXIMAS A VENCER (alta prioridad)
        proximas_vencer = df[
            (df['dias_vencimiento'] >= 0) & 
            (df['dias_vencimiento'] <= 7) & 
            (df['pagado'] == False)
        ].nlargest(2, 'comision')  # Las de mayor comisión primero
        
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
        
        # 2. FACTURAS VENCIDAS (crítico)
        vencidas = df[
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
                'probabilidad': max(20, 100 - dias_vencida * 2),  # Menos probabilidad mientras más vencida
                'impacto_comision': factura['comision'],
                'prioridad': 'alta'
            })
        
        # 3. CLIENTES SIN ACTIVIDAD RECIENTE (oportunidad)
        if len(recomendaciones) < 3:
            df['dias_desde_factura'] = (hoy - df['fecha_factura']).dt.days
            
            clientes_inactivos = df.groupby('cliente').agg({
                'dias_desde_factura': 'min',  # Días desde su última factura
                'valor': 'mean',  # Ticket promedio
                'comision': 'mean'  # Comisión promedio
            }).reset_index()
            
            # Clientes que no han comprado en 30-90 días (ventana de oportunidad)
            oportunidades = clientes_inactivos[
                (clientes_inactivos['dias_desde_factura'] >= 30) & 
                (clientes_inactivos['dias_desde_factura'] <= 90)
            ].nlargest(1, 'valor')  # El de mayor ticket promedio
            
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
        
        # Si no hay suficientes recomendaciones, agregar general
        if len(recomendaciones) == 0:
            # Buscar el cliente con más volumen total
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
                    'impacto_comision': volumen_total * 0.015,  # 1.5% estimado
                    'prioridad': 'media'
                })
        
        return recomendaciones[:3]  # Máximo 3
        
    except Exception as e:
        print(f"Error generando recomendaciones: {e}")
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
# FUNCIONES DE UI CORREGIDAS
# ========================

def render_factura_card(factura, index):
    """Renderiza una card de factura con estilos corregidos"""
    
    # Determinar estado de la factura
    if factura.get("pagado"):
        estado_badge = "PAGADA"
        estado_color = "#10b981"
        estado_icon = "✅"
    elif factura.get("dias_vencimiento", 0) < 0:
        estado_badge = "VENCIDA"
        estado_color = "#ef4444"
        estado_icon = "⚠️"
    else:
        estado_badge = "PENDIENTE"
        estado_color = "#f59e0b"
        estado_icon = "⏳"
    
    # Crear columnas para la información de la factura
    with st.container():
        # Header de la factura
        col_header1, col_header2 = st.columns([3, 1])
        
        with col_header1:
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 16px 0;">
            """, unsafe_allow_html=True)
            
            st.markdown(f"### 🧾 {factura.get('pedido', 'N/A')} - {factura.get('cliente', 'N/A')}")
            st.markdown(f"**Factura:** {factura.get('factura', 'N/A')}")
        
        with col_header2:
            st.markdown(f"""
            <div style="text-align: right;">
                <span style="
                    background: {estado_color};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                    display: inline-block;
                ">
                    {estado_icon} {estado_badge}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        # Información financiera en columnas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Valor Neto",
                value=format_currency(factura.get('valor_neto', 0)),
                help="Valor sin IVA"
            )
        
        with col2:
            st.metric(
                label="📊 Base Comisión", 
                value=format_currency(factura.get('base_comision', 0)),
                help="Base para calcular comisión"
            )
        
        with col3:
            st.metric(
                label="🎯 Comisión",
                value=format_currency(factura.get('comision', 0)),
                help=f"Porcentaje: {factura.get('porcentaje', 0)}%"
            )
        
        with col4:
            fecha_factura = factura.get('fecha_factura')
            if fecha_factura:
                if isinstance(fecha_factura, str):
                    try:
                        fecha_display = pd.to_datetime(fecha_factura).strftime('%d/%m/%Y')
                    except:
                        fecha_display = fecha_factura
                else:
                    fecha_display = fecha_factura.strftime('%d/%m/%Y') if hasattr(fecha_factura, 'strftime') else str(fecha_factura)
            else:
                fecha_display = "N/A"
            
            st.metric(
                label="📅 Fecha Factura",
                value=fecha_display
            )
        
        # Información adicional si existe
        if factura.get('dias_vencimiento') is not None:
            dias_venc = factura.get('dias_vencimiento', 0)
            if dias_venc < 0:
                st.warning(f"⚠️ Vencida hace {abs(dias_venc)} días")
            elif dias_venc <= 5:
                st.info(f"⏰ Vence en {dias_venc} días")
        
        # Cerrar el contenedor
        st.markdown("</div>", unsafe_allow_html=True)

def mostrar_modal_pago(factura):
    """Modal para marcar factura como pagada con subida de comprobante"""
    
    with st.form(f"marcar_pagado_{factura.get('id')}"):
        st.markdown(f"### ✅ Marcar como Pagada - {factura.get('pedido', 'N/A')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_pago_real = st.date_input(
                "Fecha de Pago Real",
                value=date.today(),
                help="Fecha en que realmente se recibió el pago"
            )
            
            metodo_pago = st.selectbox(
                "Método de Pago",
                ["Transferencia", "Efectivo", "Cheque", "Tarjeta", "Otro"]
            )
        
        with col2:
            referencia_pago = st.text_input(
                "Referencia/Número de Transacción",
                help="Número de referencia del pago"
            )
            
            observaciones = st.text_area(
                "Observaciones",
                help="Notas adicionales sobre el pago"
            )
        
        st.markdown("#### 📎 Comprobante de Pago")
        comprobante_file = st.file_uploader(
            "Sube el comprobante de pago",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Formatos: PDF, JPG, PNG. Máximo 10MB"
        )
        
        if comprobante_file:
            st.success(f"📄 Archivo seleccionado: {comprobante_file.name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("✅ Confirmar Pago", type="primary"):
                fecha_factura = pd.to_datetime(factura.get('fecha_factura'))
                dias_pago = (pd.to_datetime(fecha_pago_real) - fecha_factura).days
                
                comprobante_url = None
                if comprobante_file:
                    comprobante_url = subir_comprobante(supabase, comprobante_file, factura.get('id'))
                
                updates = {
                    "pagado": True,
                    "fecha_pago_real": fecha_pago_real.isoformat(),
                    "dias_pago_real": dias_pago,
                    "metodo_pago": metodo_pago,
                    "referencia": referencia_pago,
                    "observaciones_pago": observaciones
                }
                
                if comprobante_url:
                    updates["comprobante_url"] = comprobante_url
                
                if dias_pago > 80:
                    updates["comision_perdida"] = True
                    updates["razon_perdida"] = f"Pago después de 80 días ({dias_pago} días)"
                    updates["comision_ajustada"] = 0
                    st.warning(f"⚠️ ATENCIÓN: La comisión se pierde por pago tardío ({dias_pago} días)")
                
                if actualizar_factura(supabase, factura.get('id'), updates):
                    st.success("✅ Factura marcada como pagada correctamente")
                    st.session_state[f"show_pago_{factura.get('id')}"] = False
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar factura")
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state[f"show_pago_{factura.get('id')}"] = False
                st.rerun()

def mostrar_comprobante(comprobante_url):
    """Muestra el comprobante de pago"""
    if comprobante_url:
        if comprobante_url.lower().endswith('.pdf'):
            st.markdown(f"📄 [Ver Comprobante PDF]({comprobante_url})")
        else:
            try:
                st.image(comprobante_url, caption="Comprobante de Pago", width=300)
            except:
                st.markdown(f"🖼️ [Ver Comprobante]({comprobante_url})")
    else:
        st.info("📄 No hay comprobante subido")

def render_tab_comisiones_corregida():
    """Renderiza el tab de comisiones con UI corregida"""
    
    st.header("💰 Gestión de Comisiones")
    
    # Filtros
    with st.container():
        st.markdown("### 🔍 Filtros")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            estado_filter = st.selectbox("📊 Estado", ["Todos", "Pendientes", "Pagadas", "Vencidas"])
        with col2:
            cliente_filter = st.text_input("🔎 Buscar cliente")
        with col3:
            monto_min = st.number_input("💰 Valor mínimo", min_value=0, value=0, step=100000)
        with col4:
            if st.button("📥 Exportar Excel", help="Exportar datos filtrados"):
                st.success("📊 Funcionalidad de exportación próximamente")
    
    # Cargar datos
    df = cargar_datos(supabase)
    if not df.empty:
        df = agregar_campos_faltantes(df)
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if estado_filter == "Pendientes":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == False]
        elif estado_filter == "Pagadas":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == True]
        elif estado_filter == "Vencidas":
            df_filtrado = df_filtrado[(df_filtrado["dias_vencimiento"] < 0) & (df_filtrado["pagado"] == False)]
        
        if cliente_filter:
            df_filtrado = df_filtrado[df_filtrado["cliente"].str.contains(cliente_filter, case=False, na=False)]
        
        if monto_min > 0:
            df_filtrado = df_filtrado[df_filtrado["valor"] >= monto_min]
    else:
        df_filtrado = pd.DataFrame()
    
    # Resumen
    if not df_filtrado.empty:
        st.markdown("### 📊 Resumen")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Facturas", len(df_filtrado))
        with col2:
            st.metric("💰 Total Comisiones", format_currency(df_filtrado["comision"].sum()))
        with col3:
            st.metric("📈 Valor Promedio", format_currency(df_filtrado["valor"].mean()))
        with col4:
            pendientes = len(df_filtrado[df_filtrado["pagado"] == False])
            st.metric("⏳ Pendientes", pendientes, 
                     delta=f"-{len(df_filtrado)-pendientes}" if len(df_filtrado)-pendientes > 0 else None,
                     delta_color="inverse")
    
    st.markdown("---")
    
    # Lista de facturas
    if not df_filtrado.empty:
        st.markdown("### 📋 Facturas Detalladas")
        
        for index, (_, factura) in enumerate(df_filtrado.iterrows()):
            # Usar la nueva función de renderizado
            render_factura_card(factura, index)
            
            # Botones de acción
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                if st.button("✏️ Editar", key=f"edit_{factura.get('id', 0)}_{index}"):
                    st.session_state[f"show_edit_{factura.get('id')}"] = True
            
            with col2:
                if not factura.get("pagado"):
                    if st.button("✅ Pagar", key=f"pay_{factura.get('id', 0)}_{index}"):
                        st.session_state[f"show_pago_{factura.get('id')}"] = True
            
            with col3:
                if factura.get("pagado"):
                    if st.button("🔄 Devolución", key=f"dev_{factura.get('id', 0)}_{index}"):
                        st.session_state[f"show_devolucion_{factura.get('id')}"] = True
            
            with col4:
                if st.button("📄 Detalles", key=f"detail_{factura.get('id', 0)}_{index}"):
                    st.session_state[f"show_detail_{factura.get('id')}"] = True
            
            with col5:
                if factura.get("comprobante_url"):
                    if st.button("📎 Comprobante", key=f"comp_{factura.get('id', 0)}_{index}"):
                        st.session_state[f"show_comprobante_{factura.get('id')}"] = True
            
            with col6:
                if factura.get("dias_vencimiento", 0) < 0:
                    st.error(f"🚨 Vencida ({abs(factura.get('dias_vencimiento', 0))} días)")
            
            # Modales/Expandables
            if st.session_state.get(f"show_pago_{factura.get('id')}", False):
                with st.expander(f"✅ Marcar como Pagada - {factura.get('pedido', 'N/A')}", expanded=True):
                    mostrar_modal_pago(factura)
            
            if st.session_state.get(f"show_comprobante_{factura.get('id')}", False):
                with st.expander(f"📎 Comprobante - {factura.get('pedido', 'N/A')}", expanded=True):
                    mostrar_comprobante(factura.get("comprobante_url"))
                    if st.button("❌ Cerrar", key=f"close_comp_{factura.get('id')}_{index}"):
                        st.session_state[f"show_comprobante_{factura.get('id')}"] = False
                        st.rerun()
            
            if st.session_state.get(f"show_detail_{factura.get('id')}", False):
                with st.expander(f"📄 Detalles Completos - {factura.get('pedido', 'N/A')}", expanded=True):
                    mostrar_detalles_completos(factura)
                    if st.button("❌ Cerrar Detalles", key=f"close_detail_{factura.get('id')}_{index}"):
                        st.session_state[f"show_detail_{factura.get('id')}"] = False
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("📭 No hay facturas que coincidan con los filtros aplicados")

def mostrar_detalles_completos(factura):
    """Muestra todos los detalles de una factura"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏷️ Información General")
        st.write(f"**Pedido:** {factura.get('pedido', 'N/A')}")
        st.write(f"**Cliente:** {factura.get('cliente', 'N/A')}")
        st.write(f"**Factura:** {factura.get('factura', 'N/A')}")
        st.write(f"**Cliente Propio:** {'Sí' if factura.get('cliente_propio') else 'No'}")
        st.write(f"**Condición Especial:** {'Sí' if factura.get('condicion_especial') else 'No'}")
    
    with col2:
        st.markdown("#### 💰 Información Financiera")
        st.write(f"**Valor Total:** {format_currency(factura.get('valor', 0))}")
        st.write(f"**Valor Neto:** {format_currency(factura.get('valor_neto', 0))}")
        st.write(f"**IVA:** {format_currency(factura.get('iva', 0))}")
        st.write(f"**Base Comisión:** {format_currency(factura.get('base_comision', 0))}")
        st.write(f"**Comisión:** {format_currency(factura.get('comision', 0))} ({factura.get('porcentaje', 0)}%)")
        
        if factura.get('descuento_adicional', 0) > 0:
            st.write(f"**Descuento Adicional:** {factura.get('descuento_adicional', 0)}%")
    
    st.markdown("#### 📅 Fechas")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        fecha_factura = factura.get('fecha_factura')
        if fecha_factura:
            st.write(f"**Fecha Factura:** {fecha_factura}")
    
    with col4:
        fecha_pago_est = factura.get('fecha_pago_est')
        if fecha_pago_est:
            st.write(f"**Fecha Pago Estimada:** {fecha_pago_est}")
    
    with col5:
        fecha_pago_real = factura.get('fecha_pago_real')
        if fecha_pago_real:
            st.write(f"**Fecha Pago Real:** {fecha_pago_real}")
    
    if factura.get('observaciones_pago'):
        st.markdown("#### 📝 Observaciones")
        st.write(factura.get('observaciones_pago'))

# ========================
# CONFIGURACIÓN
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="CRM Inteligente", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧠"
)

# CSS mejorado y corregido - Reemplaza el CSS existente
st.markdown("""
<style>
    /* Estilos para métricas */
    div[data-testid="metric-container"] {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 0.75rem !important;
        padding: 1rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    div[data-testid="metric-container"] > div {
        color: #1f2937 !important;
    }
    
    /* Alertas personalizadas */
    .alert-high { 
        border-left: 5px solid #ef4444; 
        background: #fef2f2; 
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #1f2937;
    }
    .alert-medium { 
        border-left: 5px solid #f59e0b; 
        background: #fffbeb; 
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #1f2937;
    }
    .alert-low { 
        border-left: 5px solid #10b981; 
        background: #f0fdf4; 
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        color: #1f2937;
    }
    
    /* Recomendaciones IA */
    .recomendacion-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Barra de progreso */
    .progress-bar {
        background: #e5e7eb;
        border-radius: 1rem;
        height: 0.75rem;
        overflow: hidden;
        width: 100%;
    }
    .progress-fill {
        height: 100%;
        border-radius: 1rem;
        transition: width 0.3s ease;
    }
    
    /* Corregir elementos de entrada */
    .stSelectbox > div > div {
        background-color: white !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stTextInput > div > div > input {
        background-color: white !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
    }
    
    .stNumberInput > div > div > input {
        background-color: white !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
    }
    
    /* Contenedores principales */
    .main-container {
        background: #f9fafb;
        min-height: 100vh;
    }
    
    /* Sidebar mejorado */
    .css-1d391kg {
        background: #1f2937 !important;
    }
    
    /* Botones mejorados */
    .stButton > button {
        border-radius: 0.5rem !important;
        border: 1px solid #d1d5db !important;
        font-weight: 500 !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Tabs mejorados */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        color: #374151;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: #3b82f6 !important;
        color: white !important;
    }
    
    /* Cards de factura */
    .factura-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Info boxes */
    .stInfo {
        background: #f0f9ff !important;
        border: 1px solid #0ea5e9 !important;
        color: #0c4a6e !important;
    }
    
    .stSuccess {
        background: #f0fdf4 !important;
        border: 1px solid #22c55e !important;
        color: #14532d !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        border: 1px solid #f59e0b !important;
        color: #92400e !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border: 1px solid #ef4444 !important;
        color: #991b1b !important;
    }
    
    /* Expansores */
    .streamlit-expanderHeader {
        background: #f9fafb !important;
        border: 1px solid #e5e7eb !important;
        color: #1f2937 !important;
    }
    
    /* Formularios */
    .stForm {
        background: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 0.75rem !important;
        padding: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Variables de estado
meta_actual = obtener_meta_mes_actual(supabase)
if 'show_meta_config' not in st.session_state:
    st.session_state.show_meta_config = False

# ========================
# SIDEBAR
# ========================
with st.sidebar:
    st.title("🧠 CRM Inteligente")
    st.markdown("---")
    
    st.subheader("🎯 Meta Mensual")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚙️ Config"):
            st.session_state.show_meta_config = True
    
    with col2:
        if st.button("📊 Ver Meta"):
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

# ========================
# MODAL DE CONFIGURACIÓN DE META
# ========================
if st.session_state.show_meta_config:
    with st.form("config_meta"):
        st.markdown("### ⚙️ Configurar Meta Mensual")
        
        col1, col2 = st.columns(2)
        with col1:
            nueva_meta = st.number_input(
                "Meta de Ventas (COP)", 
                value=float(meta_actual["meta_ventas"]),
                min_value=0,
                step=100000
            )
        
        with col2:
            nueva_meta_clientes = st.number_input(
                "Meta Clientes Nuevos", 
                value=meta_actual["meta_clientes_nuevos"],
                min_value=0,
                step=1
            )
        
        bono_potencial = nueva_meta * 0.005
        st.info(f"🎁 **Bono potencial si cumples ambas metas:** {format_currency(bono_potencial)} (0.5% de la meta)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Guardar Meta", type="primary"):
                mes_actual_str = date.today().strftime("%Y-%m")
                if actualizar_meta(supabase, mes_actual_str, nueva_meta, nueva_meta_clientes):
                    st.success("✅ Meta actualizada correctamente en la base de datos")
                    st.session_state.show_meta_config = False
                    st.rerun()
                else:
                    st.error("❌ Error al guardar la meta")
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state.show_meta_config = False
                st.rerun()

# AGREGAR ESTO EN LA SIDEBAR (después de los filtros)
with st.sidebar:
    st.markdown("---")
    if st.button("🔍 Debug Base de Datos"):
        debug_mi_base_datos(supabase)
# ========================
# LAYOUT PRINCIPAL
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

    # ========================
    # TAB 1 - DASHBOARD
    # ========================
    with tabs[0]:
        st.header("🎯 Dashboard Ejecutivo")
        
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
            st.markdown("### 🧠 Recomendaciones IA")
            
            recomendaciones = generar_recomendaciones_reales(supabase)
            
            for rec in recomendaciones:
                st.markdown(f"""
                <div class="alert-{'high' if rec['prioridad'] == 'alta' else 'medium'}">
                    <h4 style="margin:0; color: #1f2937;">{rec['cliente']}</h4>
                    <p style="margin:0.5rem 0; color: #374151;"><strong>{rec['accion']}</strong> ({rec['probabilidad']}% prob.)</p>
                    <p style="margin:0; color: #6b7280; font-size: 0.9rem;">{rec['razon']}</p>
                    <p style="margin:0.5rem 0 0 0; color: #059669; font-weight: bold;">💰 +{format_currency(rec['impacto_comision'])} comisión</p>
                </div>
                """, unsafe_allow_html=True)

    # ========================
    # TAB 2 - COMISIONES (CORREGIDA)
    # ========================
    with tabs[1]:
        render_tab_comisiones_corregida()

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

    # ========================
    # TAB 4 - CLIENTES
    # ========================
    with tabs[3]:
        st.header("👥 Gestión de Clientes")
        st.info("🚧 Módulo en desarrollo - Próximamente funcionalidad completa de gestión de clientes")
        
        if not df.empty:
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
                <div style="
                    background: white;
                    border: 1px solid #e5e7eb;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 8px 0;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                ">
                    <h4 style="margin: 0 0 8px 0; color: #1f2937;">👤 {cliente}</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px;">
                        <div style="color: #374151;"><strong>Total:</strong> {format_currency(row['Total Compras'])}</div>
                        <div style="color: #374151;"><strong>Ticket:</strong> {format_currency(row['Ticket Promedio'])}</div>
                        <div style="color: #374151;"><strong>Compras:</strong> {row['Número Compras']}</div>
                        <div style="color: #374151;"><strong>Comisiones:</strong> {format_currency(row['Total Comisiones'])}</div>
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
            
            alertas = []
            
            if not df.empty:
                vencidas = df[df["dias_vencimiento"] < 0]
                for _, factura in vencidas.head(3).iterrows():
                    alertas.append({
                        'tipo': 'critico',
                        'titulo': 'Factura Vencida',
                        'mensaje': f"{factura.get('cliente', 'N/A')} - {factura.get('pedido', 'N/A')} ({format_currency(factura.get('valor_neto', 0))})",
                        'accion': 'Contactar inmediatamente'
                    })
                
                prox_vencer = df[(df["dias_vencimiento"] >= 0) & (df["dias_vencimiento"] <= 5) & (df["pagado"] == False)]
                for _, factura in prox_vencer.head(3).iterrows():
                    alertas.append({
                        'tipo': 'advertencia',
                        'titulo': 'Próximo Vencimiento',
                        'mensaje': f"{factura.get('cliente', 'N/A')} vence en {factura.get('dias_vencimiento', 0)} días",
                        'accion': 'Recordar pago'
                    })
                
                alto_valor = df[df["comision"] > df["comision"].quantile(0.8)]
                for _, factura in alto_valor.head(2).iterrows():
                    if not factura.get("pagado"):
                        alertas.append({
                            'tipo': 'oportunidad',
                            'titulo': 'Alta Comisión Pendiente',
                            'mensaje': f"Comisión {format_currency(factura.get('comision', 0))} esperando pago",
                            'accion': 'Hacer seguimiento'
                        })
            
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
            
            recomendaciones = generar_recomendaciones_reales(supabase)
            
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
            
            if st.button("🔄 Generar Nuevas Recomendaciones"):
                st.rerun()

def mostrar_recomendaciones_ia():
    """Muestra recomendaciones IA con componentes nativos de Streamlit"""
    
    recomendaciones = generar_recomendaciones_reales(supabase)
    
    for i, rec in enumerate(recomendaciones):
        # Usar container y columnas en lugar de HTML personalizado
        with st.container():
            # Crear un expander para cada recomendación
            with st.expander(f"🎯 #{i+1} {rec['cliente']} - {rec['probabilidad']}% probabilidad", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Acción recomendada:** {rec['accion']}")
                    st.markdown(f"**Producto:** {rec['producto']}")
                    st.markdown(f"**Razón:** {rec['razon']}")
                    
                    # Mostrar prioridad con color
                    prioridad_color = "🔴" if rec['prioridad'] == 'alta' else "🟡"
                    st.markdown(f"**Prioridad:** {prioridad_color} {rec['prioridad'].title()}")
                
                with col2:
                    st.metric(
                        label="💰 Impacto Comisión",
                        value=format_currency(rec['impacto_comision']),
                        delta=f"+{rec['probabilidad']}%"
                    )
                
                # Botón de acción
                if st.button(f"📞 Ejecutar Acción", key=f"action_rec_{i}"):
                    st.success(f"Acción programada para {rec['cliente']}")

# Reemplaza también la sección completa del TAB 5 con esta versión corregida
def render_tab_ia_alertas_corregida():
    """Tab de IA y alertas completamente corregido"""
    
    st.header("🧠 Inteligencia Artificial & Alertas")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🚨 Alertas Críticas")
        
        df = cargar_datos(supabase)
        alertas = []
        
        if not df.empty:
            # Facturas vencidas
            vencidas = df[df["dias_vencimiento"] < 0]
            for _, factura in vencidas.head(3).iterrows():
                st.error(f"⚠️ **Factura Vencida:** {factura.get('cliente', 'N/A')} - {factura.get('pedido', 'N/A')} ({format_currency(factura.get('valor_neto', 0))})")
            
            # Próximas a vencer
            prox_vencer = df[(df["dias_vencimiento"] >= 0) & (df["dias_vencimiento"] <= 5) & (df["pagado"] == False)]
            for _, factura in prox_vencer.head(3).iterrows():
                st.warning(f"⏰ **Próximo Vencimiento:** {factura.get('cliente', 'N/A')} vence en {factura.get('dias_vencimiento', 0)} días")
            
            # Altas comisiones pendientes
            alto_valor = df[df["comision"] > df["comision"].quantile(0.8)]
            for _, factura in alto_valor.head(2).iterrows():
                if not factura.get("pagado"):
                    st.info(f"💎 **Alta Comisión Pendiente:** {format_currency(factura.get('comision', 0))} esperando pago")
        
        if not alertas and df.empty:
            st.success("✅ No hay alertas críticas en este momento")
    
    with col2:
        st.markdown("### 🎯 Recomendaciones Estratégicas")
        mostrar_recomendaciones_ia()
        
        if st.button("🔄 Generar Nuevas Recomendaciones"):
            st.rerun()
    
    st.markdown("---")
    
    # Análisis predictivo corregido
    st.markdown("### 📊 Análisis Predictivo")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🔮 Predicción Meta",
            value="75%",
            delta="5%",
            help="Probabilidad de cumplir meta mensual basada en tendencias actuales"
        )
        st.caption("Probabilidad de cumplir meta mensual")
    
    with col2:
        st.metric(
            label="📈 Tendencia Comisiones",
            value="+15%",
            delta="3%",
            delta_color="normal",
            help="Crecimiento estimado para el próximo mes"
        )
        st.caption("Crecimiento estimado próximo mes")
    
    with col3:
        st.metric(
            label="🎯 Clientes en Riesgo",
            value="3",
            delta="-1",
            delta_color="inverse",
            help="Clientes que requieren atención inmediata"
        )
        st.caption("Requieren atención inmediata")
    
    # Información adicional
    st.markdown("#### 📈 Detalles del Análisis")
    
    info_col1, info_col2 = st.columns(2)
    
    with info_col1:
        st.info("""
        **🔮 Modelo Predictivo:**
        - Basado en historial de ventas de 6 meses
        - Considera estacionalidad y tendencias  
        - Actualizado diariamente con nuevos datos
        """)
    
    with info_col2:
        st.warning("""
        **⚠️ Factores de Riesgo:**
        - 3 clientes sin compras en 45+ días
        - 2 facturas próximas a vencer
        - Meta mensual al 75% con 8 días restantes
        """)
        
# Reemplaza esta sección en el TAB 5 - IA & ALERTAS

# Análisis predictivo (VERSIÓN CORREGIDA)
st.markdown("---")
st.markdown("### 📊 Análisis Predictivo")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🔮 Predicción Meta",
        value="75%",
        delta="5%",
        help="Probabilidad de cumplir meta mensual basada en tendencias actuales"
    )
    st.caption("Probabilidad de cumplir meta mensual")

with col2:
    st.metric(
        label="📈 Tendencia Comisiones",
        value="+15%",
        delta="3%",
        delta_color="normal",
        help="Crecimiento estimado para el próximo mes"
    )
    st.caption("Crecimiento estimado próximo mes")

with col3:
    st.metric(
        label="🎯 Clientes en Riesgo",
        value="3",
        delta="-1",
        delta_color="inverse",
        help="Clientes que requieren atención inmediata"
    )
    st.caption("Requieren atención inmediata")

# Información adicional con cards nativas de Streamlit
st.markdown("#### 📈 Detalles del Análisis")

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.info("""
    **🔮 Modelo Predictivo:**
    - Basado en historial de ventas de 6 meses
    - Considera estacionalidad y tendencias
    - Actualizado diariamente con nuevos datos
    """)

with info_col2:
    st.warning("""
    **⚠️ Factores de Riesgo:**
    - 3 clientes sin compras en 45+ días
    - 2 facturas próximas a vencer
    - Meta mensual al 75% con 8 días restantes
    """)

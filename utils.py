# utils_mejoradas.py
from datetime import datetime
import pandas as pd

def safe_get_public_url(supabase, bucket: str, path: str):
    """Obtiene la URL pública de un archivo en Supabase Storage (igual que antes)"""
    try:
        res = supabase.storage.from_(bucket).get_public_url(path)
        if isinstance(res, dict):
            for key in ("publicUrl", "public_url", "publicURL", "publicurl", "url"):
                if key in res:
                    return res[key]
            return str(res)
        return res
    except Exception:
        return None

def calcular_comision_legacy(valor, porcentaje):
    """Función de compatibilidad con código anterior"""
    return valor * (porcentaje / 100)

def format_currency(value):
    """Formatea un número a pesos colombianos"""
    if pd.isna(value) or value is None:
        return "$0"
    return f"${value:,.0f}"

def now_iso():
    """Devuelve la fecha y hora actual en formato ISO"""
    return datetime.now().isoformat()

def calcular_dias_entre_fechas(fecha_inicio, fecha_fin):
    """Calcula días entre dos fechas"""
    if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
        return None
    return (fecha_fin - fecha_inicio).days

def clasificar_cliente_automatico(historial_compras, ticket_promedio, frecuencia_dias):
    """Clasifica cliente en A, B, C automáticamente"""
    # Lógica de clasificación basada en RFM (Recency, Frequency, Monetary)
    score = 0
    
    # Monetary (40% del score)
    if ticket_promedio >= 1000000:
        score += 40
    elif ticket_promedio >= 500000:
        score += 25
    else:
        score += 10
    
    # Frequency (35% del score)  
    if frecuencia_dias <= 30:
        score += 35
    elif frecuencia_dias <= 60:
        score += 20
    else:
        score += 5
    
    # Recency se calcularía con última compra (25% restante)
    # Por ahora usar historial como proxy
    if historial_compras >= 5:
        score += 25
    elif historial_compras >= 2:
        score += 15
    else:
        score += 5
    
    # Clasificación final
    if score >= 80:
        return 'A'
    elif score >= 50:
        return 'B'
    else:
        return 'C'

def generar_alerta_vencimiento(factura_data):
    """Genera alertas basadas en estado de factura"""
    alertas = []
    
    dias_venc = factura_data.get('dias_vencimiento', 0)
    dias_pago = factura_data.get('dias_pago_real', 0)
    
    # Alertas por vencimiento
    if dias_venc is not None:
        if dias_venc < 0:
            alertas.append({
                'tipo': 'critico',
                'mensaje': f'Factura vencida hace {abs(dias_venc)} días'
            })
        elif dias_venc <= 5:
            alertas.append({
                'tipo': 'advertencia', 
                'mensaje': f'Vence en {dias_venc} días'
            })
    
    # Alertas por riesgo de pérdida de descuento
    if not factura_data.get('descuento_pie_factura', False):
        limite = 60 if factura_data.get('condicion_especial', False) else 45
        if dias_pago and dias_pago > limite:
            alertas.append({
                'tipo': 'advertencia',
                'mensaje': 'Perdió descuento por pago tardío'
            })
    
    # Alerta por riesgo de pérdida de comisión
    if dias_pago and dias_pago > 70:
        alertas.append({
            'tipo': 'critico',
            'mensaje': 'RIESGO: Cerca de perder comisión (80 días)'
        })
    elif dias_pago and dias_pago > 80:
        alertas.append({
            'tipo': 'critico',
            'mensaje': 'COMISIÓN PERDIDA: Más de 80 días sin pago'
        })
    
    return alertas

def exportar_excel(df, nombre_archivo="comisiones_export"):
    """Exporta DataFrame a Excel con formato"""
    try:
        # Preparar datos para exportación
        df_export = df.copy()
        
        # Seleccionar y renombrar columnas relevantes
        columnas_export = {
            'pedido': 'Pedido',
            'cliente': 'Cliente', 
            'factura': 'Factura',
            'valor_neto': 'Valor Neto',
            'base_comision': 'Base Comisión',
            'porcentaje': 'Porcentaje (%)',
            'comision': 'Comisión',
            'fecha_factura': 'Fecha Factura',
            'fecha_pago_real': 'Fecha Pago',
            'dias_pago_real': 'Días Pago',
            'cliente_propio': 'Cliente Propio',
            'pagado': 'Pagado',
            'comision_perdida': 'Comisión Perdida'
        }
        
        df_export = df_export[list(columnas_export.keys())].rename(columns=columnas_export)
        
        # Formatear valores monetarios
        for col in ['Valor Neto', 'Base Comisión', 'Comisión']:
            df_export[col] = df_export[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "$0")
        
        # Formatear porcentajes
        df_export['Porcentaje (%)'] = df_export['Porcentaje (%)'].apply(lambda x: f"{x}%" if pd.notna(x) else "0%")
        
        # Formatear fechas
        for col in ['Fecha Factura', 'Fecha Pago']:
            df_export[col] = pd.to_datetime(df_export[col]).dt.strftime('%Y-%m-%d')
        
        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_final = f"{nombre_archivo}_{timestamp}.xlsx"
        
        return df_export.to_excel(nombre_final, index=False)
        
    except Exception as e:
        print(f"Error exportando a Excel: {e}")
        return False

def validar_datos_venta(data):
    """Valida los datos de una venta antes de insertar"""
    errores = []
    
    # Campos obligatorios
    if not data.get('pedido'):
        errores.append("Número de pedido es obligatorio")
    
    if not data.get('cliente'):
        errores.append("Cliente es obligatorio")
    
    if not data.get('valor_neto') or data.get('valor_neto') <= 0:
        errores.append("Valor neto debe ser mayor a 0")
    
    # Validaciones lógicas
    if data.get('descuento_adicional', 0) > 50:
        errores.append("Descuento adicional parece muy alto (>50%)")
    
    if data.get('valor_total') and data.get('valor_neto'):
        iva_calculado = data['valor_total'] - data['valor_neto']
        iva_esperado = data['valor_neto'] * 0.19
        if abs(iva_calculado - iva_esperado) > 1000:  # Tolerancia de $1000
            errores.append("El IVA no parece correcto (debería ser 19%)")
    
    return errores

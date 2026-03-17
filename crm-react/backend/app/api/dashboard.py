from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
import sys
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# Agregar el directorio raíz al path para importar módulos existentes
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

load_dotenv()

router = APIRouter()

def limpiar_nan_para_json(data):
    """Reemplaza NaN, inf y -inf con valores válidos para JSON"""
    if isinstance(data, pd.DataFrame):
        # Reemplazar NaN en el DataFrame
        data = data.fillna(0)
        # Convertir a dict y limpiar valores infinitos
        result = data.to_dict('records')
        for record in result:
            for key, value in record.items():
                if isinstance(value, (float, np.floating)):
                    if pd.isna(value) or np.isinf(value):
                        record[key] = 0
        return result
    elif isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, (float, np.floating)):
                if pd.isna(value) or np.isinf(value):
                    result[key] = 0
                else:
                    result[key] = float(value)
            elif isinstance(value, dict):
                result[key] = limpiar_nan_para_json(value)
            elif isinstance(value, list):
                result[key] = [limpiar_nan_para_json(item) if isinstance(item, (dict, pd.DataFrame)) else (0 if isinstance(item, (float, np.floating)) and (pd.isna(item) or np.isinf(item)) else item) for item in value]
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [limpiar_nan_para_json(item) if isinstance(item, (dict, pd.DataFrame)) else (0 if isinstance(item, (float, np.floating)) and (pd.isna(item) or np.isinf(item)) else item) for item in data]
    elif isinstance(data, (float, np.floating)):
        if pd.isna(data) or np.isinf(data):
            return 0
        return float(data)
    return data

@router.get("/metrics")
async def get_dashboard_metrics(mes: str = None) -> Dict[str, Any]:
    """
    Obtiene las métricas principales del dashboard del vendedor
    Filtra por mes seleccionado (formato: YYYY-MM) o mes actual si no se especifica
    Solo muestra datos de clientes propios
    """
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        from datetime import datetime, date
        from fastapi import Query
        import pandas as pd

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Faltan variables de entorno para conectar a Supabase.",
                    "errors": env_status["errors"],
                },
            )
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        # Determinar si mostrar todo o filtrar por mes
        ver_todo = mes is None or mes == "" or mes.lower() == "todos"
        
        if ver_todo:
            mes_filtro = None  # No filtrar por mes
            meta_ventas = 0  # No hay meta cuando se ve todo
        else:
            mes_filtro = mes  # Formato: "2024-12"
            # Obtener meta del mes seleccionado
            try:
                meta_response = supabase.table("metas_mensuales").select("*").eq("mes", mes_filtro).execute()
                if meta_response.data and len(meta_response.data) > 0:
                    meta_actual = meta_response.data[0]
                    meta_ventas = float(meta_actual.get('meta_ventas', 0))
                else:
                    # Si no hay meta para ese mes, usar valor por defecto
                    meta_ventas = 0
            except Exception as e:
                print(f"Error obteniendo meta: {e}")
                meta_ventas = 0
        
        # Obtener datos
        df = db_manager._cargar_datos_raw()  # Sin cache para datos frescos
        
        if df.empty:
            return {
                "totalVentas": 0,
                "comisiones": 0,
                "clientesActivos": 0,
                "pedidosMes": 0,
                "metaVentas": meta_ventas,
                "progresoMeta": 0,
                "faltanteMeta": meta_ventas,
                "facturasDetalle": []
            }
        
        # Convertir fecha_factura a datetime (dayfirst=True para formato DD/MM/YYYY)
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce', dayfirst=True)
        df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)
        
        # Filtrar por mes seleccionado (si aplica) y solo clientes propios
        if mes_filtro:
            df_mes_propios = df[
                (df['mes_factura'] == mes_filtro) & 
                (df.get('cliente_propio', False) == True)
            ].copy()
        else:
            # Ver todo: solo filtrar por clientes propios
            df_mes_propios = df[
                (df.get('cliente_propio', False) == True)
            ].copy()
        
        # Calcular métricas del mes seleccionado (o todos) y clientes propios
        # IMPORTANTE: Restar devoluciones del total de ventas
        # valor_devuelto incluye IVA, por lo que se resta directamente del valor total
        
        # Obtener devoluciones (del mes seleccionado o todas)
        devoluciones_mes = pd.DataFrame()
        try:
            df_devoluciones = db_manager.cargar_devoluciones()
            if not df_devoluciones.empty and 'fecha_devolucion' in df_devoluciones.columns:
                df_devoluciones['fecha_devolucion'] = pd.to_datetime(df_devoluciones['fecha_devolucion'], errors='coerce')
                df_devoluciones['mes_devolucion'] = df_devoluciones['fecha_devolucion'].dt.to_period('M').astype(str)
                if mes_filtro:
                    devoluciones_mes = df_devoluciones[df_devoluciones['mes_devolucion'] == mes_filtro].copy()
                else:
                    # Ver todo: incluir todas las devoluciones
                    devoluciones_mes = df_devoluciones.copy()
        except Exception as e:
            print(f"Error cargando devoluciones: {e}")
            devoluciones_mes = pd.DataFrame()
        
        # Calcular total de devoluciones (del mes o todas)
        total_devoluciones_mes = 0
        if not devoluciones_mes.empty:
            # Filtrar solo devoluciones de clientes propios
            # Necesitamos obtener el cliente_propio de cada factura relacionada
            facturas_ids_devoluciones = devoluciones_mes['factura_id'].unique().tolist()
            if facturas_ids_devoluciones:
                try:
                    facturas_devoluciones = supabase.table("comisiones").select("id, cliente_propio").in_("id", facturas_ids_devoluciones).execute()
                    facturas_propios_ids = {f['id']: f.get('cliente_propio', True) for f in facturas_devoluciones.data if f.get('cliente_propio', True)}
                    # Filtrar devoluciones solo de clientes propios
                    devoluciones_mes = devoluciones_mes[devoluciones_mes['factura_id'].isin(facturas_propios_ids.keys())].copy()
                    total_devoluciones_mes = devoluciones_mes['valor_devuelto'].fillna(0).sum() if 'valor_devuelto' in devoluciones_mes.columns else 0
                except Exception as e:
                    print(f"Error filtrando devoluciones por cliente_propio: {e}")
                    total_devoluciones_mes = devoluciones_mes['valor_devuelto'].fillna(0).sum() if 'valor_devuelto' in devoluciones_mes.columns else 0
        
        if not df_mes_propios.empty:
            # Calcular valor total de ventas del mes SIN IVA y DESPUÉS de descuentos
            # 1. Obtener valor_neto (sin IVA) de cada factura
            df_mes_propios = df_mes_propios.copy()
            if 'valor_neto' not in df_mes_propios.columns or df_mes_propios['valor_neto'].isna().all():
                # Si no hay valor_neto, calcularlo desde valor (sin flete)
                if 'valor_flete' in df_mes_propios.columns:
                    valor_sin_flete = df_mes_propios['valor'].fillna(0) - df_mes_propios['valor_flete'].fillna(0)
                else:
                    valor_sin_flete = df_mes_propios['valor'].fillna(0)
                df_mes_propios['valor_neto'] = valor_sin_flete / 1.19
            else:
                df_mes_propios['valor_neto'] = df_mes_propios['valor_neto'].fillna(0)
            
            # 2. Restar descuentos en pesos si existen
            if 'valor_descuento_pesos' in df_mes_propios.columns:
                df_mes_propios['valor_neto_ajustado'] = df_mes_propios['valor_neto'] - df_mes_propios['valor_descuento_pesos'].fillna(0)
            else:
                df_mes_propios['valor_neto_ajustado'] = df_mes_propios['valor_neto']
            
            # 3. Sumar valor neto ajustado (sin IVA, después de descuentos)
            total_ventas_bruto = df_mes_propios['valor_neto_ajustado'].sum()
            
            # 4. Restar devoluciones de facturas del mes (convertir a valor sin IVA)
            devoluciones_facturas_mes = 0
            if 'valor_devuelto' in df_mes_propios.columns:
                # valor_devuelto incluye IVA, se divide por 1.19 para obtener valor sin IVA
                devoluciones_facturas_mes = (df_mes_propios['valor_devuelto'].fillna(0) / 1.19).sum()
            
            # 5. Sumar devoluciones del mes (de facturas de cualquier mes) - convertir a valor sin IVA
            # El total_devoluciones_mes ya está en valor con IVA, se divide por 1.19
            total_devoluciones_mes_sin_iva = float(total_devoluciones_mes) / 1.19 if total_devoluciones_mes > 0 else 0
            
            # 6. Calcular total de ventas neto (valor sin IVA, después de descuentos, restando devoluciones sin IVA)
            total_ventas = float(total_ventas_bruto) - float(devoluciones_facturas_mes) - float(total_devoluciones_mes_sin_iva)
            total_ventas = max(0, total_ventas)  # No puede ser negativo
        else:
            # Si no hay facturas del mes, pero hay devoluciones del mes, el total es negativo de devoluciones (sin IVA)
            total_ventas = max(0, -float(total_devoluciones_mes) / 1.19)
        
        # RECALCULAR comisión estimada basándose en el porcentaje de cada venta
        # Esto asegura que la comisión sea consistente con las reglas de negocio
        comisiones = 0
        if not df_mes_propios.empty:
            from business.calculations import ComisionCalculator
            
            # Obtener descuentos_predeterminados de todos los clientes únicos para optimizar consultas
            clientes_unicos = df_mes_propios['cliente'].unique().tolist()
            descuentos_clientes = {}
            try:
                clientes_response = supabase.table("clientes_b2b").select("nombre, descuento_predeterminado").in_("nombre", clientes_unicos).execute()
                for cliente_data in clientes_response.data:
                    descuentos_clientes[cliente_data['nombre']] = float(cliente_data.get('descuento_predeterminado', 0) or 0)
            except Exception as e:
                print(f"⚠️ No se pudieron obtener descuentos_predeterminados: {e}")
            
            # Calcular comisión para cada venta del mes
            for _, row in df_mes_propios.iterrows():
                # Obtener valores necesarios
                valor_neto = row.get('valor_neto', 0)
                if valor_neto == 0 or pd.isna(valor_neto):
                    # Si no hay valor_neto, calcularlo desde valor
                    valor_total = row.get('valor', 0)
                    if valor_total and not pd.isna(valor_total):
                        valor_neto = valor_total / 1.19
                
                cliente_propio = row.get('cliente_propio', False)
                descuento_pie_factura = row.get('descuento_pie_factura', False)
                descuento_aplicado = row.get('descuento_adicional', 0) or row.get('descuento_aplicado', 0)
                valor_devuelto = row.get('valor_devuelto', 0) or 0
                dias_pago = row.get('dias_pago_real')
                condicion_especial = row.get('condicion_especial', False)
                nombre_cliente = row.get('cliente', '')
                descuento_predeterminado = descuentos_clientes.get(nombre_cliente, 0)
                
                # Calcular base de comisión
                if descuento_pie_factura:
                    base = valor_neto
                else:
                    limite_dias = 60 if condicion_especial else 45
                    if not dias_pago or dias_pago <= limite_dias:
                        base = valor_neto * 0.85
                    else:
                        base = valor_neto
                
                # Restar devoluciones
                base_final = base - (valor_devuelto / 1.19 if valor_devuelto else 0)
                base_final = max(0, base_final)  # No puede ser negativo
                
                # Determinar porcentaje según reglas de negocio
                # REGLA: Si el descuento base es > 15%, pierde un punto (1.5% en lugar de 2.5%)
                # También si hay descuento adicional, pierde un punto
                tiene_descuento_adicional = descuento_aplicado > 0
                descuento_base_superior_15 = descuento_predeterminado > 15
                if cliente_propio:
                    porcentaje = 1.5 if (descuento_base_superior_15 or tiene_descuento_adicional) else 2.5
                else:
                    porcentaje = 0.5 if (descuento_base_superior_15 or tiene_descuento_adicional) else 1.0
                
                # Verificar pérdida por +80 días
                if dias_pago and dias_pago > 80:
                    comision_venta = 0
                else:
                    comision_venta = base_final * (porcentaje / 100)
                
                comisiones += comision_venta
        
        # Limpiar NaN
        total_ventas = float(total_ventas) if not pd.isna(total_ventas) else 0
        comisiones = float(comisiones) if not pd.isna(comisiones) else 0
        
        # Clientes activos del mes (solo propios)
        clientes_activos = df_mes_propios['cliente'].nunique() if not df_mes_propios.empty and 'cliente' in df_mes_propios.columns else 0
        
        # Pedidos del mes
        pedidos_mes = len(df_mes_propios) if not df_mes_propios.empty else 0
        
        # Información de diagnóstico (solo en desarrollo)
        diagnostico = {}
        if not df_mes_propios.empty:
            diagnostico = {
                "total_filas": len(df_mes_propios),
                "tiene_comision_ajustada": 'comision_ajustada' in df_mes_propios.columns,
                "tiene_comision": 'comision' in df_mes_propios.columns,
                "suma_comision_ajustada": float(df_mes_propios['comision_ajustada'].sum()) if 'comision_ajustada' in df_mes_propios.columns else None,
                "suma_comision": float(df_mes_propios['comision'].sum()) if 'comision' in df_mes_propios.columns else None,
                "columnas_disponibles": list(df_mes_propios.columns)
            }
        
        # Calcular progreso de meta (solo si hay meta definida y no es "Ver todo")
        if ver_todo or meta_ventas == 0:
            progreso_meta = 0
            faltante_meta = 0
        else:
            progreso_meta = (total_ventas / meta_ventas * 100) if meta_ventas > 0 else 0
            faltante_meta = max(0, meta_ventas - total_ventas)
        
        # Preparar detalle de facturas para el desglose
        # Formato similar al reporte de la empresa: cada factura/devolución como línea separada
        facturas_detalle = []
        
        # 1. Agregar facturas del mes seleccionado (cada factura como línea positiva)
        if not df_mes_propios.empty:
            for _, row in df_mes_propios.iterrows():
                # Calcular valor_neto (sin IVA)
                valor_neto = row.get('valor_neto', 0)
                if valor_neto == 0 or pd.isna(valor_neto):
                    # Si no hay valor_neto, calcularlo desde valor (sin flete)
                    valor_total = float(row.get('valor', 0)) if pd.notna(row.get('valor')) else 0
                    valor_flete = float(row.get('valor_flete', 0)) if pd.notna(row.get('valor_flete')) else 0
                    valor_sin_flete = valor_total - valor_flete
                    valor_neto = valor_sin_flete / 1.19
                
                # Restar descuentos en pesos
                valor_descuento_pesos = float(row.get('valor_descuento_pesos', 0)) if pd.notna(row.get('valor_descuento_pesos')) else 0
                valor_neto_ajustado = float(valor_neto) - valor_descuento_pesos
                
                # Devoluciones (convertir a valor sin IVA)
                valor_devuelto_factura = float(row.get('valor_devuelto', 0)) if pd.notna(row.get('valor_devuelto')) else 0
                valor_devuelto_sin_iva = valor_devuelto_factura / 1.19 if valor_devuelto_factura > 0 else 0
                
                fecha_factura = row.get('fecha_factura', '')
                if pd.notna(fecha_factura):
                    if isinstance(fecha_factura, pd.Timestamp):
                        fecha_factura_str = fecha_factura.strftime('%Y-%m-%d')
                    else:
                        fecha_factura_str = str(fecha_factura)
                else:
                    fecha_factura_str = ''
                
                # Agregar la factura (valor positivo, sin IVA, después de descuentos)
                facturas_detalle.append({
                    "id": int(row.get('id', 0)),
                    "pedido": str(row.get('pedido', 'N/A')),
                    "factura": str(row.get('factura', 'N/A')),
                    "cliente": str(row.get('cliente', 'N/A')),
                    "fecha_factura": fecha_factura_str,
                    "valor_bruto": float(valor_neto_ajustado),  # Valor sin IVA, después de descuentos
                    "valor_devuelto": 0,  # Las devoluciones se muestran como líneas separadas
                    "valor_neto": float(valor_neto_ajustado),  # Valor neto después de descuentos
                    "valor_transaccion": float(valor_neto_ajustado),  # Valor de la transacción (positivo para ventas)
                    "tipo": "factura"  # Factura del mes seleccionado
                })
                
                # Si hay devoluciones en esta factura, agregarlas como líneas negativas separadas (sin IVA)
                if valor_devuelto_sin_iva > 0:
                    facturas_detalle.append({
                        "id": int(row.get('id', 0)),
                        "pedido": str(row.get('pedido', 'N/A')),
                        "factura": str(row.get('factura', 'N/A')),
                        "cliente": str(row.get('cliente', 'N/A')),
                        "fecha_factura": fecha_factura_str,
                        "valor_bruto": 0,
                        "valor_devuelto": valor_devuelto_sin_iva,
                        "valor_neto": -valor_devuelto_sin_iva,
                        "valor_transaccion": -valor_devuelto_sin_iva,  # Negativo para devoluciones (sin IVA)
                        "tipo": "devolucion_factura_mes"  # Devolución de factura del mes
                    })
        
        # 2. Agregar devoluciones del mes de facturas de meses anteriores (como líneas negativas)
        if not devoluciones_mes.empty:
            # Obtener IDs de facturas únicas de las devoluciones
            facturas_ids_devoluciones = devoluciones_mes['factura_id'].unique().tolist()
            
            # Obtener información de esas facturas
            try:
                facturas_devoluciones_response = supabase.table("comisiones").select("*").in_("id", facturas_ids_devoluciones).execute()
                
                if facturas_devoluciones_response.data:
                    # Agrupar devoluciones por factura_id
                    devoluciones_por_factura = devoluciones_mes.groupby('factura_id')['valor_devuelto'].sum().to_dict()
                    
                    for factura_data in facturas_devoluciones_response.data:
                        factura_id = factura_data['id']
                        valor_devuelto_total = float(devoluciones_por_factura.get(factura_id, 0))
                        # Convertir devolución a valor sin IVA
                        valor_devuelto_sin_iva = valor_devuelto_total / 1.19 if valor_devuelto_total > 0 else 0
                        
                        # Solo agregar si la factura no es del mes actual (para evitar duplicados)
                        if factura_id not in df_mes_propios['id'].values if not df_mes_propios.empty else []:
                            fecha_factura = factura_data.get('fecha_factura', '')
                            if fecha_factura:
                                if isinstance(fecha_factura, str):
                                    fecha_factura_str = fecha_factura
                                else:
                                    fecha_factura_str = pd.to_datetime(fecha_factura).strftime('%Y-%m-%d')
                            else:
                                fecha_factura_str = ''
                            
                            # Obtener fecha de devolución
                            fecha_devolucion = ''
                            devoluciones_factura = devoluciones_mes[devoluciones_mes['factura_id'] == factura_id]
                            if not devoluciones_factura.empty:
                                fecha_dev = devoluciones_factura['fecha_devolucion'].max()
                                if pd.notna(fecha_dev):
                                    if isinstance(fecha_dev, pd.Timestamp):
                                        fecha_devolucion = fecha_dev.strftime('%Y-%m-%d')
                                    else:
                                        fecha_devolucion = str(fecha_dev)
                            
                            # Agregar como línea negativa (devolución, sin IVA)
                            facturas_detalle.append({
                                "id": int(factura_id),
                                "pedido": str(factura_data.get('pedido', 'N/A')),
                                "factura": str(factura_data.get('factura', 'N/A')),
                                "cliente": str(factura_data.get('cliente', 'N/A')),
                                "fecha_factura": fecha_factura_str,
                                "fecha_devolucion": fecha_devolucion,
                                "valor_bruto": 0,
                                "valor_devuelto": valor_devuelto_sin_iva,  # Sin IVA
                                "valor_neto": -valor_devuelto_sin_iva,
                                "valor_transaccion": -valor_devuelto_sin_iva,  # Negativo para devoluciones (sin IVA)
                                "tipo": "devolucion_mes"  # Devolución del mes pero factura anterior
                            })
            except Exception as e:
                print(f"Error obteniendo facturas de devoluciones: {e}")
        
        # Ordenar por cliente y luego por fecha (similar al reporte de la empresa)
        facturas_detalle.sort(key=lambda x: (x['cliente'], x['fecha_factura'], x['valor_transaccion'] < 0))
        
        return limpiar_nan_para_json({
            "totalVentas": total_ventas,
            "comisiones": comisiones,
            "clientesActivos": int(clientes_activos),
            "pedidosMes": int(pedidos_mes),
            "mes": mes_filtro,
            "metaVentas": meta_ventas,
            "progresoMeta": min(100, max(0, progreso_meta)),  # Entre 0 y 100%
            "faltanteMeta": faltante_meta,
            "facturasDetalle": facturas_detalle,  # Detalle de facturas
            "_diagnostico": diagnostico  # Información de diagnóstico
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")

@router.get("/sales-chart")
async def get_sales_chart():
    """Obtiene datos para el gráfico de ventas y comisiones de los últimos 6 meses (solo clientes propios)"""
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        from datetime import datetime, date, timedelta
        import pandas as pd

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        df = db_manager._cargar_datos_raw()
        
        if df.empty:
            return {
                "ventas_mensuales": [],
                "comisiones_mensuales": []
            }
        
        # Convertir fecha_factura (dayfirst=True para formato DD/MM/YYYY)
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce', dayfirst=True)
        df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)
        
        # Filtrar solo clientes propios
        df_propios = df[df.get('cliente_propio', False) == True].copy()
        
        if df_propios.empty:
            return {
                "ventas_mensuales": [],
                "comisiones_mensuales": []
            }
        
        # Obtener últimos 6 meses
        hoy = date.today()
        meses = []
        for i in range(5, -1, -1):  # Últimos 6 meses
            # Usar DateOffset para calcular meses correctamente (evitar problemas con meses de distinta duración)
            fecha = pd.Timestamp(hoy.replace(day=1)) - pd.DateOffset(months=i)
            meses.append(fecha.strftime("%Y-%m"))
        
        # Agrupar por mes
        ventas_mensuales = []
        comisiones_mensuales = []
        
        for mes in meses:
            df_mes = df_propios[df_propios['mes_factura'] == mes].copy()
            
            # Calcular ventas usando la MISMA lógica que /metrics
            # 1. Obtener valor_neto (sin IVA) de cada factura
            if not df_mes.empty:
                if 'valor_neto' not in df_mes.columns or df_mes['valor_neto'].isna().all():
                    # Si no hay valor_neto, calcularlo desde valor (sin flete)
                    if 'valor_flete' in df_mes.columns:
                        valor_sin_flete = df_mes['valor'].fillna(0) - df_mes['valor_flete'].fillna(0)
                    else:
                        valor_sin_flete = df_mes['valor'].fillna(0)
                    df_mes['valor_neto'] = valor_sin_flete / 1.19
                else:
                    df_mes['valor_neto'] = df_mes['valor_neto'].fillna(0)
                
                # 2. Restar descuentos en pesos si existen
                if 'valor_descuento_pesos' in df_mes.columns:
                    df_mes['valor_neto_ajustado'] = df_mes['valor_neto'] - df_mes['valor_descuento_pesos'].fillna(0)
                else:
                    df_mes['valor_neto_ajustado'] = df_mes['valor_neto']
                
                # 3. Sumar valor neto ajustado (sin IVA, después de descuentos)
                ventas_bruto = df_mes['valor_neto_ajustado'].sum()
                
                # 4. Restar devoluciones de facturas del mes (convertir a valor sin IVA)
                devoluciones_facturas_mes = 0
                if 'valor_devuelto' in df_mes.columns:
                    # valor_devuelto incluye IVA, se divide por 1.19 para obtener valor sin IVA
                    devoluciones_facturas_mes = (df_mes['valor_devuelto'].fillna(0) / 1.19).sum()
                
                # 5. Obtener devoluciones del mes (de facturas de cualquier mes)
                devoluciones_mes_totales = 0
                try:
                    df_devoluciones = db_manager.cargar_devoluciones()
                    if not df_devoluciones.empty and 'fecha_devolucion' in df_devoluciones.columns:
                        df_devoluciones['fecha_devolucion'] = pd.to_datetime(df_devoluciones['fecha_devolucion'], errors='coerce')
                        df_devoluciones['mes_devolucion'] = df_devoluciones['fecha_devolucion'].dt.to_period('M').astype(str)
                        devoluciones_mes_df = df_devoluciones[df_devoluciones['mes_devolucion'] == mes].copy()
                        
                        # Filtrar solo devoluciones de clientes propios
                        if not devoluciones_mes_df.empty:
                            facturas_ids_devoluciones = devoluciones_mes_df['factura_id'].unique().tolist()
                            if facturas_ids_devoluciones:
                                try:
                                    facturas_devoluciones = supabase.table("comisiones").select("id, cliente_propio").in_("id", facturas_ids_devoluciones).execute()
                                    facturas_propios_ids = {f['id']: f.get('cliente_propio', True) for f in facturas_devoluciones.data if f.get('cliente_propio', True)}
                                    devoluciones_mes_df = devoluciones_mes_df[devoluciones_mes_df['factura_id'].isin(facturas_propios_ids.keys())].copy()
                                    devoluciones_mes_totales = devoluciones_mes_df['valor_devuelto'].fillna(0).sum() if 'valor_devuelto' in devoluciones_mes_df.columns else 0
                                except Exception as e:
                                    print(f"Error filtrando devoluciones por cliente_propio en gráfico: {e}")
                                    devoluciones_mes_totales = devoluciones_mes_df['valor_devuelto'].fillna(0).sum() if 'valor_devuelto' in devoluciones_mes_df.columns else 0
                except Exception as e:
                    print(f"Error cargando devoluciones del mes {mes} para gráfico: {e}")
                    devoluciones_mes_totales = 0
                
                # 6. Convertir devoluciones totales a valor sin IVA
                devoluciones_mes_sin_iva = float(devoluciones_mes_totales) / 1.19 if devoluciones_mes_totales > 0 else 0
                
                # 7. Calcular total de ventas neto (valor sin IVA, después de descuentos, restando devoluciones sin IVA)
                ventas = float(ventas_bruto) - float(devoluciones_facturas_mes) - float(devoluciones_mes_sin_iva)
                ventas = max(0, ventas)  # No puede ser negativo
            else:
                # Si no hay facturas del mes, verificar si hay devoluciones del mes
                devoluciones_mes_totales = 0
                try:
                    df_devoluciones = db_manager.cargar_devoluciones()
                    if not df_devoluciones.empty and 'fecha_devolucion' in df_devoluciones.columns:
                        df_devoluciones['fecha_devolucion'] = pd.to_datetime(df_devoluciones['fecha_devolucion'], errors='coerce')
                        df_devoluciones['mes_devolucion'] = df_devoluciones['fecha_devolucion'].dt.to_period('M').astype(str)
                        devoluciones_mes_df = df_devoluciones[df_devoluciones['mes_devolucion'] == mes].copy()
                        if not devoluciones_mes_df.empty:
                            facturas_ids_devoluciones = devoluciones_mes_df['factura_id'].unique().tolist()
                            if facturas_ids_devoluciones:
                                try:
                                    facturas_devoluciones = supabase.table("comisiones").select("id, cliente_propio").in_("id", facturas_ids_devoluciones).execute()
                                    facturas_propios_ids = {f['id']: f.get('cliente_propio', True) for f in facturas_devoluciones.data if f.get('cliente_propio', True)}
                                    devoluciones_mes_df = devoluciones_mes_df[devoluciones_mes_df['factura_id'].isin(facturas_propios_ids.keys())].copy()
                                    devoluciones_mes_totales = devoluciones_mes_df['valor_devuelto'].fillna(0).sum() if 'valor_devuelto' in devoluciones_mes_df.columns else 0
                                except Exception as e:
                                    print(f"Error filtrando devoluciones por cliente_propio en gráfico: {e}")
                except Exception as e:
                    print(f"Error cargando devoluciones del mes {mes} para gráfico: {e}")
                
                ventas = max(0, -float(devoluciones_mes_totales) / 1.19) if devoluciones_mes_totales > 0 else 0
            
            # Obtener descuentos_predeterminados de todos los clientes únicos para optimizar consultas
            clientes_unicos_mes = df_mes['cliente'].unique().tolist() if not df_mes.empty else []
            descuentos_clientes_mes = {}
            if clientes_unicos_mes:
                try:
                    clientes_response = supabase.table("clientes_b2b").select("nombre, descuento_predeterminado").in_("nombre", clientes_unicos_mes).execute()
                    for cliente_data in clientes_response.data:
                        descuentos_clientes_mes[cliente_data['nombre']] = float(cliente_data.get('descuento_predeterminado', 0) or 0)
                except Exception as e:
                    print(f"⚠️ No se pudieron obtener descuentos_predeterminados para gráfico: {e}")
            
            # RECALCULAR comisiones usando las mismas reglas que en /metrics
            # Esto asegura consistencia entre el gráfico y las métricas
            comisiones = 0
            if not df_mes.empty:
                for _, row in df_mes.iterrows():
                    # Obtener valores necesarios
                    valor_neto = row.get('valor_neto', 0)
                    if valor_neto == 0 or pd.isna(valor_neto):
                        # Si no hay valor_neto, calcularlo desde valor
                        valor_total = row.get('valor', 0)
                        if valor_total and not pd.isna(valor_total):
                            valor_flete = row.get('valor_flete', 0) or 0
                            valor_neto = (valor_total - valor_flete) / 1.19
                    
                    cliente_propio = row.get('cliente_propio', False)
                    descuento_pie_factura = row.get('descuento_pie_factura', False)
                    descuento_aplicado = row.get('descuento_adicional', 0) or row.get('descuento_aplicado', 0)
                    valor_devuelto = row.get('valor_devuelto', 0) or 0
                    dias_pago = row.get('dias_pago_real')
                    condicion_especial = row.get('condicion_especial', False)
                    nombre_cliente = row.get('cliente', '')
                    descuento_predeterminado = descuentos_clientes_mes.get(nombre_cliente, 0)
                    
                    # Calcular base de comisión
                    if descuento_pie_factura:
                        base = valor_neto
                    else:
                        limite_dias = 60 if condicion_especial else 45
                        if not dias_pago or dias_pago <= limite_dias:
                            base = valor_neto * 0.85
                        else:
                            base = valor_neto
                    
                    # Restar devoluciones
                    base_final = base - (valor_devuelto / 1.19 if valor_devuelto else 0)
                    base_final = max(0, base_final)  # No puede ser negativo
                    
                    # Determinar porcentaje según reglas de negocio
                    # REGLA: Si el descuento base es > 15%, pierde un punto (1.5% en lugar de 2.5%)
                    # También si hay descuento adicional, pierde un punto
                    tiene_descuento = descuento_aplicado > 0
                    descuento_base_superior_15 = descuento_predeterminado > 15
                    if cliente_propio:
                        porcentaje = 1.5 if (descuento_base_superior_15 or tiene_descuento) else 2.5
                    else:
                        porcentaje = 0.5 if (descuento_base_superior_15 or tiene_descuento) else 1.0
                    
                    # Verificar pérdida por +80 días
                    if dias_pago and dias_pago > 80:
                        comision_venta = 0
                    else:
                        comision_venta = base_final * (porcentaje / 100)
                    
                    comisiones += comision_venta
            
            # Limpiar NaN e infinitos
            ventas = float(ventas) if not pd.isna(ventas) and not np.isinf(ventas) else 0
            comisiones = float(comisiones) if not pd.isna(comisiones) and not np.isinf(comisiones) else 0
            
            # Formatear nombre del mes
            fecha_mes = datetime.strptime(mes, "%Y-%m")
            nombre_mes = fecha_mes.strftime("%b")  # Ene, Feb, Mar, etc.
            
            ventas_mensuales.append({
                "mes": nombre_mes,
                "ventas": ventas,
                "comisiones": comisiones
            })
            
            comisiones_mensuales.append({
                "mes": nombre_mes,
                "comisiones": comisiones
            })
        
        return limpiar_nan_para_json({
            "ventas_mensuales": ventas_mensuales,
            "comisiones_mensuales": comisiones_mensuales
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/colombia-map")
async def get_colombia_map(periodo: str = "historico"):
    """Obtiene datos para el mapa de Colombia con distribución de clientes - OPTIMIZADO"""
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        import time
        from datetime import datetime, timedelta
        
        start_time = time.time()
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Faltan variables de entorno para conectar a Supabase.",
                    "errors": env_status["errors"],
                },
            )
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # OPTIMIZACIÓN: Usar compras_clientes directamente (más rápido que distribucion_geografica)
        print("🔄 Cargando compras_clientes para mapa de Colombia...")
        
        # Calcular fecha límite según período
        fecha_limite = None
        if periodo == "mes_actual":
            fecha_limite = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        elif periodo == "trimestre":
            fecha_limite = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        elif periodo == "año":
            fecha_limite = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        # Si es "historico", no aplicar filtro de fecha
        
        # Cargar compras con paginación optimizada
        query_compras = supabase.table("compras_clientes").select("nit_cliente, total, es_devolucion").eq("es_devolucion", False)
        
        if fecha_limite:
            try:
                query_compras = query_compras.gte("fecha", fecha_limite)
            except Exception as e:
                print(f"⚠️ No se pudo aplicar filtro de fecha: {e}")
        
        all_compras = []
        page_size = 1000
        current_offset = 0
        # Eliminar límite de registros para incluir todas las compras
        
        while True:
            response_compras = query_compras.range(current_offset, current_offset + page_size - 1).execute()
            if not response_compras.data:
                break
            all_compras.extend(response_compras.data)
            if len(response_compras.data) < page_size:
                break
            current_offset += page_size
        
        print(f"⏱️ Compras cargadas en {time.time() - start_time:.2f}s: {len(all_compras)} registros")
        
        if not all_compras:
            return {
                "distribucion": {
                    "datos_mapa": [],
                    "total_clientes": 0,
                    "total_ciudades": 0
                },
                "por_ciudad": [],
                "total_clientes": 0,
                "total_ciudades": 0
            }
        
        # Cargar clientes y crear diccionario
        print("🔄 Cargando clientes_b2b...")
        all_clientes = []
        current_offset_clientes = 0
        
        while True:
            response_clientes = supabase.table("clientes_b2b").select("nit, ciudad").range(current_offset_clientes, current_offset_clientes + page_size - 1).execute()
            if not response_clientes.data:
                break
            all_clientes.extend(response_clientes.data)
            if len(response_clientes.data) < page_size:
                break
            current_offset_clientes += page_size
        
        nit_a_ciudad = {cliente.get('nit', ''): cliente.get('ciudad', '') for cliente in all_clientes if cliente.get('nit')}
        
        # Procesar con pandas
        df_compras = pd.DataFrame(all_compras)
        df_compras['ciudad'] = df_compras['nit_cliente'].map(nit_a_ciudad)
        df_compras = df_compras[df_compras['ciudad'].notna() & (df_compras['ciudad'] != '')]
        
        if df_compras.empty:
            return {
                "distribucion": {
                    "datos_mapa": [],
                    "total_clientes": 0,
                    "total_ciudades": 0
                },
                "por_ciudad": [],
                "total_clientes": 0,
                "total_ciudades": 0
            }
        
        # Convertir total a numérico
        df_compras['total'] = pd.to_numeric(df_compras['total'], errors='coerce').fillna(0)
        
        # Agrupar por ciudad
        stats_por_ciudad = df_compras.groupby('ciudad').agg({
            'total': 'sum',
            'nit_cliente': 'nunique'
        }).reset_index()
        stats_por_ciudad.columns = ['ciudad', 'total_compras', 'num_clientes']
        
        # Cargar coordenadas
        from business.client_analytics import ClientAnalytics
        client_analytics = ClientAnalytics(supabase)
        coordenadas_dict = client_analytics._obtener_codigos_dane_coordenadas()
        
        # Preparar datos del mapa
        datos_mapa = []
        por_ciudad = []
        
        for _, row in stats_por_ciudad.iterrows():
            ciudad = row['ciudad']
            total_compras = float(row['total_compras'])
            num_clientes = int(row['num_clientes'])
            
            # Buscar coordenadas
            coords = coordenadas_dict.get(ciudad) or coordenadas_dict.get(ciudad.lower()) or coordenadas_dict.get(ciudad.title())
            
            if coords:
                datos_mapa.append({
                    'ciudad': ciudad,
                    'lat': coords.get('lat'),
                    'lon': coords.get('lon'),
                    'total_compras': total_compras,
                    'num_clientes': num_clientes
                })
            
            por_ciudad.append({
                'ciudad': ciudad,
                'total_compras': total_compras,
                'num_clientes': num_clientes
            })
        
        total_clientes = df_compras['nit_cliente'].nunique()
        total_ciudades = len(por_ciudad)
        
        print(f"⏱️ Mapa procesado en {time.time() - start_time:.2f}s total")
        
        return limpiar_nan_para_json({
            "distribucion": {
                "datos_mapa": datos_mapa,
                "total_clientes": int(total_clientes),
                "total_ciudades": total_ciudades
            },
            "por_ciudad": por_ciudad,
            "total_clientes": int(total_clientes),
            "total_ciudades": total_ciudades
        })
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error en get_colombia_map: {str(e)}\n{traceback.format_exc()}"
        print(f"❌ {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo mapa de Colombia: {str(e)}")

@router.get("/referencias-por-ciudad")
async def get_referencias_por_ciudad():
    """Obtiene las referencias más compradas por ciudad - USA TABLA compras_clientes"""
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Faltan variables de entorno para conectar a Supabase.",
                    "errors": env_status["errors"],
                },
            )
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Cargar compras_clientes usando paginación automática
        all_compras = []
        page_size = 1000
        current_offset = 0
        
        while True:
            response_compras = supabase.table("compras_clientes").select("*").range(current_offset, current_offset + page_size - 1).execute()
            
            if not response_compras.data:
                break
            
            all_compras.extend(response_compras.data)
            
            if len(response_compras.data) < page_size:
                break
            
            current_offset += page_size
        
        if not all_compras:
            return {
                "referencias_por_ciudad": [],
                "total_ciudades": 0,
                "total_referencias_unicas": 0
            }
        
        df_compras = pd.DataFrame(all_compras)
        
        # Cargar clientes_b2b para obtener ciudades
        all_clientes = []
        current_offset_clientes = 0
        
        while True:
            response_clientes = supabase.table("clientes_b2b").select("id, nit, ciudad").range(current_offset_clientes, current_offset_clientes + page_size - 1).execute()
            
            if not response_clientes.data:
                break
            
            all_clientes.extend(response_clientes.data)
            
            if len(response_clientes.data) < page_size:
                break
            
            current_offset_clientes += page_size
        
        # Crear diccionario de NIT a ciudad
        df_clientes = pd.DataFrame(all_clientes) if all_clientes else pd.DataFrame()
        nit_a_ciudad = {}
        if not df_clientes.empty:
            for _, row in df_clientes.iterrows():
                nit = row.get('nit', '')
                ciudad = row.get('ciudad', '')
                if nit and ciudad:
                    nit_a_ciudad[nit] = ciudad
        
        # Filtrar solo compras (no devoluciones) y referencias válidas
        df_compras_filtrado = df_compras[
            (df_compras.get('es_devolucion', False) == False) &
            df_compras['cod_articulo'].notna() & 
            (df_compras['cod_articulo'] != '') &
            (df_compras['cod_articulo'].astype(str).str.strip() != '') &
            (df_compras['cod_articulo'].astype(str) != 'N/A')
        ].copy()
        
        if df_compras_filtrado.empty:
            return {
                "referencias_por_ciudad": [],
                "total_ciudades": 0,
                "total_referencias_unicas": 0
            }
        
        # Agregar ciudad a cada compra usando nit_cliente
        df_compras_filtrado['ciudad'] = df_compras_filtrado['nit_cliente'].map(nit_a_ciudad)
        
        # Filtrar solo las que tienen ciudad
        df_compras_filtrado = df_compras_filtrado[df_compras_filtrado['ciudad'].notna() & (df_compras_filtrado['ciudad'] != '')]
        
        if df_compras_filtrado.empty:
            return {
                "referencias_por_ciudad": [],
                "total_ciudades": 0,
                "total_referencias_unicas": 0
            }
        
        # Agrupar por ciudad y cod_articulo (referencia real)
        referencias_por_ciudad = df_compras_filtrado.groupby(['ciudad', 'cod_articulo']).agg({
            'total': 'sum',  # Valor total
            'cantidad': 'sum',  # Cantidad total
            'id': 'count',  # Número de transacciones
            'nit_cliente': 'nunique'  # Número de clientes únicos
        }).reset_index()
        
        referencias_por_ciudad.columns = ['ciudad', 'referencia', 'valor_total', 'cantidad_total', 'cantidad_compras', 'num_clientes']
        
        # Ordenar por valor total descendente
        referencias_por_ciudad = referencias_por_ciudad.sort_values(['ciudad', 'valor_total'], ascending=[True, False])
        
        # Para cada ciudad, obtener top referencias
        resultado = []
        ciudades = referencias_por_ciudad['ciudad'].unique()
        
        for ciudad in ciudades:
            refs_ciudad = referencias_por_ciudad[referencias_por_ciudad['ciudad'] == ciudad].head(10)
            # Limpiar NaN antes de convertir a dict
            refs_ciudad_limpio = refs_ciudad.fillna(0)
            
            # Convertir a formato JSON limpio
            referencias_lista = []
            for _, row in refs_ciudad_limpio.iterrows():
                referencias_lista.append({
                    "referencia": str(row['referencia']),
                    "valor_total": float(row['valor_total']) if pd.notna(row['valor_total']) else 0,
                    "cantidad_compras": int(row['cantidad_compras']) if pd.notna(row['cantidad_compras']) else 0,
                    "cantidad_total": float(row['cantidad_total']) if pd.notna(row['cantidad_total']) else 0,
                    "num_clientes": int(row['num_clientes']) if pd.notna(row['num_clientes']) else 0
                })
            
            resultado.append({
                "ciudad": ciudad,
                "total_referencias": len(referencias_lista),
                "referencias": referencias_lista
            })
        
        return {
            "referencias_por_ciudad": resultado,
            "total_ciudades": len(ciudades),
            "total_referencias_unicas": df_compras_filtrado['cod_articulo'].nunique()
        }
    except Exception as e:
        import traceback
        print(f"Error en get_referencias_por_ciudad: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo referencias por ciudad: {str(e)}")

@router.get("/mapa-interactivo")
async def get_mapa_interactivo(
    referencia: Optional[str] = Query(None, description="Filtrar por referencia específica"),
    periodo: Optional[str] = Query("historico", description="Período: mes_actual, trimestre, año, historico")
):
    """Obtiene datos para el mapa interactivo: top cliente por ciudad y distribución de referencias - OPTIMIZADO"""
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        import time
        from datetime import datetime, timedelta
        
        start_time = time.time()
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "Faltan variables de entorno para conectar a Supabase.",
                    "errors": env_status["errors"],
                },
            )
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # OPTIMIZACIÓN 1: Cargar solo campos necesarios y filtrar en la consulta
        print(f"🔄 Cargando compras_clientes... (período: {periodo})")
        campos_necesarios = "nit_cliente, cod_articulo, total, cantidad, es_devolucion, fecha"
        query_compras = supabase.table("compras_clientes").select(campos_necesarios).eq("es_devolucion", False)
        
        if referencia:
            query_compras = query_compras.eq("cod_articulo", referencia)
        
        # Calcular fecha límite según período (igual que en get_colombia_map)
        fecha_limite = None
        if periodo == "mes_actual":
            fecha_limite = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        elif periodo == "trimestre":
            fecha_limite = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        elif periodo == "año":
            fecha_limite = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        # Si es "historico", no aplicar filtro de fecha
        
        if fecha_limite:
            try:
                query_compras = query_compras.gte("fecha", fecha_limite)
                print(f"📅 Aplicando filtro de fecha desde: {fecha_limite}")
            except Exception as e:
                # Si la columna fecha no existe o hay error, continuar sin filtro
                print(f"⚠️ No se pudo aplicar filtro de fecha: {e}")
        
        # Cargar con paginación optimizada - límite máximo de 10000 registros para velocidad
        all_compras = []
        page_size = 1000
        current_offset = 0
        max_registros = 10000  # Aumentado para mantener datos pero con límite
        
        while len(all_compras) < max_registros:
            response_compras = query_compras.range(current_offset, current_offset + page_size - 1).execute()
            if not response_compras.data:
                break
            all_compras.extend(response_compras.data)
            if len(response_compras.data) < page_size:
                break
            current_offset += page_size
        
        print(f"⏱️ Compras cargadas en {time.time() - start_time:.2f}s: {len(all_compras)} registros")
        
        if not all_compras:
            return {
                "ciudades": [],
                "referencias_disponibles": [],
                "referencia_filtro": referencia
            }
        
        # OPTIMIZACIÓN 2: Cargar clientes solo una vez y crear diccionarios eficientes
        print("🔄 Cargando clientes_b2b...")
        clientes_start = time.time()
        all_clientes = []
        current_offset_clientes = 0
        
        while True:
            response_clientes = supabase.table("clientes_b2b").select("nit, nombre, ciudad").range(current_offset_clientes, current_offset_clientes + page_size - 1).execute()
            if not response_clientes.data:
                break
            all_clientes.extend(response_clientes.data)
            if len(response_clientes.data) < page_size:
                break
            current_offset_clientes += page_size
        
        # Crear diccionarios de mapeo (más eficiente que DataFrame)
        nit_a_ciudad = {}
        nit_a_nombre = {}
        for cliente in all_clientes:
            nit = cliente.get('nit', '')
            if nit:
                if cliente.get('ciudad'):
                    nit_a_ciudad[nit] = cliente['ciudad']
                if cliente.get('nombre'):
                    nit_a_nombre[nit] = cliente['nombre']
        
        print(f"⏱️ Clientes cargados en {time.time() - clientes_start:.2f}s: {len(all_clientes)} registros")
        
        # OPTIMIZACIÓN 3: Cargar coordenadas una sola vez y crear diccionario optimizado
        print("🔄 Cargando coordenadas...")
        coords_start = time.time()
        ciudad_a_coordenadas = {}
        ciudad_a_coordenadas_lower = {}  # Diccionario separado para búsqueda rápida
        
        try:
            from business.client_analytics import ClientAnalytics
            client_analytics = ClientAnalytics(supabase)
            coordenadas_dict = client_analytics._obtener_codigos_dane_coordenadas()
            
            for ciudad_nombre, datos in coordenadas_dict.items():
                coords_data = {
                    'lat': datos.get('lat'),
                    'lon': datos.get('lon'),
                    'departamento': datos.get('departamento', '')
                }
                ciudad_a_coordenadas[ciudad_nombre] = coords_data
                ciudad_a_coordenadas_lower[ciudad_nombre.lower().strip()] = coords_data
                # También sin acentos
                ciudad_clean = ciudad_nombre.lower().strip().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                if ciudad_clean not in ciudad_a_coordenadas_lower:
                    ciudad_a_coordenadas_lower[ciudad_clean] = coords_data
        except Exception as e:
            print(f"Error obteniendo coordenadas: {e}")
        
        print(f"⏱️ Coordenadas cargadas en {time.time() - coords_start:.2f}s")
        
        # OPTIMIZACIÓN 4: Procesar con pandas de manera más eficiente
        print("🔄 Procesando datos...")
        process_start = time.time()
        
        df_compras = pd.DataFrame(all_compras)
        
        # Agregar ciudad y nombre usando map (muy rápido)
        df_compras['ciudad'] = df_compras['nit_cliente'].map(nit_a_ciudad)
        df_compras['nombre_cliente'] = df_compras['nit_cliente'].map(nit_a_nombre)
        
        # Filtrar solo las que tienen ciudad
        df_compras = df_compras[df_compras['ciudad'].notna() & (df_compras['ciudad'] != '')]
        
        if df_compras.empty:
            return {
                "ciudades": [],
                "referencias_disponibles": [],
                "referencia_filtro": referencia
            }
        
        # OPTIMIZACIÓN 5: Obtener referencias disponibles de manera eficiente
        referencias_disponibles = df_compras['cod_articulo'].dropna().unique().tolist()
        referencias_disponibles = [r for r in referencias_disponibles if r and str(r).strip() != '' and str(r) != 'N/A']
        referencias_disponibles.sort()
        
        # OPTIMIZACIÓN 6: Agrupar todo de una vez en lugar de ciudad por ciudad
        # Agrupar por ciudad y nit_cliente para top cliente
        top_clientes_por_ciudad = df_compras.groupby(['ciudad', 'nit_cliente']).agg({
            'total': 'sum',
            'nombre_cliente': 'first'
        }).reset_index().sort_values(['ciudad', 'total'], ascending=[True, False])
        
        # Agrupar por ciudad para estadísticas generales
        stats_por_ciudad = df_compras.groupby('ciudad').agg({
            'total': 'sum',
            'nit_cliente': 'nunique',
            'cod_articulo': 'nunique'
        }).reset_index()
        stats_por_ciudad.columns = ['ciudad', 'total_ventas', 'num_clientes', 'num_referencias']
        
        # Top referencia por ciudad (solo si no hay filtro)
        top_refs_por_ciudad = {}
        if not referencia:
            top_refs = df_compras.groupby(['ciudad', 'cod_articulo']).agg({
                'total': 'sum',
                'cantidad': 'sum'
            }).reset_index().sort_values(['ciudad', 'total'], ascending=[True, False])
            
            for ciudad in top_refs['ciudad'].unique():
                top_ref_ciudad = top_refs[top_refs['ciudad'] == ciudad].iloc[0]
                top_refs_por_ciudad[ciudad] = {
                    'codigo': str(top_ref_ciudad['cod_articulo']),
                    'total_ventas': float(top_ref_ciudad['total']),
                    'cantidad': float(top_ref_ciudad['cantidad'])
                }
        
        # Si hay una referencia seleccionada, obtener TODOS los clientes que la compran por ciudad
        clientes_por_referencia_ciudad = {}
        if referencia:
            clientes_ref = df_compras.groupby(['ciudad', 'nit_cliente']).agg({
                'total': 'sum',
                'nombre_cliente': 'first'
            }).reset_index().sort_values(['ciudad', 'total'], ascending=[True, False])
            
            for ciudad in clientes_ref['ciudad'].unique():
                clientes_ciudad = clientes_ref[clientes_ref['ciudad'] == ciudad]
                clientes_por_referencia_ciudad[ciudad] = [
                    {
                        'nit': row['nit_cliente'],
                        'nombre': row['nombre_cliente'] if pd.notna(row['nombre_cliente']) else row['nit_cliente'],
                        'total_ventas': float(row['total'])
                    }
                    for _, row in clientes_ciudad.iterrows()
                ]
        
        # Construir resultado final
        ciudades_data = []
        for _, row in stats_por_ciudad.iterrows():
            ciudad = row['ciudad']
            
            # Obtener top cliente
            top_cliente_data = top_clientes_por_ciudad[top_clientes_por_ciudad['ciudad'] == ciudad]
            top_cliente = None
            if not top_cliente_data.empty:
                top_row = top_cliente_data.iloc[0]
                top_cliente = {
                    'nit': top_row['nit_cliente'],
                    'nombre': top_row['nombre_cliente'] if pd.notna(top_row['nombre_cliente']) else top_row['nit_cliente'],
                    'total_ventas': float(top_row['total'])
                }
            
            # Obtener top referencia
            top_referencia = top_refs_por_ciudad.get(ciudad) if not referencia else None
            
            # Obtener todos los clientes que compran la referencia (si hay filtro)
            clientes_referencia = clientes_por_referencia_ciudad.get(ciudad, []) if referencia else None
            
            # Buscar coordenadas (optimizado)
            ciudad_lower = ciudad.lower().strip()
            coords = ciudad_a_coordenadas_lower.get(ciudad_lower) or ciudad_a_coordenadas.get(ciudad) or ciudad_a_coordenadas.get(ciudad.title()) or {}
            
            ciudad_data = {
                'ciudad': ciudad,
                'departamento': coords.get('departamento', '') if coords else '',
                'lat': coords.get('lat') if coords else None,
                'lon': coords.get('lon') if coords else None,
                'total_ventas': float(row['total_ventas']),
                'num_clientes': int(row['num_clientes']),
                'num_referencias': int(row['num_referencias']),
                'top_cliente': top_cliente,
                'top_referencia': top_referencia
            }
            
            # Si hay una referencia seleccionada, agregar todos los clientes que la compran
            if referencia and clientes_referencia:
                ciudad_data['clientes_referencia'] = clientes_referencia
            
            ciudades_data.append(ciudad_data)
        
        # Ordenar por ventas descendente
        ciudades_data.sort(key=lambda x: x['total_ventas'], reverse=True)
        
        total_time = time.time() - start_time
        print(f"✅ Procesamiento completado en {total_time:.2f}s")
        print(f"📊 Ciudades procesadas: {len(ciudades_data)}, Referencias: {len(referencias_disponibles)}")
        
        return limpiar_nan_para_json({
            "ciudades": ciudades_data,
            "referencias_disponibles": referencias_disponibles,
            "referencia_filtro": referencia,
            "total_ciudades": len(ciudades_data),
            "ciudades_con_coordenadas": len([c for c in ciudades_data if c.get('lat') and c.get('lon')])
        })
    except Exception as e:
        import traceback
        print(f"Error en get_mapa_interactivo: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos del mapa interactivo: {str(e)}")

@router.get("/meses-disponibles")
async def get_meses_disponibles():
    """Obtiene la lista de meses disponibles en la base de datos"""
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        from datetime import datetime
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        df = db_manager._cargar_datos_raw()
        
        if df.empty:
            return {"meses": []}
        
        # Convertir fecha_factura a datetime
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
        
        # Obtener meses únicos
        df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)
        meses_unicos = df['mes_factura'].dropna().unique()
        
        # Agregar el mes actual si no está en la lista (para que siempre aparezca aunque no tenga datos)
        mes_actual = datetime.now().strftime("%Y-%m")
        if mes_actual not in meses_unicos:
            meses_unicos = list(meses_unicos) + [mes_actual]
        
        # Ordenar meses de más reciente a más antiguo
        meses_ordenados = sorted(set(meses_unicos), reverse=True)
        
        # Formatear meses para mostrar (en español)
        nombres_meses_es = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        
        meses_formateados = []
        for mes in meses_ordenados:
            try:
                fecha = datetime.strptime(mes, "%Y-%m")
                nombre_mes = f"{nombres_meses_es[fecha.month]} {fecha.year}"  # "Noviembre 2024"
                nombre_mes_corto = f"{nombres_meses_es[fecha.month][:3]} {fecha.year}"  # "Nov 2024"
                meses_formateados.append({
                    "valor": mes,  # "2024-11"
                    "nombre": nombre_mes,  # "Noviembre 2024"
                    "nombre_corto": nombre_mes_corto,  # "Nov 2024"
                    "año": fecha.year,
                    "mes_numero": fecha.month
                })
            except:
                continue
        
        return {"meses": meses_formateados}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo meses disponibles: {str(e)}")

@router.get("/clientes-clave")
async def get_clientes_clave(mes: str = None):
    """Obtiene los clientes clave para el dashboard filtrados por mes (solo clientes propios)"""
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        from datetime import date
        import pandas as pd

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        df = db_manager._cargar_datos_raw()
        
        if df.empty:
            return {"clientes_clave": []}
        
        # Convertir fecha_factura a datetime (dayfirst=True para formato DD/MM/YYYY)
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce', dayfirst=True)
        df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)
        
        # Filtrar solo clientes propios
        df_propios = df[
            (df.get('cliente_propio', False) == True)
        ].copy()
        
        # Si se especifica un mes, filtrar por ese mes
        if mes:
            mes_filtro = mes  # Formato: "2024-12"
            df_propios = df_propios[df_propios['mes_factura'] == mes_filtro].copy()
        # Si mes es None, mostrar todos los meses (no filtrar)
        
        if df_propios.empty:
            return {"clientes_clave": []}
        
        # Calcular valor neto sin IVA y menos descuentos para cada factura
        # valor_neto ya es sin IVA, pero debemos restar valor_descuento_pesos si existe
        if 'valor_neto' not in df_propios.columns:
            # Si no hay valor_neto, calcularlo desde valor (sin IVA, sin flete)
            if 'valor_flete' in df_propios.columns:
                df_propios['valor_neto'] = (df_propios['valor'] - df_propios['valor_flete'].fillna(0)) / 1.19
            else:
                df_propios['valor_neto'] = df_propios['valor'] / 1.19
        
        # Restar descuentos en pesos si existen
        if 'valor_descuento_pesos' in df_propios.columns:
            df_propios['valor_neto_ajustado'] = df_propios['valor_neto'] - df_propios['valor_descuento_pesos'].fillna(0)
        else:
            df_propios['valor_neto_ajustado'] = df_propios['valor_neto']
        
        # Asegurar que no sea negativo
        df_propios['valor_neto_ajustado'] = df_propios['valor_neto_ajustado'].clip(lower=0)
        
        # Agrupar por cliente y calcular métricas del mes
        clientes_stats = df_propios.groupby('cliente').agg({
            'valor_neto_ajustado': 'sum',  # Valor neto sin IVA y menos descuentos
            'fecha_factura': 'max',
            'id': 'count'
        }).reset_index()
        
        clientes_stats.columns = ['cliente', 'total_ventas', 'ultima_compra', 'num_facturas']
        
        # Ordenar por total de ventas
        clientes_stats = clientes_stats.sort_values('total_ventas', ascending=False).head(10)
        
        # Formatear resultados
        resultado = []
        for _, row in clientes_stats.iterrows():
            # Obtener iniciales del cliente
            nombre = str(row['cliente'])
            palabras = nombre.split()
            iniciales = ''.join([p[0].upper() for p in palabras[:3] if p and len(p) > 0])
            
            # Limpiar NaN
            total_ventas_limpio = float(row['total_ventas']) if not pd.isna(row['total_ventas']) else 0
            ultima_compra_limpio = row['ultima_compra'].strftime('%Y-%m-%d') if pd.notna(row['ultima_compra']) else 'N/A'
            num_facturas_limpio = int(row['num_facturas']) if not pd.isna(row['num_facturas']) else 0
            
            resultado.append({
                "cliente": nombre,
                "iniciales": iniciales[:4] if iniciales else 'N/A',
                "total_ventas": total_ventas_limpio,  # Ahora es valor_neto - descuentos
                "ultima_compra": ultima_compra_limpio,
                "num_facturas": num_facturas_limpio
            })
        
        return limpiar_nan_para_json({"clientes_clave": resultado})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

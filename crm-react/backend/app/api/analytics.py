from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Dict, Any
import sys
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
import io
from datetime import datetime

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

load_dotenv()

router = APIRouter()

def limpiar_nan_para_json(data):
    """Reemplaza NaN, inf y -inf con valores válidos para JSON"""
    if isinstance(data, pd.DataFrame):
        data = data.fillna(0)
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

@router.get("/geografico")
async def get_analisis_geografico(periodo: str = Query("historico", description="Periodo: historico, mes_actual, personalizado")):
    """Obtiene análisis geográfico detallado"""
    try:
        from business.client_analytics import ClientAnalytics
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        client_analytics = ClientAnalytics(supabase)
        
        # Obtener distribución geográfica
        distribucion = client_analytics.distribucion_geografica(periodo=periodo)
        
        # Obtener ranking de clientes por ciudad
        ranking = client_analytics.ranking_clientes(periodo_meses=12)
        
        # Segmentación
        segmentacion = client_analytics.segmentar_por_presupuesto()
        
        return {
            "distribucion": limpiar_nan_para_json(distribucion),
            "ranking": limpiar_nan_para_json(ranking) if not ranking.empty else [],
            "segmentacion": limpiar_nan_para_json(segmentacion)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comercial")
async def get_analisis_comercial():
    """Obtiene análisis comercial avanzado"""
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        from datetime import datetime, timedelta
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        df = db_manager._cargar_datos_raw()
        
        if df.empty:
            return {
                "ventas_mensuales": [],
                "top_clientes": [],
                "top_productos": [],
                "tendencias": {}
            }
        
        # Calcular valor_neto_final si no existe (valor sin IVA, después de descuentos y devoluciones)
        if 'valor_neto_final' not in df.columns:
            # Calcular valor_neto si no existe
            if 'valor_neto' not in df.columns:
                valor_total = df['valor'].fillna(0)
                valor_flete = df['valor_flete'].fillna(0) if 'valor_flete' in df.columns else 0
                df['valor_neto'] = (valor_total - valor_flete) / 1.19
            else:
                df['valor_neto'] = df['valor_neto'].fillna(0)
            
            # Calcular descuentos y devoluciones
            valor_descuento = df['valor_descuento_pesos'].fillna(0) if 'valor_descuento_pesos' in df.columns else 0
            valor_devuelto = (df['valor_devuelto'].fillna(0) / 1.19) if 'valor_devuelto' in df.columns else 0
            
            df['valor_neto_final'] = df['valor_neto'] - valor_descuento - valor_devuelto
            df['valor_neto_final'] = df['valor_neto_final'].clip(lower=0)  # No permitir valores negativos
        
        # Ventas mensuales últimos 12 meses (usar valor_neto_final)
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
        df['mes'] = df['fecha_factura'].dt.to_period('M').astype(str)
        
        ventas_mensuales = df.groupby('mes').agg({
            'valor_neto_final': 'sum',
            'comision': 'sum',
            'id': 'count'
        }).reset_index()
        ventas_mensuales.columns = ['mes', 'total_ventas', 'total_comisiones', 'num_facturas']
        
        # Top clientes (usar valor_neto_final)
        top_clientes = df.groupby('cliente').agg({
            'valor_neto_final': 'sum',
            'comision': 'sum',
            'id': 'count'
        }).reset_index()
        top_clientes.columns = ['cliente', 'total_ventas', 'total_comisiones', 'num_facturas']
        top_clientes = top_clientes.sort_values('total_ventas', ascending=False).head(20)
        
        # Top productos/referencias - USAR TABLA compras_clientes (referencias reales)
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
        
        if all_compras:
            df_compras = pd.DataFrame(all_compras)
            
            # Filtrar solo compras (no devoluciones) y referencias válidas
            df_compras_filtrado = df_compras[
                (df_compras.get('es_devolucion', False) == False) &
                df_compras['cod_articulo'].notna() & 
                (df_compras['cod_articulo'] != '') &
                (df_compras['cod_articulo'].astype(str).str.strip() != '')
            ].copy()
            
            if not df_compras_filtrado.empty:
                # Cargar nombres de clientes para enriquecer los datos
                clientes_response = supabase.table("clientes_b2b").select("nit, nombre").execute()
                nit_a_nombre = {}
                if clientes_response.data:
                    for cliente in clientes_response.data:
                        nit = cliente.get('nit', '')
                        nombre = cliente.get('nombre', '')
                        if nit and nombre:
                            nit_a_nombre[nit] = nombre
                
                # Agregar nombre de cliente
                df_compras_filtrado['nombre_cliente'] = df_compras_filtrado['nit_cliente'].map(nit_a_nombre)
                
                # Agrupar por cod_articulo (referencia real)
                top_productos = df_compras_filtrado.groupby('cod_articulo').agg({
                    'total': 'sum',  # Usar total de compras_clientes
                    'cantidad': 'sum',  # Sumar cantidades
                    'id': 'count'  # Contar registros
                }).reset_index()
                
                top_productos.columns = ['referencia', 'total_ventas', 'cantidad_vendida', 'num_registros']
                
                # Ordenar por total_ventas descendente
                top_productos = top_productos.sort_values('total_ventas', ascending=False).head(20)
                
                # Para cada referencia del top, obtener los clientes que la compran
                top_productos_con_clientes = []
                for _, row in top_productos.iterrows():
                    ref = row['referencia']
                    df_ref = df_compras_filtrado[df_compras_filtrado['cod_articulo'] == ref]
                    
                    # Obtener top 5 clientes que compran esta referencia
                    clientes_ref = df_ref.groupby('nit_cliente').agg({
                        'total': 'sum',
                        'cantidad': 'sum',
                        'nombre_cliente': 'first'
                    }).reset_index().sort_values('total', ascending=False).head(5)
                    
                    clientes_lista = []
                    for _, cliente_row in clientes_ref.iterrows():
                        clientes_lista.append({
                            'nit': cliente_row['nit_cliente'],
                            'nombre': cliente_row['nombre_cliente'] if pd.notna(cliente_row['nombre_cliente']) else cliente_row['nit_cliente'],
                            'total_comprado': float(cliente_row['total']),
                            'cantidad': float(cliente_row['cantidad'])
                        })
                    
                    top_productos_con_clientes.append({
                        'referencia': ref,
                        'total_ventas': float(row['total_ventas']),
                        'cantidad_vendida': float(row['cantidad_vendida']),
                        'num_clientes': len(df_ref['nit_cliente'].unique()),
                        'top_clientes': clientes_lista
                    })
                
                # Convertir a lista de diccionarios para JSON
                top_productos = top_productos_con_clientes
            else:
                top_productos = pd.DataFrame(columns=['referencia', 'total_ventas', 'cantidad_vendida'])
        else:
            top_productos = pd.DataFrame(columns=['referencia', 'total_ventas', 'cantidad_vendida'])
        
        # Tendencias
        hoy = datetime.now()
        mes_actual = hoy.strftime('%Y-%m')
        mes_anterior = (hoy.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        
        ventas_actual = ventas_mensuales[ventas_mensuales['mes'] == mes_actual]['total_ventas'].sum()
        ventas_anterior = ventas_mensuales[ventas_mensuales['mes'] == mes_anterior]['total_ventas'].sum()
        
        crecimiento = ((ventas_actual - ventas_anterior) / ventas_anterior * 100) if ventas_anterior > 0 else 0
        
        return {
            "ventas_mensuales": limpiar_nan_para_json(ventas_mensuales),
            "top_clientes": limpiar_nan_para_json(top_clientes),
            "top_productos": limpiar_nan_para_json(top_productos),
            "tendencias": limpiar_nan_para_json({
                "crecimiento_mensual": float(crecimiento) if not pd.isna(crecimiento) else 0,
                "ventas_mes_actual": float(ventas_actual) if not pd.isna(ventas_actual) else 0,
                "ventas_mes_anterior": float(ventas_anterior) if not pd.isna(ventas_anterior) else 0
            })
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comisiones-mensuales")
async def get_comisiones_mensuales():
    """
    Obtiene las comisiones mensuales del vendedor (solo clientes propios)
    Muestra comisiones mes tras mes basadas en fecha de pago
    """
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        from datetime import datetime, date, timedelta
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        df = db_manager._cargar_datos_raw()
        
        if df.empty:
            return {
                "comisiones_mensuales": [],
                "resumen": {}
            }
        
        # NO filtrar por cliente_propio - incluir TODOS los clientes (propios y externos)
        # Las comisiones se calculan para todos los clientes
        
        # Convertir fechas
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
        df['fecha_pago_real'] = pd.to_datetime(df['fecha_pago_real'], errors='coerce')
        
        # Separar facturas pagadas y pendientes
        df['pagado'] = df.get('pagado', False).fillna(False)
        df_pagadas = df[df['pagado'] == True].copy()
        df_pendientes = df[df['pagado'] != True].copy()
        
        # ==========================================
        # COMISIONES PAGADAS POR MES DE PAGO
        # Usar las comisiones YA calculadas en la tabla de facturas
        # Si pago >80 días, comision_ajustada ya será 0
        # IMPORTANTE: Solo incluir facturas con fecha_pago_real válida
        # ==========================================
        comisiones_mensuales = []
        
        if not df_pagadas.empty:
            # Filtrar solo facturas con fecha_pago_real válida (no NaT)
            df_pagadas_validas = df_pagadas[df_pagadas['fecha_pago_real'].notna()].copy()
            
            if not df_pagadas_validas.empty:
                df_pagadas_validas['mes_pago'] = df_pagadas_validas['fecha_pago_real'].dt.to_period('M').astype(str)
                
                # Usar comision_ajustada si existe (ya tiene en cuenta pérdida por >80 días)
                # Si no existe, usar comision
                if 'comision_ajustada' in df_pagadas_validas.columns:
                    df_pagadas_validas['comision_final'] = df_pagadas_validas['comision_ajustada'].fillna(df_pagadas_validas['comision']).fillna(0)
                else:
                    df_pagadas_validas['comision_final'] = df_pagadas_validas['comision'].fillna(0)
                
                # Agrupar por mes de pago - solo sumar las comisiones ya calculadas
                comisiones_por_mes = df_pagadas_validas.groupby('mes_pago').agg({
                    'comision_final': 'sum',
                    'id': 'count'
                }).reset_index()
                
                comisiones_por_mes.columns = ['mes', 'comisiones', 'num_facturas']
                comisiones_mensuales = comisiones_por_mes.sort_values('mes').to_dict('records')
        
        # ==========================================
        # IDENTIFICAR FACTURAS CON PROBLEMAS (pagadas sin fecha)
        # ==========================================
        facturas_sin_fecha = []
        if not df_pagadas.empty:
            df_sin_fecha = df_pagadas[df_pagadas['fecha_pago_real'].isna()].copy()
            if not df_sin_fecha.empty:
                # Usar comision_ajustada si existe, sino comision
                if 'comision_ajustada' in df_sin_fecha.columns:
                    df_sin_fecha['comision_final'] = df_sin_fecha['comision_ajustada'].fillna(df_sin_fecha['comision']).fillna(0)
                else:
                    df_sin_fecha['comision_final'] = df_sin_fecha['comision'].fillna(0)
                
                for _, row in df_sin_fecha.iterrows():
                    facturas_sin_fecha.append({
                        "id": int(row.get('id', 0)),
                        "factura": str(row.get('factura', 'N/A')),
                        "cliente": str(row.get('cliente', 'N/A')),
                        "pedido": str(row.get('pedido', 'N/A')),
                        "fecha_factura": str(row.get('fecha_factura', 'N/A')),
                        "comision": float(row.get('comision_final', 0)),
                        "problema": "Factura marcada como pagada pero sin fecha de pago"
                    })
        
        # ==========================================
        # RESUMEN
        # Usar las comisiones YA calculadas en la tabla
        # Solo contar facturas con fecha_pago_real válida
        # ==========================================
        # Comisiones pagadas: usar comision_ajustada (ya tiene pérdida por >80 días)
        # Solo contar facturas con fecha_pago_real válida
        if not df_pagadas.empty:
            df_pagadas_validas = df_pagadas[df_pagadas['fecha_pago_real'].notna()].copy()
            if not df_pagadas_validas.empty:
                if 'comision_ajustada' in df_pagadas_validas.columns:
                    total_comisiones_pagadas = float(df_pagadas_validas['comision_ajustada'].fillna(df_pagadas_validas['comision']).sum())
                else:
                    total_comisiones_pagadas = float(df_pagadas_validas['comision'].sum())
            else:
                total_comisiones_pagadas = 0
        else:
            total_comisiones_pagadas = 0
        
        # Contar facturas pagadas válidas (con fecha)
        num_facturas_pagadas = len(df_pagadas[df_pagadas['fecha_pago_real'].notna()]) if not df_pagadas.empty else 0
        
        # Comisiones pendientes: usar comision (aún no se sabe si perderá por >80 días)
        if not df_pendientes.empty:
            total_comisiones_pendientes = float(df_pendientes['comision'].fillna(0).sum())
        else:
            total_comisiones_pendientes = 0
        
        return {
            "comisiones_mensuales": limpiar_nan_para_json(comisiones_mensuales),
            "facturas_sin_fecha_pago": limpiar_nan_para_json(facturas_sin_fecha),
            "resumen": limpiar_nan_para_json({
                "total_comisiones_pagadas": total_comisiones_pagadas,
                "total_comisiones_pendientes": total_comisiones_pendientes,
                "num_facturas_pagadas": num_facturas_pagadas,
                "num_facturas_pendientes": len(df_pendientes)
            })
        }
    except Exception as e:
        import traceback
        print(f"Error en get_comisiones_mensuales: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comisiones-mensuales/{mes}/facturas")
async def get_facturas_por_mes(mes: str):
    """
    Obtiene las facturas que componen las comisiones de un mes específico.
    El mes debe estar en formato YYYY-MM (ej: "2025-09")
    """
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)

        df = db_manager._cargar_datos_raw()

        if df.empty:
            return {"facturas": []}

        # Convertir fechas
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
        df['fecha_pago_real'] = pd.to_datetime(df['fecha_pago_real'], errors='coerce')
        
        # Filtrar solo facturas pagadas con fecha_pago_real válida
        df['pagado'] = df.get('pagado', False).fillna(False)
        df_pagadas = df[df['pagado'] == True].copy()
        df_pagadas_validas = df_pagadas[df_pagadas['fecha_pago_real'].notna()].copy()
        
        if df_pagadas_validas.empty:
            return {"facturas": []}
        
        # Convertir mes a formato Period para comparación
        try:
            mes_periodo = pd.Period(mes)
            df_pagadas_validas['mes_pago'] = df_pagadas_validas['fecha_pago_real'].dt.to_period('M')
            
            # Filtrar facturas del mes solicitado
            df_mes = df_pagadas_validas[df_pagadas_validas['mes_pago'] == mes_periodo].copy()
            
            if df_mes.empty:
                return {"facturas": []}
            
            # Usar comision_ajustada si existe, sino comision
            if 'comision_ajustada' in df_mes.columns:
                df_mes['comision_final'] = df_mes['comision_ajustada'].fillna(df_mes['comision']).fillna(0)
            else:
                df_mes['comision_final'] = df_mes['comision'].fillna(0)
            
            # Seleccionar columnas relevantes
            facturas = []
            for _, row in df_mes.iterrows():
                facturas.append({
                    "id": int(row.get('id', 0)),
                    "factura": str(row.get('factura', 'N/A')),
                    "cliente": str(row.get('cliente', 'N/A')),
                    "pedido": str(row.get('pedido', 'N/A')),
                    "fecha_factura": str(row.get('fecha_factura', 'N/A')),
                    "fecha_pago_real": str(row.get('fecha_pago_real', 'N/A')),
                    "valor_neto_final": float(row.get('valor_neto_final', 0)) if pd.notna(row.get('valor_neto_final')) else 0,
                    "comision": float(row.get('comision_final', 0)),
                    "comision_ajustada": float(row.get('comision_ajustada', 0)) if pd.notna(row.get('comision_ajustada')) else None,
                    "dias_pago_real": int(row.get('dias_pago_real', 0)) if pd.notna(row.get('dias_pago_real')) else None,
                    "comision_perdida": bool(row.get('comision_perdida', False)) if pd.notna(row.get('comision_perdida')) else False,
                    "razon_perdida": str(row.get('razon_perdida', '')) if pd.notna(row.get('razon_perdida')) else None,
                    "cliente_propio": bool(row.get('cliente_propio', True)) if pd.notna(row.get('cliente_propio')) else True
                })
            
            return limpiar_nan_para_json({"facturas": facturas, "mes": mes})
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Formato de mes inválido. Use YYYY-MM (ej: 2025-09): {str(e)}")
    except Exception as e:
        import traceback
        print(f"Error en get_facturas_por_mes: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/comisiones-gerencia")
async def get_comisiones_gerencia():
    """
    Obtiene análisis de comisiones para gerencia
    NUEVA LÓGICA: Basada en facturas PAGADAS, no solo facturadas
    - Comisiones pagadas por mes de pago
    - Recaudo mensual (facturas pagadas)
    - Proyección de ingresos (facturas pendientes)
    """
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        from datetime import datetime, date
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        df = db_manager._cargar_datos_raw()
        
        if df.empty:
            return {
                "comisiones_pagadas_mensuales": [],
                "recaudo_mensual": [],
                "proyeccion_ingresos": [],
                "comisiones_por_cliente": [],
                "resumen": {}
            }
        
        # Convertir fechas
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
        df['fecha_pago_real'] = pd.to_datetime(df['fecha_pago_real'], errors='coerce')
        df['fecha_pago_est'] = pd.to_datetime(df['fecha_pago_est'], errors='coerce')
        
        # Separar facturas pagadas y pendientes
        df['pagado'] = df.get('pagado', False).fillna(False)
        df_pagadas = df[df['pagado'] == True].copy()
        df_pendientes = df[df['pagado'] != True].copy()
        
        # ==========================================
        # 1. COMISIONES PAGADAS POR MES DE PAGO
        # ==========================================
        comisiones_pagadas_mensuales = []
        if not df_pagadas.empty:
            df_pagadas['mes_pago'] = df_pagadas['fecha_pago_real'].dt.to_period('M').astype(str)
            
            # Usar comision_ajustada si existe y está pagada, sino comision
            if 'comision_ajustada' in df_pagadas.columns:
                df_pagadas['comision_final'] = df_pagadas['comision_ajustada'].fillna(df_pagadas['comision']).fillna(0)
            else:
                df_pagadas['comision_final'] = df_pagadas['comision'].fillna(0)
            
            # Calcular valor_neto_final para facturas pagadas
            if 'valor_neto_final' not in df_pagadas.columns:
                if 'valor_neto' in df_pagadas.columns:
                    valor_neto = df_pagadas['valor_neto'].fillna(0)
                else:
                    valor_total = df_pagadas['valor'].fillna(0)
                    valor_flete = df_pagadas['valor_flete'].fillna(0) if 'valor_flete' in df_pagadas.columns else 0
                    valor_neto = (valor_total - valor_flete) / 1.19
                
                valor_descuento = df_pagadas['valor_descuento_pesos'].fillna(0) if 'valor_descuento_pesos' in df_pagadas.columns else 0
                valor_devuelto = (df_pagadas['valor_devuelto'].fillna(0) / 1.19) if 'valor_devuelto' in df_pagadas.columns else 0
                df_pagadas['valor_neto_final'] = valor_neto - valor_descuento - valor_devuelto
            
            comisiones_mes_pago = df_pagadas.groupby('mes_pago').agg({
                'comision_final': 'sum',
                'valor_neto_final': 'sum',
                'id': 'count'
            }).reset_index()
            
            comisiones_mes_pago.columns = ['mes', 'total_comisiones', 'total_ventas', 'num_facturas']
            comisiones_pagadas_mensuales = comisiones_mes_pago.to_dict('records')
        
        # ==========================================
        # 2. RECAUDO MENSUAL (Facturas pagadas por mes de pago)
        # ==========================================
        recaudo_mensual = []
        if not df_pagadas.empty:
            # Calcular valor neto final (sin IVA, después de descuentos y devoluciones)
            if 'valor_neto_final' not in df_pagadas.columns:
                # Calcular valor_neto_final
                if 'valor_neto' in df_pagadas.columns:
                    valor_neto = df_pagadas['valor_neto'].fillna(0)
                else:
                    valor_total = df_pagadas['valor'].fillna(0)
                    valor_flete = df_pagadas['valor_flete'].fillna(0)
                    valor_neto = (valor_total - valor_flete) / 1.19
                
                valor_descuento = df_pagadas['valor_descuento_pesos'].fillna(0) if 'valor_descuento_pesos' in df_pagadas.columns else 0
                valor_devuelto = df_pagadas['valor_devuelto'].fillna(0) / 1.19 if 'valor_devuelto' in df_pagadas.columns else 0
                df_pagadas['valor_neto_final'] = valor_neto - valor_descuento - valor_devuelto
            
            recaudo_mes = df_pagadas.groupby('mes_pago').agg({
                'valor_neto_final': 'sum',
                'id': 'count'
            }).reset_index()
            
            recaudo_mes.columns = ['mes', 'total_recaudo', 'num_facturas']
            recaudo_mensual = recaudo_mes.to_dict('records')
        
        # ==========================================
        # 3. PROYECCIÓN DE INGRESOS (Facturas pendientes)
        # ==========================================
        proyeccion_ingresos = []
        if not df_pendientes.empty:
            # Usar fecha_pago_est (estimada) o calcular desde fecha_factura
            df_pendientes['fecha_pago_proyectada'] = df_pendientes['fecha_pago_est'].fillna(
                df_pendientes['fecha_factura'] + pd.Timedelta(days=35)
            )
            df_pendientes['mes_proyectado'] = df_pendientes['fecha_pago_proyectada'].dt.to_period('M').astype(str)
            
            # Calcular comisiones proyectadas
            if 'comision_ajustada' in df_pendientes.columns:
                df_pendientes['comision_proyectada'] = df_pendientes['comision_ajustada'].fillna(df_pendientes['comision'])
            else:
                df_pendientes['comision_proyectada'] = df_pendientes['comision']
            
            proyeccion_mes = df_pendientes.groupby('mes_proyectado').agg({
                'comision_proyectada': 'sum',
                'valor_neto': lambda x: x.sum() if 'valor_neto' in df_pendientes.columns else 0,
                'id': 'count'
            }).reset_index()
            
            proyeccion_mes.columns = ['mes', 'comisiones_proyectadas', 'ventas_proyectadas', 'num_facturas']
            proyeccion_ingresos = proyeccion_mes.to_dict('records')
        
        # ==========================================
        # 4. COMISIONES POR CLIENTE (Solo pagadas)
        # ==========================================
        comisiones_por_cliente = []
        if not df_pagadas.empty:
            # Asegurar que comision_final y valor_neto_final ya están calculados
            if 'comision_final' not in df_pagadas.columns:
                if 'comision_ajustada' in df_pagadas.columns:
                    df_pagadas['comision_final'] = df_pagadas['comision_ajustada'].fillna(df_pagadas['comision']).fillna(0)
                else:
                    df_pagadas['comision_final'] = df_pagadas['comision'].fillna(0)
            
            if 'valor_neto_final' not in df_pagadas.columns:
                if 'valor_neto' in df_pagadas.columns:
                    valor_neto = df_pagadas['valor_neto'].fillna(0)
                else:
                    valor_total = df_pagadas['valor'].fillna(0)
                    valor_flete = df_pagadas['valor_flete'].fillna(0) if 'valor_flete' in df_pagadas.columns else 0
                    valor_neto = (valor_total - valor_flete) / 1.19
                
                valor_descuento = df_pagadas['valor_descuento_pesos'].fillna(0) if 'valor_descuento_pesos' in df_pagadas.columns else 0
                valor_devuelto = (df_pagadas['valor_devuelto'].fillna(0) / 1.19) if 'valor_devuelto' in df_pagadas.columns else 0
                df_pagadas['valor_neto_final'] = valor_neto - valor_descuento - valor_devuelto
            
            comisiones_cliente = df_pagadas.groupby('cliente').agg({
                'comision_final': 'sum',
                'valor_neto_final': 'sum',
                'id': 'count'
            }).reset_index()
            
            comisiones_cliente.columns = ['cliente', 'total_comisiones', 'total_ventas', 'num_facturas']
            comisiones_cliente = comisiones_cliente.sort_values('total_comisiones', ascending=False).head(30)
            comisiones_por_cliente = comisiones_cliente.to_dict('records')
        
        # ==========================================
        # 5. RESUMEN
        # ==========================================
        # Calcular totales de comisiones pagadas
        if not df_pagadas.empty:
            if 'comision_final' in df_pagadas.columns:
                total_comisiones_pagadas = float(df_pagadas['comision_final'].sum())
            elif 'comision_ajustada' in df_pagadas.columns:
                total_comisiones_pagadas = float(df_pagadas['comision_ajustada'].fillna(df_pagadas['comision']).sum())
            else:
                total_comisiones_pagadas = float(df_pagadas['comision'].sum())
            
            if 'valor_neto_final' in df_pagadas.columns:
                total_recaudo = float(df_pagadas['valor_neto_final'].sum())
            else:
                # Calcular si no existe
                if 'valor_neto' in df_pagadas.columns:
                    valor_neto = df_pagadas['valor_neto'].fillna(0)
                else:
                    valor_total = df_pagadas['valor'].fillna(0)
                    valor_flete = df_pagadas['valor_flete'].fillna(0) if 'valor_flete' in df_pagadas.columns else 0
                    valor_neto = (valor_total - valor_flete) / 1.19
                
                valor_descuento = df_pagadas['valor_descuento_pesos'].fillna(0) if 'valor_descuento_pesos' in df_pagadas.columns else 0
                valor_devuelto = (df_pagadas['valor_devuelto'].fillna(0) / 1.19) if 'valor_devuelto' in df_pagadas.columns else 0
                total_recaudo = float((valor_neto - valor_descuento - valor_devuelto).sum())
        else:
            total_comisiones_pagadas = 0
            total_recaudo = 0
        
        # Calcular totales de comisiones pendientes
        if not df_pendientes.empty:
            if 'comision_proyectada' in df_pendientes.columns:
                total_comisiones_pendientes = float(df_pendientes['comision_proyectada'].sum())
            elif 'comision_ajustada' in df_pendientes.columns:
                total_comisiones_pendientes = float(df_pendientes['comision_ajustada'].fillna(df_pendientes['comision']).sum())
            else:
                total_comisiones_pendientes = float(df_pendientes['comision'].sum())
        else:
            total_comisiones_pendientes = 0
        
        total_ventas_pagadas = total_recaudo
        porcentaje_promedio = (total_comisiones_pagadas / total_ventas_pagadas * 100) if total_ventas_pagadas > 0 else 0
        
        return {
            "comisiones_pagadas_mensuales": limpiar_nan_para_json(comisiones_pagadas_mensuales),
            "recaudo_mensual": limpiar_nan_para_json(recaudo_mensual),
            "proyeccion_ingresos": limpiar_nan_para_json(proyeccion_ingresos),
            "comisiones_por_cliente": limpiar_nan_para_json(comisiones_por_cliente),
            "resumen": limpiar_nan_para_json({
                "total_comisiones_pagadas": float(total_comisiones_pagadas) if not pd.isna(total_comisiones_pagadas) else 0,
                "total_comisiones_pendientes": float(total_comisiones_pendientes) if not pd.isna(total_comisiones_pendientes) else 0,
                "total_recaudo": float(total_recaudo) if not pd.isna(total_recaudo) else 0,
                "total_ventas_pagadas": float(total_ventas_pagadas) if not pd.isna(total_ventas_pagadas) else 0,
                "porcentaje_promedio": float(porcentaje_promedio) if not pd.isna(porcentaje_promedio) else 0,
                "num_facturas_pagadas": len(df_pagadas),
                "num_facturas_pendientes": len(df_pendientes)
            })
        }
    except Exception as e:
        import traceback
        print(f"Error en get_comisiones_gerencia: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compras")
async def get_analisis_compras(
    periodo: str = Query("12", description="Número de meses a analizar")
):
    """
    Obtiene análisis detallado de compras de clientes
    Incluye KPIs, tendencias, top clientes, top referencias y análisis de frecuencia
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        from datetime import datetime, timedelta
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Calcular fecha de inicio según periodo
        try:
            meses = int(periodo)
        except:
            meses = 12
        
        fecha_inicio = (datetime.now() - timedelta(days=meses * 30)).strftime('%Y-%m-%d')
        
        # Cargar compras_clientes usando paginación automática
        all_compras = []
        page_size = 1000
        current_offset = 0
        
        while True:
            query = supabase.table("compras_clientes").select("*")
            query = query.eq("es_devolucion", False)  # Solo compras, no devoluciones
            query = query.gte("fecha", fecha_inicio)
            query = query.range(current_offset, current_offset + page_size - 1).order("fecha", desc=True)
            response = query.execute()
            
            if not response.data:
                break
            
            all_compras.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            current_offset += page_size
        
        if not all_compras:
            return {
                "kpis": {
                    "total_compras": 0,
                    "valor_total": 0,
                    "promedio_compra": 0,
                    "clientes_activos": 0,
                    "referencias_unicas": 0
                },
                "tendencias": {
                    "compras_mensuales": [],
                    "crecimiento_mensual": 0
                },
                "top_clientes": [],
                "top_referencias": [],
                "frecuencia_compras": []
            }
        
        df_compras = pd.DataFrame(all_compras)
        
        # Convertir fechas
        df_compras['fecha'] = pd.to_datetime(df_compras['fecha'], errors='coerce')
        df_compras['mes'] = df_compras['fecha'].dt.to_period('M').astype(str)
        
        # Cargar información de clientes
        clientes_response = supabase.table("clientes_b2b").select("nit, nombre, ciudad").execute()
        nit_a_info = {}
        if clientes_response.data:
            for cliente in clientes_response.data:
                nit = cliente.get('nit', '')
                if nit:
                    nit_a_info[nit] = {
                        'nombre': cliente.get('nombre', ''),
                        'ciudad': cliente.get('ciudad', '')
                    }
        
        # Agregar información de clientes
        df_compras['nombre_cliente'] = df_compras['nit_cliente'].map(lambda x: nit_a_info.get(x, {}).get('nombre', x) if x else 'N/A')
        df_compras['ciudad_cliente'] = df_compras['nit_cliente'].map(lambda x: nit_a_info.get(x, {}).get('ciudad', '') if x else '')
        
        # KPIs
        total_compras = len(df_compras)
        valor_total = float(df_compras['total'].sum()) if 'total' in df_compras.columns else 0
        promedio_compra = valor_total / total_compras if total_compras > 0 else 0
        clientes_activos = df_compras['nit_cliente'].nunique()
        referencias_unicas = df_compras['cod_articulo'].nunique() if 'cod_articulo' in df_compras.columns else 0
        
        # Tendencias - Compras mensuales
        compras_mensuales = df_compras.groupby('mes').agg({
            'total': 'sum',
            'id': 'count',
            'nit_cliente': 'nunique'
        }).reset_index()
        compras_mensuales.columns = ['mes', 'valor_total', 'num_compras', 'clientes_activos']
        
        # Calcular crecimiento mensual
        if len(compras_mensuales) >= 2:
            ultimo_mes = compras_mensuales.iloc[-1]['valor_total']
            penultimo_mes = compras_mensuales.iloc[-2]['valor_total']
            crecimiento = ((ultimo_mes - penultimo_mes) / penultimo_mes * 100) if penultimo_mes > 0 else 0
        else:
            crecimiento = 0
        
        # Top clientes por valor total
        top_clientes = df_compras.groupby('nit_cliente').agg({
            'total': 'sum',
            'id': 'count',
            'nombre_cliente': 'first',
            'ciudad_cliente': 'first',
            'fecha': ['min', 'max']
        }).reset_index()
        
        top_clientes.columns = ['nit', 'valor_total', 'num_compras', 'nombre', 'ciudad', 'primera_compra', 'ultima_compra']
        top_clientes = top_clientes.sort_values('valor_total', ascending=False).head(20)
        
        # Calcular días desde última compra
        hoy = datetime.now()
        top_clientes['dias_desde_compra'] = top_clientes['ultima_compra'].apply(
            lambda x: (hoy - pd.to_datetime(x).to_pydatetime()).days if pd.notna(x) else None
        )
        
        # Top referencias por valor total
        top_referencias = df_compras.groupby('cod_articulo').agg({
            'total': 'sum',
            'cantidad': 'sum',
            'id': 'count',
            'nit_cliente': 'nunique',
            'detalle': 'first',
            'marca': 'first'
        }).reset_index()
        
        top_referencias.columns = ['codigo', 'valor_total', 'cantidad_total', 'num_compras', 'clientes_unicos', 'detalle', 'marca']
        top_referencias = top_referencias.sort_values('valor_total', ascending=False).head(20)
        
        # Análisis de frecuencia de compras por cliente
        frecuencia_compras = df_compras.groupby('nit_cliente').agg({
            'fecha': ['min', 'max', 'count'],
            'total': 'sum',
            'nombre_cliente': 'first'
        }).reset_index()
        
        frecuencia_compras.columns = ['nit', 'primera_compra', 'ultima_compra', 'num_compras', 'valor_total', 'nombre']
        
        # Calcular frecuencia promedio (compras por mes)
        frecuencia_compras['dias_activo'] = frecuencia_compras.apply(
            lambda row: (pd.to_datetime(row['ultima_compra']) - pd.to_datetime(row['primera_compra'])).days + 1
            if pd.notna(row['primera_compra']) and pd.notna(row['ultima_compra']) else 1,
            axis=1
        )
        frecuencia_compras['frecuencia_mensual'] = (frecuencia_compras['num_compras'] / (frecuencia_compras['dias_activo'] / 30)).round(2)
        frecuencia_compras = frecuencia_compras.sort_values('valor_total', ascending=False).head(20)
        
        return {
            "kpis": limpiar_nan_para_json({
                "total_compras": int(total_compras),
                "valor_total": float(valor_total),
                "promedio_compra": float(promedio_compra),
                "clientes_activos": int(clientes_activos),
                "referencias_unicas": int(referencias_unicas)
            }),
            "tendencias": limpiar_nan_para_json({
                "compras_mensuales": limpiar_nan_para_json(compras_mensuales),
                "crecimiento_mensual": float(crecimiento) if not pd.isna(crecimiento) else 0
            }),
            "top_clientes": limpiar_nan_para_json(top_clientes),
            "top_referencias": limpiar_nan_para_json(top_referencias),
            "frecuencia_compras": limpiar_nan_para_json(frecuencia_compras)
        }
    except Exception as e:
        import traceback
        print(f"Error en get_analisis_compras: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo análisis de compras: {str(e)}")

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import base64

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

@router.get("/facturas")
async def get_facturas(
    mes: Optional[str] = Query(None, description="Mes en formato YYYY-MM"),
    cliente: Optional[str] = Query(None, description="Filtrar por nombre de cliente"),
    solo_propios: bool = Query(False, description="Solo clientes propios (False = todas las facturas)")
) -> Dict[str, Any]:
    """
    Obtiene las facturas (todas por defecto, o solo clientes propios si se especifica)
    """
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        from business.calculations import ComisionCalculator

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)

        # Obtener datos
        df = db_manager._cargar_datos_raw()

        if df.empty:
            return {
                "facturas": [],
                "total_facturas": 0,
                "total_valor": 0,
                "total_comisiones": 0
            }

        # Convertir fecha_factura
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
        df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)

        # Filtrar por clientes propios si es necesario
        if solo_propios:
            df = df[df.get('cliente_propio', False) == True].copy()

        # Filtrar por mes si se especifica
        if mes:
            df = df[df['mes_factura'] == mes].copy()

        # Filtrar por cliente si se especifica
        if cliente:
            df = df[df['cliente'].str.contains(cliente, case=False, na=False)].copy()

        if df.empty:
            return {
                "facturas": [],
                "total_facturas": 0,
                "total_valor": 0,
                "total_comisiones": 0
            }

        # Obtener ciudades de clientes desde clientes_b2b
        ciudades_clientes = {}
        try:
            clientes_b2b = supabase.table("clientes_b2b").select("nombre, ciudad").execute()
            if clientes_b2b.data:
                for cliente in clientes_b2b.data:
                    nombre_cliente = cliente.get('nombre', '').strip()
                    ciudad_cliente = cliente.get('ciudad', '').strip()
                    if nombre_cliente and ciudad_cliente:
                        ciudades_clientes[nombre_cliente] = ciudad_cliente
        except Exception as e:
            print(f"Error obteniendo ciudades de clientes: {e}")
            # Continuar sin ciudades si hay error

        # Recalcular comisiones para cada factura
        comision_calc = ComisionCalculator()
        facturas_lista = []
        facturas_actualizar_ciudad = []  # Para actualizar ciudades en BD

        for _, row in df.iterrows():
            # Obtener valores necesarios
            valor_neto = row.get('valor_neto', 0)
            if valor_neto == 0 or pd.isna(valor_neto):
                valor_total = row.get('valor', 0)
                if valor_total and not pd.isna(valor_total):
                    valor_flete = row.get('valor_flete', 0) or 0
                    valor_productos = valor_total - valor_flete
                    valor_neto = valor_productos / 1.19

            cliente_propio = row.get('cliente_propio', False)
            descuento_pie_factura = row.get('descuento_pie_factura', False)
            descuento_aplicado = row.get('descuento_adicional', 0) or row.get('descuento_aplicado', 0)
            valor_devuelto = row.get('valor_devuelto', 0) or 0
            dias_pago = row.get('dias_pago_real')
            condicion_especial = row.get('condicion_especial', False)

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
            base_final = max(0, base_final)

            # Determinar porcentaje
            # REGLA CORREGIDA:
            # - El descuento_pie_factura (15% base de la empresa) NO reduce la comisión
            # - Solo los descuentos ADICIONALES (descuento_aplicado > 0) reducen la comisión
            # - descuento_pie_factura solo afecta la base, no el porcentaje
            tiene_descuento_adicional = descuento_aplicado > 0
            if cliente_propio:
                porcentaje = 1.5 if tiene_descuento_adicional else 2.5
            else:
                porcentaje = 0.5 if tiene_descuento_adicional else 1.0

            # Verificar pérdida por +80 días
            if dias_pago and dias_pago > 80:
                comision_calculada = 0
            else:
                comision_calculada = base_final * (porcentaje / 100)

            # Formatear fecha
            fecha_factura_str = row['fecha_factura'].strftime('%Y-%m-%d') if pd.notna(row['fecha_factura']) else 'N/A'
            fecha_pago_str = row.get('fecha_pago_real')
            if fecha_pago_str and pd.notna(fecha_pago_str):
                if isinstance(fecha_pago_str, str):
                    fecha_pago_str = fecha_pago_str
                else:
                    fecha_pago_str = fecha_pago_str.strftime('%Y-%m-%d')
            else:
                fecha_pago_str = None

            # Obtener ciudad destino
            ciudad_destino = str(row.get('ciudad_destino', 'N/A'))
            cliente_nombre = str(row.get('cliente', 'N/A'))
            
            # Si la ciudad es "Resto" o está vacía, buscar en clientes_b2b
            if (ciudad_destino == 'Resto' or ciudad_destino == 'N/A' or not ciudad_destino or ciudad_destino.strip() == '') and cliente_nombre != 'N/A':
                if cliente_nombre in ciudades_clientes:
                    ciudad_destino = ciudades_clientes[cliente_nombre]
                    # Guardar para actualizar en BD
                    factura_id = int(row.get('id', 0))
                    if factura_id > 0:
                        facturas_actualizar_ciudad.append({
                            'id': factura_id,
                            'ciudad': ciudad_destino
                        })

            # Calcular valor_neto_ajustado (sin IVA, después de descuentos)
            valor_descuento_pesos = float(row.get('valor_descuento_pesos', 0)) if pd.notna(row.get('valor_descuento_pesos')) else 0
            valor_neto_ajustado = float(valor_neto) - valor_descuento_pesos
            
            # Calcular valor_devuelto sin IVA
            valor_devuelto_sin_iva = (valor_devuelto / 1.19) if valor_devuelto > 0 else 0
            
            # Valor neto final (después de descuentos y devoluciones)
            valor_neto_final = max(0, valor_neto_ajustado - valor_devuelto_sin_iva)
            
            factura = {
                "id": int(row.get('id', 0)),
                "pedido": str(row.get('pedido', 'N/A')),
                "factura": str(row.get('factura', 'N/A')),
                "cliente": cliente_nombre,
                "fecha_factura": fecha_factura_str,
                "fecha_pago": fecha_pago_str,
                "valor": float(row.get('valor', 0)) if not pd.isna(row.get('valor', 0)) else 0,  # Valor con IVA (para referencia)
                "valor_neto": float(valor_neto) if not pd.isna(valor_neto) else 0,  # Valor neto sin IVA (antes de descuentos)
                "valor_neto_ajustado": float(valor_neto_ajustado),  # Valor neto sin IVA, después de descuentos
                "valor_neto_final": float(valor_neto_final),  # Valor neto final (después de descuentos y devoluciones)
                "valor_descuento_pesos": float(valor_descuento_pesos),
                "valor_devuelto": float(valor_devuelto) if not pd.isna(valor_devuelto) else 0,
                "comision": float(comision_calculada) if not pd.isna(comision_calculada) else 0,
                "porcentaje": float(porcentaje),
                "dias_pago": int(dias_pago) if dias_pago and not pd.isna(dias_pago) else None,
                "pagado": bool(row.get('pagado', False)),
                "ciudad_destino": ciudad_destino if ciudad_destino and ciudad_destino != 'N/A' else 'Resto',
                "referencia": str(row.get('referencia', 'N/A')) if pd.notna(row.get('referencia')) else 'N/A',
                "cliente_propio": bool(cliente_propio),
                "estado": "Pagado" if row.get('pagado', False) else ("Vencido" if dias_pago and dias_pago > 80 else "Pendiente")
            }

            facturas_lista.append(factura)

        # Actualizar ciudades en la base de datos para facturas que tenían "Resto"
        if facturas_actualizar_ciudad:
            try:
                for factura_update in facturas_actualizar_ciudad:
                    supabase.table("comisiones").update({
                        'ciudad_destino': factura_update['ciudad']
                    }).eq("id", factura_update['id']).execute()
                print(f"✅ Actualizadas {len(facturas_actualizar_ciudad)} facturas con ciudades de clientes")
            except Exception as e:
                print(f"⚠️ Error actualizando ciudades en BD: {e}")
                # Continuar aunque haya error al actualizar

        # Ordenar por fecha más reciente primero
        facturas_lista.sort(key=lambda x: x['fecha_factura'], reverse=True)

        # Calcular totales
        # IMPORTANTE: total_valor debe ser valor sin IVA y después de descuentos (igual que en el dashboard)
        total_facturas = len(facturas_lista)
        
        # Calcular total_valor usando valor_neto_final (ya calculado en cada factura)
        # valor_neto_final = valor_neto - descuentos - devoluciones (sin IVA)
        total_valor = sum(f.get('valor_neto_final', f.get('valor_neto_ajustado', f.get('valor_neto', 0))) for f in facturas_lista)
        
        total_comisiones = sum(f['comision'] for f in facturas_lista)

        return limpiar_nan_para_json({
            "facturas": facturas_lista,
            "total_facturas": total_facturas,
            "total_valor": total_valor,
            "total_comisiones": total_comisiones
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo facturas: {str(e)}")

@router.get("/facturas/{factura_id}/comprobante")
async def obtener_comprobante_pago(factura_id: int) -> Dict[str, Any]:
    """
    Obtiene el comprobante de pago de una factura
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)

        # Obtener factura con comprobante
        factura = supabase.table("comisiones").select("id, factura, cliente, comprobante_pago, comprobante_nombre, comprobante_tipo").eq("id", factura_id).execute()
        
        if not factura.data:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        factura_data = factura.data[0]

        if not factura_data.get('comprobante_pago'):
            raise HTTPException(status_code=404, detail="Esta factura no tiene comprobante de pago")

        # Decodificar base64 para obtener tamaño
        comprobante_base64 = factura_data['comprobante_pago']
        comprobante_bytes = base64.b64decode(comprobante_base64)

        # Determinar content type
        content_type = factura_data.get('comprobante_tipo', 'application/octet-stream')
        if not content_type:
            # Intentar determinar por extensión
            nombre = factura_data.get('comprobante_nombre', '')
            if nombre.lower().endswith('.pdf'):
                content_type = 'application/pdf'
            elif nombre.lower().endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif nombre.lower().endswith('.png'):
                content_type = 'image/png'
            else:
                content_type = 'application/octet-stream'

        return {
            "success": True,
            "comprobante": comprobante_base64,
            "nombre": factura_data.get('comprobante_nombre', 'comprobante'),
            "tipo": content_type,
            "tamaño": len(comprobante_bytes)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo comprobante: {str(e)}")

# Modelos Pydantic para actualización
class FacturaUpdate(BaseModel):
    pedido: Optional[str] = None
    factura: Optional[str] = None
    cliente: Optional[str] = None
    fecha_factura: Optional[str] = None
    fecha_pago_real: Optional[str] = None  # Permitir actualizar fecha de pago
    valor_total: Optional[float] = None
    valor_flete: Optional[float] = None
    descuento_adicional: Optional[float] = None
    ciudad_destino: Optional[str] = None
    referencia: Optional[str] = None
    fecha_pago_real: Optional[str] = None  # Permitir actualizar fecha de pago

@router.put("/facturas/{factura_id}")
async def actualizar_factura(factura_id: int, factura_data: FacturaUpdate) -> Dict[str, Any]:
    """
    Actualiza una factura existente
    Si el cliente existe en clientes_b2b, actualiza la ciudad_destino con la ciudad del cliente
    """
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        from business.calculations import ComisionCalculator

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)

        # Obtener factura actual
        factura_actual = supabase.table("comisiones").select("*").eq("id", factura_id).execute()
        
        if not factura_actual.data:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        factura_actual = factura_actual.data[0]

        # Si se actualiza el cliente, buscar su ciudad en clientes_b2b
        cliente_nombre = factura_data.cliente if factura_data.cliente else factura_actual.get('cliente')
        ciudad_destino = factura_data.ciudad_destino

        # Si se actualiza el cliente o no se especifica ciudad, buscar en clientes_b2b
        if cliente_nombre and (not ciudad_destino or factura_data.cliente):
            try:
                cliente_b2b = supabase.table("clientes_b2b").select("ciudad").eq("nombre", cliente_nombre).execute()
                if cliente_b2b.data and cliente_b2b.data[0].get('ciudad'):
                    ciudad_destino = cliente_b2b.data[0]['ciudad']
                    # Si la ciudad del cliente existe y es diferente, actualizarla
                    if ciudad_destino and ciudad_destino.strip():
                        factura_data.ciudad_destino = ciudad_destino
            except Exception as e:
                print(f"Error buscando ciudad del cliente: {e}")
                # Continuar sin actualizar ciudad si hay error

        # Preparar datos de actualización
        # Usar el método de validación del DatabaseManager para asegurar que solo se actualicen columnas existentes
        update_data = {}
        
        # Campos que se pueden actualizar directamente
        if factura_data.pedido is not None:
            update_data['pedido'] = factura_data.pedido
        if factura_data.factura is not None:
            update_data['factura'] = factura_data.factura
        if factura_data.cliente is not None:
            update_data['cliente'] = factura_data.cliente
        if factura_data.ciudad_destino is not None:
            update_data['ciudad_destino'] = factura_data.ciudad_destino
        if factura_data.referencia is not None:
            update_data['referencia'] = factura_data.referencia
        if factura_data.descuento_adicional is not None:
            update_data['descuento_adicional'] = float(factura_data.descuento_adicional)
        
        # valor_flete puede no existir en la tabla
        # Lo agregamos al update_data, pero será validado después
        if factura_data.valor_flete is not None:
            update_data['valor_flete'] = float(factura_data.valor_flete)

        # Si se actualiza fecha_pago_real, recalcular días de pago y comisión ajustada
        if factura_data.fecha_pago_real:
            try:
                fecha_pago_str = factura_data.fecha_pago_real.strip()
                
                # Manejar formato DD/MM/YYYY o YYYY-MM-DD
                if '/' in fecha_pago_str:
                    # Formato DD/MM/YYYY
                    partes = fecha_pago_str.split('/')
                    if len(partes) == 3:
                        fecha_pago = date(int(partes[2]), int(partes[1]), int(partes[0]))
                    else:
                        raise ValueError("Formato de fecha inválido")
                else:
                    # Formato YYYY-MM-DD o ISO
                    try:
                        fecha_pago = datetime.fromisoformat(fecha_pago_str.replace('Z', '+00:00')).date()
                    except:
                        fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date()
                
                update_data['fecha_pago_real'] = fecha_pago.isoformat()
                
                # Calcular días de pago desde fecha_factura
                fecha_factura_str = factura_actual.get('fecha_factura')
                if fecha_factura_str:
                    if isinstance(fecha_factura_str, str):
                        fecha_factura = datetime.fromisoformat(fecha_factura_str.replace('Z', '+00:00')).date()
                    else:
                        fecha_factura = fecha_factura_str
                    
                    dias_pago = (fecha_pago - fecha_factura).days
                    update_data['dias_pago_real'] = dias_pago
                    
                    # Recalcular comision_ajustada si pago >80 días
                    if dias_pago > 80:
                        update_data['comision_perdida'] = True
                        update_data['razon_perdida'] = f"Pago tardío: {dias_pago} días"
                        update_data['comision_ajustada'] = 0
                    else:
                        # Si ya estaba pagada y tenía comision_ajustada, mantenerla
                        # Si no, usar comision
                        comision_actual = factura_actual.get('comision_ajustada') or factura_actual.get('comision', 0)
                        update_data['comision_perdida'] = False
                        update_data['comision_ajustada'] = float(comision_actual) if comision_actual else 0
                    
                    # Asegurar que esté marcada como pagada
                    update_data['pagado'] = True
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Formato de fecha de pago inválido: {str(e)}")

        # Si se actualiza fecha_factura, recalcular fechas de pago
        if factura_data.fecha_factura:
            fecha_factura = datetime.fromisoformat(factura_data.fecha_factura.replace('Z', '+00:00')).date()
            update_data['fecha_factura'] = fecha_factura.isoformat()
            
            condicion_especial = factura_actual.get('condicion_especial', False)
            dias_pago = 60 if condicion_especial else 35
            dias_max = 60 if condicion_especial else 45
            fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
            fecha_pago_max = fecha_factura + timedelta(days=dias_max)
            update_data['fecha_pago_est'] = fecha_pago_est.isoformat()
            update_data['fecha_pago_max'] = fecha_pago_max.isoformat()

        # Si se actualiza valor_total, recalcular valores y comisión
        if factura_data.valor_total is not None:
            valor_total = float(factura_data.valor_total)
            valor_flete = float(factura_data.valor_flete) if factura_data.valor_flete is not None else factura_actual.get('valor_flete', 0)
            
            valor_productos_con_iva = valor_total - valor_flete
            valor_neto = valor_productos_con_iva / 1.19
            iva = valor_productos_con_iva - valor_neto

            update_data['valor'] = valor_total
            update_data['valor_neto'] = valor_neto
            update_data['iva'] = iva

            # Recalcular comisión
            cliente_propio = factura_actual.get('cliente_propio', True)
            descuento_pie_factura = factura_actual.get('descuento_pie_factura', False)
            descuento_adicional = float(factura_data.descuento_adicional) if factura_data.descuento_adicional is not None else factura_actual.get('descuento_adicional', 0)
            
            comision_calc = ComisionCalculator()
            tiene_descuento = descuento_adicional > 0
            
            calc = comision_calc.calcular_comision_inteligente(
                valor_neto + iva,
                cliente_propio,
                tiene_descuento,
                descuento_pie_factura
            )

            update_data['base_comision'] = calc['base_comision']
            update_data['comision'] = calc['comision']
            update_data['porcentaje'] = calc['porcentaje']

        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        # Validar y limpiar update_data usando el método del DatabaseManager
        # Esto asegura que solo se actualicen columnas que existen en la tabla
        try:
            columnas_existentes = db_manager._get_default_columns()
            update_data_validado = db_manager._validar_updates(update_data, columnas_existentes)
        except Exception as e:
            print(f"Advertencia al validar updates: {e}")
            # Si falla la validación, intentar actualizar de todas formas
            update_data_validado = update_data

        # Si después de validar no hay campos, verificar si valor_flete fue el único campo
        if not update_data_validado and factura_data.valor_flete is not None:
            # Si solo se intentaba actualizar valor_flete y no existe, dar un mensaje más claro
            raise HTTPException(
                status_code=400, 
                detail="La columna 'valor_flete' no existe en la tabla 'comisiones'. Por favor, ejecuta el script SQL para agregar esta columna."
            )

        if not update_data_validado:
            raise HTTPException(status_code=400, detail="No hay campos válidos para actualizar")

        # Actualizar en Supabase
        try:
            resultado = supabase.table("comisiones").update(update_data_validado).eq("id", factura_id).execute()
        except Exception as e:
            error_msg = str(e)
            if 'valor_flete' in error_msg.lower():
                raise HTTPException(
                    status_code=400,
                    detail="La columna 'valor_flete' no existe en la base de datos. Por favor, ejecuta el script SQL para agregar esta columna."
                )
            raise HTTPException(status_code=400, detail=f"Error actualizando factura: {error_msg}")

        if not resultado.data:
            raise HTTPException(status_code=400, detail="Error actualizando factura")

        return {
            "success": True,
            "message": "Factura actualizada correctamente",
            "factura": resultado.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando factura: {str(e)}")

class MarcarPagadoRequest(BaseModel):
    fecha_pago: Optional[str] = None
    dias_pago: Optional[int] = None

@router.patch("/facturas/{factura_id}/marcar-pagado")
async def marcar_factura_pagado(factura_id: int, request: MarcarPagadoRequest) -> Dict[str, Any]:
    """
    Marca una factura como pagada
    Calcula automáticamente los días de pago si no se proporcionan
    """
    try:
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)

        # Obtener factura actual
        factura_actual = supabase.table("comisiones").select("*").eq("id", factura_id).execute()
        
        if not factura_actual.data:
            raise HTTPException(status_code=404, detail="Factura no encontrada")

        factura_actual = factura_actual.data[0]

        # Preparar datos de actualización
        update_data = {
            "pagado": True
        }

        # Procesar fecha de pago
        if request.fecha_pago:
            # Convertir fecha de pago a formato ISO
            try:
                fecha_pago_str = request.fecha_pago.strip()
                
                # El frontend envía formato YYYY-MM-DD (input type="date")
                if '/' in fecha_pago_str:
                    # Formato DD/MM/YYYY
                    partes = fecha_pago_str.split('/')
                    if len(partes) == 3:
                        fecha_pago = date(int(partes[2]), int(partes[1]), int(partes[0]))
                    else:
                        raise ValueError("Formato de fecha inválido")
                else:
                    # Formato YYYY-MM-DD o ISO
                    try:
                        fecha_pago = datetime.fromisoformat(fecha_pago_str.replace('Z', '+00:00')).date()
                    except:
                        # Intentar parsear YYYY-MM-DD directamente
                        fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date()
                
                update_data['fecha_pago_real'] = fecha_pago.isoformat()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Formato de fecha inválido: {str(e)}")
        else:
            # Si no se proporciona fecha, usar la fecha actual
            fecha_pago = date.today()
            update_data['fecha_pago_real'] = fecha_pago.isoformat()

        # Calcular días de pago
        if request.dias_pago is not None:
            dias_pago = request.dias_pago
        else:
            # Calcular días desde fecha_factura hasta fecha_pago
            fecha_factura_str = factura_actual.get('fecha_factura')
            if fecha_factura_str:
                try:
                    if isinstance(fecha_factura_str, str):
                        fecha_factura = datetime.fromisoformat(fecha_factura_str.replace('Z', '+00:00')).date()
                    else:
                        fecha_factura = fecha_factura_str
                    
                    dias_pago = (fecha_pago - fecha_factura).days
                except Exception as e:
                    print(f"Error calculando días de pago: {e}")
                    dias_pago = 0
            else:
                dias_pago = 0

        update_data['dias_pago_real'] = dias_pago

        # Verificar si la comisión se pierde por pago tardío (>80 días)
        if dias_pago > 80:
            update_data['comision_perdida'] = True
            update_data['razon_perdida'] = f"Pago tardío: {dias_pago} días"
            update_data['comision_ajustada'] = 0
        else:
            update_data['comision_perdida'] = False
            # Mantener la comisión original si no se pierde
            comision_original = factura_actual.get('comision', 0)
            update_data['comision_ajustada'] = float(comision_original) if comision_original else 0

        # Validar y limpiar update_data usando el método del DatabaseManager
        try:
            columnas_existentes = db_manager._get_default_columns()
            update_data_validado = db_manager._validar_updates(update_data, columnas_existentes)
        except Exception as e:
            print(f"Advertencia al validar updates: {e}")
            update_data_validado = update_data

        # Actualizar en Supabase
        try:
            resultado = supabase.table("comisiones").update(update_data_validado).eq("id", factura_id).execute()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error actualizando factura: {str(e)}")

        if not resultado.data:
            raise HTTPException(status_code=400, detail="Error marcando factura como pagada")

        return {
            "success": True,
            "message": "Factura marcada como pagada correctamente",
            "factura": resultado.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marcando factura como pagada: {str(e)}")

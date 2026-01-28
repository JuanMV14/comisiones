from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

load_dotenv()

router = APIRouter()

# Modelos Pydantic
class DevolucionCreate(BaseModel):
    factura_id: int
    valor_devuelto: float
    fecha_devolucion: str  # ISO format
    motivo: Optional[str] = None
    afecta_comision: bool = True

class DevolucionUpdate(BaseModel):
    valor_devuelto: Optional[float] = None
    fecha_devolucion: Optional[str] = None
    motivo: Optional[str] = None
    afecta_comision: Optional[bool] = None

@router.get("/compras-clientes")
async def get_devoluciones_compras_clientes(
    mes: Optional[str] = Query(None, description="Mes en formato YYYY-MM"),
    cliente: Optional[str] = Query(None, description="Filtrar por NIT o nombre de cliente")
) -> Dict[str, Any]:
    """
    Obtiene devoluciones desde la tabla compras_clientes organizadas por mes, año y cliente
    """
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
        
        # Cargar devoluciones desde compras_clientes
        query = supabase.table("compras_clientes").select("*").eq("es_devolucion", True)
        
        # Si se especifica un mes, filtrar por mes
        if mes:
            # Convertir mes a rango de fechas
            try:
                fecha_inicio = pd.to_datetime(f"{mes}-01")
                fecha_fin = fecha_inicio + pd.offsets.MonthEnd(0)
                query = query.gte("fecha", fecha_inicio.strftime('%Y-%m-%d'))
                query = query.lte("fecha", fecha_fin.strftime('%Y-%m-%d'))
            except Exception as e:
                print(f"⚠️ Error aplicando filtro de fecha: {e}")
        
        # Si se especifica un cliente, filtrar por NIT o nombre
        if cliente:
            # Primero buscar el NIT en clientes_b2b
            try:
                clientes_result = supabase.table("clientes_b2b").select("nit, nombre").or_(f"nit.ilike.%{cliente}%,nombre.ilike.%{cliente}%").execute()
                if clientes_result.data:
                    nits = [c['nit'] for c in clientes_result.data]
                    query = query.in_("nit_cliente", nits)
            except Exception as e:
                print(f"⚠️ Error filtrando por cliente: {e}")
        
        # Ejecutar consulta con paginación
        all_devoluciones = []
        page_size = 1000
        offset = 0
        
        while True:
            try:
                result = query.range(offset, offset + page_size - 1).execute()
                if not result.data:
                    break
                all_devoluciones.extend(result.data)
                if len(result.data) < page_size:
                    break
                offset += page_size
            except Exception as e:
                print(f"⚠️ Error cargando página {offset}: {e}")
                break
        
        if not all_devoluciones:
            return {
                "devoluciones": [],
                "resumen_por_mes": {},
                "resumen_por_cliente": {},
                "total_devoluciones": 0,
                "total_valor_devuelto": 0
            }
        
        # Convertir a DataFrame para procesamiento
        df = pd.DataFrame(all_devoluciones)
        
        # Asegurar que total sea numérico y negativo
        if 'total' in df.columns:
            df['total'] = pd.to_numeric(df['total'], errors='coerce').fillna(0)
            # Asegurar que los totales sean negativos (devoluciones)
            df['total'] = df['total'].abs() * -1
        
        # Convertir fecha a datetime
        if 'fecha' in df.columns:
            df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
            df['mes'] = df['fecha'].dt.to_period('M').astype(str)
            df['año'] = df['fecha'].dt.year
            df['mes_nombre'] = df['fecha'].dt.strftime('%B %Y')
        
        # Obtener información de clientes
        nits_unicos = df['nit_cliente'].unique().tolist() if 'nit_cliente' in df.columns else []
        clientes_info = {}
        if nits_unicos:
            try:
                clientes_result = supabase.table("clientes_b2b").select("nit, nombre").in_("nit", nits_unicos).execute()
                if clientes_result.data:
                    clientes_info = {c['nit']: c['nombre'] for c in clientes_result.data}
            except Exception as e:
                print(f"⚠️ Error obteniendo información de clientes: {e}")
        
        # Agregar nombre de cliente al DataFrame
        if 'nit_cliente' in df.columns:
            df['nombre_cliente'] = df['nit_cliente'].map(clientes_info).fillna(df['nit_cliente'])
        
        # Resumen por mes
        resumen_mes = {}
        if 'mes' in df.columns and 'total' in df.columns:
            resumen_mes_df = df.groupby('mes').agg({
                'total': ['sum', 'count'],
                'año': 'first',
                'mes_nombre': 'first'
            }).reset_index()
            resumen_mes_df.columns = ['mes', 'valor_total', 'cantidad', 'año', 'mes_nombre']
            
            for _, row in resumen_mes_df.iterrows():
                resumen_mes[row['mes']] = {
                    "mes": row['mes'],
                    "mes_nombre": row['mes_nombre'],
                    "año": int(row['año']) if pd.notna(row['año']) else None,
                    "cantidad": int(row['cantidad']),
                    "valor_total": abs(float(row['valor_total']))
                }
        
        # Resumen por cliente
        resumen_cliente = {}
        if 'nit_cliente' in df.columns and 'total' in df.columns:
            resumen_cliente_df = df.groupby(['nit_cliente', 'nombre_cliente']).agg({
                'total': ['sum', 'count']
            }).reset_index()
            resumen_cliente_df.columns = ['nit_cliente', 'nombre_cliente', 'valor_total', 'cantidad']
            
            for _, row in resumen_cliente_df.iterrows():
                resumen_cliente[row['nit_cliente']] = {
                    "nit": row['nit_cliente'],
                    "nombre": row['nombre_cliente'],
                    "cantidad": int(row['cantidad']),
                    "valor_total": abs(float(row['valor_total']))
                }
        
        # Formatear devoluciones para respuesta
        devoluciones_lista = []
        for _, row in df.iterrows():
            fecha_str = row['fecha'].strftime('%Y-%m-%d') if pd.notna(row['fecha']) else None
            
            devolucion = {
                "id": int(row.get('id', 0)),
                "nit_cliente": str(row.get('nit_cliente', 'N/A')),
                "nombre_cliente": str(row.get('nombre_cliente', row.get('nit_cliente', 'N/A'))),
                "num_documento": str(row.get('num_documento', 'N/A')),
                "cod_articulo": str(row.get('cod_articulo', 'N/A')),
                "referencia": str(row.get('referencia', 'N/A')),
                "cantidad": float(row.get('cantidad', 0)),
                "total": abs(float(row.get('total', 0))),  # Valor absoluto para mostrar positivo
                "fecha": fecha_str,
                "mes": str(row.get('mes', 'N/A')),
                "año": int(row.get('año', 0)) if pd.notna(row.get('año')) else None,
                "fuente": str(row.get('fuente', 'DV')) if 'fuente' in row else 'DV'
            }
            devoluciones_lista.append(devolucion)
        
        # Calcular totales
        total_valor = abs(df['total'].sum()) if 'total' in df.columns else 0
        
        return {
            "devoluciones": devoluciones_lista,
            "resumen_por_mes": resumen_mes,
            "resumen_por_cliente": resumen_cliente,
            "total_devoluciones": len(devoluciones_lista),
            "total_valor_devuelto": float(total_valor)
        }
        
    except Exception as e:
        import traceback
        print(f"❌ Error obteniendo devoluciones de compras_clientes: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo devoluciones: {str(e)}")

@router.get("")
async def get_devoluciones(
    factura_id: Optional[int] = Query(None, description="Filtrar por ID de factura"),
    cliente: Optional[str] = Query(None, description="Filtrar por nombre de cliente"),
    mes: Optional[str] = Query(None, description="Mes en formato YYYY-MM"),
    afecta_comision: Optional[bool] = Query(None, description="Filtrar por si afecta comisión")
) -> Dict[str, Any]:
    """
    Obtiene lista de devoluciones con información de factura relacionada
    """
    try:
        from database.queries import DatabaseManager
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
        db_manager = DatabaseManager(supabase)
        
        # Cargar devoluciones
        df = db_manager.cargar_devoluciones()
        
        if df.empty:
            return {
                "devoluciones": [],
                "total_devoluciones": 0,
                "total_valor_devuelto": 0
            }
        
        # Filtrar por factura_id si se especifica
        if factura_id:
            df = df[df['factura_id'] == factura_id].copy()
        
        # Filtrar por cliente si se especifica
        if cliente:
            if 'factura_cliente' in df.columns:
                df = df[df['factura_cliente'].str.contains(cliente, case=False, na=False)].copy()
        
        # Filtrar por mes si se especifica
        if mes:
            df['fecha_devolucion'] = pd.to_datetime(df['fecha_devolucion'], errors='coerce')
            df['mes_devolucion'] = df['fecha_devolucion'].dt.to_period('M').astype(str)
            df = df[df['mes_devolucion'] == mes].copy()
        
        # Filtrar por afecta_comision si se especifica
        if afecta_comision is not None:
            df = df[df['afecta_comision'] == afecta_comision].copy()
        
        # Convertir a lista de diccionarios
        devoluciones_lista = []
        for _, row in df.iterrows():
            fecha_devolucion = row.get('fecha_devolucion')
            if pd.notna(fecha_devolucion):
                if isinstance(fecha_devolucion, pd.Timestamp):
                    fecha_devolucion_str = fecha_devolucion.strftime('%Y-%m-%d')
                else:
                    fecha_devolucion_str = str(fecha_devolucion)
            else:
                fecha_devolucion_str = None
            
            devolucion = {
                "id": int(row.get('id', 0)),
                "factura_id": int(row.get('factura_id', 0)),
                "valor_devuelto": float(row.get('valor_devuelto', 0)),
                "fecha_devolucion": fecha_devolucion_str,
                "motivo": str(row.get('motivo', '')) if pd.notna(row.get('motivo')) else '',
                "afecta_comision": bool(row.get('afecta_comision', True)),
                "factura": {
                    "pedido": str(row.get('factura_pedido', 'N/A')) if 'factura_pedido' in row else 'N/A',
                    "cliente": str(row.get('factura_cliente', 'N/A')) if 'factura_cliente' in row else 'N/A',
                    "factura": str(row.get('factura_factura', 'N/A')) if 'factura_factura' in row else 'N/A',
                    "valor": float(row.get('factura_valor', 0)) if 'factura_valor' in row else 0,
                    "comision": float(row.get('factura_comision', 0)) if 'factura_comision' in row else 0
                }
            }
            devoluciones_lista.append(devolucion)
        
        # Calcular totales
        total_valor_devuelto = df['valor_devuelto'].sum() if not df.empty else 0
        
        return {
            "devoluciones": devoluciones_lista,
            "total_devoluciones": len(devoluciones_lista),
            "total_valor_devuelto": float(total_valor_devuelto) if not pd.isna(total_valor_devuelto) else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo devoluciones: {str(e)}")

@router.get("/facturas-disponibles")
async def get_facturas_disponibles() -> List[Dict[str, Any]]:
    """
    Obtiene lista de facturas disponibles para crear devoluciones
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
        
        # Obtener facturas
        df = db_manager.cargar_datos()
        
        if df.empty:
            return []
        
        # Convertir a lista
        facturas = []
        for _, row in df.iterrows():
            factura = {
                "id": int(row.get('id', 0)),
                "pedido": str(row.get('pedido', 'N/A')),
                "cliente": str(row.get('cliente', 'N/A')),
                "factura": str(row.get('factura', 'N/A')),
                "fecha_factura": str(row.get('fecha_factura', '')) if pd.notna(row.get('fecha_factura')) else '',
                "valor": float(row.get('valor', 0)) if pd.notna(row.get('valor')) else 0,
                "valor_neto": float(row.get('valor_neto', 0)) if pd.notna(row.get('valor_neto')) else 0
            }
            facturas.append(factura)
        
        return facturas
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo facturas: {str(e)}")

@router.post("")
async def crear_devolucion(devolucion_data: DevolucionCreate) -> Dict[str, Any]:
    """
    Crea una nueva devolución
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
        
        # Validar que la factura existe
        factura = supabase.table("comisiones").select("*").eq("id", devolucion_data.factura_id).execute()
        if not factura.data:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        
        # Preparar datos
        data = {
            "factura_id": devolucion_data.factura_id,
            "valor_devuelto": float(devolucion_data.valor_devuelto),
            "fecha_devolucion": devolucion_data.fecha_devolucion,
            "motivo": devolucion_data.motivo or '',
            "afecta_comision": devolucion_data.afecta_comision
        }
        
        # Insertar devolución
        success = db_manager.insertar_devolucion(data)
        
        if not success:
            raise HTTPException(status_code=400, detail="Error creando devolución")
        
        # Obtener la devolución creada
        response = supabase.table("devoluciones").select("""
            *,
            comisiones!devoluciones_factura_id_fkey(
                pedido,
                cliente,
                factura,
                valor
            )
        """).order("id", desc=True).limit(1).execute()
        
        if response.data:
            devolucion = response.data[0]
            return {
                "success": True,
                "mensaje": "Devolución creada exitosamente",
                "devolucion": devolucion
            }
        
        return {"success": True, "mensaje": "Devolución creada exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando devolución: {str(e)}")

@router.put("/{devolucion_id}")
async def actualizar_devolucion(devolucion_id: int, devolucion_data: DevolucionUpdate) -> Dict[str, Any]:
    """
    Actualiza una devolución existente
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Verificar que la devolución existe
        devolucion_actual = supabase.table("devoluciones").select("*").eq("id", devolucion_id).execute()
        if not devolucion_actual.data:
            raise HTTPException(status_code=404, detail="Devolución no encontrada")
        
        factura_id = devolucion_actual.data[0]['factura_id']
        valor_original = devolucion_actual.data[0]['valor_devuelto']
        afecta_original = devolucion_actual.data[0].get('afecta_comision', True)
        
        # Preparar datos de actualización
        update_data = {}
        if devolucion_data.valor_devuelto is not None:
            update_data['valor_devuelto'] = float(devolucion_data.valor_devuelto)
        if devolucion_data.fecha_devolucion is not None:
            update_data['fecha_devolucion'] = devolucion_data.fecha_devolucion
        if devolucion_data.motivo is not None:
            update_data['motivo'] = devolucion_data.motivo
        if devolucion_data.afecta_comision is not None:
            update_data['afecta_comision'] = devolucion_data.afecta_comision
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Actualizar
        resultado = supabase.table("devoluciones").update(update_data).eq("id", devolucion_id).execute()
        
        if not resultado.data:
            raise HTTPException(status_code=400, detail="Error actualizando devolución")
        
        # Si cambió afecta_comision o valor_devuelto, recalcular comisión
        if (devolucion_data.afecta_comision is not None and devolucion_data.afecta_comision != afecta_original) or \
           (devolucion_data.valor_devuelto is not None and devolucion_data.valor_devuelto != valor_original):
            from database.queries import DatabaseManager
            db_manager = DatabaseManager(supabase)
            db_manager._actualizar_comision_por_devolucion(factura_id, update_data.get('valor_devuelto', valor_original))
        
        return {
            "success": True,
            "mensaje": "Devolución actualizada exitosamente",
            "devolucion": resultado.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando devolución: {str(e)}")

@router.delete("/{devolucion_id}")
async def eliminar_devolucion(devolucion_id: int) -> Dict[str, Any]:
    """
    Elimina una devolución
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        from database.queries import DatabaseManager

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Obtener devolución antes de eliminar
        devolucion = supabase.table("devoluciones").select("*").eq("id", devolucion_id).execute()
        if not devolucion.data:
            raise HTTPException(status_code=404, detail="Devolución no encontrada")
        
        factura_id = devolucion.data[0]['factura_id']
        afecta_comision = devolucion.data[0].get('afecta_comision', True)
        
        # Eliminar
        resultado = supabase.table("devoluciones").delete().eq("id", devolucion_id).execute()
        
        if not resultado.data:
            raise HTTPException(status_code=400, detail="Error eliminando devolución")
        
        # Si afectaba comisión, recalcular comisión de la factura
        if afecta_comision:
            db_manager = DatabaseManager(supabase)
            # Obtener total de devoluciones restantes
            devoluciones_restantes = supabase.table("devoluciones").select("valor_devuelto").eq("factura_id", factura_id).eq("afecta_comision", True).execute()
            total_devuelto = sum([d['valor_devuelto'] for d in devoluciones_restantes.data]) if devoluciones_restantes.data else 0
            db_manager._actualizar_comision_por_devolucion(factura_id, total_devuelto)
        
        return {
            "success": True,
            "mensaje": "Devolución eliminada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando devolución: {str(e)}")

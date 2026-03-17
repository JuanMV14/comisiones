from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

load_dotenv()

router = APIRouter()

# Modelos Pydantic
class PresupuestoCreate(BaseModel):
    mes: str  # Formato: YYYY-MM
    meta_ventas: float
    meta_clientes_nuevos: Optional[int] = 0  # Meta de cantidad de clientes a los que se les vende (no clientes nuevos)
    # meta_comisiones: Optional[float] = 0  # Comentado porque no existe en la BD

class PresupuestoUpdate(BaseModel):
    meta_ventas: Optional[float] = None
    meta_clientes_nuevos: Optional[int] = None  # Meta de cantidad de clientes a los que se les vende (no clientes nuevos)
    # meta_comisiones: Optional[float] = None  # Comentado porque no existe en la BD

@router.get("/presupuestos")
async def obtener_presupuestos() -> Dict[str, Any]:
    """
    Obtiene todos los presupuestos mensuales
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Obtener todos los presupuestos ordenados por mes descendente
        response = supabase.table("metas_mensuales").select("*").order("mes", desc=True).execute()
        
        return {
            "presupuestos": response.data if response.data else [],
            "total": len(response.data) if response.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error obteniendo presupuestos: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo presupuestos: {str(e)}")

@router.get("/presupuestos/{mes}")
async def obtener_presupuesto_mes(mes: str) -> Dict[str, Any]:
    """
    Obtiene el presupuesto de un mes específico (formato: YYYY-MM)
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        response = supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
        
        if not response.data or len(response.data) == 0:
            return {
                "presupuesto": None,
                "mes": mes
            }
        
        return {
            "presupuesto": response.data[0],
            "mes": mes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error obteniendo presupuesto: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo presupuesto: {str(e)}")

@router.post("/presupuestos")
async def crear_presupuesto(presupuesto: PresupuestoCreate) -> Dict[str, Any]:
    """
    Crea un nuevo presupuesto mensual
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Validar formato de mes
        try:
            datetime.strptime(presupuesto.mes, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de mes inválido. Debe ser YYYY-MM")
        
        # Verificar si ya existe un presupuesto para ese mes
        existing = supabase.table("metas_mensuales").select("*").eq("mes", presupuesto.mes).execute()
        
        if existing.data and len(existing.data) > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya existe un presupuesto para el mes {presupuesto.mes}. Use PUT para actualizar."
            )
        
        # Crear el presupuesto
        data = {
            "mes": presupuesto.mes,
            "meta_ventas": presupuesto.meta_ventas,
            "meta_clientes_nuevos": presupuesto.meta_clientes_nuevos or 0
        }
        
        response = supabase.table("metas_mensuales").insert(data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Error al crear el presupuesto")
        
        return {
            "mensaje": "Presupuesto creado exitosamente",
            "presupuesto": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error creando presupuesto: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error creando presupuesto: {str(e)}")

@router.put("/presupuestos/{mes}")
async def actualizar_presupuesto(mes: str, presupuesto: PresupuestoUpdate) -> Dict[str, Any]:
    """
    Actualiza un presupuesto mensual existente
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Validar formato de mes
        try:
            datetime.strptime(mes, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de mes inválido. Debe ser YYYY-MM")
        
        # Verificar si existe el presupuesto
        existing = supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
        
        if not existing.data or len(existing.data) == 0:
            raise HTTPException(status_code=404, detail=f"No existe un presupuesto para el mes {mes}")
        
        # Preparar datos para actualizar (solo los campos que se proporcionaron)
        data = {}
        if presupuesto.meta_ventas is not None:
            data["meta_ventas"] = presupuesto.meta_ventas
        if presupuesto.meta_clientes_nuevos is not None:
            data["meta_clientes_nuevos"] = presupuesto.meta_clientes_nuevos
        # if presupuesto.meta_comisiones is not None:
        #     data["meta_comisiones"] = presupuesto.meta_comisiones  # Comentado porque no existe en la BD
        
        if not data:
            raise HTTPException(status_code=400, detail="Debe proporcionar al menos un campo para actualizar")
        
        # Actualizar el presupuesto
        response = supabase.table("metas_mensuales").update(data).eq("mes", mes).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Error al actualizar el presupuesto")
        
        return {
            "mensaje": "Presupuesto actualizado exitosamente",
            "presupuesto": response.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error actualizando presupuesto: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error actualizando presupuesto: {str(e)}")

@router.delete("/presupuestos/{mes}")
async def eliminar_presupuesto(mes: str) -> Dict[str, Any]:
    """
    Elimina un presupuesto mensual
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Validar formato de mes
        try:
            datetime.strptime(mes, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de mes inválido. Debe ser YYYY-MM")
        
        # Verificar si existe el presupuesto
        existing = supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
        
        if not existing.data or len(existing.data) == 0:
            raise HTTPException(status_code=404, detail=f"No existe un presupuesto para el mes {mes}")
        
        # Eliminar el presupuesto
        response = supabase.table("metas_mensuales").delete().eq("mes", mes).execute()
        
        return {
            "mensaje": "Presupuesto eliminado exitosamente",
            "mes": mes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error eliminando presupuesto: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error eliminando presupuesto: {str(e)}")

# Modelos para presupuestos por marca (presupuesto total para las 4 marcas)
class PresupuestoMarcaCreate(BaseModel):
    mes: str  # Formato: YYYY-MM
    meta_ventas: float  # Presupuesto total para EFFIX, MOTEK USA, KBS, TOYAMA combinadas

class PresupuestoMarcaUpdate(BaseModel):
    meta_ventas: Optional[float] = None

@router.get("/presupuestos-marcas")
async def obtener_presupuestos_marcas(mes: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene presupuestos por marca.
    Si se especifica mes, solo retorna ese mes. Si no, retorna todos.
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Intentar obtener de la tabla metas_marcas_mensuales
        # Si no existe, usar JSONB en metas_mensuales o crear estructura temporal
        query = supabase.table("metas_mensuales").select("*")
        if mes:
            query = query.eq("mes", mes)
        else:
            query = query.order("mes", desc=True)
        
        response = query.execute()
        
        # Por ahora, retornar estructura vacía si no existe la tabla específica
        # Más adelante podemos crear la tabla metas_marcas_mensuales
        return {
            "presupuestos": [],
            "total": 0,
            "mensaje": "Tabla de presupuestos por marca aún no implementada en BD"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error obteniendo presupuestos por marca: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo presupuestos por marca: {str(e)}")

@router.get("/presupuestos-marcas/{mes}")
async def obtener_presupuestos_marcas_mes(mes: str) -> Dict[str, Any]:
    """
    Obtiene presupuesto total para las 4 marcas (EFFIX, MOTEK USA, KBS, TOYAMA) 
    y calcula ventas reales combinadas de esas marcas.
    Retorna un solo presupuesto total y ventas por marca individual.
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        import json
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Validar formato de mes
        try:
            datetime.strptime(mes, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de mes inválido. Debe ser YYYY-MM")
        
        # Marcas objetivo
        marcas_objetivo = ['EFFIX', 'MOTEK USA', 'KBS', 'TOYAMA']
        
        # Presupuesto total (uno solo para las 4 marcas)
        meta_ventas_total = 0
        
        # Intentar obtener presupuesto guardado desde metas_mensuales
        existing = supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
        if existing.data and len(existing.data) > 0:
            registro = existing.data[0]
            if 'presupuesto_marcas_total' in registro and registro['presupuesto_marcas_total']:
                try:
                    if isinstance(registro['presupuesto_marcas_total'], (int, float)):
                        meta_ventas_total = float(registro['presupuesto_marcas_total'])
                    elif isinstance(registro['presupuesto_marcas_total'], str):
                        meta_ventas_total = float(registro['presupuesto_marcas_total'])
                except Exception as e:
                    print(f"Error parseando presupuesto_marcas_total: {e}")
        
        # Obtener NITs de clientes propios
        clientes_propios_response = supabase.table("clientes_b2b").select("nit").eq("cliente_propio", True).eq("activo", True).execute()
        nits_clientes_propios = set()
        if clientes_propios_response.data:
            nits_clientes_propios = {str(c['nit']).strip() for c in clientes_propios_response.data}
        
        if not nits_clientes_propios:
            # Si no hay clientes propios, retornar presupuesto con ventas en 0
            return {
                "mes": mes,
                "meta_ventas_total": meta_ventas_total,
                "ventas_totales_marcas": 0,
                "progreso_total": 0,
                "faltante_total": meta_ventas_total,
                "ventas_por_marca": {marca: 0 for marca in marcas_objetivo},
                "marcas": marcas_objetivo,
                "mensaje": "No hay clientes propios registrados"
            }
        
        # Calcular ventas reales desde compras_clientes
        # Obtener todas las compras (sin devoluciones) y filtrar por mes después de parsear
        # No filtrar por fecha en Supabase porque puede haber problemas de formato
        # Mejor cargar todas y filtrar después de parsear correctamente
        
        # Cargar compras usando paginación (sin filtro de fecha inicial)
        all_compras = []
        page_size = 1000
        current_offset = 0
        
        while True:
            response_compras = supabase.table("compras_clientes").select("*").eq("es_devolucion", False).range(current_offset, current_offset + page_size - 1).execute()
            
            if not response_compras.data:
                break
            
            all_compras.extend(response_compras.data)
            
            if len(response_compras.data) < page_size:
                break
            
            current_offset += page_size
        
        # Inicializar variables para ventas
        ventas_totales_marcas = 0
        ventas_por_marca_individual = {marca: 0 for marca in marcas_objetivo}
        
        if all_compras:
            df_compras = pd.DataFrame(all_compras)
            
            # Convertir fecha a datetime - usar dayfirst=False para interpretar MM/DD/YYYY (mes/día/año)
            df_compras['fecha'] = pd.to_datetime(df_compras['fecha'], errors='coerce', dayfirst=False)
            
            # Filtrar fechas válidas
            df_compras = df_compras[df_compras['fecha'].notna()].copy()
            
            # Calcular mes de compra
            df_compras['mes_compra'] = df_compras['fecha'].dt.strftime('%Y-%m')
            
            # Filtrar por mes exacto
            df_mes = df_compras[df_compras['mes_compra'] == mes].copy()
            
            # Debug: imprimir información sobre las compras encontradas
            print(f"🔍 Presupuestos por marca - Mes: {mes}")
            print(f"   Total compras cargadas: {len(df_compras)}")
            print(f"   Compras del mes {mes}: {len(df_mes)}")
            if not df_mes.empty:
                print(f"   Rango de fechas encontradas: {df_mes['fecha'].min()} a {df_mes['fecha'].max()}")
                print(f"   Meses únicos en df_mes: {df_mes['mes_compra'].unique()}")
                print(f"   NITs únicos en df_mes: {df_mes['nit_cliente'].unique()[:10] if 'nit_cliente' in df_mes.columns else 'N/A'}")
                print(f"   Marcas únicas en df_mes: {df_mes['marca'].unique()[:10] if 'marca' in df_mes.columns else 'N/A'}")
            
            # FILTRAR SOLO COMPRAS DE CLIENTES PROPIOS
            if not df_mes.empty and 'nit_cliente' in df_mes.columns:
                df_mes['nit_cliente_normalizado'] = df_mes['nit_cliente'].astype(str).str.strip()
                print(f"   Total compras antes de filtrar clientes propios: {len(df_mes)}")
                print(f"   NITs de clientes propios: {list(nits_clientes_propios)[:10]}")
                df_mes = df_mes[df_mes['nit_cliente_normalizado'].isin(nits_clientes_propios)].copy()
                print(f"   Total compras después de filtrar clientes propios: {len(df_mes)}")
            
            if not df_mes.empty:
                # Normalizar nombres de marcas (mayúsculas, sin espacios extra)
                df_mes['marca_normalizada'] = df_mes['marca'].astype(str).str.upper().str.strip()
                
                # Mapeo de variaciones de nombres de marcas
                mapeo_marcas = {
                    'EFFIX': ['EFFIX'],
                    'MOTEK USA': ['MOTEK USA', 'MOTEK', 'MOTEKUSA'],
                    'KBS': ['KBS'],
                    'TOYAMA': ['TOYAMA']
                }
                
                # Filtrar solo las compras de las marcas objetivo
                df_marcas_objetivo = pd.DataFrame()
                for marca_obj in marcas_objetivo:
                    variaciones = mapeo_marcas.get(marca_obj, [marca_obj])
                    for variacion in variaciones:
                        mask = df_mes['marca_normalizada'].str.contains(variacion.upper(), case=False, na=False) | \
                               (df_mes['marca_normalizada'] == variacion.upper())
                        df_marcas_objetivo = pd.concat([df_marcas_objetivo, df_mes[mask]], ignore_index=True)
                
                # Eliminar duplicados si hay alguna compra que coincida con múltiples variaciones
                df_marcas_objetivo = df_marcas_objetivo.drop_duplicates(subset=['id'] if 'id' in df_marcas_objetivo.columns else [])
                
                print(f"   Compras de marcas objetivo encontradas: {len(df_marcas_objetivo)}")
                if not df_marcas_objetivo.empty:
                    print(f"   Marcas encontradas: {df_marcas_objetivo['marca_normalizada'].unique()}")
                    print(f"   Total ventas marcas objetivo: {df_marcas_objetivo['total'].sum()}")
                
                # Calcular ventas totales de las 4 marcas combinadas
                ventas_totales_marcas = float(df_marcas_objetivo['total'].sum()) if not df_marcas_objetivo.empty else 0
                
                # Calcular ventas por marca individual (para mostrar desglose)
                if not df_marcas_objetivo.empty:
                    ventas_por_marca_df = df_marcas_objetivo.groupby('marca_normalizada').agg({
                        'total': 'sum'
                    }).reset_index()
                    
                    for _, row in ventas_por_marca_df.iterrows():
                        marca_normalizada = row['marca_normalizada']
                        total_ventas = float(row['total'])
                        
                        # Asignar a la marca correspondiente
                        for marca_obj in marcas_objetivo:
                            variaciones = mapeo_marcas.get(marca_obj, [marca_obj])
                            for variacion in variaciones:
                                if variacion.upper() == marca_normalizada or marca_normalizada.startswith(variacion.upper()) or variacion.upper() in marca_normalizada:
                                    ventas_por_marca_individual[marca_obj] += total_ventas
                                    break
        
        # Calcular progreso total
        progreso_total = 0
        faltante_total = 0
        if meta_ventas_total > 0:
            progreso_total = (ventas_totales_marcas / meta_ventas_total) * 100
            faltante_total = max(0, meta_ventas_total - ventas_totales_marcas)
        
        # Construir resultado con presupuesto total y desglose por marca
        resultado = {
            "mes": mes,
            "meta_ventas_total": meta_ventas_total,
            "ventas_totales_marcas": ventas_totales_marcas,
            "progreso_total": round(progreso_total, 2),
            "faltante_total": round(faltante_total, 2),
            "ventas_por_marca": ventas_por_marca_individual,
            "marcas": marcas_objetivo
        }
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error obteniendo presupuestos por marca: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo presupuestos por marca: {str(e)}")

@router.post("/presupuestos-marcas")
async def crear_presupuesto_marca(presupuesto: PresupuestoMarcaCreate) -> Dict[str, Any]:
    """
    Crea o actualiza el presupuesto total para las 4 marcas (EFFIX, MOTEK USA, KBS, TOYAMA) 
    para un mes específico.
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Validar formato de mes
        try:
            datetime.strptime(presupuesto.mes, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de mes inválido. Debe ser YYYY-MM")
        
        # Obtener o crear registro en metas_mensuales
        existing = supabase.table("metas_mensuales").select("*").eq("mes", presupuesto.mes).execute()
        
        try:
            if existing.data and len(existing.data) > 0:
                # Actualizar existente
                update_data = {
                    'presupuesto_marcas_total': presupuesto.meta_ventas
                }
                response = supabase.table("metas_mensuales").update(update_data).eq("mes", presupuesto.mes).execute()
            else:
                # Crear nuevo registro
                data = {
                    "mes": presupuesto.mes,
                    "meta_ventas": 0,  # Mantener compatibilidad
                    "meta_clientes_nuevos": 0,
                    "presupuesto_marcas_total": presupuesto.meta_ventas
                }
                response = supabase.table("metas_mensuales").insert(data).execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Error al guardar el presupuesto por marca")
        except Exception as e:
            error_msg = str(e)
            if "column" in error_msg.lower() and "presupuesto_marcas_total" in error_msg.lower():
                raise HTTPException(
                    status_code=500, 
                    detail="El campo 'presupuesto_marcas_total' no existe en la tabla metas_mensuales. Por favor ejecuta el script SQL 'database/agregar_campo_presupuesto_marcas_total.sql' en Supabase."
                )
            raise
        
        return {
            "mensaje": f"Presupuesto total para las 4 marcas guardado exitosamente",
            "presupuesto": {
                "mes": presupuesto.mes,
                "meta_ventas_total": presupuesto.meta_ventas
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error guardando presupuesto por marca: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error guardando presupuesto por marca: {str(e)}")

@router.put("/presupuestos-marcas/{mes}")
async def actualizar_presupuesto_marca(mes: str, presupuesto: PresupuestoMarcaUpdate) -> Dict[str, Any]:
    """
    Actualiza el presupuesto total para las 4 marcas existente
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Validar formato de mes
        try:
            datetime.strptime(mes, "%Y-%m")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de mes inválido. Debe ser YYYY-MM")
        
        if presupuesto.meta_ventas is None:
            raise HTTPException(status_code=400, detail="Debe proporcionar meta_ventas")
        
        # Obtener registro existente
        existing = supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
        
        if not existing.data or len(existing.data) == 0:
            raise HTTPException(status_code=404, detail=f"No existe un registro para el mes {mes}")
        
        # Actualizar presupuesto total
        try:
            update_data = {
                'presupuesto_marcas_total': presupuesto.meta_ventas
            }
            
            response = supabase.table("metas_mensuales").update(update_data).eq("mes", mes).execute()
            
            if not response.data:
                raise HTTPException(status_code=500, detail="Error al actualizar el presupuesto por marca")
        except Exception as e:
            error_msg = str(e)
            if "column" in error_msg.lower() and "presupuesto_marcas_total" in error_msg.lower():
                raise HTTPException(
                    status_code=500, 
                    detail="El campo 'presupuesto_marcas_total' no existe en la tabla metas_mensuales. Por favor ejecuta el script SQL 'database/agregar_campo_presupuesto_marcas_total.sql' en Supabase."
                )
            raise
        
        return {
            "mensaje": f"Presupuesto total para las 4 marcas actualizado exitosamente",
            "presupuesto": {
                "mes": mes,
                "meta_ventas_total": presupuesto.meta_ventas
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error actualizando presupuesto por marca: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error actualizando presupuesto por marca: {str(e)}")

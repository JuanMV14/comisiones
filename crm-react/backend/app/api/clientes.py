from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

load_dotenv()

router = APIRouter()

# Modelos Pydantic para validación
class ClienteCreate(BaseModel):
    nombre: str
    nit: Optional[str] = None
    contacto: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    cupo_total: Optional[float] = 0
    plazo_pago: Optional[int] = 30
    descuento_predeterminado: Optional[float] = 0
    cliente_propio: Optional[bool] = True
    vendedor: Optional[str] = None

class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    nit: Optional[str] = None
    contacto: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    ciudad: Optional[str] = None
    direccion: Optional[str] = None
    cupo_total: Optional[float] = None
    plazo_pago: Optional[int] = None
    descuento_predeterminado: Optional[float] = None
    cliente_propio: Optional[bool] = None
    activo: Optional[bool] = None
    vendedor: Optional[str] = None

@router.get("")
async def get_clientes() -> List[Dict[str, Any]]:
    """
    Obtiene lista de todos los clientes
    Reutiliza database/queries.py y database/client_purchases_manager.py
    """
    try:
        from database.queries import DatabaseManager
        from database.client_purchases_manager import ClientPurchasesManager
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
        
        # Obtener clientes de la tabla comisiones
        df_comisiones = db_manager.cargar_datos()
        clientes_comisiones = []
        
        if not df_comisiones.empty and 'cliente' in df_comisiones.columns:
            clientes_unicos = df_comisiones['cliente'].dropna().unique()
            for cliente in clientes_unicos:
                cliente_data = df_comisiones[df_comisiones['cliente'] == cliente].iloc[0]
                clientes_comisiones.append({
                    "id": hash(cliente) % 1000000,  # ID temporal
                    "nombre": cliente,
                    "contacto": cliente_data.get('cliente', ''),
                    "ciudad": cliente_data.get('ciudad_destino', 'N/A') if 'ciudad_destino' in cliente_data else 'N/A',
                    "estado": "activo"
                })
        
        # También obtener clientes B2B
        try:
            clientes_manager = ClientPurchasesManager(supabase)
            df_clientes_b2b = clientes_manager.listar_clientes()
            
            if not df_clientes_b2b.empty:
                for _, row in df_clientes_b2b.iterrows():
                    # Buscar si ya existe en la lista
                    cliente_existe_idx = next((i for i, c in enumerate(clientes_comisiones) if c['nombre'] == row['nombre']), None)
                    
                    if cliente_existe_idx is not None:
                        # Actualizar con datos de B2B (tiene más información)
                        clientes_comisiones[cliente_existe_idx].update({
                            "id": int(row.get('id', hash(row['nombre']) % 1000000)),  # Usar ID real de BD
                            "nit": row.get('nit', ''),
                            "contacto": row.get('contacto', clientes_comisiones[cliente_existe_idx].get('contacto', '')),
                            "email": row.get('email', ''),
                            "telefono": row.get('telefono', ''),
                            "ciudad": row.get('ciudad', clientes_comisiones[cliente_existe_idx].get('ciudad', 'N/A')),
                            "direccion": row.get('direccion', ''),
                            "credito": float(row.get('cupo_total', 0)) if pd.notna(row.get('cupo_total')) else 0,
                            "cupo_total": float(row.get('cupo_total', 0)) if pd.notna(row.get('cupo_total')) else 0,
                            "plazo_pago": int(row.get('plazo_pago', 30)) if pd.notna(row.get('plazo_pago')) else 30,
                            "descuento_predeterminado": float(row.get('descuento_predeterminado', 0)) if pd.notna(row.get('descuento_predeterminado')) else 0,
                            "cliente_propio": bool(row.get('cliente_propio', True)) if pd.notna(row.get('cliente_propio')) else True,
                            "estado": "activo" if row.get('activo', True) else "inactivo"
                        })
                    else:
                        # Agregar nuevo cliente B2B
                        clientes_comisiones.append({
                            "id": int(row.get('id', hash(row['nombre']) % 1000000)),  # Usar ID real de BD
                            "nombre": row['nombre'],
                            "nit": row.get('nit', ''),
                            "contacto": row.get('contacto', ''),
                            "email": row.get('email', ''),
                            "telefono": row.get('telefono', ''),
                            "ciudad": row.get('ciudad', 'N/A'),
                            "direccion": row.get('direccion', ''),
                            "credito": float(row.get('cupo_total', 0)) if pd.notna(row.get('cupo_total')) else 0,
                            "cupo_total": float(row.get('cupo_total', 0)) if pd.notna(row.get('cupo_total')) else 0,
                            "plazo_pago": int(row.get('plazo_pago', 30)) if pd.notna(row.get('plazo_pago')) else 30,
                            "descuento_predeterminado": float(row.get('descuento_predeterminado', 0)) if pd.notna(row.get('descuento_predeterminado')) else 0,
                            "cliente_propio": bool(row.get('cliente_propio', True)) if pd.notna(row.get('cliente_propio')) else True,
                            "estado": "activo" if row.get('activo', True) else "inactivo"
                        })
        except Exception as e:
            print(f"Error obteniendo clientes B2B: {e}")
            pass  # Si hay error con B2B, continuar solo con comisiones
        
        return clientes_comisiones
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo clientes: {str(e)}")

@router.get("/detalle")
async def get_cliente_detalle(nombre: str = Query(...)):
    """
    Obtiene el detalle completo de un cliente
    Reutiliza la lógica de ui/tabs.py render_clientes_vendedor
    """
    try:
        from database.queries import DatabaseManager
        from database.client_purchases_manager import ClientPurchasesManager
        from supabase import create_client
        from config.settings import AppConfig

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
        
        # Obtener datos del cliente (reutilizar lógica existente)
        df = db_manager.cargar_datos()
        df_cliente = df[df['cliente'] == nombre] if not df.empty and 'cliente' in df.columns else pd.DataFrame()
        
        # Obtener cliente B2B si existe
        clientes_manager = ClientPurchasesManager(supabase)
        # ... más lógica de detalle de cliente
        
        return {
            "nombre": nombre,
            "compras": len(df_cliente) if not df_cliente.empty else 0,
            # ... más campos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{cliente_id}")
async def get_cliente_by_id(cliente_id: int):
    """Obtiene un cliente por ID"""
    try:
        clientes = await get_clientes()
        cliente = next((c for c in clientes if c['id'] == cliente_id), None)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return cliente
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def crear_cliente(cliente_data: ClienteCreate) -> Dict[str, Any]:
    """Crea un nuevo cliente en la tabla clientes_b2b"""
    try:
        from database.client_purchases_manager import ClientPurchasesManager
        from supabase import create_client
        from config.settings import AppConfig

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        clientes_manager = ClientPurchasesManager(supabase)

        # Preparar datos (solo campos que existen en la tabla)
        datos_cliente = {
            'nombre': cliente_data.nombre,
            'nit': cliente_data.nit or '',
            'email': cliente_data.email or '',
            'telefono': cliente_data.telefono or '',
            'ciudad': cliente_data.ciudad or '',
            'direccion': cliente_data.direccion or '',
            'cupo_total': cliente_data.cupo_total or 0,
            'plazo_pago': cliente_data.plazo_pago or 30,
            'descuento_predeterminado': cliente_data.descuento_predeterminado or 0,
            'vendedor': cliente_data.vendedor or ''
        }
        
        # Campos opcionales (pueden no existir en la tabla aún)
        if cliente_data.contacto:
            datos_cliente['contacto'] = cliente_data.contacto or cliente_data.nombre
        
        if cliente_data.cliente_propio is not None:
            datos_cliente['cliente_propio'] = cliente_data.cliente_propio

        resultado = clientes_manager.registrar_cliente(datos_cliente)
        
        if 'error' in resultado:
            raise HTTPException(status_code=400, detail=resultado['error'])
        
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando cliente: {str(e)}")

@router.put("/{cliente_id}")
async def actualizar_cliente(cliente_id: int, cliente_data: ClienteUpdate) -> Dict[str, Any]:
    """Actualiza un cliente existente o lo crea si no existe"""
    try:
        from database.client_purchases_manager import ClientPurchasesManager
        from supabase import create_client
        from config.settings import AppConfig
        from datetime import datetime

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        clientes_manager = ClientPurchasesManager(supabase)
        
        # Intentar obtener cliente por ID
        cliente_actual = supabase.table("clientes_b2b").select("*").eq("id", cliente_id).execute()
        
        # Si no existe por ID, buscar por nombre o NIT
        if not cliente_actual.data:
            # El ID puede ser un hash generado, buscar por nombre o NIT
            nombre_buscar = cliente_data.nombre
            nit_buscar = cliente_data.nit
            
            if nombre_buscar:
                cliente_por_nombre = supabase.table("clientes_b2b").select("*").eq("nombre", nombre_buscar).execute()
                if cliente_por_nombre.data:
                    cliente_actual = cliente_por_nombre
                    cliente_id = cliente_por_nombre.data[0]['id']
            
            if not cliente_actual.data and nit_buscar:
                cliente_por_nit = supabase.table("clientes_b2b").select("*").eq("nit", nit_buscar).execute()
                if cliente_por_nit.data:
                    cliente_actual = cliente_por_nit
                    cliente_id = cliente_por_nit.data[0]['id']
        
        # Si aún no existe, crear el cliente
        if not cliente_actual.data:
            # Crear nuevo cliente usando los datos proporcionados
            datos_cliente = {
                'nombre': cliente_data.nombre or 'Cliente sin nombre',
                'nit': cliente_data.nit or '',
                'email': cliente_data.email or '',
                'telefono': cliente_data.telefono or '',
                'ciudad': cliente_data.ciudad or '',
                'direccion': cliente_data.direccion or '',
                'cupo_total': float(cliente_data.cupo_total) if cliente_data.cupo_total is not None else 0,
                'plazo_pago': int(cliente_data.plazo_pago) if cliente_data.plazo_pago is not None else 30,
                'descuento_predeterminado': float(cliente_data.descuento_predeterminado) if cliente_data.descuento_predeterminado is not None else 0,
                'vendedor': cliente_data.vendedor or ''
            }
            
            # Campos opcionales
            if cliente_data.contacto:
                datos_cliente['contacto'] = cliente_data.contacto or cliente_data.nombre or ''
            
            if cliente_data.cliente_propio is not None:
                datos_cliente['cliente_propio'] = cliente_data.cliente_propio
            
            resultado_crear = clientes_manager.registrar_cliente(datos_cliente)
            
            if 'error' in resultado_crear:
                raise HTTPException(status_code=400, detail=resultado_crear['error'])
            
            # Obtener el cliente recién creado
            if nit_buscar:
                cliente_creado = clientes_manager.obtener_cliente(nit_buscar)
            else:
                # Buscar por nombre
                cliente_creado = supabase.table("clientes_b2b").select("*").eq("nombre", datos_cliente['nombre']).execute()
                cliente_creado = cliente_creado.data[0] if cliente_creado.data else None
            
            return {"success": True, "mensaje": "Cliente creado", "cliente": cliente_creado}
        
        # Si existe, actualizar
        # Preparar datos de actualización
        # Solo incluir campos que sabemos que existen en la tabla
        update_data = {}
        if cliente_data.nombre is not None:
            update_data['nombre'] = cliente_data.nombre
        if cliente_data.nit is not None:
            update_data['nit'] = cliente_data.nit
        if cliente_data.email is not None:
            update_data['email'] = cliente_data.email
        if cliente_data.telefono is not None:
            update_data['telefono'] = cliente_data.telefono
        if cliente_data.ciudad is not None:
            update_data['ciudad'] = cliente_data.ciudad
        if cliente_data.direccion is not None:
            update_data['direccion'] = cliente_data.direccion
        if cliente_data.cupo_total is not None:
            update_data['cupo_total'] = float(cliente_data.cupo_total)
        if cliente_data.plazo_pago is not None:
            update_data['plazo_pago'] = int(cliente_data.plazo_pago)
        if cliente_data.descuento_predeterminado is not None:
            update_data['descuento_predeterminado'] = float(cliente_data.descuento_predeterminado)
        if cliente_data.activo is not None:
            update_data['activo'] = bool(cliente_data.activo)
        if cliente_data.vendedor is not None:
            update_data['vendedor'] = cliente_data.vendedor
        
        # Campos opcionales (pueden no existir en la tabla aún)
        # Intentar actualizar, pero no fallar si la columna no existe
        if cliente_data.contacto is not None:
            try:
                update_data['contacto'] = cliente_data.contacto
            except:
                pass  # Ignorar si la columna no existe
        
        if cliente_data.cliente_propio is not None:
            try:
                update_data['cliente_propio'] = bool(cliente_data.cliente_propio)
            except:
                pass  # Ignorar si la columna no existe
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        update_data['fecha_actualizacion'] = datetime.now().isoformat()
        
        # Actualizar
        resultado = supabase.table("clientes_b2b").update(update_data).eq("id", cliente_id).execute()
        
        if not resultado.data:
            raise HTTPException(status_code=400, detail="Error actualizando cliente")
        
        return {"success": True, "mensaje": "Cliente actualizado", "cliente": resultado.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando cliente: {str(e)}")

@router.get("/b2b/listado")
async def get_clientes_b2b_listado(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    ciudad: Optional[str] = Query(None, description="Filtrar por ciudad"),
    busqueda: Optional[str] = Query(None, description="Buscar por nombre o NIT"),
    limit: int = Query(0, description="Límite de resultados (0 = sin límite)"),
    offset: int = Query(0, description="Offset para paginación")
) -> Dict[str, Any]:
    """
    Obtiene lista completa de clientes B2B con estadísticas de compras
    """
    try:
        from database.client_purchases_manager import ClientPurchasesManager
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        from datetime import datetime, timedelta

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        clientes_manager = ClientPurchasesManager(supabase)

        # Cargar todos los clientes B2B usando paginación automática
        all_clientes = []
        page_size = 1000
        current_offset = 0
        
        while True:
            query = supabase.table("clientes_b2b").select("*")
            
            if activo is not None:
                query = query.eq("activo", activo)
            
            if ciudad:
                query = query.ilike("ciudad", f"%{ciudad}%")
            
            if busqueda:
                query = query.or_(f"nombre.ilike.%{busqueda}%,nit.ilike.%{busqueda}%")
            
            query = query.range(current_offset, current_offset + page_size - 1).order("nombre", desc=False)
            response = query.execute()
            
            if not response.data:
                break
            
            all_clientes.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            current_offset += page_size

        if not all_clientes:
            return {
                "clientes": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }

        df_clientes = pd.DataFrame(all_clientes)

        # Cargar compras de todos los clientes (usando paginación)
        all_compras = []
        current_offset_compras = 0
        
        while True:
            query_compras = supabase.table("compras_clientes").select("*").range(current_offset_compras, current_offset_compras + page_size - 1)
            response_compras = query_compras.execute()
            
            if not response_compras.data:
                break
            
            all_compras.extend(response_compras.data)
            
            if len(response_compras.data) < page_size:
                break
            
            current_offset_compras += page_size

        df_compras = pd.DataFrame(all_compras) if all_compras else pd.DataFrame()

        # Calcular estadísticas por cliente
        clientes_con_stats = []
        for _, cliente_row in df_clientes.iterrows():
            cliente_id = cliente_row.get('id')
            nit_cliente = cliente_row.get('nit', '')
            
            # Filtrar compras de este cliente
            if not df_compras.empty:
                compras_cliente = df_compras[
                    (df_compras['cliente_id'] == cliente_id) | 
                    (df_compras['nit_cliente'] == nit_cliente)
                ].copy()
            else:
                compras_cliente = pd.DataFrame()

            # Calcular estadísticas
            total_compras = len(compras_cliente[compras_cliente.get('es_devolucion', False) == False]) if not compras_cliente.empty else 0
            total_devoluciones = len(compras_cliente[compras_cliente.get('es_devolucion', False) == True]) if not compras_cliente.empty else 0
            
            # Calcular valor total de compras (sin devoluciones)
            if not compras_cliente.empty:
                compras_sin_devol = compras_cliente[compras_cliente.get('es_devolucion', False) == False]
                valor_total_compras = float(compras_sin_devol['total'].sum()) if 'total' in compras_sin_devol.columns else 0
                
                # Última compra
                compras_sin_devol['fecha'] = pd.to_datetime(compras_sin_devol['fecha'], errors='coerce')
                ultima_compra = compras_sin_devol['fecha'].max() if not compras_sin_devol.empty else None
                ultima_compra_str = ultima_compra.isoformat() if ultima_compra and pd.notna(ultima_compra) else None
                
                # Días desde última compra
                if ultima_compra and pd.notna(ultima_compra):
                    dias_desde_compra = (datetime.now() - ultima_compra.to_pydatetime()).days
                else:
                    dias_desde_compra = None
            else:
                valor_total_compras = 0
                ultima_compra_str = None
                dias_desde_compra = None

            # Calcular cupo disponible
            cupo_total = float(cliente_row.get('cupo_total', 0)) if pd.notna(cliente_row.get('cupo_total')) else 0
            cupo_utilizado = float(cliente_row.get('cupo_utilizado', 0)) if pd.notna(cliente_row.get('cupo_utilizado')) else 0
            cupo_disponible = cupo_total - cupo_utilizado

            cliente_dict = {
                "id": int(cliente_row.get('id', 0)),
                "nombre": str(cliente_row.get('nombre', '')),
                "nit": str(cliente_row.get('nit', '')),
                "ciudad": str(cliente_row.get('ciudad', '')) if pd.notna(cliente_row.get('ciudad')) else None,
                "email": str(cliente_row.get('email', '')) if pd.notna(cliente_row.get('email')) else None,
                "telefono": str(cliente_row.get('telefono', '')) if pd.notna(cliente_row.get('telefono')) else None,
                "direccion": str(cliente_row.get('direccion', '')) if pd.notna(cliente_row.get('direccion')) else None,
                "cupo_total": cupo_total,
                "cupo_utilizado": cupo_utilizado,
                "cupo_disponible": cupo_disponible,
                "plazo_pago": int(cliente_row.get('plazo_pago', 30)) if pd.notna(cliente_row.get('plazo_pago')) else 30,
                "descuento_predeterminado": float(cliente_row.get('descuento_predeterminado', 0)) if pd.notna(cliente_row.get('descuento_predeterminado')) else 0,
                "vendedor": str(cliente_row.get('vendedor', '')) if pd.notna(cliente_row.get('vendedor')) else None,
                "cliente_propio": bool(cliente_row.get('cliente_propio', True)) if pd.notna(cliente_row.get('cliente_propio')) else True,
                "activo": bool(cliente_row.get('activo', True)) if pd.notna(cliente_row.get('activo')) else True,
                "fecha_registro": str(cliente_row.get('fecha_registro', '')) if pd.notna(cliente_row.get('fecha_registro')) else None,
                "fecha_actualizacion": str(cliente_row.get('fecha_actualizacion', '')) if pd.notna(cliente_row.get('fecha_actualizacion')) else None,
                # Estadísticas de compras
                "total_compras": total_compras,
                "total_devoluciones": total_devoluciones,
                "valor_total_compras": valor_total_compras,
                "ultima_compra": ultima_compra_str,
                "dias_desde_compra": dias_desde_compra
            }
            
            clientes_con_stats.append(cliente_dict)

        # Aplicar filtro de búsqueda adicional si es necesario
        if busqueda:
            busqueda_lower = busqueda.lower()
            clientes_con_stats = [
                c for c in clientes_con_stats
                if busqueda_lower in c['nombre'].lower() or busqueda_lower in c['nit'].lower()
            ]

        # Aplicar paginación del cliente si se especifica
        total_filtrado = len(clientes_con_stats)
        if limit > 0 and offset >= 0:
            clientes_paginados = clientes_con_stats[offset:offset + limit]
        else:
            clientes_paginados = clientes_con_stats

        return {
            "clientes": clientes_paginados,
            "total": total_filtrado,
            "limit": limit if limit > 0 else total_filtrado,
            "offset": offset
        }

    except Exception as e:
        import traceback
        print(f"Error en get_clientes_b2b_listado: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo clientes B2B: {str(e)}")

@router.get("/b2b/{cliente_id}/compras")
async def get_compras_cliente(
    cliente_id: int,
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    solo_compras: Optional[bool] = Query(False, description="Solo compras, excluir devoluciones"),
    limit: int = Query(0, description="Límite de resultados (0 = sin límite)"),
    offset: int = Query(0, description="Offset para paginación")
) -> Dict[str, Any]:
    """
    Obtiene el historial de compras de un cliente B2B específico
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        from datetime import datetime

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)

        # Obtener información del cliente
        cliente_response = supabase.table("clientes_b2b").select("*").eq("id", cliente_id).execute()
        
        if not cliente_response.data:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        cliente = cliente_response.data[0]
        nit_cliente = cliente.get('nit', '')

        # Cargar compras usando paginación automática
        all_compras = []
        page_size = 1000
        current_offset = 0
        
        while True:
            query = supabase.table("compras_clientes").select("*")
            
            # Filtrar por cliente (ID o NIT)
            query = query.or_(f"cliente_id.eq.{cliente_id},nit_cliente.eq.{nit_cliente}")
            
            if solo_compras:
                query = query.eq("es_devolucion", False)
            
            if fecha_inicio:
                query = query.gte("fecha", fecha_inicio)
            
            if fecha_fin:
                query = query.lte("fecha", fecha_fin)
            
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
                "compras": [],
                "total": 0,
                "cliente": cliente,
                "resumen": {
                    "total_compras": 0,
                    "total_devoluciones": 0,
                    "valor_total": 0,
                    "valor_devoluciones": 0
                }
            }

        df_compras = pd.DataFrame(all_compras)
        
        # Convertir fechas
        df_compras['fecha'] = pd.to_datetime(df_compras['fecha'], errors='coerce')

        # Calcular resumen
        compras_sin_devol = df_compras[df_compras.get('es_devolucion', False) == False]
        devoluciones = df_compras[df_compras.get('es_devolucion', False) == True]
        
        valor_total = float(compras_sin_devol['total'].sum()) if 'total' in compras_sin_devol.columns and not compras_sin_devol.empty else 0
        valor_devoluciones = float(devoluciones['total'].sum()) if 'total' in devoluciones.columns and not devoluciones.empty else 0

        # Calcular totales por factura/documento
        totales_por_factura = {}
        if not df_compras.empty and 'num_documento' in df_compras.columns:
            # Agrupar por documento y calcular total (solo compras, no devoluciones)
            compras_por_doc = compras_sin_devol.groupby('num_documento').agg({
                'total': 'sum',
                'fecha': 'first',
                'id': 'count'
            }).reset_index()
            
            for _, doc_row in compras_por_doc.iterrows():
                doc_num = str(doc_row['num_documento']) if pd.notna(doc_row['num_documento']) else 'N/A'
                totales_por_factura[doc_num] = {
                    'total_factura': float(doc_row['total']),
                    'fecha': str(doc_row['fecha']) if pd.notna(doc_row['fecha']) else None,
                    'num_items': int(doc_row['id'])
                }

        # Formatear compras
        compras_formateadas = []
        for _, row in df_compras.iterrows():
            num_doc = str(row.get('num_documento', '')) if pd.notna(row.get('num_documento')) else 'N/A'
            total_factura_info = totales_por_factura.get(num_doc, {})
            
            compras_formateadas.append({
                "id": int(row.get('id', 0)),
                "num_documento": num_doc,
                "fecha": str(row.get('fecha', '')) if pd.notna(row.get('fecha')) else None,
                "cod_articulo": str(row.get('cod_articulo', '')),
                "detalle": str(row.get('detalle', '')),
                "cantidad": int(row.get('cantidad', 0)) if pd.notna(row.get('cantidad')) else 0,
                "valor_unitario": float(row.get('valor_unitario', 0)) if pd.notna(row.get('valor_unitario')) else 0,
                "descuento": float(row.get('descuento', 0)) if pd.notna(row.get('descuento')) else 0,
                "total": float(row.get('total', 0)) if pd.notna(row.get('total')) else 0,
                "marca": str(row.get('marca', '')) if pd.notna(row.get('marca')) else None,
                "familia": str(row.get('familia', '')) if pd.notna(row.get('familia')) else None,
                "grupo": str(row.get('grupo', '')) if pd.notna(row.get('grupo')) else None,
                "es_devolucion": bool(row.get('es_devolucion', False)) if pd.notna(row.get('es_devolucion')) else False,
                "sincronizado": bool(row.get('sincronizado', False)) if pd.notna(row.get('sincronizado')) else False,
                "factura_id": int(row.get('factura_id', 0)) if pd.notna(row.get('factura_id')) else None,
                # Agregar información del total de la factura
                "total_factura": total_factura_info.get('total_factura', 0),
                "num_items_factura": total_factura_info.get('num_items', 0)
            })

        # Aplicar paginación si se especifica
        total_compras = len(compras_formateadas)
        if limit > 0 and offset >= 0:
            compras_paginadas = compras_formateadas[offset:offset + limit]
        else:
            compras_paginadas = compras_formateadas

        return {
            "compras": compras_paginadas,
            "total": total_compras,
            "cliente": cliente,
            "resumen": {
                "total_compras": len(compras_sin_devol),
                "total_devoluciones": len(devoluciones),
                "valor_total": valor_total,
                "valor_devoluciones": valor_devoluciones,
                "valor_neto": valor_total - valor_devoluciones
            },
            "limit": limit if limit > 0 else total_compras,
            "offset": offset
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error en get_compras_cliente: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo compras del cliente: {str(e)}")

@router.get("/b2b/stats/resumen")
async def get_resumen_clientes_b2b() -> Dict[str, Any]:
    """
    Obtiene estadísticas generales de clientes B2B
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)

        # Cargar todos los clientes usando paginación
        all_clientes = []
        page_size = 1000
        current_offset = 0
        
        while True:
            response = supabase.table("clientes_b2b").select("*").range(current_offset, current_offset + page_size - 1).execute()
            
            if not response.data:
                break
            
            all_clientes.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            current_offset += page_size

        if not all_clientes:
            return {
                "total_clientes": 0,
                "clientes_activos": 0,
                "clientes_inactivos": 0,
                "total_cupo": 0,
                "cupo_utilizado": 0,
                "cupo_disponible": 0,
                "ciudades": []
            }

        df_clientes = pd.DataFrame(all_clientes)

        # Estadísticas básicas
        total_clientes = len(df_clientes)
        clientes_activos = len(df_clientes[df_clientes.get('activo', True) == True]) if 'activo' in df_clientes.columns else 0
        clientes_inactivos = total_clientes - clientes_activos

        # Cupos
        total_cupo = float(df_clientes['cupo_total'].sum()) if 'cupo_total' in df_clientes.columns else 0
        cupo_utilizado = float(df_clientes['cupo_utilizado'].sum()) if 'cupo_utilizado' in df_clientes.columns else 0
        cupo_disponible = total_cupo - cupo_utilizado

        # Ciudades únicas
        ciudades = []
        if 'ciudad' in df_clientes.columns:
            ciudades_df = df_clientes[df_clientes['ciudad'].notna() & (df_clientes['ciudad'] != '')]['ciudad'].unique()
            ciudades = sorted([str(c) for c in ciudades_df])

        return {
            "total_clientes": total_clientes,
            "clientes_activos": clientes_activos,
            "clientes_inactivos": clientes_inactivos,
            "total_cupo": total_cupo,
            "cupo_utilizado": cupo_utilizado,
            "cupo_disponible": cupo_disponible,
            "ciudades": ciudades
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")

@router.delete("/{cliente_id}")
async def eliminar_cliente(cliente_id: int) -> Dict[str, Any]:
    """Elimina un cliente (soft delete: marca como inactivo)"""
    try:
        from supabase import create_client
        from config.settings import AppConfig
        from datetime import datetime

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Verificar si el cliente existe
        cliente_actual = supabase.table("clientes_b2b").select("*").eq("id", cliente_id).execute()
        
        # Si no existe por ID, puede ser un cliente de comisiones (ID hash)
        # Buscar por nombre en la lista de clientes
        if not cliente_actual.data:
            # Obtener información del cliente desde la lista de clientes
            clientes_lista = await get_clientes()
            cliente_info = next((c for c in clientes_lista if c.get('id') == cliente_id), None)
            
            if cliente_info:
                # Es un cliente de comisiones, buscar por nombre en clientes_b2b
                nombre_cliente = cliente_info.get('nombre')
                if nombre_cliente:
                    cliente_por_nombre = supabase.table("clientes_b2b").select("*").eq("nombre", nombre_cliente).execute()
                    if cliente_por_nombre.data:
                        cliente_actual = cliente_por_nombre
                        cliente_id = cliente_por_nombre.data[0]['id']
            
            # Si aún no existe, el cliente solo está en comisiones, no en clientes_b2b
            if not cliente_actual.data:
                return {
                    "success": False,
                    "mensaje": "Cliente no encontrado en clientes_b2b. Este cliente solo existe en el historial de comisiones y no puede ser eliminado desde aquí.",
                    "cliente": None,
                    "nota": "Los clientes que solo existen en comisiones no se pueden eliminar desde esta interfaz."
                }
        
        # Soft delete: marcar como inactivo en lugar de eliminar físicamente
        # Esto mantiene la integridad de los datos históricos
        update_data = {
            'activo': False,
            'fecha_actualizacion': datetime.now().isoformat()
        }
        
        resultado = supabase.table("clientes_b2b").update(update_data).eq("id", cliente_id).execute()
        
        if not resultado.data:
            raise HTTPException(status_code=400, detail="Error eliminando cliente")
        
        return {
            "success": True, 
            "mensaje": "Cliente eliminado (marcado como inactivo)", 
            "cliente": resultado.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando cliente: {str(e)}")

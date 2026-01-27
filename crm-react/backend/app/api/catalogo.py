from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
import sys
import os
import pandas as pd
import io

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

router = APIRouter()

# Modelos Pydantic
class ProductoCreate(BaseModel):
    cod_ur: str
    referencia: str
    descripcion: str
    precio: float
    marca: Optional[str] = None
    linea: Optional[str] = None
    equivalencia: Optional[str] = None
    detalle_descuento: Optional[str] = None
    activo: bool = True

class ProductoUpdate(BaseModel):
    cod_ur: Optional[str] = None
    referencia: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    marca: Optional[str] = None
    linea: Optional[str] = None
    equivalencia: Optional[str] = None
    detalle_descuento: Optional[str] = None
    activo: Optional[bool] = None

@router.get("/productos")
async def get_productos(
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    linea: Optional[str] = Query(None, description="Filtrar por línea"),
    marca: Optional[str] = Query(None, description="Filtrar por marca"),
    busqueda: Optional[str] = Query(None, description="Buscar en código, referencia, descripción, línea o marca"),
    limit: int = Query(0, description="Límite de resultados (0 = sin límite, cargar todos)"),
    offset: int = Query(0, description="Offset para paginación")
) -> Dict[str, Any]:
    """
    Obtiene la lista de productos del catálogo con filtros opcionales
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

        # Cargar TODOS los productos usando paginación automática (similar a CatalogManager)
        # Supabase tiene un límite de 1000 registros por consulta, así que necesitamos paginar
        all_data = []
        page_size = 1000  # Máximo permitido por Supabase
        current_offset = 0
        
        while True:
            # Construir query base para esta página
            query = supabase.table("catalogo_productos").select("*", count="exact")

            # Aplicar filtros
            if activo is not None:
                query = query.eq("activo", activo)
            
            if marca:
                query = query.ilike("marca", f"%{marca}%")
            
            if linea:
                query = query.ilike("linea", f"%{linea}%")
            
            if busqueda:
                # Buscar en múltiples campos usando OR
                query = query.or_(f"descripcion.ilike.%{busqueda}%,cod_ur.ilike.%{busqueda}%,referencia.ilike.%{busqueda}%,linea.ilike.%{busqueda}%,marca.ilike.%{busqueda}%")

            # Aplicar paginación para esta página
            query = query.range(current_offset, current_offset + page_size - 1)
            
            # Ordenar por cod_ur
            query = query.order("cod_ur", desc=False)

            response = query.execute()
            
            if not response.data:
                break
            
            all_data.extend(response.data)
            
            # Si obtuvimos menos registros que el tamaño de página, terminamos
            if len(response.data) < page_size:
                break
            
            current_offset += page_size
        
        if not all_data:
            return {
                "productos": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }

        # Convertir a DataFrame para procesamiento
        df = pd.DataFrame(all_data)
        
        # Obtener el total antes de aplicar filtros adicionales
        total_registros = len(df)

        # Si hay búsqueda, filtrar más específicamente (por si el filtro de Supabase no fue suficiente)
        if busqueda:
            busqueda_lower = busqueda.lower()
            mask = (
                df['cod_ur'].astype(str).str.lower().str.contains(busqueda_lower, na=False) |
                df['referencia'].astype(str).str.lower().str.contains(busqueda_lower, na=False) |
                df['descripcion'].astype(str).str.lower().str.contains(busqueda_lower, na=False) |
                df['linea'].astype(str).str.lower().str.contains(busqueda_lower, na=False) |
                df['marca'].astype(str).str.lower().str.contains(busqueda_lower, na=False)
            )
            df = df[mask]

        # Aplicar paginación del cliente si se especifica (para la respuesta)
        total_filtrado = len(df)
        # Si limit es 0 o negativo, devolver todos los resultados
        if limit > 0 and offset >= 0:
            df_paginado = df.iloc[offset:offset + limit]
        else:
            df_paginado = df

        productos = []
        for _, row in df_paginado.iterrows():
            productos.append({
                "id": int(row.get('id', 0)),
                "cod_ur": str(row.get('cod_ur', '')),
                "referencia": str(row.get('referencia', '')),
                "descripcion": str(row.get('descripcion', '')),
                "precio": float(row.get('precio', 0)) if pd.notna(row.get('precio')) else 0,
                "marca": str(row.get('marca', '')) if pd.notna(row.get('marca')) else None,
                "linea": str(row.get('linea', '')) if pd.notna(row.get('linea')) else None,
                "equivalencia": str(row.get('equivalencia', '')) if pd.notna(row.get('equivalencia')) else None,
                "detalle_descuento": str(row.get('detalle_descuento', '')) if pd.notna(row.get('detalle_descuento')) else None,
                "activo": bool(row.get('activo', True)) if pd.notna(row.get('activo')) else True,
                "fecha_actualizacion": str(row.get('fecha_actualizacion', '')) if pd.notna(row.get('fecha_actualizacion')) else None
            })

        return {
            "productos": productos,
            "total": total_filtrado,  # Total después de filtros
            "total_sin_filtros": total_registros,  # Total antes de filtros
            "limit": limit if limit > 0 else total_filtrado,
            "offset": offset
        }

    except Exception as e:
        import traceback
        print(f"Error en get_productos: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")

@router.get("/productos/{producto_id}")
async def get_producto(producto_id: int) -> Dict[str, Any]:
    """
    Obtiene un producto específico por ID
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)

        response = supabase.table("catalogo_productos").select("*").eq("id", producto_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        producto = response.data[0]

        return {
            "id": int(producto.get('id', 0)),
            "cod_ur": str(producto.get('cod_ur', '')),
            "referencia": str(producto.get('referencia', '')),
            "descripcion": str(producto.get('descripcion', '')),
            "precio": float(producto.get('precio', 0)) if producto.get('precio') is not None else 0,
            "marca": producto.get('marca'),
            "linea": producto.get('linea'),
            "equivalencia": producto.get('equivalencia'),
            "detalle_descuento": producto.get('detalle_descuento'),
            "activo": bool(producto.get('activo', True)),
            "fecha_actualizacion": str(producto.get('fecha_actualizacion', '')) if producto.get('fecha_actualizacion') else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo producto: {str(e)}")

@router.post("/productos")
async def crear_producto(producto: ProductoCreate) -> Dict[str, Any]:
    """
    Crea un nuevo producto en el catálogo
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)

        # Verificar si ya existe un producto con el mismo cod_ur
        existente = supabase.table("catalogo_productos").select("id").eq("cod_ur", producto.cod_ur).execute()
        
        if existente.data:
            raise HTTPException(status_code=400, detail=f"Ya existe un producto con el código {producto.cod_ur}")

        # Crear el producto
        nuevo_producto = {
            "cod_ur": producto.cod_ur.strip().upper(),
            "referencia": producto.referencia.strip().upper(),
            "descripcion": producto.descripcion.strip(),
            "precio": float(producto.precio),
            "marca": producto.marca.strip() if producto.marca else None,
            "linea": producto.linea.strip() if producto.linea else None,
            "equivalencia": producto.equivalencia.strip() if producto.equivalencia else None,
            "detalle_descuento": producto.detalle_descuento.strip() if producto.detalle_descuento else None,
            "activo": producto.activo,
            "fecha_actualizacion": datetime.now().isoformat()
        }

        response = supabase.table("catalogo_productos").insert(nuevo_producto).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Error creando producto")

        return {
            "success": True,
            "message": "Producto creado correctamente",
            "producto": response.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando producto: {str(e)}")

@router.put("/productos/{producto_id}")
async def actualizar_producto(producto_id: int, producto: ProductoUpdate) -> Dict[str, Any]:
    """
    Actualiza un producto existente
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)

        # Verificar que el producto existe
        producto_actual = supabase.table("catalogo_productos").select("*").eq("id", producto_id).execute()
        
        if not producto_actual.data:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # Preparar datos de actualización
        update_data = {}
        
        if producto.cod_ur is not None:
            # Verificar que el nuevo cod_ur no esté en uso por otro producto
            existente = supabase.table("catalogo_productos").select("id").eq("cod_ur", producto.cod_ur).neq("id", producto_id).execute()
            if existente.data:
                raise HTTPException(status_code=400, detail=f"Ya existe otro producto con el código {producto.cod_ur}")
            update_data["cod_ur"] = producto.cod_ur.strip().upper()
        
        if producto.referencia is not None:
            update_data["referencia"] = producto.referencia.strip().upper()
        
        if producto.descripcion is not None:
            update_data["descripcion"] = producto.descripcion.strip()
        
        if producto.precio is not None:
            update_data["precio"] = float(producto.precio)
        
        if producto.marca is not None:
            update_data["marca"] = producto.marca.strip() if producto.marca else None
        
        if producto.linea is not None:
            update_data["linea"] = producto.linea.strip() if producto.linea else None
        
        if producto.equivalencia is not None:
            update_data["equivalencia"] = producto.equivalencia.strip() if producto.equivalencia else None
        
        if producto.detalle_descuento is not None:
            update_data["detalle_descuento"] = producto.detalle_descuento.strip() if producto.detalle_descuento else None
        
        if producto.activo is not None:
            update_data["activo"] = producto.activo
        
        update_data["fecha_actualizacion"] = datetime.now().isoformat()

        if not update_data:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")

        # Actualizar
        response = supabase.table("catalogo_productos").update(update_data).eq("id", producto_id).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Error actualizando producto")

        return {
            "success": True,
            "message": "Producto actualizado correctamente",
            "producto": response.data[0]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error actualizando producto: {str(e)}")

@router.delete("/productos/{producto_id}")
async def eliminar_producto(producto_id: int) -> Dict[str, Any]:
    """
    Elimina un producto del catálogo (marca como inactivo en lugar de eliminar físicamente)
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)

        # Verificar que el producto existe
        producto_actual = supabase.table("catalogo_productos").select("*").eq("id", producto_id).execute()
        
        if not producto_actual.data:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # Marcar como inactivo en lugar de eliminar
        response = supabase.table("catalogo_productos").update({
            "activo": False,
            "fecha_actualizacion": datetime.now().isoformat()
        }).eq("id", producto_id).execute()

        if not response.data:
            raise HTTPException(status_code=400, detail="Error desactivando producto")

        return {
            "success": True,
            "message": "Producto desactivado correctamente"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error desactivando producto: {str(e)}")

@router.get("/productos/stats/resumen")
async def get_resumen_catalogo() -> Dict[str, Any]:
    """
    Obtiene estadísticas del catálogo
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)

        # Obtener TODOS los productos usando paginación automática
        all_data = []
        page_size = 1000
        current_offset = 0
        
        while True:
            response = supabase.table("catalogo_productos").select("*").range(current_offset, current_offset + page_size - 1).execute()
            
            if not response.data:
                break
            
            all_data.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            current_offset += page_size

        if not all_data:
            return {
                "total_productos": 0,
                "productos_activos": 0,
                "productos_inactivos": 0,
                "lineas": [],
                "marcas": []
            }

        df = pd.DataFrame(all_data)

        # Estadísticas básicas
        total_productos = len(df)
        productos_activos = len(df[df.get('activo', True) == True]) if 'activo' in df.columns else 0
        productos_inactivos = total_productos - productos_activos

        # Líneas únicas (equivalente a categorías)
        lineas = []
        if 'linea' in df.columns:
            lineas_df = df[df['linea'].notna() & (df['linea'] != '')]['linea'].unique()
            lineas = sorted([str(l) for l in lineas_df])

        # Marcas únicas
        marcas = []
        if 'marca' in df.columns:
            marcas_df = df[df['marca'].notna() & (df['marca'] != '')]['marca'].unique()
            marcas = sorted([str(m) for m in marcas_df])

        return {
            "total_productos": total_productos,
            "productos_activos": productos_activos,
            "productos_inactivos": productos_inactivos,
            "lineas": lineas,
            "marcas": marcas
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")

@router.get("/exportar-csv")
async def exportar_catalogo_csv():
    """
    Exporta el catálogo completo a CSV con formato: Artículo, Bodega O., Descripción, Cantidad/Precio
    """
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Cargar todos los productos con paginación automática
        all_productos = []
        page_size = 1000
        current_offset = 0
        
        while True:
            response = supabase.table("catalogo_productos").select("*").range(current_offset, current_offset + page_size - 1).order("cod_ur", desc=False).execute()
            
            if not response.data:
                break
            
            all_productos.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            current_offset += page_size
        
        if not all_productos:
            raise HTTPException(status_code=404, detail="No hay productos para exportar")
        
        # Convertir a DataFrame
        df = pd.DataFrame(all_productos)
        
        # Crear CSV con el formato de las imágenes: Artículo, Bodega O., Descripción, Cantidad/Precio
        # Formato basado en las imágenes: código, "99 - Bodega (descripción)", descripción completa, precio
        datos_csv = []
        for _, row in df.iterrows():
            codigo = str(row.get('cod_ur', '') or row.get('referencia', ''))
            descripcion = str(row.get('descripcion', ''))
            precio = float(row.get('precio', 0)) if pd.notna(row.get('precio')) else 0
            
            # Formato "99 - Bodega (TIPO)" basado en la descripción
            # Extraer el tipo de producto de la descripción si es posible
            tipo_producto = descripcion.split()[0] if descripcion else ''
            bodega = f"99 - Bodega ({tipo_producto}" if tipo_producto else "99 - Bodega"
            
            datos_csv.append({
                'Artículo': codigo,
                'Bodega O.': bodega,
                'Descripción': descripcion,
                'Cantidad': f"{precio:.2f}"
            })
        
        df_csv = pd.DataFrame(datos_csv)
        
        # Convertir a CSV en memoria con encoding UTF-8-sig para Excel
        output = io.StringIO()
        df_csv.to_csv(output, index=False, encoding='utf-8-sig', sep=',')
        csv_content = output.getvalue()
        output.close()
        
        # Devolver como Response con tipo CSV
        return Response(
            content=csv_content.encode('utf-8-sig'),
            media_type="text/csv; charset=utf-8-sig",
            headers={
                "Content-Disposition": f"attachment; filename=catalogo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error exportando catálogo a CSV: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error exportando catálogo: {str(e)}")

import pandas as pd
from datetime import datetime
from supabase import Client
import streamlit as st
from typing import Dict, List, Any, Optional
import os

class CatalogManager:
    """Gestor del catálogo de productos"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table_name = "catalogo_productos"
    
    @st.cache_data(ttl=300)
    def cargar_catalogo(_self):
        """Carga el catálogo completo desde la base de datos"""
        try:
            # Cargar todos los registros usando paginación
            all_data = []
            page_size = 1000
            offset = 0
            
            while True:
                response = _self.supabase.table(_self.table_name).select(
                    "*", count="exact"
                ).eq("activo", True).range(offset, offset + page_size - 1).execute()
                
                if not response.data:
                    break
                
                all_data.extend(response.data)
                
                # Si obtuvimos menos registros que el tamaño de página, terminamos
                if len(response.data) < page_size:
                    break
                
                offset += page_size
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            # Asegurar que cod_ur esté en mayúsculas para consistencia
            if 'cod_ur' in df.columns:
                df['cod_ur'] = df['cod_ur'].astype(str).str.strip().str.upper()
            return df
            
        except Exception as e:
            error_msg = str(e)
            # Verificar si es error de tabla no encontrada
            if "Could not find the table" in error_msg or "PGRST205" in error_msg:
                st.warning(
                    "⚠️ **La tabla del catálogo no existe aún.**\n\n"
                    "📋 **Para solucionarlo:**\n"
                    "1. Ve a Supabase → SQL Editor\n"
                    "2. Ejecuta el script: `crear_tabla_catalogo.sql`\n"
                    "3. O haz clic en 'Actualizar Catálogo' para crearla automáticamente"
                )
            else:
                st.error(f"Error cargando catálogo: {error_msg}")
            return pd.DataFrame()
    
    def cargar_catalogo_completo(self):
        """Carga el catálogo completo incluyendo productos inactivos"""
        try:
            # Cargar todos los registros usando paginación
            all_data = []
            page_size = 1000
            offset = 0
            
            while True:
                response = self.supabase.table(self.table_name).select(
                    "*", count="exact"
                ).range(offset, offset + page_size - 1).execute()
                
                if not response.data:
                    break
                
                all_data.extend(response.data)
                
                # Si obtuvimos menos registros que el tamaño de página, terminamos
                if len(response.data) < page_size:
                    break
                
                offset += page_size
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            # Asegurar que cod_ur esté en mayúsculas para consistencia
            if 'cod_ur' in df.columns:
                df['cod_ur'] = df['cod_ur'].astype(str).str.strip().str.upper()
            return df
            
        except Exception as e:
            error_msg = str(e)
            # No mostrar error si es tabla no encontrada (ya se mostró antes)
            if "Could not find the table" not in error_msg and "PGRST205" not in error_msg:
                st.error(f"Error cargando catálogo completo: {error_msg}")
            return pd.DataFrame()
    
    def cargar_catalogo_desde_excel(self, archivo_path: str) -> Dict[str, Any]:
        """Carga el catálogo desde un archivo Excel y lo sincroniza con la base de datos"""
        try:
            # Verificar si la tabla existe y si ya tiene suficientes productos
            try:
                # Cargar catálogo completo para verificar cantidad
                catalogo_actual = self.cargar_catalogo_completo()
                # Si ya hay suficientes productos (>= 10), no cargar automáticamente
                if not catalogo_actual.empty and len(catalogo_actual) >= 10:
                    return {
                        "success": True,
                        "total_productos": len(catalogo_actual),
                        "productos_nuevos": 0,
                        "productos_actualizados": 0,
                        "productos_desactivados": 0,
                        "mensaje": f"El catálogo ya está actualizado en la base de datos con {len(catalogo_actual)} productos."
                    }
            except Exception as e:
                if "Could not find the table" in str(e) or "PGRST205" in str(e):
                    # La tabla no existe, mostrar instrucciones
                    return {
                        "error": "La tabla 'catalogo_productos' no existe en Supabase. Por favor, ejecuta el script SQL 'crear_tabla_catalogo.sql' en el SQL Editor de Supabase primero."
                    }
            # Leer Excel
            df = pd.read_excel(archivo_path)
            
            # Normalizar nombres de columnas
            df.columns = df.columns.str.strip()
            
            # Mapear columnas (case insensitive)
            columnas_mapeo = {
                'Cod_UR': 'cod_ur',
                'Referencia': 'referencia',
                'Equivalencia': 'equivalencia',
                'Descripcion': 'descripcion',
                'Marca': 'marca',
                'Linea': 'linea',
                'Precio': 'precio',
                'DetalleDescuento': 'detalle_descuento'
            }
            
            # Renombrar columnas
            for col_original, col_nuevo in columnas_mapeo.items():
                if col_original in df.columns:
                    df.rename(columns={col_original: col_nuevo}, inplace=True)
            
            # Validar columnas requeridas
            columnas_requeridas = ['cod_ur', 'referencia', 'descripcion', 'precio']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                return {
                    "error": f"El archivo debe contener las columnas: {', '.join(columnas_faltantes)}"
                }
            
            # Limpiar datos
            df = self._limpiar_datos_catalogo(df)
            
            # Debug: mostrar algunos códigos para verificar
            if not df.empty:
                st.info(f"📊 Procesando {len(df)} productos. Ejemplos de códigos: {df['cod_ur'].head(5).tolist()}")
            
            # Obtener catálogo actual de la BD
            catalogo_actual = self.cargar_catalogo_completo()
            
            # Determinar qué productos son nuevos, actualizados o desactivados
            resultado = self._sincronizar_catalogo(df, catalogo_actual)
            
            # Limpiar cache después de actualizar
            st.cache_data.clear()
            
            return resultado
            
        except Exception as e:
            return {
                "error": f"Error procesando archivo: {str(e)}"
            }
    
    def _limpiar_datos_catalogo(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpia y normaliza los datos del catálogo"""
        # Eliminar filas completamente vacías
        df = df.dropna(how='all')
        
        # Limpiar cod_ur y referencia (requeridos)
        df = df[df['cod_ur'].notna() & (df['cod_ur'] != '')]
        df = df[df['referencia'].notna() & (df['referencia'] != '')]
        
        # Convertir a string y limpiar espacios
        df['cod_ur'] = df['cod_ur'].astype(str).str.strip().str.upper()
        df['referencia'] = df['referencia'].astype(str).str.strip().str.upper()
        
        # Limpiar otros campos
        if 'equivalencia' in df.columns:
            df['equivalencia'] = df['equivalencia'].fillna('').astype(str).str.strip()
        
        if 'descripcion' in df.columns:
            df['descripcion'] = df['descripcion'].fillna('').astype(str).str.strip()
        
        if 'marca' in df.columns:
            df['marca'] = df['marca'].fillna('').astype(str).str.strip()
        
        if 'linea' in df.columns:
            df['linea'] = df['linea'].fillna('').astype(str).str.strip()
        
        # Asegurar que precio sea numérico
        if 'precio' in df.columns:
            df['precio'] = pd.to_numeric(df['precio'], errors='coerce').fillna(0)
        
        if 'detalle_descuento' in df.columns:
            df['detalle_descuento'] = df['detalle_descuento'].fillna('').astype(str)
        
        # Eliminar duplicados por cod_ur
        df = df.drop_duplicates(subset=['cod_ur'], keep='first')
        
        return df
    
    def _sincronizar_catalogo(self, df_nuevo: pd.DataFrame, df_actual: pd.DataFrame) -> Dict[str, Any]:
        """Sincroniza el catálogo nuevo con el actual"""
        productos_nuevos = []
        productos_actualizados = []
        productos_desactivados = []
        productos_reactivados = []
        
        # Crear sets de códigos
        codigos_nuevos = set(df_nuevo['cod_ur'].unique())
        codigos_actuales = set(df_actual['cod_ur'].unique()) if not df_actual.empty else set()
        
        # Productos nuevos (están en el nuevo pero no en el actual)
        productos_agregar = df_nuevo[~df_nuevo['cod_ur'].isin(codigos_actuales)]
        
        # Productos que ya existen (actualizar)
        productos_existentes = df_nuevo[df_nuevo['cod_ur'].isin(codigos_actuales)]
        
        # Productos desactivados (están en el actual pero no en el nuevo)
        productos_eliminar = df_actual[~df_actual['cod_ur'].isin(codigos_nuevos)] if not df_actual.empty else pd.DataFrame()
        
        # Insertar productos nuevos en lotes (más eficiente)
        if not productos_agregar.empty:
            try:
                # Preparar datos para inserción en lote
                datos_insercion = []
                for _, producto in productos_agregar.iterrows():
                    data = {
                        'cod_ur': producto['cod_ur'],
                        'referencia': producto['referencia'],
                        'equivalencia': producto.get('equivalencia', ''),
                        'descripcion': producto.get('descripcion', ''),
                        'marca': producto.get('marca', ''),
                        'linea': producto.get('linea', ''),
                        'precio': float(producto.get('precio', 0)),
                        'detalle_descuento': producto.get('detalle_descuento', ''),
                        'activo': True,
                        'fecha_creacion': datetime.now().isoformat(),
                        'fecha_actualizacion': datetime.now().isoformat()
                    }
                    datos_insercion.append(data)
                    productos_nuevos.append(producto['cod_ur'])
                
                # Insertar en lotes de 100 para evitar timeouts
                lote_size = 100
                for i in range(0, len(datos_insercion), lote_size):
                    lote = datos_insercion[i:i + lote_size]
                    try:
                        self.supabase.table(self.table_name).insert(lote).execute()
                    except Exception as e:
                        # Si falla el lote, intentar uno por uno
                        for item in lote:
                            try:
                                self.supabase.table(self.table_name).insert(item).execute()
                            except:
                                # Si falla por duplicado, intentar actualizar
                                try:
                                    cod_ur = item['cod_ur']
                                    producto_row = productos_agregar[productos_agregar['cod_ur'] == cod_ur].iloc[0]
                                    self._actualizar_producto(producto_row)
                                    if cod_ur in productos_nuevos:
                                        productos_nuevos.remove(cod_ur)
                                    productos_actualizados.append(cod_ur)
                                except:
                                    pass
            except Exception as e:
                # Fallback: insertar uno por uno si falla el lote
                for _, producto in productos_agregar.iterrows():
                    try:
                        data = {
                            'cod_ur': producto['cod_ur'],
                            'referencia': producto['referencia'],
                            'equivalencia': producto.get('equivalencia', ''),
                            'descripcion': producto.get('descripcion', ''),
                            'marca': producto.get('marca', ''),
                            'linea': producto.get('linea', ''),
                            'precio': float(producto.get('precio', 0)),
                            'detalle_descuento': producto.get('detalle_descuento', ''),
                            'activo': True,
                            'fecha_creacion': datetime.now().isoformat(),
                            'fecha_actualizacion': datetime.now().isoformat()
                        }
                        
                        self.supabase.table(self.table_name).insert(data).execute()
                        productos_nuevos.append(producto['cod_ur'])
                    except Exception as e:
                        # Si falla por duplicado, intentar actualizar
                        try:
                            self._actualizar_producto(producto)
                            productos_actualizados.append(producto['cod_ur'])
                        except:
                            pass
        
        # Actualizar productos existentes
        for _, producto in productos_existentes.iterrows():
            try:
                self._actualizar_producto(producto)
                productos_actualizados.append(producto['cod_ur'])
            except Exception as e:
                pass
        
        # Desactivar productos que ya no están en el nuevo catálogo
        for _, producto in productos_eliminar.iterrows():
            try:
                # Verificar si estaba activo antes
                estaba_activo = producto.get('activo', True)
                
                self.supabase.table(self.table_name).update({
                    'activo': False,
                    'fecha_actualizacion': datetime.now().isoformat()
                }).eq('cod_ur', producto['cod_ur']).execute()
                
                if estaba_activo:
                    productos_desactivados.append(producto['cod_ur'])
                else:
                    productos_reactivados.append(producto['cod_ur'])
                    
            except Exception as e:
                pass
        
        # Limpiar cache
        st.cache_data.clear()
        
        return {
            "success": True,
            "total_productos": len(df_nuevo),
            "productos_nuevos": len(productos_nuevos),
            "productos_actualizados": len(productos_actualizados),
            "productos_desactivados": len(productos_desactivados),
            "detalle_nuevos": productos_nuevos[:10],  # Primeros 10
            "detalle_actualizados": productos_actualizados[:10],
            "detalle_desactivados": productos_desactivados[:10]
        }
    
    def _actualizar_producto(self, producto: pd.Series):
        """Actualiza un producto existente"""
        data = {
            'referencia': producto['referencia'],
            'equivalencia': producto.get('equivalencia', ''),
            'descripcion': producto.get('descripcion', ''),
            'marca': producto.get('marca', ''),
            'linea': producto.get('linea', ''),
            'precio': float(producto.get('precio', 0)),
            'detalle_descuento': producto.get('detalle_descuento', ''),
            'activo': True,  # Reactivar si estaba desactivado
            'fecha_actualizacion': datetime.now().isoformat()
        }
        
        self.supabase.table(self.table_name).update(data).eq('cod_ur', producto['cod_ur']).execute()
    
    def buscar_productos(self, termino: str, filtros: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Busca productos en el catálogo"""
        df = self.cargar_catalogo()
        
        if df.empty:
            return df
        
        # Búsqueda por término
        if termino:
            termino_lower = termino.lower()
            mask = (
                df['cod_ur'].str.lower().str.contains(termino_lower, na=False) |
                df['referencia'].str.lower().str.contains(termino_lower, na=False) |
                df['descripcion'].str.lower().str.contains(termino_lower, na=False) |
                df['marca'].str.lower().str.contains(termino_lower, na=False)
            )
            df = df[mask]
        
        # Aplicar filtros
        if filtros:
            if 'marca' in filtros and filtros['marca']:
                df = df[df['marca'] == filtros['marca']]
            
            if 'linea' in filtros and filtros['linea']:
                df = df[df['linea'] == filtros['linea']]
            
            if 'precio_min' in filtros and filtros['precio_min']:
                df = df[df['precio'] >= filtros['precio_min']]
            
            if 'precio_max' in filtros and filtros['precio_max']:
                df = df[df['precio'] <= filtros['precio_max']]
        
        return df
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """Obtiene estadísticas del catálogo"""
        df = self.cargar_catalogo_completo()
        
        if df.empty:
            return {
                "total_productos": 0,
                "productos_activos": 0,
                "productos_inactivos": 0,
                "marcas": 0,
                "lineas": 0,
                "precio_promedio": 0,
                "precio_min": 0,
                "precio_max": 0
            }
        
        return {
            "total_productos": len(df),
            "productos_activos": len(df[df['activo'] == True]),
            "productos_inactivos": len(df[df['activo'] == False]),
            "marcas": df['marca'].nunique() if 'marca' in df.columns else 0,
            "lineas": df['linea'].nunique() if 'linea' in df.columns else 0,
            "precio_promedio": float(df['precio'].mean()) if 'precio' in df.columns else 0,
            "precio_min": float(df['precio'].min()) if 'precio' in df.columns else 0,
            "precio_max": float(df['precio'].max()) if 'precio' in df.columns else 0
        }


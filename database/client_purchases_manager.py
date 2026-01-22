import pandas as pd
from datetime import datetime, timedelta
from supabase import Client
import streamlit as st
from typing import Dict, List, Any, Optional
import os


class ClientPurchasesManager:
    """Gestor de compras de clientes y análisis"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.clientes_table = "clientes_b2b"
        self.compras_table = "compras_clientes"
    
    # ========================
    # GESTIÓN DE CLIENTES
    # ========================
    
    def registrar_cliente(self, datos_cliente: Dict[str, Any]) -> Dict[str, Any]:
        """Registra un nuevo cliente B2B"""
        try:
            data = {
                'nombre': datos_cliente['nombre'],
                'nit': datos_cliente['nit'],
                'cupo_total': float(datos_cliente.get('cupo_total', 0)),
                'cupo_utilizado': float(datos_cliente.get('cupo_utilizado', 0)),
                'plazo_pago': int(datos_cliente.get('plazo_pago', 30)),
                'ciudad': datos_cliente.get('ciudad', ''),
                'direccion': datos_cliente.get('direccion', ''),
                'telefono': datos_cliente.get('telefono', ''),
                'email': datos_cliente.get('email', ''),
                'vendedor': datos_cliente.get('vendedor', ''),
                'descuento_predeterminado': float(datos_cliente.get('descuento_predeterminado', 0)),
                'activo': True,
                'fecha_registro': datetime.now().isoformat(),
                'fecha_actualizacion': datetime.now().isoformat()
            }
            
            # Verificar si ya existe
            existing = self.supabase.table(self.clientes_table).select("id").eq("nit", datos_cliente['nit']).execute()
            
            if existing.data:
                # Actualizar
                self.supabase.table(self.clientes_table).update(data).eq("nit", datos_cliente['nit']).execute()
                return {"success": True, "mensaje": "Cliente actualizado", "cliente_id": existing.data[0]['id']}
            else:
                # Insertar
                result = self.supabase.table(self.clientes_table).insert(data).execute()
                return {"success": True, "mensaje": "Cliente registrado", "cliente_id": result.data[0]['id'] if result.data else None}
                
        except Exception as e:
            return {"error": str(e)}
    
    def obtener_cliente(self, nit: str) -> Optional[Dict[str, Any]]:
        """Obtiene datos de un cliente por NIT"""
        try:
            result = self.supabase.table(self.clientes_table).select("*").eq("nit", nit).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            return None
    
    def obtener_patron_descuentos_cliente(self, nit_cliente: str) -> Dict[str, Any]:
        """Obtiene el patrón de descuentos de un cliente desde sus facturas en comisiones"""
        try:
            # Obtener cliente
            cliente = self.obtener_cliente(nit_cliente)
            if not cliente:
                return {
                    'cliente_propio': False,
                    'descuento_pie_factura': False,
                    'descuento_adicional': 0.0,
                    'condicion_especial': False
                }
            
            # Buscar facturas del cliente en comisiones por nombre o NIT
            nombre_cliente = cliente.get('nombre', '')
            
            # Intentar buscar por nombre exacto
            facturas_response = self.supabase.table("comisiones").select(
                "cliente_propio, descuento_pie_factura, descuento_adicional, condicion_especial"
            ).eq("cliente", nombre_cliente).execute()
            
            if not facturas_response.data:
                # Si no hay por nombre, buscar por NIT en compras y luego en facturas relacionadas
                compras_response = self.supabase.table("compras_clientes").select(
                    "num_documento"
                ).eq("nit_cliente", nit_cliente).limit(10).execute()
                
                if compras_response.data:
                    documentos = [c['num_documento'] for c in compras_response.data]
                    # Buscar facturas que coincidan con estos documentos
                    facturas_response = self.supabase.table("comisiones").select(
                        "cliente_propio, descuento_pie_factura, descuento_adicional, condicion_especial"
                    ).in_("factura", documentos).execute()
            
            if not facturas_response.data:
                return {
                    'cliente_propio': False,
                    'descuento_pie_factura': False,
                    'descuento_adicional': 0.0,
                    'condicion_especial': False,
                    'num_facturas': 0
                }
            
            df_facturas = pd.DataFrame(facturas_response.data)
            
            # Calcular patrones
            cliente_propio = df_facturas['cliente_propio'].mode().iloc[0] if not df_facturas['cliente_propio'].mode().empty else False
            descuento_pie = df_facturas['descuento_pie_factura'].mode().iloc[0] if not df_facturas['descuento_pie_factura'].mode().empty else False
            descuento_adicional = float(df_facturas['descuento_adicional'].mean()) if 'descuento_adicional' in df_facturas.columns else 0.0
            condicion_especial = df_facturas['condicion_especial'].mode().iloc[0] if not df_facturas['condicion_especial'].mode().empty else False
            
            return {
                'cliente_propio': bool(cliente_propio),
                'descuento_pie_factura': bool(descuento_pie),
                'descuento_adicional': descuento_adicional,
                'condicion_especial': bool(condicion_especial),
                'num_facturas': len(df_facturas)
            }
            
        except Exception as e:
            return {
                'cliente_propio': False,
                'descuento_pie_factura': False,
                'descuento_adicional': 0.0,
                'condicion_especial': False,
                'error': str(e)
            }
    
    def listar_clientes(self) -> pd.DataFrame:
        """Lista todos los clientes"""
        try:
            result = self.supabase.table(self.clientes_table).select("*").eq("activo", True).execute()
            return pd.DataFrame(result.data) if result.data else pd.DataFrame()
        except Exception as e:
            return pd.DataFrame()
    
    # ========================
    # GESTIÓN DE COMPRAS
    # ========================
    
    def cargar_compras_desde_excel(self, archivo_path: str, nit_cliente: str) -> Dict[str, Any]:
        """Carga compras de un cliente desde archivo Excel (FE=compras, DV=devoluciones)"""
        try:
            # Leer Excel
            df = pd.read_excel(archivo_path)
            
            # Normalizar columnas
            df.columns = df.columns.str.strip()
            
            # Obtener cliente
            cliente = self.obtener_cliente(nit_cliente)
            if not cliente:
                return {"error": f"Cliente con NIT {nit_cliente} no encontrado. Regístralo primero."}
            
            cliente_id = cliente['id']
            
            # Separar compras (FE) y devoluciones (DV)
            df_compras = df[df['FUENTE'].astype(str).str.upper() == 'FE'].copy()
            df_devoluciones = df[df['FUENTE'].astype(str).str.upper() == 'DV'].copy()
            
            # Preparar datos para inserción
            compras_nuevas = 0
            compras_actualizadas = 0
            devoluciones_nuevas = 0
            devoluciones_actualizadas = 0
            
            # Procesar COMPRAS (FE)
            for _, row in df_compras.iterrows():
                try:
                    # Parsear fecha
                    fecha = row.get('FECHA', '')
                    if pd.notna(fecha):
                        if isinstance(fecha, str):
                            fecha = pd.to_datetime(fecha).isoformat()
                        else:
                            fecha = pd.to_datetime(fecha).isoformat()
                    else:
                        fecha = datetime.now().isoformat()
                    
                    data = {
                        'cliente_id': cliente_id,
                        'nit_cliente': nit_cliente,
                        'fuente': str(row.get('FUENTE', '')),
                        'num_documento': str(row.get('NUM_DCTO', '')),
                        'fecha': fecha,
                        'cod_articulo': str(row.get('COD_ARTICULO', '')),
                        'detalle': str(row.get('DETALLE', '')),
                        'cantidad': int(row.get('CANTIDAD', 0)) if pd.notna(row.get('CANTIDAD')) else 0,
                        'valor_unitario': float(row.get('valor_Unitario', 0)) if pd.notna(row.get('valor_Unitario')) else 0,
                        'descuento': float(row.get('dcto', 0)) if pd.notna(row.get('dcto')) else 0,
                        'total': float(row.get('Total', 0)) if pd.notna(row.get('Total')) else 0,
                        'familia': str(row.get('FAMILIA', '')),
                        'marca': str(row.get('Marca', '')),
                        'subgrupo': str(row.get('SUBGRUPO', '')),
                        'grupo': str(row.get('GRUPO', '')),
                        'es_devolucion': False,  # FE = compra
                        'fecha_carga': datetime.now().isoformat()
                    }
                    
                    # Verificar si ya existe esta compra
                    existing = self.supabase.table(self.compras_table).select("id").eq("nit_cliente", nit_cliente).eq("num_documento", data['num_documento']).eq("cod_articulo", data['cod_articulo']).execute()
                    
                    if existing.data:
                        # Actualizar
                        self.supabase.table(self.compras_table).update(data).eq("id", existing.data[0]['id']).execute()
                        compras_actualizadas += 1
                    else:
                        # Insertar
                        self.supabase.table(self.compras_table).insert(data).execute()
                        compras_nuevas += 1
                        
                except Exception as e:
                    continue
            
            # Procesar DEVOLUCIONES (DV)
            for _, row in df_devoluciones.iterrows():
                try:
                    # Parsear fecha
                    fecha = row.get('FECHA', '')
                    if pd.notna(fecha):
                        if isinstance(fecha, str):
                            fecha = pd.to_datetime(fecha).isoformat()
                        else:
                            fecha = pd.to_datetime(fecha).isoformat()
                    else:
                        fecha = datetime.now().isoformat()
                    
                    # Para devoluciones, el total es negativo
                    total_devolucion = abs(float(row.get('Total', 0))) if pd.notna(row.get('Total')) else 0
                    
                    data = {
                        'cliente_id': cliente_id,
                        'nit_cliente': nit_cliente,
                        'fuente': str(row.get('FUENTE', '')),
                        'num_documento': str(row.get('NUM_DCTO', '')),
                        'fecha': fecha,
                        'cod_articulo': str(row.get('COD_ARTICULO', '')),
                        'detalle': str(row.get('DETALLE', '')),
                        'cantidad': int(row.get('CANTIDAD', 0)) if pd.notna(row.get('CANTIDAD')) else 0,
                        'valor_unitario': float(row.get('valor_Unitario', 0)) if pd.notna(row.get('valor_Unitario')) else 0,
                        'descuento': float(row.get('dcto', 0)) if pd.notna(row.get('dcto')) else 0,
                        'total': -total_devolucion,  # Negativo para devoluciones
                        'familia': str(row.get('FAMILIA', '')),
                        'marca': str(row.get('Marca', '')),
                        'subgrupo': str(row.get('SUBGRUPO', '')),
                        'grupo': str(row.get('GRUPO', '')),
                        'es_devolucion': True,  # DV = devolución
                        'fecha_carga': datetime.now().isoformat()
                    }
                    
                    # Verificar si ya existe esta devolución
                    existing = self.supabase.table(self.compras_table).select("id").eq("nit_cliente", nit_cliente).eq("num_documento", data['num_documento']).eq("cod_articulo", data['cod_articulo']).eq("es_devolucion", True).execute()
                    
                    if existing.data:
                        # Actualizar
                        self.supabase.table(self.compras_table).update(data).eq("id", existing.data[0]['id']).execute()
                        devoluciones_actualizadas += 1
                    else:
                        # Insertar
                        self.supabase.table(self.compras_table).insert(data).execute()
                        devoluciones_nuevas += 1
                        
                except Exception as e:
                    continue
            
            # Limpiar cache
            st.cache_data.clear()
            
            return {
                "success": True,
                "total_registros": len(df),
                "compras_nuevas": compras_nuevas,
                "compras_actualizadas": compras_actualizadas,
                "devoluciones_nuevas": devoluciones_nuevas,
                "devoluciones_actualizadas": devoluciones_actualizadas,
                "total_compras": len(df_compras),
                "total_devoluciones": len(df_devoluciones),
                "cliente": cliente['nombre']
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def obtener_compras_cliente(self, nit_cliente: str, incluir_devoluciones: bool = False) -> pd.DataFrame:
        """Obtiene todas las compras de un cliente (excluye devoluciones por defecto)"""
        try:
            # Obtener todos los registros primero
            result = self.supabase.table(self.compras_table).select("*").eq("nit_cliente", nit_cliente).execute()
            df = pd.DataFrame(result.data) if result.data else pd.DataFrame()
            
            if df.empty:
                return df
            
            # Si no incluir devoluciones, filtrar
            if not incluir_devoluciones:
                # Filtrar por es_devolucion si existe, sino por fuente
                if 'es_devolucion' in df.columns:
                    df = df[df['es_devolucion'] == False].copy()
                elif 'fuente' in df.columns:
                    df = df[df['fuente'].astype(str).str.upper() != 'DV'].copy()
            
            return df
        except Exception as e:
            return pd.DataFrame()
    
    def eliminar_compras(self, ids_compras: List[int]) -> Dict[str, Any]:
        """Elimina compras por sus IDs"""
        try:
            eliminadas = 0
            errores = 0
            
            for compra_id in ids_compras:
                try:
                    self.supabase.table(self.compras_table).delete().eq("id", compra_id).execute()
                    eliminadas += 1
                except Exception as e:
                    errores += 1
                    continue
            
            st.cache_data.clear()
            
            return {
                "success": True,
                "eliminadas": eliminadas,
                "errores": errores
            }
        except Exception as e:
            return {"error": str(e)}
    
    def eliminar_todas_compras_cliente(self, nit_cliente: str) -> Dict[str, Any]:
        """Elimina TODAS las compras (y devoluciones) de un cliente"""
        try:
            # Obtener todas las compras del cliente
            result = self.supabase.table(self.compras_table).select("id").eq("nit_cliente", nit_cliente).execute()
            
            if not result.data:
                return {
                    "success": True,
                    "eliminadas": 0,
                    "mensaje": "No hay compras para eliminar"
                }
            
            total_registros = len(result.data)
            
            # Eliminar todas las compras
            self.supabase.table(self.compras_table).delete().eq("nit_cliente", nit_cliente).execute()
            
            st.cache_data.clear()
            
            return {
                "success": True,
                "eliminadas": total_registros,
                "mensaje": f"Se eliminaron {total_registros} registros (compras y devoluciones) del cliente {nit_cliente}"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def obtener_resumen_compras_cliente(self, nit_cliente: str) -> Dict[str, Any]:
        """Obtiene un resumen detallado de las compras de un cliente"""
        try:
            # Obtener todas las compras (incluyendo devoluciones)
            df = self.obtener_compras_cliente(nit_cliente, incluir_devoluciones=True)
            
            if df.empty:
                return {"error": "No hay compras registradas para este cliente"}
            
            # Convertir fechas
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Separar compras y devoluciones
            df_compras = df[df.get('es_devolucion', False) == False].copy()
            df_devoluciones = df[df.get('es_devolucion', False) == True].copy()
            
            # Agrupar por documento
            compras_por_doc = df_compras.groupby('num_documento').agg({
                'fecha': 'first',
                'total': 'sum',
                'cantidad': 'sum',
                'cod_articulo': 'count'
            }).reset_index()
            
            return {
                "total_registros": len(df),
                "total_compras": len(df_compras),
                "total_devoluciones": len(df_devoluciones),
                "documentos_unicos": compras_por_doc['num_documento'].nunique(),
                "fecha_primera_compra": df_compras['fecha'].min().strftime("%Y-%m-%d") if not df_compras.empty else None,
                "fecha_ultima_compra": df_compras['fecha'].max().strftime("%Y-%m-%d") if not df_compras.empty else None,
                "total_valor_compras": df_compras['total'].sum(),
                "total_valor_devoluciones": abs(df_devoluciones['total'].sum()) if not df_devoluciones.empty else 0,
                "compras_por_documento": compras_por_doc.to_dict('records')
            }
        except Exception as e:
            return {"error": str(e)}
    
    # ========================
    # ANÁLISIS DE COMPRAS
    # ========================
    
    def analizar_cliente(self, nit_cliente: str) -> Dict[str, Any]:
        """Análisis completo de un cliente"""
        try:
            # Obtener TODAS las compras incluyendo devoluciones directamente desde la BD
            try:
                result = self.supabase.table(self.compras_table).select("*").eq("nit_cliente", nit_cliente).execute()
                df = pd.DataFrame(result.data) if result.data else pd.DataFrame()
            except:
                df = self.obtener_compras_cliente(nit_cliente, incluir_devoluciones=True)
            
            cliente = self.obtener_cliente(nit_cliente)
            
            if df.empty:
                return {"error": "No hay compras registradas para este cliente"}
            
            # Convertir fecha
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Separar compras y devoluciones
            # Usar fuente como fuente principal de verdad (más confiable)
            if 'fuente' in df.columns:
                # Filtrar por fuente (FE vs DV)
                df_compras = df[df['fuente'].astype(str).str.upper() == 'FE'].copy()
                df_devoluciones = df[df['fuente'].astype(str).str.upper() == 'DV'].copy()
            elif 'es_devolucion' in df.columns:
                # Fallback: usar es_devolucion si no hay fuente
                df_compras = df[(df['es_devolucion'] == False) | (df['es_devolucion'].isna())].copy()
                df_devoluciones = df[df['es_devolucion'] == True].copy()
            else:
                # Si no hay ninguna, asumir que todo son compras
                df_compras = df.copy()
                df_devoluciones = pd.DataFrame()
            
            # Debug: mostrar conteos
            # st.write(f"DEBUG: Total registros: {len(df)}, Compras: {len(df_compras)}, Devoluciones: {len(df_devoluciones)}")
            
            # Análisis general (solo compras, sin devoluciones)
            total_compras = df_compras['total'].sum() if not df_compras.empty else 0
            # Para devoluciones, el total ya es negativo, así que usamos abs() para mostrar el valor positivo
            total_devoluciones = abs(df_devoluciones['total'].sum()) if not df_devoluciones.empty else 0
            neto_compras = total_compras - total_devoluciones
            num_transacciones = df_compras['num_documento'].nunique() if not df_compras.empty else 0
            productos_diferentes = df_compras['cod_articulo'].nunique() if not df_compras.empty else 0
            
            # Análisis de marcas (solo compras)
            marcas_preferidas = df_compras.groupby('marca').agg({
                'total': 'sum',
                'cantidad': 'sum',
                'cod_articulo': 'count'
            }).rename(columns={'cod_articulo': 'transacciones'}).sort_values('total', ascending=False) if not df_compras.empty else pd.DataFrame()
            
            # Análisis de grupos/categorías (solo compras)
            grupos_preferidos = df_compras.groupby('grupo').agg({
                'total': 'sum',
                'cantidad': 'sum'
            }).sort_values('total', ascending=False) if not df_compras.empty else pd.DataFrame()
            
            # Análisis de subgrupos (solo compras)
            subgrupos_preferidos = df_compras.groupby('subgrupo').agg({
                'total': 'sum',
                'cantidad': 'sum'
            }).sort_values('total', ascending=False) if not df_compras.empty else pd.DataFrame()
            
            # Productos más comprados (solo compras)
            productos_top = df_compras.groupby(['cod_articulo', 'detalle', 'marca']).agg({
                'cantidad': 'sum',
                'total': 'sum',
                'num_documento': 'count'
            }).rename(columns={'num_documento': 'veces_comprado'}).sort_values('cantidad', ascending=False).head(20) if not df_compras.empty else pd.DataFrame()
            
            # Frecuencia de compra (solo compras)
            fechas_compra = df_compras.groupby('num_documento')['fecha'].first().sort_values() if not df_compras.empty else pd.Series()
            if len(fechas_compra) > 1:
                dias_entre_compras = fechas_compra.diff().dt.days.dropna()
                frecuencia_promedio = dias_entre_compras.mean()
            else:
                frecuencia_promedio = 0
            
            # Última compra
            ultima_compra = df['fecha'].max()
            dias_sin_comprar = (datetime.now() - ultima_compra).days
            
            # Ticket promedio
            ticket_promedio = df.groupby('num_documento')['total'].sum().mean()
            
            # Descuento promedio
            descuento_promedio = df['descuento'].mean()
            
            return {
                "cliente": cliente,
                "resumen": {
                    "total_compras": total_compras,
                    "total_devoluciones": total_devoluciones,
                    "neto_compras": neto_compras,
                    "num_transacciones": num_transacciones,
                    "productos_diferentes": productos_diferentes,
                    "ticket_promedio": ticket_promedio,
                    "frecuencia_dias": frecuencia_promedio,
                    "dias_sin_comprar": dias_sin_comprar,
                    "ultima_compra": ultima_compra.strftime("%Y-%m-%d") if pd.notna(ultima_compra) else None,
                    "descuento_promedio": descuento_promedio,
                    "num_devoluciones": len(df_devoluciones)
                },
                "marcas_preferidas": marcas_preferidas.reset_index().to_dict('records'),
                "grupos_preferidos": grupos_preferidos.reset_index().to_dict('records'),
                "subgrupos_preferidos": subgrupos_preferidos.reset_index().to_dict('records'),
                "productos_top": productos_top.reset_index().to_dict('records')
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ========================
    # RECOMENDACIONES
    # ========================
    
    def generar_recomendaciones(self, nit_cliente: str, catalog_manager) -> Dict[str, Any]:
        """Genera recomendaciones de productos para un cliente"""
        try:
            # Obtener análisis del cliente
            analisis = self.analizar_cliente(nit_cliente)
            if "error" in analisis:
                return analisis
            
            # Obtener catálogo completo
            catalogo = catalog_manager.cargar_catalogo()
            if catalogo.empty:
                return {"error": "No hay catálogo disponible"}
            
            df_compras = self.obtener_compras_cliente(nit_cliente)
            
            recomendaciones = {
                "por_marca": [],
                "por_categoria": [],
                "complementarios": [],
                "recompra": []
            }
            
            # 1. Recomendaciones por marca preferida
            marcas_cliente = [m['marca'] for m in analisis['marcas_preferidas'][:3]]
            productos_comprados = set(df_compras['cod_articulo'].unique())
            
            for marca in marcas_cliente:
                productos_marca = catalogo[
                    (catalogo['marca'].str.upper() == marca.upper()) & 
                    (~catalogo['cod_ur'].isin(productos_comprados))
                ].head(5)
                
                for _, prod in productos_marca.iterrows():
                    recomendaciones['por_marca'].append({
                        'cod_ur': prod['cod_ur'],
                        'referencia': prod.get('referencia', ''),
                        'descripcion': prod.get('descripcion', ''),
                        'marca': prod.get('marca', ''),
                        'precio': prod.get('precio', 0),
                        'razon': f"Compra frecuentemente marca {marca}"
                    })
            
            # 2. Recomendaciones por categoría/línea
            lineas_cliente = [g['grupo'] for g in analisis['grupos_preferidos'][:3]]
            
            for linea in lineas_cliente:
                # Buscar en catálogo por línea similar
                productos_linea = catalogo[
                    (catalogo['linea'].str.upper().str.contains(linea.upper().split()[0], na=False)) &
                    (~catalogo['cod_ur'].isin(productos_comprados))
                ].head(5)
                
                for _, prod in productos_linea.iterrows():
                    if prod['cod_ur'] not in [r['cod_ur'] for r in recomendaciones['por_categoria']]:
                        recomendaciones['por_categoria'].append({
                            'cod_ur': prod['cod_ur'],
                            'referencia': prod.get('referencia', ''),
                            'descripcion': prod.get('descripcion', ''),
                            'marca': prod.get('marca', ''),
                            'precio': prod.get('precio', 0),
                            'razon': f"Compra productos de {linea}"
                        })
            
            # 3. Productos para recompra (comprados hace tiempo)
            df_compras['fecha'] = pd.to_datetime(df_compras['fecha'])
            hace_90_dias = datetime.now() - timedelta(days=90)
            
            productos_antiguos = df_compras[df_compras['fecha'] < hace_90_dias].groupby('cod_articulo').agg({
                'cantidad': 'sum',
                'detalle': 'first',
                'marca': 'first',
                'fecha': 'max'
            }).sort_values('cantidad', ascending=False).head(10)
            
            for cod, row in productos_antiguos.iterrows():
                dias_desde_compra = (datetime.now() - row['fecha']).days
                recomendaciones['recompra'].append({
                    'cod_articulo': cod,
                    'detalle': row['detalle'],
                    'marca': row['marca'],
                    'cantidad_historica': row['cantidad'],
                    'dias_sin_comprar': dias_desde_compra,
                    'razon': f"No ha comprado en {dias_desde_compra} días"
                })
            
            return {
                "cliente": analisis['cliente']['nombre'],
                "recomendaciones": recomendaciones,
                "total_recomendaciones": (
                    len(recomendaciones['por_marca']) +
                    len(recomendaciones['por_categoria']) +
                    len(recomendaciones['recompra'])
                )
            }
            
        except Exception as e:
            return {"error": str(e)}

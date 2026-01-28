import pandas as pd
from datetime import datetime, date, timedelta
from supabase import Client
import streamlit as st
from typing import Optional, Dict, List, Any

class DatabaseManager:
    """Gestor centralizado de todas las operaciones de base de datos"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self._columnas_cache = None

    # ========================
    # OPERACIONES DE COMISIONES
    # ========================
    
    @st.cache_data(ttl=300)
    def cargar_datos(_self):
        """Carga datos de la tabla comisiones con cache"""
        return _self._cargar_datos_raw()

    def _cargar_datos_raw(self):
        """Carga datos sin cache - método interno"""
        try:
            response = self.supabase.table("comisiones").select("*").execute()
            if not response.data:
                return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            # Procesar datos
            df = self._procesar_datos_comisiones(df)
            return df
            
        except Exception as e:
            st.error(f"Error cargando datos: {str(e)}")
            return pd.DataFrame()

    def _procesar_datos_comisiones(self, df: pd.DataFrame) -> pd.DataFrame:
        """Procesa y limpia los datos de comisiones"""
        if df.empty:
            return df
            
        # Conversión de tipos numéricos
        columnas_numericas_str = ['valor_base', 'valor_neto', 'iva', 'base_comision', 'comision_ajustada', 'valor_descuento_pesos']
        for col in columnas_numericas_str:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: 0 if x in [None, "NULL", "null", ""] else float(x) if str(x).replace('.','').replace('-','').isdigit() else 0)

        columnas_numericas_existentes = ['valor', 'porcentaje', 'comision', 'porcentaje_descuento', 'descuento_adicional', 'valor_devuelto']
        for col in columnas_numericas_existentes:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Calcular campos derivados
        self._calcular_campos_derivados(df)
        
        # Convertir fechas
        self._procesar_fechas(df)
        
        # Crear columnas derivadas
        df['mes_factura'] = df['fecha_factura'].dt.to_period('M').astype(str)
        self._calcular_dias_vencimiento(df)
        
        # Normalizar identificadores de factura
        self._normalizar_facturas(df)
        
        # Asegurar tipos de columnas
        self._asegurar_tipos_columnas(df)
        
        return df

    def _calcular_campos_derivados(self, df: pd.DataFrame):
        """Calcula campos derivados como valor_neto, iva, base_comision y valida consistencia"""
        if df.empty:
            return
            
        # Calcular o corregir valor_neto si está vacío o inconsistente
        if 'valor' in df.columns and 'valor_neto' in df.columns:
            # Restar flete del valor total antes de calcular valor_neto
            if 'valor_flete' in df.columns:
                valor_sin_flete = df['valor'] - df['valor_flete'].fillna(0)
            else:
                valor_sin_flete = df['valor']
            
            # Si valor_neto es 0 o está vacío, calcularlo del valor total
            mask_valor_neto_vacio = (df['valor_neto'].fillna(0) == 0) & (valor_sin_flete > 0)
            df.loc[mask_valor_neto_vacio, 'valor_neto'] = valor_sin_flete[mask_valor_neto_vacio] / 1.19
            
            # Validar y corregir consistencia: valor = valor_neto + iva + flete
            if 'iva' in df.columns:
                if 'valor_flete' in df.columns:
                    valor_calculado = df['valor_neto'] + df['iva'].fillna(0) + df['valor_flete'].fillna(0)
                else:
                    valor_calculado = df['valor_neto'] + df['iva'].fillna(0)
                
                # Si hay diferencia significativa (más de 1 peso), corregir
                diferencia = abs(df['valor'] - valor_calculado)
                mask_inconsistente = diferencia > 1
                
                if mask_inconsistente.any():
                    # Recalcular valor_neto e IVA para hacerlos consistentes
                    if 'valor_flete' in df.columns:
                        valor_para_calcular = df.loc[mask_inconsistente, 'valor'] - df.loc[mask_inconsistente, 'valor_flete'].fillna(0)
                    else:
                        valor_para_calcular = df.loc[mask_inconsistente, 'valor']
                    
                    df.loc[mask_inconsistente, 'valor_neto'] = valor_para_calcular / 1.19
                    df.loc[mask_inconsistente, 'iva'] = valor_para_calcular - df.loc[mask_inconsistente, 'valor_neto']
            
        # Calcular IVA si está vacío o inconsistente
        if 'iva' in df.columns and 'valor_neto' in df.columns:
            mask_iva_vacio = df['iva'].fillna(0) == 0
            if mask_iva_vacio.any():
                df.loc[mask_iva_vacio, 'iva'] = df.loc[mask_iva_vacio, 'valor_neto'] * 0.19
            
        # Siempre recalcular base_comision para asegurar consistencia
        if 'base_comision' in df.columns and 'valor_neto' in df.columns:
            df['base_comision'] = df.apply(lambda row:
                row['valor_neto'] if row.get('descuento_pie_factura', False)
                else row['valor_neto'] * 0.85, axis=1)

    def _procesar_fechas(self, df: pd.DataFrame):
        """Procesa todas las columnas de fecha"""
        columnas_fecha = ['fecha_factura', 'fecha_pago_est', 'fecha_pago_max', 'fecha_pago_real', 'created_at', 'updated_at']
        for col in columnas_fecha:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

    def _calcular_dias_vencimiento(self, df: pd.DataFrame):
        """Calcula días de vencimiento solo para facturas NO PAGADAS"""
        hoy = pd.Timestamp.now()
        df['dias_vencimiento'] = df.apply(lambda row:
            (row['fecha_pago_max'] - hoy).days if not row.get('pagado', False) and pd.notna(row['fecha_pago_max'])
            else None, axis=1)

    def _normalizar_facturas(self, df: pd.DataFrame):
        """Genera columnas auxiliares para identificar facturas únicas"""
        if 'factura' not in df.columns:
            df['factura_base'] = None
            return
        
        facturas = df['factura'].astype(str).str.strip().fillna("")
        # Reemplazar sufijos tipo -1, -2 manteniendo el número base
        factura_base = facturas.str.replace(r"-\d+$", "", regex=True)
        
        # Cuando el campo queda vacío, conservar el valor original
        factura_base = factura_base.where(factura_base != "", facturas)
        
        df['factura'] = facturas.replace("", pd.NA)
        df['factura_base'] = factura_base.replace("", pd.NA)

    def obtener_clientes_frecuentes(self) -> List[Dict[str, Any]]:
        """Obtiene lista de clientes ordenados por frecuencia de compra con sus configuraciones típicas"""
        df = self.cargar_datos()
        
        if df.empty:
            return []
        
        # Filtrar solo clientes con al menos una factura
        df_clientes = df[df['cliente'].notna() & (df['cliente'] != '')]
        
        if df_clientes.empty:
            return []
        
        # Agrupar por cliente y calcular estadísticas
        clientes_stats = df_clientes.groupby('cliente').agg({
            'id': 'count',  # Número de facturas
            'valor': 'sum',  # Valor total
            'cliente_propio': lambda x: self._calcular_valor_mas_comun(x, False),  # Valor más común
            'descuento_pie_factura': lambda x: self._calcular_valor_mas_comun(x, False),
            'descuento_adicional': lambda x: x.mean() if len(x) > 0 else 0.0,  # Promedio de descuentos
            'condicion_especial': lambda x: self._calcular_valor_mas_comun(x, False),
            'fecha_factura': 'max'  # Última compra
        }).reset_index()
        
        # Renombrar columnas
        clientes_stats.columns = ['cliente', 'num_facturas', 'valor_total', 'cliente_propio_usual', 
                                  'descuento_pie_usual', 'descuento_adicional_promedio', 
                                  'condicion_especial_usual', 'ultima_compra']
        
        # Filtrar clientes con al menos 2 facturas para tener datos más confiables
        clientes_stats = clientes_stats[clientes_stats['num_facturas'] >= 2]
        
        # Ordenar por número de facturas (más frecuentes primero)
        clientes_stats = clientes_stats.sort_values('num_facturas', ascending=False)
        
        # Convertir a lista de diccionarios
        return clientes_stats.to_dict('records')
    
    def crear_tabla_prospectos(self):
        """Crea la tabla de clientes prospectos si no existe"""
        try:
            # Definir la estructura de la tabla de prospectos
            tabla_prospectos = {
                "id": "bigserial PRIMARY KEY",
                "nombre": "varchar(255) NOT NULL",
                "empresa": "varchar(255)",
                "telefono": "varchar(20)",
                "email": "varchar(255)",
                "ciudad": "varchar(100)",
                "tipo_negocio": "varchar(100)",  # Almacén, Serviteca, Concesionario, etc.
                "origen": "varchar(100)",  # Referido, web, llamada, etc.
                "estado": "varchar(50) DEFAULT 'Nuevo'",  # Nuevo, En seguimiento, Calificado, Convertido, Perdido
                "prioridad": "varchar(20) DEFAULT 'Media'",  # Alta, Media, Baja
                "notas": "text",
                "fecha_creacion": "timestamp DEFAULT NOW()",
                "ultimo_contacto": "timestamp",
                "proximo_contacto": "timestamp",
                "tipo_proximo_contacto": "varchar(50)",
                "tipo_ultimo_contacto": "varchar(50)",
                "created_at": "timestamp DEFAULT NOW()",
                "updated_at": "timestamp DEFAULT NOW()"
            }
            
            # Crear tabla usando Supabase
            for columna, tipo in tabla_prospectos.items():
                try:
                    # Esta es una operación de creación de tabla que se hace manualmente en Supabase
                    # Por ahora solo registramos que necesitamos esta tabla
                    pass
                except Exception as e:
                    print(f"Error creando tabla prospectos: {e}")
            
            return True
            
        except Exception as e:
            print(f"Error en crear_tabla_prospectos: {e}")
            return False
    
    def cargar_prospectos(self) -> pd.DataFrame:
        """Carga todos los clientes prospectos de la base de datos"""
        try:
            result = self.supabase.table('prospectos').select('*').execute()
            df = pd.DataFrame(result.data) if result.data else pd.DataFrame()
            return df
        except Exception as e:
            print(f"Error cargando prospectos: {e}")
            return pd.DataFrame()
    
    def agregar_prospecto(self, datos_prospecto: Dict[str, Any]) -> bool:
        """Agrega un nuevo cliente prospecto"""
        try:
            result = self.supabase.table('prospectos').insert(datos_prospecto).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error agregando prospecto: {e}")
            return False
    
    def actualizar_prospecto(self, id_prospecto: int, datos_actualizacion: Dict[str, Any]) -> bool:
        """Actualiza un cliente prospecto existente"""
        try:
            datos_actualizacion['updated_at'] = datetime.now().isoformat()
            result = self.supabase.table('prospectos').update(datos_actualizacion).eq('id', id_prospecto).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error actualizando prospecto: {e}")
            return False
    
    def eliminar_prospecto(self, id_prospecto: int) -> bool:
        """Elimina un cliente prospecto"""
        try:
            result = self.supabase.table('prospectos').delete().eq('id', id_prospecto).execute()
            return True
        except Exception as e:
            print(f"Error eliminando prospecto: {e}")
            return False
    
    def _calcular_valor_mas_comun(self, series, default_value=False):
        """Calcula el valor más común en una serie, con manejo de errores"""
        try:
            # Filtrar valores no nulos
            clean_series = series.dropna()
            if len(clean_series) == 0:
                return default_value
            
            # Calcular moda
            mode_values = clean_series.mode()
            if len(mode_values) > 0:
                return bool(mode_values[0])
            else:
                return default_value
        except Exception:
            return default_value
    
    def obtener_lista_clientes(self) -> List[str]:
        """Obtiene lista única de todos los clientes ordenados alfabéticamente"""
        df = self.cargar_datos()
        
        if df.empty:
            return []
        
        # Obtener clientes únicos y ordenarlos
        clientes = df['cliente'].dropna().unique().tolist()
        clientes_ordenados = sorted([c for c in clientes if c and str(c).strip()])
        
        return clientes_ordenados
    
    def obtener_patron_cliente(self, nombre_cliente: str) -> Dict[str, Any]:
        """Obtiene el patrón de configuración de un cliente basado en su historial"""
        df = self.cargar_datos()
        
        if df.empty or not nombre_cliente:
            return {
                'existe': False,
                'cliente_propio': False,
                'descuento_pie_factura': False,
                'descuento_adicional': 0.0,
                'condicion_especial': False,
                'num_compras': 0
            }
        
        # Filtrar facturas del cliente
        df_cliente = df[df['cliente'] == nombre_cliente]
        
        if df_cliente.empty:
            return {
                'existe': False,
                'cliente_propio': False,
                'descuento_pie_factura': False,
                'descuento_adicional': 0.0,
                'condicion_especial': False,
                'num_compras': 0
            }
        
        # Calcular patrones
        return {
            'existe': True,
            'cliente_propio': self._calcular_valor_mas_comun(df_cliente['cliente_propio'], False),
            'descuento_pie_factura': self._calcular_valor_mas_comun(df_cliente['descuento_pie_factura'], False),
            'descuento_adicional': float(df_cliente['descuento_adicional'].mean()) if 'descuento_adicional' in df_cliente.columns else 0.0,
            'condicion_especial': self._calcular_valor_mas_comun(df_cliente['condicion_especial'], False),
            'num_compras': len(df_cliente),
            'ultima_compra': df_cliente['fecha_factura'].max() if 'fecha_factura' in df_cliente.columns else None,
            'valor_promedio': float(df_cliente['valor'].mean()) if 'valor' in df_cliente.columns else 0.0
        }
    
    def _asegurar_tipos_columnas(self, df: pd.DataFrame):
        """Asegura tipos correctos para columnas boolean y string"""
        columnas_boolean = ['pagado', 'condicion_especial', 'cliente_propio', 'descuento_pie_factura', 'comision_perdida', 'descuentos_multiples', 'cliente_nuevo']
        for col in columnas_boolean:
            if col in df.columns:
                df[col] = df[col].fillna(False).astype(bool)

        columnas_string = ['pedido', 'cliente', 'factura', 'comprobante_url', 'razon_perdida', 'metodo_pago']
        for col in columnas_string:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str)

    def insertar_venta(self, data: Dict[str, Any]) -> bool:
        """Inserta una nueva venta"""
        try:
            # Verificar y filtrar campos válidos
            columnas_validas = self._obtener_columnas_tabla()
            data_filtrada = {k: v for k, v in data.items() if k in columnas_validas}
            
            data_filtrada["created_at"] = datetime.now().isoformat()
            data_filtrada["updated_at"] = datetime.now().isoformat()
            
            result = self.supabase.table("comisiones").insert(data_filtrada).execute()
            
            if result.data:
                # Limpiar cache si streamlit está disponible
                try:
                    import streamlit as st
                    st.cache_data.clear()
                except:
                    pass  # No es un problema si streamlit no está disponible
                return True
            return False
            
        except Exception as e:
            # Log error sin depender de streamlit
            print(f"Error insertando venta: {e}")
            return False

    def actualizar_factura(self, factura_id: int, updates: Dict[str, Any]) -> bool:
        """Actualiza una factura con detección automática de columnas MEJORADA"""
        try:
            if not factura_id or factura_id == 0:
                st.error("ID de factura inválido")
                return False

            factura_id = int(factura_id)
            
            # Verificar existencia
            check_response = self.supabase.table("comisiones").select("id").eq("id", factura_id).execute()
            if not check_response.data:
                st.error("Factura no encontrada")
                return False

            # Obtener columnas existentes
            columnas_existentes = self._obtener_columnas_tabla()
            
            # Filtrar y validar updates
            safe_updates = self._validar_updates(updates, columnas_existentes)
            
            if not safe_updates:
                st.warning("No hay campos válidos para actualizar")
                return False

            # Siempre agregar updated_at si existe
            if 'updated_at' in columnas_existentes:
                safe_updates["updated_at"] = datetime.now().isoformat()

            # Ejecutar actualización
            result = self.supabase.table("comisiones").update(safe_updates).eq("id", factura_id).execute()
            
            if result.data:
                st.cache_data.clear()
                return True
            else:
                st.error("No se pudo actualizar la factura")
                return False

        except Exception as e:
            st.error(f"Error actualizando factura: {e}")
            return False

    def _obtener_columnas_tabla(self) -> set:
        """Obtiene las columnas existentes en la tabla comisiones CON CACHE"""
        if self._columnas_cache is not None:
            return self._columnas_cache
            
        try:
            # Hacer una consulta pequeña para obtener estructura
            sample_query = self.supabase.table("comisiones").select("*").limit(1).execute()
            if sample_query.data:
                self._columnas_cache = set(sample_query.data[0].keys())
            else:
                # Si no hay datos, crear una entrada dummy para obtener columnas
                try:
                    test_insert = {
                        'pedido': 'TEST_ESTRUCTURA',
                        'cliente': 'TEST',
                        'valor': 1
                    }
                    test_response = self.supabase.table("comisiones").insert(test_insert).execute()
                    if test_response.data:
                        self._columnas_cache = set(test_response.data[0].keys())
                        # Eliminar el registro de prueba
                        test_id = test_response.data[0]['id']
                        self.supabase.table("comisiones").delete().eq("id", test_id).execute()
                    else:
                        raise Exception("No se pudo obtener estructura")
                except:
                    pass
            
            return self._columnas_cache if self._columnas_cache else self._get_default_columns()
                
        except Exception as e:
            st.warning(f"Error obteniendo columnas de tabla: {e}")
            return self._get_default_columns()

    def _get_default_columns(self) -> set:
        """Columnas mínimas que deberían existir"""
        return {
            'id', 'pedido', 'cliente', 'factura', 'valor', 'valor_neto', 'iva', 
            'base_comision', 'comision', 'porcentaje', 'pagado', 'fecha_factura', 
            'fecha_pago_est', 'fecha_pago_max', 'fecha_pago_real', 'cliente_propio',
            'condicion_especial', 'descuento_pie_factura', 'descuento_adicional',
            'dias_pago_real', 'metodo_pago', 'referencia', 'observaciones_pago',
            'comprobante_url', 'comision_perdida', 'razon_perdida', 'valor_devuelto',
            'comision_ajustada', 'descuentos_multiples', 'valor_descuento_pesos',
            'valor_flete', 'ciudad_destino', 'recogida_local',  # Campos de flete y destino
            'created_at', 'updated_at'
        }

    def _validar_updates(self, updates: Dict[str, Any], columnas_existentes: set) -> Dict[str, Any]:
        """Valida y filtra los updates según las columnas existentes MEJORADO"""
        safe_updates = {}
        
        for campo, valor in updates.items():
            if campo not in columnas_existentes:
                continue
                
            try:
                # Validación por tipo de campo
                if campo in ['pedido', 'cliente', 'factura', 'referencia', 'observaciones_pago', 
                           'razon_perdida', 'comprobante_url', 'metodo_pago', 'ciudad_destino']:
                    safe_updates[campo] = str(valor) if valor is not None else ""
                    
                elif campo in ['valor', 'valor_neto', 'iva', 'base_comision', 'comision', 
                             'porcentaje', 'comision_ajustada', 'descuento_adicional', 'valor_descuento_pesos', 'valor_flete']:
                    safe_updates[campo] = float(valor) if valor is not None else 0
                    
                elif campo in ['dias_pago_real']:
                    safe_updates[campo] = int(float(valor)) if valor is not None else 0
                    
                elif campo in ['pagado', 'comision_perdida', 'cliente_propio', 'condicion_especial', 
                             'descuento_pie_factura', 'descuentos_multiples', 'recogida_local']:
                    safe_updates[campo] = bool(valor)
                    
                elif campo in ['fecha_factura', 'fecha_pago_est', 'fecha_pago_max', 'fecha_pago_real']:
                    if isinstance(valor, str):
                        # Validar que es una fecha ISO válida
                        datetime.fromisoformat(valor.replace('Z', '+00:00'))
                        safe_updates[campo] = valor
                    elif hasattr(valor, 'isoformat'):
                        safe_updates[campo] = valor.isoformat()
                    else:
                        safe_updates[campo] = valor
                        
                else:
                    # Campo desconocido, agregar tal como viene
                    safe_updates[campo] = valor
                    
            except (ValueError, TypeError) as e:
                st.warning(f"Error procesando campo {campo}: {e}")
                continue
                
        return safe_updates

    # ========================
    # OPERACIONES DE DEVOLUCIONES CORREGIDAS
    # ========================

    def cargar_devoluciones(self) -> pd.DataFrame:
        """Carga datos de devoluciones con información de factura"""
        try:
            response = self.supabase.table("devoluciones").select("""
                *,
                comisiones!devoluciones_factura_id_fkey(
                    pedido,
                    cliente,
                    factura,
                    valor,
                    comision
                )
            """).execute()

            if not response.data:
                return pd.DataFrame()

            df = pd.DataFrame(response.data)

            # Expandir datos de la factura relacionada
            if 'comisiones' in df.columns:
                factura_data = pd.json_normalize(df['comisiones'])
                factura_data.columns = ['factura_' + col for col in factura_data.columns]
                df = pd.concat([df.drop('comisiones', axis=1), factura_data], axis=1)

            # Procesar tipos de datos
            df['valor_devuelto'] = pd.to_numeric(df['valor_devuelto'], errors='coerce').fillna(0)
            df['afecta_comision'] = df['afecta_comision'].fillna(True).astype(bool)

            # Convertir fechas
            for col in ['fecha_devolucion', 'created_at']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # Campos string
            for col in ['motivo']:
                if col in df.columns:
                    df[col] = df[col].fillna('').astype(str)

            return df

        except Exception as e:
            st.error(f"Error cargando devoluciones: {str(e)}")
            return pd.DataFrame()

    def insertar_devolucion(self, data: Dict[str, Any]) -> bool:
        """Inserta una nueva devolución"""
        try:
            data["created_at"] = datetime.now().isoformat()
            result = self.supabase.table("devoluciones").insert(data).execute()

            if result.data:
                # Si la devolución afecta la comisión, actualizar la factura
                if data.get("afecta_comision", True):
                    success = self._actualizar_comision_por_devolucion(data["factura_id"], data["valor_devuelto"])
                    if not success:
                        st.warning("Devolución registrada pero error actualizando comisión")
                return True
            return False

        except Exception as e:
            st.error(f"Error insertando devolución: {e}")
            return False

    def _actualizar_comision_por_devolucion(self, factura_id: int, valor_devuelto: float) -> bool:
        """Actualiza la comisión de una factura considerando devoluciones - CORREGIDO"""
        try:
            # Obtener datos actuales de la factura
            factura_response = self.supabase.table("comisiones").select("*").eq("id", factura_id).execute()
            if not factura_response.data:
                st.error("Factura no encontrada para actualizar comisión")
                return False

            factura = factura_response.data[0]

            # Obtener total de devoluciones que afectan comisión
            devoluciones_response = self.supabase.table("devoluciones").select("valor_devuelto").eq("factura_id", factura_id).eq("afecta_comision", True).execute()
            total_devuelto = sum([d['valor_devuelto'] for d in devoluciones_response.data]) if devoluciones_response.data else 0

            # Valores originales de la factura
            valor_original = factura.get('valor', 0)
            valor_neto_original = factura.get('valor_neto', 0)
            porcentaje = factura.get('porcentaje', 0)
            
            # CORREGIR: Calcular nuevo valor base después de devoluciones
            valor_neto_efectivo = valor_neto_original - (total_devuelto / 1.19)
            
            # Recalcular base comisión considerando descuentos múltiples
            if factura.get('descuentos_multiples', False):
                # Si tiene descuentos múltiples, restar el valor en pesos
                valor_descuento_pesos = factura.get('valor_descuento_pesos', 0)
                base_comision_efectiva = valor_neto_efectivo - valor_descuento_pesos
            elif factura.get('descuento_pie_factura', False):
                base_comision_efectiva = valor_neto_efectivo
            else:
                base_comision_efectiva = valor_neto_efectivo * 0.85

            # Nueva comisión (asegurar que no sea negativa)
            comision_efectiva = max(0, base_comision_efectiva * (porcentaje / 100))

            updates = {
                "valor_devuelto": total_devuelto,
                "comision_ajustada": comision_efectiva,
                "updated_at": datetime.now().isoformat()
            }

            result = self.supabase.table("comisiones").update(updates).eq("id", factura_id).execute()
            
            if result.data:
                st.cache_data.clear()  # Limpiar cache
                return True
            return False

        except Exception as e:
            st.error(f"Error actualizando comisión por devolución: {e}")
            return False

    def obtener_facturas_para_devolucion(self) -> pd.DataFrame:
        """Obtiene facturas disponibles para devoluciones"""
        try:
            response = self.supabase.table("comisiones").select(
                "id, pedido, cliente, factura, valor, comision, fecha_factura"
            ).order("fecha_factura", desc=True).execute()

            if response.data:
                df = pd.DataFrame(response.data)
                df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
                return df
            return pd.DataFrame()

        except Exception as e:
            st.error(f"Error obteniendo facturas: {e}")
            return pd.DataFrame()

    # ========================
    # OPERACIONES DE METAS
    # ========================

    def obtener_meta_mes_actual(self) -> Dict[str, Any]:
        """Obtiene la meta del mes actual"""
        try:
            mes_actual = date.today().strftime("%Y-%m")
            response = self.supabase.table("metas_mensuales").select("*").eq("mes", mes_actual).execute()

            if response.data:
                return response.data[0]
            else:
                # Crear meta por defecto
                meta_default = {
                    "mes": mes_actual,
                    "meta_ventas": 10000000,
                    "meta_clientes_nuevos": 5,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                result = self.supabase.table("metas_mensuales").insert(meta_default).execute()
                return result.data[0] if result.data else meta_default

        except Exception as e:
            return {
                "mes": date.today().strftime("%Y-%m"),
                "meta_ventas": 10000000,
                "meta_clientes_nuevos": 5
            }

    def actualizar_meta(self, mes: str, meta_ventas: float, meta_clientes: int) -> bool:
        """Actualiza meta mensual"""
        try:
            response = self.supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
            
            data = {
                "meta_ventas": meta_ventas,
                "meta_clientes_nuevos": meta_clientes,
                "updated_at": datetime.now().isoformat()
            }

            if response.data:
                result = self.supabase.table("metas_mensuales").update(data).eq("mes", mes).execute()
            else:
                data["mes"] = mes
                data["created_at"] = datetime.now().isoformat()
                result = self.supabase.table("metas_mensuales").insert(data).execute()

            return True if result.data else False

        except Exception as e:
            st.error(f"Error actualizando meta: {e}")
            return False

    # ========================
    # OPERACIONES DE ARCHIVOS
    # ========================

    def subir_comprobante(self, file, factura_id: int) -> Optional[str]:
        """Sube comprobante de pago"""
        try:
            if file is None:
                return None

            file_content = file.getvalue()
            original_extension = file.name.split('.')[-1].lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"comprobante_{factura_id}_{timestamp}.{original_extension}"

            result = self.supabase.storage.from_("comprobantes").upload(
                new_filename,
                file_content,
                file_options={
                    "content-type": f"application/{original_extension}",
                    "upsert": "true"
                }
            )

            if result:
                public_url = self.supabase.storage.from_("comprobantes").get_public_url(new_filename)
                return public_url
            return None

        except Exception as e:
            st.error(f"Error subiendo comprobante: {e}")
            return None

    # ========================
    # UTILIDADES Y HELPERS
    # ========================

    def agregar_campos_faltantes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Agrega campos que podrían no existir en el DataFrame"""
        if df.empty:
            return df

        campos_nuevos = {
            'valor_neto': lambda row: row.get('valor', 0) / 1.19 if row.get('valor') else 0,
            'iva': lambda row: row.get('valor', 0) - (row.get('valor', 0) / 1.19) if row.get('valor') else 0,
            'base_comision': lambda row: (row.get('valor', 0) / 1.19) * 0.85 if row.get('valor') else 0,
            'descuentos_multiples': False,
            'valor_descuento_pesos': 0,
            'metodo_pago': ''
        }

        for campo, default in campos_nuevos.items():
            if campo not in df.columns:
                if callable(default):
                    df[campo] = df.apply(default, axis=1)
                else:
                    df[campo] = default

        return df

    def limpiar_cache(self):
        """Limpia todos los caches de datos"""
        st.cache_data.clear()
        self._columnas_cache = None  # Limpiar cache de columnas también
    
    def obtener_factura_por_id(self, factura_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene una factura específica por su ID
        
        Args:
            factura_id: ID de la factura
            
        Returns:
            Dict con los datos de la factura o None si no existe
        """
        try:
            response = self.supabase.table("comisiones").select("*").eq("id", factura_id).execute()
            
            if not response.data:
                return None
            
            factura = response.data[0]
            
            # Procesar la factura individual
            df_temp = pd.DataFrame([factura])
            df_procesado = self._procesar_datos_comisiones(df_temp)
            
            if df_procesado.empty:
                return None
            
            return df_procesado.iloc[0].to_dict()
            
        except Exception as e:
            st.error(f"Error obteniendo factura {factura_id}: {str(e)}")
            return None
    
    def obtener_facturas_mes(self, mes: str) -> pd.DataFrame:
        """
        Obtiene todas las facturas de un mes específico
        
        Args:
            mes: Mes en formato YYYY-MM
            
        Returns:
            DataFrame con las facturas del mes
        """
        try:
            # Convertir mes a fecha de inicio y fin
            fecha_inicio = datetime.strptime(f"{mes}-01", "%Y-%m-%d")
            
            # Calcular último día del mes
            if fecha_inicio.month == 12:
                fecha_fin = datetime(fecha_inicio.year + 1, 1, 1) - timedelta(days=1)
            else:
                fecha_fin = datetime(fecha_inicio.year, fecha_inicio.month + 1, 1) - timedelta(days=1)
            
            # Consultar facturas del mes
            response = self.supabase.table("comisiones").select("*").gte("fecha_factura", fecha_inicio.strftime("%Y-%m-%d")).lte("fecha_factura", fecha_fin.strftime("%Y-%m-%d")).execute()
            
            if not response.data:
                return pd.DataFrame()
            
            df = pd.DataFrame(response.data)
            
            # Procesar datos
            df = self._procesar_datos_comisiones(df)
            
            # Agregar columna de estado si no existe
            if 'estado' not in df.columns:
                df['estado'] = df.apply(self._determinar_estado_factura, axis=1)
            
            return df
            
        except Exception as e:
            st.error(f"Error obteniendo facturas del mes {mes}: {str(e)}")
            return pd.DataFrame()
    
    def _determinar_estado_factura(self, row) -> str:
        """
        Determina el estado de una factura basado en fechas y pagos
        
        Args:
            row: Fila del DataFrame
            
        Returns:
            Estado de la factura: 'Pagada', 'Pendiente', 'Vencida'
        """
        try:
            # Si ya está pagada
            if row.get('pagado', False):
                return 'Pagada'
            
            # Si tiene fecha de pago real
            if pd.notna(row.get('fecha_pago_real')) and row.get('fecha_pago_real') != '':
                return 'Pagada'
            
            # Verificar si está vencida
            fecha_vencimiento = row.get('fecha_pago_max')
            if pd.notna(fecha_vencimiento) and fecha_vencimiento != '':
                try:
                    if isinstance(fecha_vencimiento, str):
                        fecha_vencimiento = datetime.strptime(fecha_vencimiento, "%Y-%m-%d").date()
                    elif hasattr(fecha_vencimiento, 'date'):
                        fecha_vencimiento = fecha_vencimiento.date()
                    
                    if fecha_vencimiento < date.today():
                        return 'Vencida'
                except:
                    pass
            
            return 'Pendiente'
            
        except Exception:
            return 'Pendiente'
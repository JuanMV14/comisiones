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
        
        # Asegurar tipos de columnas
        self._asegurar_tipos_columnas(df)
        
        return df

    def _calcular_campos_derivados(self, df: pd.DataFrame):
        """Calcula campos derivados como valor_neto, iva, base_comision"""
        if df['valor_neto'].sum() == 0 and df['valor'].sum() > 0:
            df['valor_neto'] = df['valor'] / 1.19
            
        if df['iva'].sum() == 0 and df['valor'].sum() > 0:
            df['iva'] = df['valor'] - df['valor_neto']
            
        if df['base_comision'].sum() == 0:
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

    def _asegurar_tipos_columnas(self, df: pd.DataFrame):
        """Asegura tipos correctos para columnas boolean y string"""
        columnas_boolean = ['pagado', 'condicion_especial', 'cliente_propio', 'descuento_pie_factura', 'comision_perdida', 'descuentos_multiples']
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
                st.cache_data.clear()
                return True
            return False
            
        except Exception as e:
            st.error(f"Error insertando venta: {e}")
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
                           'razon_perdida', 'comprobante_url', 'metodo_pago']:
                    safe_updates[campo] = str(valor) if valor is not None else ""
                    
                elif campo in ['valor', 'valor_neto', 'iva', 'base_comision', 'comision', 
                             'porcentaje', 'comision_ajustada', 'descuento_adicional', 'valor_descuento_pesos']:
                    safe_updates[campo] = float(valor) if valor is not None else 0
                    
                elif campo in ['dias_pago_real']:
                    safe_updates[campo] = int(float(valor)) if valor is not None else 0
                    
                elif campo in ['pagado', 'comision_perdida', 'cliente_propio', 'condicion_especial', 
                             'descuento_pie_factura', 'descuentos_multiples']:
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
                    "ventas_actuales": 0,
                    "clientes_nuevos_actuales": 0,
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

"""
Sistema de Radicación de Facturas
Gestiona el proceso de radicación y seguimiento de facturas ante clientes
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd
from database.queries import DatabaseManager


class InvoiceRadicationSystem:
    """Sistema para gestionar la radicación de facturas"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def obtener_facturas_pendientes_radicacion(self) -> pd.DataFrame:
        """Obtiene facturas que no han sido radicadas"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return pd.DataFrame()
            
            # Filtrar facturas sin radicar (campo fecha_radicacion es null)
            if 'fecha_radicacion' not in df.columns:
                # Si no existe el campo, todas están pendientes
                df['fecha_radicacion'] = None
            
            pendientes = df[
                (df['pagado'] == False) & 
                (df['fecha_radicacion'].isna())
            ].copy()
            
            # Ordenar por fecha de factura (más antiguas primero)
            if not pendientes.empty:
                pendientes = pendientes.sort_values('fecha_factura', ascending=True)
            
            return pendientes
            
        except Exception as e:
            print(f"Error obteniendo facturas pendientes: {e}")
            return pd.DataFrame()
    
    def obtener_facturas_radicadas(self) -> pd.DataFrame:
        """Obtiene facturas que ya han sido radicadas"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return pd.DataFrame()
            
            if 'fecha_radicacion' not in df.columns:
                return pd.DataFrame()
            
            radicadas = df[df['fecha_radicacion'].notna()].copy()
            
            # Ordenar por fecha de radicación (más recientes primero)
            if not radicadas.empty:
                radicadas = radicadas.sort_values('fecha_radicacion', ascending=False)
            
            return radicadas
            
        except Exception as e:
            print(f"Error obteniendo facturas radicadas: {e}")
            return pd.DataFrame()
    
    def radicar_factura(self, factura_id: int, datos_radicacion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Radica una factura con sus datos correspondientes
        
        Args:
            factura_id: ID de la factura a radicar
            datos_radicacion: Diccionario con los datos de radicación:
                - fecha_radicacion: Fecha de radicación
                - numero_radicado: Número de radicado asignado
                - medio_radicacion: Medio usado (correo, físico, portal, etc)
                - recibido_por: Persona que recibió la factura
                - observaciones_radicacion: Notas adicionales
        
        Returns:
            Diccionario con el resultado de la operación
        """
        try:
            # Validar datos mínimos
            if not datos_radicacion.get('fecha_radicacion'):
                return {"error": "La fecha de radicación es obligatoria"}
            
            # Preparar datos para actualizar
            datos_actualizacion = {
                "fecha_radicacion": datos_radicacion.get('fecha_radicacion'),
                "numero_radicado": datos_radicacion.get('numero_radicado', ''),
                "medio_radicacion": datos_radicacion.get('medio_radicacion', ''),
                "recibido_por": datos_radicacion.get('recibido_por', ''),
                "observaciones_radicacion": datos_radicacion.get('observaciones_radicacion', ''),
                "updated_at": datetime.now().isoformat()
            }
            
            # Actualizar factura
            response = self.db_manager.supabase.table("comisiones")\
                .update(datos_actualizacion)\
                .eq("id", factura_id)\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "mensaje": "Factura radicada exitosamente",
                    "factura_id": factura_id
                }
            else:
                return {"error": "No se pudo radicar la factura"}
                
        except Exception as e:
            return {"error": f"Error al radicar factura: {str(e)}"}
    
    def actualizar_radicacion(self, factura_id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza los datos de radicación de una factura ya radicada"""
        try:
            datos_actualizacion = {
                **datos,
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.db_manager.supabase.table("comisiones")\
                .update(datos_actualizacion)\
                .eq("id", factura_id)\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "mensaje": "Radicación actualizada exitosamente"
                }
            else:
                return {"error": "No se pudo actualizar la radicación"}
                
        except Exception as e:
            return {"error": f"Error actualizando radicación: {str(e)}"}
    
    def cancelar_radicacion(self, factura_id: int, motivo: str = "") -> Dict[str, Any]:
        """Cancela/elimina la radicación de una factura"""
        try:
            datos_limpieza = {
                "fecha_radicacion": None,
                "numero_radicado": None,
                "medio_radicacion": None,
                "recibido_por": None,
                "observaciones_radicacion": f"Radicación cancelada. {motivo}",
                "updated_at": datetime.now().isoformat()
            }
            
            response = self.db_manager.supabase.table("comisiones")\
                .update(datos_limpieza)\
                .eq("id", factura_id)\
                .execute()
            
            if response.data:
                return {
                    "success": True,
                    "mensaje": "Radicación cancelada exitosamente"
                }
            else:
                return {"error": "No se pudo cancelar la radicación"}
                
        except Exception as e:
            return {"error": f"Error cancelando radicación: {str(e)}"}
    
    def obtener_estadisticas_radicacion(self) -> Dict[str, Any]:
        """Obtiene estadísticas sobre la radicación de facturas"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return {
                    "total_facturas": 0,
                    "facturas_radicadas": 0,
                    "facturas_pendientes": 0,
                    "porcentaje_radicadas": 0,
                    "valor_radicado": 0,
                    "valor_pendiente": 0
                }
            
            # Asegurar que existe la columna
            if 'fecha_radicacion' not in df.columns:
                df['fecha_radicacion'] = None
            
            # Filtrar solo facturas no pagadas
            df_activas = df[df['pagado'] == False]
            
            radicadas = df_activas[df_activas['fecha_radicacion'].notna()]
            pendientes = df_activas[df_activas['fecha_radicacion'].isna()]
            
            total = len(df_activas)
            num_radicadas = len(radicadas)
            num_pendientes = len(pendientes)
            
            porcentaje = (num_radicadas / total * 100) if total > 0 else 0
            
            return {
                "total_facturas": total,
                "facturas_radicadas": num_radicadas,
                "facturas_pendientes": num_pendientes,
                "porcentaje_radicadas": round(porcentaje, 1),
                "valor_radicado": float(radicadas['valor'].sum()) if not radicadas.empty else 0,
                "valor_pendiente": float(pendientes['valor'].sum()) if not pendientes.empty else 0,
                "comision_radicada": float(radicadas['comision'].sum()) if not radicadas.empty else 0,
                "comision_pendiente": float(pendientes['comision'].sum()) if not pendientes.empty else 0
            }
            
        except Exception as e:
            print(f"Error calculando estadísticas: {e}")
            return {
                "total_facturas": 0,
                "facturas_radicadas": 0,
                "facturas_pendientes": 0,
                "porcentaje_radicadas": 0,
                "valor_radicado": 0,
                "valor_pendiente": 0,
                "comision_radicada": 0,
                "comision_pendiente": 0
            }
    
    def obtener_reporte_radicacion_por_cliente(self) -> pd.DataFrame:
        """Genera reporte de radicación agrupado por cliente"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return pd.DataFrame()
            
            if 'fecha_radicacion' not in df.columns:
                df['fecha_radicacion'] = None
            
            # Solo facturas no pagadas
            df_activas = df[df['pagado'] == False]
            
            if df_activas.empty:
                return pd.DataFrame()
            
            # Agrupar por cliente
            reporte = df_activas.groupby('cliente').agg({
                'id': 'count',
                'valor': 'sum',
                'comision': 'sum',
                'fecha_radicacion': lambda x: x.notna().sum()
            }).reset_index()
            
            reporte.columns = ['Cliente', 'Total Facturas', 'Valor Total', 'Comisión Total', 'Facturas Radicadas']
            
            # Calcular pendientes
            reporte['Facturas Pendientes'] = reporte['Total Facturas'] - reporte['Facturas Radicadas']
            # Proteger contra división por cero
            reporte['% Radicadas'] = reporte.apply(
                lambda row: round((row['Facturas Radicadas'] / row['Total Facturas'] * 100), 1) if row['Total Facturas'] > 0 else 0,
                axis=1
            )
            
            # Ordenar por % radicadas (menor a mayor - prioridad a los que tienen menos radicadas)
            reporte = reporte.sort_values('% Radicadas', ascending=True)
            
            return reporte
            
        except Exception as e:
            print(f"Error generando reporte: {e}")
            return pd.DataFrame()
    
    def obtener_facturas_vencidas_sin_radicar(self) -> pd.DataFrame:
        """Obtiene facturas vencidas que aún no han sido radicadas - URGENTE"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return pd.DataFrame()
            
            if 'fecha_radicacion' not in df.columns:
                df['fecha_radicacion'] = None
            
            # Facturas vencidas, no pagadas y sin radicar
            urgentes = df[
                (df['dias_vencimiento'].notna()) &
                (df['dias_vencimiento'] < 0) &
                (df['pagado'] == False) &
                (df['fecha_radicacion'].isna())
            ].copy()
            
            if not urgentes.empty:
                urgentes = urgentes.sort_values('dias_vencimiento', ascending=True)
            
            return urgentes
            
        except Exception as e:
            print(f"Error obteniendo facturas urgentes: {e}")
            return pd.DataFrame()
    
    def generar_mensaje_cliente(self, factura: Dict[str, Any]) -> str:
        """
        Genera un mensaje predeterminado para enviar al cliente con todos los detalles de la factura
        
        Args:
            factura: Diccionario o Serie con los datos de la factura
        
        Returns:
            String con el mensaje formateado listo para copiar
        """
        try:
            # Extraer datos de la factura
            cliente = factura.get('cliente', 'Cliente')
            num_factura = factura.get('factura', 'N/A')
            pedido = factura.get('pedido', 'N/A')
            valor_total = float(factura.get('valor', 0))
            valor_neto = float(factura.get('valor_neto', 0))
            iva = float(factura.get('iva', 0))
            
            # Fechas
            fecha_pago_est = factura.get('fecha_pago_est', '')
            fecha_pago_max = factura.get('fecha_pago_max', '')
            
            # Convertir fechas si son strings
            if isinstance(fecha_pago_est, str):
                from datetime import datetime
                try:
                    fecha_pago_est = datetime.fromisoformat(fecha_pago_est.replace('Z', '+00:00')).date()
                except:
                    fecha_pago_est = date.today()
            
            if isinstance(fecha_pago_max, str):
                from datetime import datetime
                try:
                    fecha_pago_max = datetime.fromisoformat(fecha_pago_max.replace('Z', '+00:00')).date()
                except:
                    fecha_pago_max = date.today()
            
            # Calcular descuento del 15% por pago puntual (solo sobre el subtotal)
            # El IVA NO se modifica, se mantiene el mismo de la factura
            descuento_15 = valor_neto * 0.15
            subtotal_con_descuento = valor_neto - descuento_15
            total_con_descuento = subtotal_con_descuento + iva  # IVA original sin cambios
            
            # Formatear montos
            def format_money(value):
                return f"${value:,.0f}".replace(",", ".")
            
            # Formatear fechas
            def format_date(fecha):
                if isinstance(fecha, date):
                    return fecha.strftime('%d/%m/%Y')
                return str(fecha)
            
            # Construir mensaje
            mensaje = f"""Estimado/a {cliente},

Le informamos que su factura #{num_factura} (Pedido: {pedido}) por {format_money(valor_total)} vence el {format_date(fecha_pago_est)}.

Desglose de la factura:
• Subtotal: {format_money(valor_neto)}
• IVA (19%): {format_money(iva)}
• Total factura: {format_money(valor_total)}

¡BENEFICIO ESPECIAL!
Si paga a tiempo (antes del vencimiento), recibirá un descuento del 15%:
• Descuento por pago puntual (15% sobre subtotal): -{format_money(descuento_15)}
• Nuevo subtotal: {format_money(subtotal_con_descuento)}
• IVA (19%): {format_money(iva)}
• TOTAL A PAGAR: {format_money(total_con_descuento)}

Fechas importantes:
• Fecha de vencimiento de la factura: {format_date(fecha_pago_est)}
• Fecha límite de pago: {format_date(fecha_pago_max)}

Aproveche este descuento y realice su pago antes de la fecha de vencimiento."""
            
            return mensaje
            
        except Exception as e:
            return f"Error generando mensaje: {str(e)}"
    
    def generar_mensaje_cliente_unificado(self, facturas: List[Dict[str, Any]]) -> str:
        """
        Genera un mensaje unificado para múltiples facturas del mismo cliente que vencen el mismo día
        
        Args:
            facturas: Lista de diccionarios con los datos de las facturas (mismo cliente, misma fecha de vencimiento)
        
        Returns:
            String con el mensaje unificado formateado listo para copiar
        """
        try:
            if not facturas:
                return "Error: No hay facturas para generar mensaje"
            
            # Extraer datos comunes (todas las facturas son del mismo cliente)
            primera_factura = facturas[0]
            cliente = primera_factura.get('cliente', 'Cliente')
            
            # Obtener fecha de vencimiento (debe ser la misma para todas)
            fecha_pago_est = primera_factura.get('fecha_pago_est', '')
            fecha_pago_max = primera_factura.get('fecha_pago_max', '')
            
            # Convertir fechas si son strings
            if isinstance(fecha_pago_est, str):
                from datetime import datetime
                try:
                    fecha_pago_est = datetime.fromisoformat(fecha_pago_est.replace('Z', '+00:00')).date()
                except:
                    fecha_pago_est = date.today()
            
            if isinstance(fecha_pago_max, str):
                from datetime import datetime
                try:
                    fecha_pago_max = datetime.fromisoformat(fecha_pago_max.replace('Z', '+00:00')).date()
                except:
                    fecha_pago_max = date.today()
            
            # Sumar todos los valores
            total_valor = sum(float(f.get('valor', 0)) for f in facturas)
            total_valor_neto = sum(float(f.get('valor_neto', 0)) for f in facturas)
            total_iva = sum(float(f.get('iva', 0)) for f in facturas)
            
            # Calcular descuento del 15% por pago puntual (solo sobre el subtotal)
            descuento_15 = total_valor_neto * 0.15
            subtotal_con_descuento = total_valor_neto - descuento_15
            total_con_descuento = subtotal_con_descuento + total_iva  # IVA original sin cambios
            
            # Obtener números de facturas y pedidos
            numeros_facturas = [f.get('factura', 'N/A') for f in facturas]
            numeros_pedidos = [f.get('pedido', 'N/A') for f in facturas]
            
            # Formatear montos
            def format_money(value):
                return f"${value:,.0f}".replace(",", ".")
            
            # Formatear fechas
            def format_date(fecha):
                if isinstance(fecha, date):
                    return fecha.strftime('%d/%m/%Y')
                return str(fecha)
            
            # Construir lista de facturas
            num_facturas = len(facturas)
            lista_facturas = "\n".join([f"• Factura #{num_fact} (Pedido: {pedido})" for num_fact, pedido in zip(numeros_facturas, numeros_pedidos)])
            
            # Construir mensaje unificado
            mensaje = f"""Estimado/a {cliente},

Le informamos que tiene {num_facturas} factura(s) pendiente(s) de pago que vencen el {format_date(fecha_pago_est)}.

Facturas pendientes:
{lista_facturas}

Desglose consolidado:
• Subtotal: {format_money(total_valor_neto)}
• IVA (19%): {format_money(total_iva)}
• Total facturas: {format_money(total_valor)}

¡BENEFICIO ESPECIAL!
Si paga a tiempo (antes del vencimiento), recibirá un descuento del 15% sobre el total:
• Descuento por pago puntual (15% sobre subtotal): -{format_money(descuento_15)}
• Nuevo subtotal: {format_money(subtotal_con_descuento)}
• IVA (19%): {format_money(total_iva)}
• TOTAL A PAGAR: {format_money(total_con_descuento)}

Fechas importantes:
• Fecha de vencimiento: {format_date(fecha_pago_est)}
• Fecha límite de pago: {format_date(fecha_pago_max)}

Aproveche este descuento y realice su pago antes de la fecha de vencimiento."""
            
            return mensaje
            
        except Exception as e:
            return f"Error generando mensaje unificado: {str(e)}"



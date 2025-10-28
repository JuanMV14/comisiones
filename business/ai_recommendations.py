import pandas as pd
from typing import List, Dict, Any
from database.queries import DatabaseManager

class AIRecommendations:
    """Sistema de recomendaciones basado en IA y análisis de datos"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def generar_recomendaciones_reales(self) -> List[Dict[str, Any]]:
        """Genera insights estratégicos del negocio"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return [{
                    'tipo': 'Sin datos',
                    'titulo': 'No hay datos disponibles',
                    'insight': 'Comienza registrando tus primeras ventas',
                    'metrica': 'N/A',
                    'impacto': 0,
                    'accion_recomendada': 'Registra ventas en la pestaña "Nueva Venta"',
                    'prioridad': 'alta'
                }]
            
            insights = []
            hoy = pd.Timestamp.now()
            mes_actual = hoy.strftime("%Y-%m")
            mes_anterior = (hoy - pd.DateOffset(months=1)).strftime("%Y-%m")
            
            # 1. ANÁLISIS DE CARTERA
            df_mes_actual = df[df['mes_factura'] == mes_actual]
            df_mes_anterior = df[df['mes_factura'] == mes_anterior]
            
            ventas_mes_actual = df_mes_actual['valor'].sum()
            ventas_mes_anterior = df_mes_anterior['valor'].sum()
            
            if ventas_mes_anterior > 0:
                variacion_cartera = ((ventas_mes_actual - ventas_mes_anterior) / ventas_mes_anterior) * 100
                
                if variacion_cartera < -10:
                    insights.append({
                        'tipo': 'Cartera',
                        'titulo': '📉 La cartera está bajando',
                        'insight': f'Ventas bajaron {abs(variacion_cartera):.1f}% vs mes anterior',
                        'metrica': f'${ventas_mes_actual:,.0f} vs ${ventas_mes_anterior:,.0f}',
                        'impacto': abs(ventas_mes_actual - ventas_mes_anterior),
                        'accion_recomendada': 'Intensificar prospección y reactivar clientes inactivos',
                        'prioridad': 'alta'
                    })
                elif variacion_cartera > 15:
                    insights.append({
                        'tipo': 'Cartera',
                        'titulo': '📈 ¡Cartera en crecimiento!',
                        'insight': f'Ventas subieron {variacion_cartera:.1f}% vs mes anterior',
                        'metrica': f'${ventas_mes_actual:,.0f} vs ${ventas_mes_anterior:,.0f}',
                        'impacto': ventas_mes_actual - ventas_mes_anterior,
                        'accion_recomendada': 'Mantener el ritmo y explorar nuevos mercados',
                        'prioridad': 'media'
                    })
                else:
                    insights.append({
                        'tipo': 'Cartera',
                        'titulo': '📊 Cartera estable',
                        'insight': f'Ventas con variación del {variacion_cartera:.1f}%',
                        'metrica': f'${ventas_mes_actual:,.0f} este mes',
                        'impacto': abs(ventas_mes_actual - ventas_mes_anterior),
                        'accion_recomendada': 'Buscar oportunidades de crecimiento para aumentar ventas',
                        'prioridad': 'media'
                    })
            
            # 2. ANÁLISIS DE COMISIONES PENDIENTES
            comisiones_pendientes = df[df['pagado'] == False]['comision'].sum()
            num_facturas_pendientes = len(df[df['pagado'] == False])
            
            if comisiones_pendientes > 0:
                insights.append({
                    'tipo': 'Comisiones',
                    'titulo': '💰 Comisiones por cobrar',
                    'insight': f'{num_facturas_pendientes} factura(s) pendiente(s) de pago',
                    'metrica': f'${comisiones_pendientes:,.0f} en comisiones',
                    'impacto': comisiones_pendientes,
                    'accion_recomendada': 'Hacer seguimiento de cobro para asegurar tus comisiones',
                    'prioridad': 'alta'
                })
            
            # 3. ANÁLISIS DE CLIENTES NUEVOS (Basado en checkbox cliente_nuevo)
            clientes_mes_actual = df_mes_actual['cliente'].nunique()
            
            # Contar clientes nuevos usando el campo cliente_nuevo DEL AÑO ACTUAL
            if 'cliente_nuevo' in df.columns:
                # Filtrar por año actual (los clientes nuevos son meta anual)
                from datetime import datetime
                anio_actual = datetime.now().strftime("%Y")
                df_anio_actual = df[df['mes_factura'].str.startswith(anio_actual)]
                
                # Contar clientes únicos marcados como nuevos del año
                df_clientes_nuevos = df_anio_actual[df_anio_actual['cliente_nuevo'] == True]
                clientes_nuevos_mes = df_clientes_nuevos['cliente'].nunique()
            else:
                # Fallback: comparar con mes anterior si no existe el campo
                clientes_mes_anterior = df_mes_anterior['cliente'].nunique()
                clientes_nuevos_mes = max(0, clientes_mes_actual - clientes_mes_anterior)
            
            # Generar insight según la cantidad de clientes nuevos
            if clientes_nuevos_mes > 0:
                insights.append({
                    'tipo': 'Clientes',
                    'titulo': '✨ Crecimiento de clientes',
                    'insight': f'Ganaste {clientes_nuevos_mes} cliente(s) nuevo(s) este año',
                    'metrica': f'{clientes_mes_actual} clientes activos este mes',
                    'impacto': clientes_nuevos_mes * (ventas_mes_actual / max(clientes_mes_actual, 1)),
                    'accion_recomendada': 'Fidelizar nuevos clientes y aumentar ticket promedio',
                    'prioridad': 'media'
                })
            elif clientes_mes_actual < 5:
                insights.append({
                    'tipo': 'Clientes',
                    'titulo': '⚠️ Pocos clientes activos',
                    'insight': f'Solo {clientes_mes_actual} cliente(s) activo(s) este mes',
                    'metrica': f'Necesitas ampliar tu cartera',
                    'impacto': 0,
                    'accion_recomendada': 'Buscar nuevos prospectos y reactivar clientes antiguos',
                    'prioridad': 'alta'
                })
            
            # 4. TICKET PROMEDIO
            if not df_mes_actual.empty:
                ticket_promedio_actual = df_mes_actual['valor'].mean()
                ticket_promedio_anterior = df_mes_anterior['valor'].mean() if not df_mes_anterior.empty else 0
                
                if ticket_promedio_anterior > 0:
                    variacion_ticket = ((ticket_promedio_actual - ticket_promedio_anterior) / ticket_promedio_anterior) * 100
                    
                    if abs(variacion_ticket) > 10:
                        insights.append({
                            'tipo': 'Ticket',
                            'titulo': f"{'💎' if variacion_ticket > 0 else '📦'} Ticket promedio {'aumentó' if variacion_ticket > 0 else 'bajó'}",
                            'insight': f'Variación del {variacion_ticket:.1f}% en valor promedio de venta',
                            'metrica': f'${ticket_promedio_actual:,.0f} promedio',
                            'impacto': abs(ticket_promedio_actual - ticket_promedio_anterior) * clientes_mes_actual,
                            'accion_recomendada': 'Vender productos complementarios' if variacion_ticket < 0 else 'Mantener estrategia de valor agregado',
                            'prioridad': 'media'
                        })
            
            # 5. CLIENTES EN RIESGO (facturas vencidas)
            clientes_riesgo = df[
                (df['dias_vencimiento'].notna()) & 
                (df['dias_vencimiento'] < 0) & 
                (df['pagado'] == False)
            ]['cliente'].nunique()
            
            if clientes_riesgo > 2:
                comision_riesgo = df[
                    (df['dias_vencimiento'].notna()) & 
                    (df['dias_vencimiento'] < 0) & 
                    (df['pagado'] == False)
                ]['comision'].sum()
                
                insights.append({
                    'tipo': 'Riesgo',
                    'titulo': '🚨 Clientes con facturas vencidas',
                    'insight': f'{clientes_riesgo} cliente(s) con pagos atrasados',
                    'metrica': f'${comision_riesgo:,.0f} en riesgo',
                    'impacto': comision_riesgo,
                    'accion_recomendada': 'Contactar urgente para gestionar cobro y evitar pérdidas',
                    'prioridad': 'alta'
                })
            
            # Si no hay suficientes insights, agregar uno genérico positivo
            if len(insights) == 0:
                insights.append({
                    'tipo': 'General',
                    'titulo': '✅ Todo en orden',
                    'insight': 'Tu negocio está funcionando bien',
                    'metrica': f'${ventas_mes_actual:,.0f} en ventas',
                    'impacto': ventas_mes_actual * 0.02,
                    'accion_recomendada': 'Buscar oportunidades de crecimiento y nuevos clientes',
                    'prioridad': 'media'
                })
            
            return insights[:4]
            
        except Exception as e:
            return [{
                'tipo': 'Error',
                'titulo': 'Error técnico',
                'insight': f'Error al generar insights: {str(e)[:50]}',
                'metrica': 'N/A',
                'impacto': 0,
                'accion_recomendada': 'Contactar soporte técnico',
                'prioridad': 'baja'
            }]
    
    def analizar_patron_cliente(self, cliente: str) -> Dict[str, Any]:
        """Analiza el patrón de comportamiento de un cliente específico"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return {"error": "No hay datos disponibles"}
            
            cliente_data = df[df['cliente'] == cliente]
            
            if cliente_data.empty:
                return {"error": f"Cliente {cliente} no encontrado"}
            
            # Análisis del patrón
            analisis = {
                'cliente': cliente,
                'total_facturas': len(cliente_data),
                'volumen_total': cliente_data['valor'].sum(),
                'ticket_promedio': cliente_data['valor'].mean(),
                'comision_total': cliente_data['comision'].sum(),
                'ultima_compra': cliente_data['fecha_factura'].max(),
                'frecuencia_dias': self._calcular_frecuencia(cliente_data),
                'patron_pago': self._analizar_patron_pago(cliente_data),
                'riesgo': self._evaluar_riesgo_cliente(cliente_data)
            }
            
            return analisis
            
        except Exception as e:
            return {"error": f"Error analizando cliente: {str(e)}"}
    
    def _calcular_frecuencia(self, cliente_data: pd.DataFrame) -> int:
        """Calcula la frecuencia promedio de compras del cliente"""
        if len(cliente_data) <= 1:
            return 0
        
        fechas = cliente_data['fecha_factura'].sort_values()
        diferencias = fechas.diff().dt.days.dropna()
        
        return int(diferencias.mean()) if not diferencias.empty else 0
    
    def _analizar_patron_pago(self, cliente_data: pd.DataFrame) -> Dict[str, Any]:
        """Analiza el patrón de pago del cliente"""
        pagadas = cliente_data[cliente_data['pagado'] == True]
        
        if pagadas.empty:
            return {
                'promedio_dias_pago': 0,
                'puntualidad': 'Sin datos',
                'facturas_pagadas': 0
            }
        
        dias_pago = pagadas['dias_pago_real'].dropna()
        
        return {
            'promedio_dias_pago': int(dias_pago.mean()) if not dias_pago.empty else 0,
            'puntualidad': self._evaluar_puntualidad(dias_pago),
            'facturas_pagadas': len(pagadas)
        }
    
    def _evaluar_puntualidad(self, dias_pago: pd.Series) -> str:
        """Evalúa la puntualidad del cliente"""
        if dias_pago.empty:
            return "Sin datos"
        
        promedio = dias_pago.mean()
        
        if promedio <= 30:
            return "Excelente"
        elif promedio <= 45:
            return "Buena"
        elif promedio <= 60:
            return "Regular"
        else:
            return "Tardía"
    
    def _evaluar_riesgo_cliente(self, cliente_data: pd.DataFrame) -> str:
        """Evalúa el riesgo del cliente"""
        # Factores de riesgo
        facturas_vencidas = len(cliente_data[
            (cliente_data['dias_vencimiento'].notna()) & 
            (cliente_data['dias_vencimiento'] < 0) & 
            (cliente_data['pagado'] == False)
        ])
        
        hoy = pd.Timestamp.now()
        ultima_compra = cliente_data['fecha_factura'].max()
        dias_sin_compra = (hoy - ultima_compra).days if pd.notna(ultima_compra) else 999
        
        score_riesgo = 0
        
        # Facturas vencidas (40% del score)
        if facturas_vencidas > 2:
            score_riesgo += 40
        elif facturas_vencidas > 0:
            score_riesgo += 20
        
        # Inactividad (35% del score)
        if dias_sin_compra > 90:
            score_riesgo += 35
        elif dias_sin_compra > 60:
            score_riesgo += 20
        elif dias_sin_compra > 30:
            score_riesgo += 10
        
        # Patrón de pago (25% del score)
        pagadas = cliente_data[cliente_data['pagado'] == True]
        if not pagadas.empty:
            dias_pago_promedio = pagadas['dias_pago_real'].mean()
            if dias_pago_promedio > 60:
                score_riesgo += 25
            elif dias_pago_promedio > 45:
                score_riesgo += 15
            elif dias_pago_promedio > 30:
                score_riesgo += 5
        
        # Clasificación final
        if score_riesgo >= 60:
            return "Alto"
        elif score_riesgo >= 30:
            return "Medio"
        else:
            return "Bajo"
    
    def generar_recomendacion_personalizada(self, cliente: str) -> Dict[str, Any]:
        """Genera una recomendación personalizada para un cliente específico"""
        analisis = self.analizar_patron_cliente(cliente)
        
        if "error" in analisis:
            return {"error": analisis["error"]}
        
        # Generar recomendación basada en el análisis
        if analisis['riesgo'] == 'Alto':
            accion = "Contacto urgente y seguimiento intensivo"
            prioridad = "alta"
            probabilidad = 30
        elif analisis['riesgo'] == 'Medio':
            accion = "Seguimiento comercial proactivo"
            prioridad = "media"
            probabilidad = 60
        else:
            accion = "Oferta de productos complementarios"
            prioridad = "media"
            probabilidad = 80
        
        return {
            'cliente': cliente,
            'accion': accion,
            'razon': f"Análisis: {analisis['patron_pago']['puntualidad']} pago, riesgo {analisis['riesgo'].lower()}",
            'impacto_potencial': analisis['ticket_promedio'] * 0.02,  # 2% del ticket promedio
            'prioridad': prioridad,
            'probabilidad': probabilidad,
            'siguiente_accion': self._generar_siguiente_accion(analisis)
        }
    
    def _generar_siguiente_accion(self, analisis: Dict[str, Any]) -> str:
        """Genera la siguiente acción recomendada"""
        if analisis['riesgo'] == 'Alto':
            return "Llamada telefónica inmediata para negociar condiciones de pago"
        elif analisis['frecuencia_dias'] > 60:
            return "Email con oferta especial para reactivar al cliente"
        else:
            return "Propuesta comercial con productos complementarios"

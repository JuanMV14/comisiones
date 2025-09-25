import pandas as pd
from typing import List, Dict, Any
from database.queries import DatabaseManager

class AIRecommendations:
    """Sistema de recomendaciones basado en IA y análisis de datos"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def generar_recomendaciones_reales(self) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en datos reales"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return [{
                    'cliente': 'No hay datos disponibles',
                    'accion': 'Revisar base de datos',
                    'producto': 'N/A',
                    'razon': 'La tabla comisiones está vacía o hay error de conexión',
                    'probabilidad': 0,
                    'impacto_comision': 0,
                    'prioridad': 'alta'
                }]
            
            recomendaciones = []
            hoy = pd.Timestamp.now()
            
            # Facturas próximas a vencer (solo las no pagadas)
            proximas_vencer = df[
                (df['dias_vencimiento'].notna()) & 
                (df['dias_vencimiento'] >= 0) & 
                (df['dias_vencimiento'] <= 7) & 
                (df['pagado'] == False)
            ].nlargest(2, 'comision')
            
            for _, factura in proximas_vencer.iterrows():
                recomendaciones.append({
                    'cliente': factura['cliente'],
                    'accion': f"URGENTE: Cobrar en {int(factura['dias_vencimiento'])} días",
                    'producto': f"Factura {factura['factura']} - ${factura['valor']:,.0f}",
                    'razon': f"Comisión de ${factura['comision']:,.0f} en riesgo de perderse",
                    'probabilidad': 90,
                    'impacto_comision': factura['comision'],
                    'prioridad': 'alta'
                })
            
            # Facturas vencidas (solo las no pagadas)
            vencidas = df[
                (df['dias_vencimiento'].notna()) & 
                (df['dias_vencimiento'] < 0) & 
                (df['pagado'] == False)
            ].nlargest(2, 'comision')
            
            for _, factura in vencidas.iterrows():
                dias_vencida = abs(int(factura['dias_vencimiento']))
                recomendaciones.append({
                    'cliente': factura['cliente'],
                    'accion': f"CRÍTICO: Vencida hace {dias_vencida} días",
                    'producto': f"Factura {factura['factura']} - ${factura['valor']:,.0f}",
                    'razon': f"Comisión perdida si no se cobra pronto (${factura['comision']:,.0f})",
                    'probabilidad': max(20, 100 - dias_vencida * 2),
                    'impacto_comision': factura['comision'],
                    'prioridad': 'alta'
                })
            
            # Clientes sin actividad reciente
            if len(recomendaciones) < 3:
                df['dias_desde_factura'] = (hoy - df['fecha_factura']).dt.days
                
                clientes_inactivos = df.groupby('cliente').agg({
                    'dias_desde_factura': 'min',
                    'valor': 'mean',
                    'comision': 'mean'
                }).reset_index()
                
                oportunidades = clientes_inactivos[
                    (clientes_inactivos['dias_desde_factura'] >= 30) & 
                    (clientes_inactivos['dias_desde_factura'] <= 90)
                ].nlargest(1, 'valor')
                
                for _, cliente in oportunidades.iterrows():
                    recomendaciones.append({
                        'cliente': cliente['cliente'],
                        'accion': 'Reactivar cliente',
                        'producto': f"Oferta personalizada (${cliente['valor']*0.8:,.0f})",
                        'razon': f"Sin compras {int(cliente['dias_desde_factura'])} días - Cliente valioso",
                        'probabilidad': max(30, 90 - int(cliente['dias_desde_factura'])),
                        'impacto_comision': cliente['comision'],
                        'prioridad': 'media'
                    })
            
            # Si no hay suficientes recomendaciones
            if len(recomendaciones) == 0:
                top_cliente = df.groupby('cliente')['valor'].sum().nlargest(1)
                if not top_cliente.empty:
                    cliente_nombre = top_cliente.index[0]
                    volumen_total = top_cliente.iloc[0]
                    
                    recomendaciones.append({
                        'cliente': cliente_nombre,
                        'accion': 'Seguimiento comercial',
                        'producto': f"Nueva propuesta (${volumen_total*0.3:,.0f})",
                        'razon': f"Tu cliente #1 por volumen total (${volumen_total:,.0f})",
                        'probabilidad': 65,
                        'impacto_comision': volumen_total * 0.015,
                        'prioridad': 'media'
                    })
            
            return recomendaciones[:3]
            
        except Exception as e:
            return [{
                'cliente': 'Error técnico',
                'accion': 'Revisar logs',
                'producto': 'N/A',
                'razon': f'Error: {str(e)[:100]}',
                'probabilidad': 0,
                'impacto_comision': 0,
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

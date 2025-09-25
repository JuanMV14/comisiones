import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Tuple
from calendar import monthrange

class MonthlyCommissionCalculator:
    """Calculadora de comisiones mensuales con pagos mes vencido"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Configuración de descuentos
        self.DESCUENTO_SALUD = 0.04  # 4%
        self.DESCUENTO_RESERVA = 0.025  # 2.5%
        self.DESCUENTO_TOTAL = self.DESCUENTO_SALUD + self.DESCUENTO_RESERVA  # 6.5%
        
        # Configuración de descuento automático
        self.DESCUENTO_AUTOMATICO = 0.15  # 15%
        self.DIAS_DESCUENTO_MIN = 35
        self.DIAS_DESCUENTO_MAX = 45
    
    def calcular_comisiones_mes(self, mes: str = None, año: int = None) -> Dict[str, Any]:
        """
        Calcula comisiones del mes especificado
        
        Args:
            mes: Mes en formato 'YYYY-MM' (ej: '2024-01')
            año: Año para el cálculo (si no se especifica mes)
        """
        try:
            # Determinar mes de cálculo
            if mes:
                fecha_calculo = datetime.strptime(mes, '%Y-%m')
            elif año:
                fecha_calculo = datetime(año, 12, 1)  # Diciembre del año especificado
            else:
                # Mes anterior al actual (pagos mes vencido)
                hoy = date.today()
                if hoy.month == 1:
                    fecha_calculo = datetime(hoy.year - 1, 12, 1)
                else:
                    fecha_calculo = datetime(hoy.year, hoy.month - 1, 1)
            
            mes_calculo = fecha_calculo.strftime('%Y-%m')
            
            # Obtener facturas pagadas en el mes de cálculo
            facturas_pagadas = self._obtener_facturas_pagadas_mes(fecha_calculo)
            
            if facturas_pagadas.empty:
                return {
                    "mes": mes_calculo,
                    "total_comisiones_brutas": 0,
                    "descuento_salud": 0,
                    "descuento_reserva": 0,
                    "total_descuentos": 0,
                    "comisiones_netas": 0,
                    "facturas_procesadas": 0,
                    "detalle_facturas": [],
                    "resumen_por_cliente": {},
                    "alertas": ["No hay facturas pagadas en este mes"]
                }
            
            # Calcular comisiones con descuento automático
            facturas_con_comisiones = self._calcular_comisiones_con_descuento(facturas_pagadas)
            
            # Calcular totales
            total_comisiones_brutas = facturas_con_comisiones['comision_final'].sum()
            descuento_salud = total_comisiones_brutas * self.DESCUENTO_SALUD
            descuento_reserva = total_comisiones_brutas * self.DESCUENTO_RESERVA
            total_descuentos = descuento_salud + descuento_reserva
            comisiones_netas = total_comisiones_brutas - total_descuentos
            
            # Generar resumen por cliente
            resumen_clientes = self._generar_resumen_por_cliente(facturas_con_comisiones)
            
            # Generar alertas
            alertas = self._generar_alertas_mes(facturas_con_comisiones, fecha_calculo)
            
            return {
                "mes": mes_calculo,
                "total_comisiones_brutas": total_comisiones_brutas,
                "descuento_salud": descuento_salud,
                "descuento_reserva": descuento_reserva,
                "total_descuentos": total_descuentos,
                "comisiones_netas": comisiones_netas,
                "facturas_procesadas": len(facturas_con_comisiones),
                "detalle_facturas": facturas_con_comisiones.to_dict('records'),
                "resumen_por_cliente": resumen_clientes,
                "alertas": alertas,
                "fecha_calculo": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Error calculando comisiones del mes: {str(e)}",
                "mes": mes_calculo if 'mes_calculo' in locals() else "N/A"
            }
    
    def _obtener_facturas_pagadas_mes(self, fecha_mes: datetime) -> pd.DataFrame:
        """Obtiene facturas pagadas en el mes especificado"""
        df = self.db_manager.cargar_datos()
        
        if df.empty:
            return pd.DataFrame()
        
        # Filtrar solo facturas pagadas
        df_pagadas = df[df['pagado'] == True].copy()
        
        if df_pagadas.empty:
            return pd.DataFrame()
        
        # Convertir fecha de pago
        df_pagadas['fecha_pago_real'] = pd.to_datetime(df_pagadas['fecha_pago_real'])
        
        # Filtrar por mes
        inicio_mes = fecha_mes.replace(day=1)
        fin_mes = inicio_mes.replace(day=monthrange(inicio_mes.year, inicio_mes.month)[1])
        
        df_mes = df_pagadas[
            (df_pagadas['fecha_pago_real'].dt.date >= inicio_mes.date()) &
            (df_pagadas['fecha_pago_real'].dt.date <= fin_mes.date())
        ]
        
        return df_mes
    
    def _calcular_comisiones_con_descuento(self, facturas: pd.DataFrame) -> pd.DataFrame:
        """Calcula comisiones aplicando descuento automático del 15%"""
        facturas_calc = facturas.copy()
        
        # Aplicar lógica de descuento automático
        facturas_calc['aplica_descuento_15'] = facturas_calc.apply(
            lambda row: self._debe_aplicar_descuento_15(row), axis=1
        )
        
        # Recalcular comisiones
        facturas_calc['comision_final'] = facturas_calc.apply(
            lambda row: self._calcular_comision_final(row), axis=1
        )
        
        # Calcular descuento aplicado
        facturas_calc['descuento_aplicado'] = facturas_calc['comision'] - facturas_calc['comision_final']
        
        return facturas_calc
    
    def _debe_aplicar_descuento_15(self, factura: pd.Series) -> bool:
        """
        Determina si se debe aplicar el descuento del 15%
        
        Reglas:
        1. Si el cliente NO tiene descuento a pie de factura
        2. Y paga entre 35-45 días
        3. Entonces se aplica el 15% de descuento automático
        """
        # Verificar si ya tiene descuento a pie de factura
        if factura.get('descuento_pie_factura', False):
            return False
        
        # Verificar días de pago
        dias_pago = factura.get('dias_pago_real', 0)
        
        if self.DIAS_DESCUENTO_MIN <= dias_pago <= self.DIAS_DESCUENTO_MAX:
            return True
        
        return False
    
    def _calcular_comision_final(self, factura: pd.Series) -> float:
        """Calcula la comisión final aplicando descuentos"""
        comision_original = factura.get('comision', 0)
        
        if self._debe_aplicar_descuento_15(factura):
            # Aplicar descuento del 15% sobre la base de comisión
            base_comision = factura.get('base_comision', 0)
            porcentaje = factura.get('porcentaje', 0)
            
            # Recalcular con descuento del 15%
            nueva_base = base_comision * (1 - self.DESCUENTO_AUTOMATICO)
            comision_final = nueva_base * (porcentaje / 100)
            
            return comision_final
        
        return comision_original
    
    def _generar_resumen_por_cliente(self, facturas: pd.DataFrame) -> Dict[str, Any]:
        """Genera resumen de comisiones por cliente"""
        if facturas.empty:
            return {}
        
        resumen = facturas.groupby('cliente').agg({
            'comision_final': ['sum', 'count'],
            'valor': 'sum',
            'descuento_aplicado': 'sum',
            'dias_pago_real': 'mean'
        }).round(2)
        
        # Aplanar columnas
        resumen.columns = ['comision_total', 'facturas_count', 'valor_total', 'descuento_total', 'dias_pago_promedio']
        resumen = resumen.reset_index()
        
        # Convertir a diccionario
        return resumen.to_dict('records')
    
    def _generar_alertas_mes(self, facturas: pd.DataFrame, fecha_mes: datetime) -> List[str]:
        """Genera alertas para el mes calculado"""
        alertas = []
        
        if facturas.empty:
            return ["No hay facturas pagadas en este mes"]
        
        # Alertas de comisiones perdidas
        comisiones_perdidas = facturas[facturas.get('comision_perdida', False)]
        if not comisiones_perdidas.empty:
            alertas.append(f"⚠️ {len(comisiones_perdidas)} facturas con comisiones perdidas por pago tardío")
        
        # Alertas de descuentos aplicados
        facturas_con_descuento = facturas[facturas['aplica_descuento_15'] == True]
        if not facturas_con_descuento.empty:
            total_descuento = facturas_con_descuento['descuento_aplicado'].sum()
            alertas.append(f"💰 {len(facturas_con_descuento)} facturas con descuento automático del 15% (${total_descuento:,.0f})")
        
        # Alertas de clientes con pagos tardíos
        pagos_tardios = facturas[facturas['dias_pago_real'] > 60]
        if not pagos_tardios.empty:
            alertas.append(f"⏰ {len(pagos_tardios)} facturas con pagos tardíos (>60 días)")
        
        # Alertas de clientes nuevos
        clientes_nuevos = facturas[facturas['dias_pago_real'].isna() | (facturas['dias_pago_real'] == 0)]
        if not clientes_nuevos.empty:
            alertas.append(f"🆕 {len(clientes_nuevos)} facturas de clientes nuevos")
        
        return alertas
    
    def calcular_proyeccion_mes_actual(self) -> Dict[str, Any]:
        """Calcula proyección de comisiones para el mes actual"""
        try:
            # Obtener facturas del mes actual
            hoy = date.today()
            inicio_mes = hoy.replace(day=1)
            
            df = self.db_manager.cargar_datos()
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
            
            facturas_mes = df[
                (df['fecha_factura'].dt.date >= inicio_mes) &
                (df['fecha_factura'].dt.date <= hoy)
            ]
            
            if facturas_mes.empty:
                return {
                    "mes": hoy.strftime('%Y-%m'),
                    "proyeccion_comisiones": 0,
                    "facturas_estimadas": 0,
                    "dias_restantes": 0,
                    "velocidad_actual": 0
                }
            
            # Calcular velocidad actual
            dias_transcurridos = (hoy - inicio_mes).days + 1
            comisiones_actuales = facturas_mes['comision'].sum()
            velocidad_actual = comisiones_actuales / dias_transcurridos
            
            # Proyectar para el mes completo
            dias_mes = monthrange(hoy.year, hoy.month)[1]
            dias_restantes = dias_mes - dias_transcurridos
            proyeccion_total = velocidad_actual * dias_mes
            
            # Aplicar descuentos
            descuento_salud = proyeccion_total * self.DESCUENTO_SALUD
            descuento_reserva = proyeccion_total * self.DESCUENTO_RESERVA
            proyeccion_neta = proyeccion_total - descuento_salud - descuento_reserva
            
            return {
                "mes": hoy.strftime('%Y-%m'),
                "comisiones_actuales": comisiones_actuales,
                "proyeccion_comisiones_brutas": proyeccion_total,
                "descuento_salud": descuento_salud,
                "descuento_reserva": descuento_reserva,
                "proyeccion_comisiones_netas": proyeccion_neta,
                "facturas_actuales": len(facturas_mes),
                "dias_transcurridos": dias_transcurridos,
                "dias_restantes": dias_restantes,
                "velocidad_actual": velocidad_actual,
                "probabilidad_cumplimiento": min(100, (comisiones_actuales / proyeccion_total) * 100) if proyeccion_total > 0 else 0
            }
            
        except Exception as e:
            return {
                "error": f"Error calculando proyección: {str(e)}"
            }
    
    def obtener_historial_comisiones(self, meses: int = 12) -> Dict[str, Any]:
        """Obtiene historial de comisiones de los últimos meses"""
        try:
            historial = []
            hoy = date.today()
            
            for i in range(meses):
                # Calcular fecha del mes
                if hoy.month - i <= 0:
                    mes_calculo = hoy.month - i + 12
                    año_calculo = hoy.year - 1
                else:
                    mes_calculo = hoy.month - i
                    año_calculo = hoy.year
                
                fecha_mes = datetime(año_calculo, mes_calculo, 1)
                mes_str = fecha_mes.strftime('%Y-%m')
                
                # Calcular comisiones del mes
                comisiones_mes = self.calcular_comisiones_mes(mes_str)
                
                if 'error' not in comisiones_mes:
                    historial.append({
                        "mes": mes_str,
                        "comisiones_netas": comisiones_mes['comisiones_netas'],
                        "facturas_procesadas": comisiones_mes['facturas_procesadas'],
                        "total_descuentos": comisiones_mes['total_descuentos']
                    })
            
            # Calcular tendencias
            if len(historial) >= 2:
                ultimo_mes = historial[0]['comisiones_netas']
                mes_anterior = historial[1]['comisiones_netas']
                tendencia = ((ultimo_mes - mes_anterior) / mes_anterior * 100) if mes_anterior > 0 else 0
            else:
                tendencia = 0
            
            return {
                "historial": historial,
                "tendencia_porcentaje": tendencia,
                "promedio_mensual": sum([h['comisiones_netas'] for h in historial]) / len(historial) if historial else 0,
                "total_periodo": sum([h['comisiones_netas'] for h in historial])
            }
            
        except Exception as e:
            return {
                "error": f"Error obteniendo historial: {str(e)}"
            }
    
    def generar_reporte_mensual(self, mes: str = None) -> Dict[str, Any]:
        """Genera reporte completo del mes"""
        try:
            # Calcular comisiones del mes
            comisiones = self.calcular_comisiones_mes(mes)
            
            if 'error' in comisiones:
                return comisiones
            
            # Obtener proyección del mes actual
            proyeccion = self.calcular_proyeccion_mes_actual()
            
            # Obtener historial
            historial = self.obtener_historial_comisiones(6)
            
            return {
                "reporte_mes": comisiones,
                "proyeccion_actual": proyeccion,
                "historial_tendencias": historial,
                "resumen_ejecutivo": self._generar_resumen_ejecutivo(comisiones, proyeccion, historial)
            }
            
        except Exception as e:
            return {
                "error": f"Error generando reporte: {str(e)}"
            }
    
    def _generar_resumen_ejecutivo(self, comisiones: Dict, proyeccion: Dict, historial: Dict) -> Dict[str, Any]:
        """Genera resumen ejecutivo del reporte"""
        return {
            "comisiones_mes": comisiones.get('comisiones_netas', 0),
            "proyeccion_mes_actual": proyeccion.get('proyeccion_comisiones_netas', 0),
            "tendencia": historial.get('tendencia_porcentaje', 0),
            "promedio_historico": historial.get('promedio_mensual', 0),
            "estado_general": self._evaluar_estado_general(comisiones, proyeccion, historial)
        }
    
    def _evaluar_estado_general(self, comisiones: Dict, proyeccion: Dict, historial: Dict) -> str:
        """Evalúa el estado general de las comisiones"""
        tendencia = historial.get('tendencia_porcentaje', 0)
        promedio = historial.get('promedio_mensual', 0)
        actual = comisiones.get('comisiones_netas', 0)
        
        if tendencia > 10 and actual > promedio:
            return "Excelente - Crecimiento sostenido"
        elif tendencia > 5:
            return "Bueno - Crecimiento moderado"
        elif tendencia > -5:
            return "Estable - Mantenimiento"
        else:
            return "Atención - Tendencia a la baja"

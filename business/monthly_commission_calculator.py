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
        self.DESCUENTO_PENSION = 0.04  # 4%
        self.DESCUENTO_RESERVA = 0.025  # 2.5%
        self.DESCUENTO_TOTAL = self.DESCUENTO_SALUD + self.DESCUENTO_PENSION + self.DESCUENTO_RESERVA  # 10.5%
    
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
                    "descuento_pension": 0,
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
            descuento_pension = total_comisiones_brutas * self.DESCUENTO_PENSION
            descuento_reserva = total_comisiones_brutas * self.DESCUENTO_RESERVA
            total_descuentos = descuento_salud + descuento_pension + descuento_reserva
            comisiones_netas = total_comisiones_brutas - total_descuentos
            
            # Generar resumen por cliente
            resumen_clientes = self._generar_resumen_por_cliente(facturas_con_comisiones)
            
            # Generar alertas
            alertas = self._generar_alertas_mes(facturas_con_comisiones, fecha_calculo)
            
            return {
                "mes": mes_calculo,
                "total_comisiones_brutas": total_comisiones_brutas,
                "descuento_salud": descuento_salud,
                "descuento_pension": descuento_pension,
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
        """Calcula comisiones (sin descuento automático del 15%)"""
        facturas_calc = facturas.copy()
        
        # La comisión final es igual a la comisión calculada
        # NO aplicamos descuento automático del 15%
        facturas_calc['comision_final'] = facturas_calc['comision']
        facturas_calc['aplica_descuento_15'] = False
        facturas_calc['descuento_aplicado'] = 0
        
        return facturas_calc
    
    
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
        
        # Alertas de descuentos aplicados (deshabilitado - ya no hay descuento automático del 15%)
        # facturas_con_descuento = facturas[facturas['aplica_descuento_15'] == True]
        # if not facturas_con_descuento.empty:
        #     total_descuento = facturas_con_descuento['descuento_aplicado'].sum()
        #     alertas.append(f"💰 {len(facturas_con_descuento)} facturas con descuento automático del 15% (${total_descuento:,.0f})")
        
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
        """Calcula comisiones de facturas PAGADAS en el mes actual"""
        try:
            # Obtener facturas PAGADAS del mes actual
            hoy = date.today()
            inicio_mes = hoy.replace(day=1)
            fin_mes = inicio_mes.replace(day=monthrange(inicio_mes.year, inicio_mes.month)[1])
            
            df = self.db_manager.cargar_datos()
            df['fecha_pago_real'] = pd.to_datetime(df['fecha_pago_real'])
            
            # FACTURAS PAGADAS EN EL MES ACTUAL
            facturas_mes = df[
                (df['pagado'] == True) &
                (df['fecha_pago_real'].notna()) &
                (df['fecha_pago_real'].dt.date >= inicio_mes) &
                (df['fecha_pago_real'].dt.date <= fin_mes)
            ]
            
            if facturas_mes.empty:
                return {
                    "mes": hoy.strftime('%Y-%m'),
                    "total_comisiones_brutas": 0,
                    "descuento_salud": 0,
                    "descuento_pension": 0,
                    "descuento_reserva": 0,
                    "total_descuentos": 0,
                    "comisiones_netas": 0,
                    "facturas_procesadas": 0
                }
            
            # Calcular comisiones con descuento automático del 15%
            facturas_con_comisiones = self._calcular_comisiones_con_descuento(facturas_mes)
            
            # Calcular totales
            total_comisiones_brutas = facturas_con_comisiones['comision_final'].sum()
            descuento_salud = total_comisiones_brutas * self.DESCUENTO_SALUD
            descuento_pension = total_comisiones_brutas * self.DESCUENTO_PENSION
            descuento_reserva = total_comisiones_brutas * self.DESCUENTO_RESERVA
            total_descuentos = descuento_salud + descuento_pension + descuento_reserva
            comisiones_netas = total_comisiones_brutas - total_descuentos
            
            return {
                "mes": hoy.strftime('%Y-%m'),
                "total_comisiones_brutas": total_comisiones_brutas,
                "descuento_salud": descuento_salud,
                "descuento_pension": descuento_pension,
                "descuento_reserva": descuento_reserva,
                "total_descuentos": total_descuentos,
                "comisiones_netas": comisiones_netas,
                "facturas_procesadas": len(facturas_con_comisiones),
                "detalle_facturas": facturas_con_comisiones.to_dict('records')
            }
            
        except Exception as e:
            return {
                "error": f"Error calculando proyección: {str(e)}"
            }
    
    def calcular_potencial_mes_actual(self) -> Dict[str, Any]:
        """Calcula comisiones potenciales de facturas con fecha límite en el mes actual"""
        try:
            hoy = date.today()
            inicio_mes = hoy.replace(day=1)
            fin_mes = inicio_mes.replace(day=monthrange(inicio_mes.year, inicio_mes.month)[1])

            df = self.db_manager.cargar_datos()

            if df.empty:
                return {
                    "mes": hoy.strftime('%Y-%m'),
                    "facturas_objetivo": 0,
                    "valor_total_facturas": 0,
                    "comisiones_brutas": 0,
                    "descuento_salud": 0,
                    "descuento_pension": 0,
                    "descuento_reserva": 0,
                    "total_descuentos": 0,
                    "comisiones_netas": 0,
                    "detalle_facturas": []
                }

            df = df[df['pagado'] == False].copy()

            if df.empty:
                return {
                    "mes": hoy.strftime('%Y-%m'),
                    "facturas_objetivo": 0,
                    "valor_total_facturas": 0,
                    "comisiones_brutas": 0,
                    "descuento_salud": 0,
                    "descuento_pension": 0,
                    "descuento_reserva": 0,
                    "total_descuentos": 0,
                    "comisiones_netas": 0,
                    "detalle_facturas": []
                }

            df['fecha_pago_est'] = pd.to_datetime(df['fecha_pago_est'], errors='coerce')

            facturas_mes = df[
                (df['fecha_pago_est'].notna()) &
                (df['fecha_pago_est'].dt.date >= inicio_mes) &
                (df['fecha_pago_est'].dt.date <= fin_mes)
            ].copy()

            if facturas_mes.empty:
                return {
                    "mes": hoy.strftime('%Y-%m'),
                    "facturas_objetivo": 0,
                    "valor_total_facturas": 0,
                    "comisiones_brutas": 0,
                    "descuento_salud": 0,
                    "descuento_pension": 0,
                    "descuento_reserva": 0,
                    "total_descuentos": 0,
                    "comisiones_netas": 0,
                    "detalle_facturas": []
                }

            if 'valor_devuelto' in facturas_mes.columns:
                facturas_mes['valor_devuelto'] = pd.to_numeric(
                    facturas_mes['valor_devuelto'], errors='coerce'
                ).fillna(0)
            else:
                facturas_mes['valor_devuelto'] = 0

            facturas_mes['comision_ajustada'] = facturas_mes['comision'] - facturas_mes['valor_devuelto']
            facturas_mes['comision_ajustada'] = facturas_mes['comision_ajustada'].clip(lower=0)

            total_comisiones_brutas = facturas_mes['comision_ajustada'].sum()
            descuento_salud = total_comisiones_brutas * self.DESCUENTO_SALUD
            descuento_pension = total_comisiones_brutas * self.DESCUENTO_PENSION
            descuento_reserva = total_comisiones_brutas * self.DESCUENTO_RESERVA
            total_descuentos = descuento_salud + descuento_pension + descuento_reserva
            comisiones_netas = total_comisiones_brutas - total_descuentos

            return {
                "mes": hoy.strftime('%Y-%m'),
                "facturas_objetivo": len(facturas_mes),
                "valor_total_facturas": facturas_mes['valor'].sum(),
                "comisiones_brutas": total_comisiones_brutas,
                "descuento_salud": descuento_salud,
                "descuento_pension": descuento_pension,
                "descuento_reserva": descuento_reserva,
                "total_descuentos": total_descuentos,
                "comisiones_netas": comisiones_netas,
                "detalle_facturas": facturas_mes.to_dict('records')
            }

        except Exception as e:
            return {
                "error": f"Error calculando potencial del mes actual: {str(e)}"
            }

    def obtener_historial_comisiones(self, meses: int = 12) -> Dict[str, Any]:
        """Obtiene historial de comisiones de los últimos meses"""
        try:
            historial = []
            hoy = date.today()
            df_completo = self.db_manager.cargar_datos()
            
            if df_completo.empty:
                return {
                    "historial": [],
                    "tendencia_porcentaje": 0,
                    "promedio_mensual": 0,
                    "total_periodo": 0
                }
            
            # Asegurar que mes_factura existe
            if 'mes_factura' not in df_completo.columns:
                df_completo['fecha_factura'] = pd.to_datetime(df_completo['fecha_factura'])
                df_completo['mes_factura'] = df_completo['fecha_factura'].dt.to_period('M').astype(str)
            
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
                
                # Obtener TODAS las facturas emitidas en el mes (no solo pagadas)
                facturas_mes = df_completo[df_completo['mes_factura'] == mes_str].copy()
                
                if not facturas_mes.empty:
                    # Calcular comisiones de todas las facturas emitidas
                    comisiones_emitidas = facturas_mes['comision'].sum()
                    
                    # Calcular comisiones solo de facturas pagadas
                    facturas_pagadas = facturas_mes[facturas_mes['pagado'] == True]
                    comisiones_pagadas = facturas_pagadas['comision'].sum() if not facturas_pagadas.empty else 0
                    
                    # Aplicar descuentos solo a comisiones pagadas
                    total_descuentos = comisiones_pagadas * (self.DESCUENTO_SALUD + self.DESCUENTO_RESERVA)
                    comisiones_netas = comisiones_pagadas - total_descuentos
                    
                    historial.append({
                        "mes": mes_str,
                        "comisiones_netas": comisiones_netas,
                        "facturas_procesadas": len(facturas_mes),
                        "total_descuentos": total_descuentos
                    })
                else:
                    historial.append({
                        "mes": mes_str,
                        "comisiones_netas": 0,
                        "facturas_procesadas": 0,
                        "total_descuentos": 0
                    })
            
            # Calcular tendencias (con protección contra división por cero)
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

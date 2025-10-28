"""
Dashboard Ejecutivo - KPIs y Métricas Avanzadas para Gerencia
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Tuple
from database.queries import DatabaseManager

class ExecutiveDashboard:
    """Sistema de Dashboard Ejecutivo con KPIs avanzados"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_executive_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen ejecutivo completo
        
        Returns:
            Diccionario con todas las métricas ejecutivas
        """
        df = self.db_manager.cargar_datos()
        
        if df.empty:
            return self._empty_summary()
        
        # Filtrar solo facturas pagadas
        df_pagadas = df[df['pagado'] == True].copy()
        
        # Convertir fechas
        df_pagadas['fecha_factura'] = pd.to_datetime(df_pagadas['fecha_factura'])
        df_pagadas['fecha_pago_real'] = pd.to_datetime(df_pagadas['fecha_pago_real'])
        
        # Mes actual y anterior
        hoy = datetime.now()
        inicio_mes_actual = hoy.replace(day=1)
        inicio_mes_anterior = (inicio_mes_actual - timedelta(days=1)).replace(day=1)
        
        # Datos mes actual
        df_mes_actual = df_pagadas[df_pagadas['fecha_pago_real'] >= inicio_mes_actual]
        # Datos mes anterior
        df_mes_anterior = df_pagadas[
            (df_pagadas['fecha_pago_real'] >= inicio_mes_anterior) &
            (df_pagadas['fecha_pago_real'] < inicio_mes_actual)
        ]
        
        return {
            # KPIs Financieros
            "kpis_financieros": self._calcular_kpis_financieros(df_pagadas, df_mes_actual, df_mes_anterior),
            
            # KPIs Operacionales
            "kpis_operacionales": self._calcular_kpis_operacionales(df, df_pagadas, df_mes_actual),
            
            # Tendencias
            "tendencias": self._calcular_tendencias(df_pagadas),
            
            # Top Performers
            "top_performers": self._obtener_top_performers(df_pagadas),
            
            # Análisis de Riesgo
            "analisis_riesgo": self._analizar_riesgos(df),
            
            # Proyecciones
            "proyecciones": self._calcular_proyecciones(df_pagadas, df_mes_actual),
            
            # Comparativas
            "comparativas": self._generar_comparativas(df_mes_actual, df_mes_anterior)
        }
    
    def _calcular_kpis_financieros(
        self, 
        df_all: pd.DataFrame, 
        df_actual: pd.DataFrame, 
        df_anterior: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calcula KPIs financieros principales"""
        
        # Mes actual
        revenue_actual = df_actual['valor'].sum() if not df_actual.empty else 0
        commission_actual = df_actual['comision'].sum() if not df_actual.empty else 0
        
        # Mes anterior
        revenue_anterior = df_anterior['valor'].sum() if not df_anterior.empty else 0
        commission_anterior = df_anterior['comision'].sum() if not df_anterior.empty else 0
        
        # Calcular cambios
        revenue_change = self._calcular_cambio_porcentual(revenue_actual, revenue_anterior)
        commission_change = self._calcular_cambio_porcentual(commission_actual, commission_anterior)
        
        # Margen de comisión
        commission_margin = (commission_actual / revenue_actual * 100) if revenue_actual > 0 else 0
        
        # Ticket promedio
        avg_ticket_actual = revenue_actual / len(df_actual) if not df_actual.empty else 0
        avg_ticket_anterior = revenue_anterior / len(df_anterior) if not df_anterior.empty else 0
        avg_ticket_change = self._calcular_cambio_porcentual(avg_ticket_actual, avg_ticket_anterior)
        
        # YTD (Year to Date)
        year_start = datetime(datetime.now().year, 1, 1)
        df_ytd = df_all[df_all['fecha_pago_real'] >= year_start]
        revenue_ytd = df_ytd['valor'].sum() if not df_ytd.empty else 0
        commission_ytd = df_ytd['comision'].sum() if not df_ytd.empty else 0
        
        return {
            "revenue_actual": revenue_actual,
            "revenue_anterior": revenue_anterior,
            "revenue_change": revenue_change,
            "revenue_ytd": revenue_ytd,
            
            "commission_actual": commission_actual,
            "commission_anterior": commission_anterior,
            "commission_change": commission_change,
            "commission_ytd": commission_ytd,
            "commission_margin": commission_margin,
            
            "avg_ticket": avg_ticket_actual,
            "avg_ticket_change": avg_ticket_change,
            
            "invoices_count": len(df_actual),
            "invoices_change": self._calcular_cambio_porcentual(len(df_actual), len(df_anterior))
        }
    
    def _calcular_kpis_operacionales(
        self,
        df_all: pd.DataFrame,
        df_pagadas: pd.DataFrame,
        df_mes_actual: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calcula KPIs operacionales"""
        
        # Tasa de conversión (pagadas vs total)
        total_facturas = len(df_all)
        facturas_pagadas = len(df_pagadas)
        conversion_rate = (facturas_pagadas / total_facturas * 100) if total_facturas > 0 else 0
        
        # Ciclo promedio de venta (días desde factura hasta pago)
        if not df_mes_actual.empty:
            df_ciclo = df_mes_actual.copy()
            df_ciclo['ciclo_dias'] = (
                df_ciclo['fecha_pago_real'] - df_ciclo['fecha_factura']
            ).dt.days
            avg_sales_cycle = df_ciclo['ciclo_dias'].mean()
            median_sales_cycle = df_ciclo['ciclo_dias'].median()
        else:
            avg_sales_cycle = 0
            median_sales_cycle = 0
        
        # Facturas vencidas
        hoy = pd.Timestamp.now()
        df_pendientes = df_all[df_all['pagado'] == False].copy()
        df_pendientes['fecha_pago_max'] = pd.to_datetime(df_pendientes['fecha_pago_max'])
        df_vencidas = df_pendientes[df_pendientes['fecha_pago_max'] < hoy]
        
        facturas_vencidas = len(df_vencidas)
        valor_vencido = df_vencidas['valor'].sum() if not df_vencidas.empty else 0
        
        # Clientes nuevos este mes
        if 'cliente_nuevo' in df_mes_actual.columns:
            clientes_nuevos = df_mes_actual['cliente_nuevo'].sum()
        else:
            clientes_nuevos = 0
        
        # Churn (clientes inactivos últimos 60 días)
        fecha_limite = hoy - timedelta(days=60)
        df_reciente = df_pagadas[df_pagadas['fecha_pago_real'] >= fecha_limite]
        clientes_activos = df_reciente['cliente'].nunique()
        clientes_totales = df_pagadas['cliente'].nunique()
        
        churn_rate = ((clientes_totales - clientes_activos) / clientes_totales * 100) if clientes_totales > 0 else 0
        
        return {
            "conversion_rate": conversion_rate,
            "avg_sales_cycle": avg_sales_cycle,
            "median_sales_cycle": median_sales_cycle,
            "facturas_vencidas": facturas_vencidas,
            "valor_vencido": valor_vencido,
            "clientes_nuevos": clientes_nuevos,
            "clientes_activos": clientes_activos,
            "clientes_totales": clientes_totales,
            "churn_rate": churn_rate,
            "retention_rate": 100 - churn_rate
        }
    
    def _calcular_tendencias(self, df_pagadas: pd.DataFrame) -> Dict[str, Any]:
        """Calcula tendencias de los últimos 6 meses"""
        
        if df_pagadas.empty:
            return {"monthly_trend": [], "growth_rate": 0}
        
        # Últimos 6 meses
        df_copy = df_pagadas.copy()
        df_copy['mes'] = df_copy['fecha_pago_real'].dt.to_period('M')
        
        # Agrupar por mes
        monthly_data = df_copy.groupby('mes').agg({
            'valor': 'sum',
            'comision': 'sum',
            'id': 'count'
        }).rename(columns={'id': 'facturas'}).reset_index()
        
        monthly_data['mes'] = monthly_data['mes'].astype(str)
        
        # Tomar últimos 6 meses
        monthly_trend = monthly_data.tail(6).to_dict('records')
        
        # Calcular tasa de crecimiento
        if len(monthly_trend) >= 2:
            primer_mes = monthly_trend[0]['valor']
            ultimo_mes = monthly_trend[-1]['valor']
            growth_rate = self._calcular_cambio_porcentual(ultimo_mes, primer_mes)
        else:
            growth_rate = 0
        
        return {
            "monthly_trend": monthly_trend,
            "growth_rate": growth_rate,
            "months_analyzed": len(monthly_trend)
        }
    
    def _obtener_top_performers(self, df_pagadas: pd.DataFrame) -> Dict[str, List]:
        """Obtiene top performers (clientes, productos, etc.)"""
        
        if df_pagadas.empty:
            return {
                "top_clientes": [],
                "top_comisiones": [],
                "clientes_frecuentes": []
            }
        
        # Top 5 clientes por valor
        top_clientes = df_pagadas.groupby('cliente')['valor'].sum().nlargest(5).reset_index()
        top_clientes_list = [
            {"cliente": row['cliente'], "valor": row['valor']}
            for _, row in top_clientes.iterrows()
        ]
        
        # Top 5 clientes por comisión generada
        top_comisiones = df_pagadas.groupby('cliente')['comision'].sum().nlargest(5).reset_index()
        top_comisiones_list = [
            {"cliente": row['cliente'], "comision": row['comision']}
            for _, row in top_comisiones.iterrows()
        ]
        
        # Clientes más frecuentes
        clientes_frecuentes = df_pagadas.groupby('cliente').size().nlargest(5).reset_index(name='facturas')
        clientes_frecuentes_list = [
            {"cliente": row['cliente'], "facturas": row['facturas']}
            for _, row in clientes_frecuentes.iterrows()
        ]
        
        return {
            "top_clientes": top_clientes_list,
            "top_comisiones": top_comisiones_list,
            "clientes_frecuentes": clientes_frecuentes_list
        }
    
    def _analizar_riesgos(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza riesgos del negocio"""
        
        hoy = pd.Timestamp.now()
        df_pendientes = df[df['pagado'] == False].copy()
        
        if df_pendientes.empty:
            return {
                "facturas_en_riesgo": 0,
                "valor_en_riesgo": 0,
                "comision_en_riesgo": 0,
                "risk_score": 0,
                "alertas": []
            }
        
        df_pendientes['fecha_pago_max'] = pd.to_datetime(df_pendientes['fecha_pago_max'])
        df_pendientes['dias_vencimiento'] = (df_pendientes['fecha_pago_max'] - hoy).dt.days
        
        # Facturas en riesgo (próximas a vencer o vencidas)
        df_riesgo = df_pendientes[df_pendientes['dias_vencimiento'] <= 7]
        
        facturas_en_riesgo = len(df_riesgo)
        valor_en_riesgo = df_riesgo['valor'].sum()
        comision_en_riesgo = df_riesgo['comision'].sum()
        
        # Risk score (0-100)
        total_pendiente = df_pendientes['valor'].sum()
        risk_score = (valor_en_riesgo / total_pendiente * 100) if total_pendiente > 0 else 0
        
        # Generar alertas
        alertas = []
        if facturas_en_riesgo > 0:
            alertas.append(f"{facturas_en_riesgo} facturas en riesgo de vencimiento")
        if risk_score > 30:
            alertas.append(f"Risk score elevado: {risk_score:.1f}%")
        
        return {
            "facturas_en_riesgo": facturas_en_riesgo,
            "valor_en_riesgo": valor_en_riesgo,
            "comision_en_riesgo": comision_en_riesgo,
            "risk_score": risk_score,
            "alertas": alertas
        }
    
    def _calcular_proyecciones(
        self,
        df_pagadas: pd.DataFrame,
        df_mes_actual: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calcula proyecciones para fin de mes"""
        
        if df_mes_actual.empty:
            return {
                "proyeccion_revenue": 0,
                "proyeccion_comision": 0,
                "dias_transcurridos": 0,
                "dias_restantes": 0,
                "confianza": "baja"
            }
        
        # Días del mes
        hoy = datetime.now()
        inicio_mes = hoy.replace(day=1)
        fin_mes = (inicio_mes.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        dias_mes = (fin_mes - inicio_mes).days + 1
        dias_transcurridos = (hoy - inicio_mes).days + 1
        dias_restantes = (fin_mes - hoy).days
        
        # Promedio diario hasta ahora
        revenue_actual = df_mes_actual['valor'].sum()
        comision_actual = df_mes_actual['comision'].sum()
        
        promedio_diario_revenue = revenue_actual / dias_transcurridos
        promedio_diario_comision = comision_actual / dias_transcurridos
        
        # Proyección lineal
        proyeccion_revenue = promedio_diario_revenue * dias_mes
        proyeccion_comision = promedio_diario_comision * dias_mes
        
        # Nivel de confianza basado en días transcurridos
        if dias_transcurridos < 7:
            confianza = "baja"
        elif dias_transcurridos < 15:
            confianza = "media"
        else:
            confianza = "alta"
        
        return {
            "proyeccion_revenue": proyeccion_revenue,
            "proyeccion_comision": proyeccion_comision,
            "revenue_actual": revenue_actual,
            "comision_actual": comision_actual,
            "dias_transcurridos": dias_transcurridos,
            "dias_restantes": dias_restantes,
            "dias_mes": dias_mes,
            "confianza": confianza,
            "promedio_diario": promedio_diario_revenue
        }
    
    def _generar_comparativas(
        self,
        df_actual: pd.DataFrame,
        df_anterior: pd.DataFrame
    ) -> Dict[str, Any]:
        """Genera comparativas entre períodos"""
        
        # Clientes propios vs externos - Mes actual
        if not df_actual.empty:
            df_actual_copy = df_actual.copy()
            propios_actual = df_actual_copy[df_actual_copy['cliente_propio'] == True]
            externos_actual = df_actual_copy[df_actual_copy['cliente_propio'] == False]
            
            revenue_propios = propios_actual['valor'].sum()
            revenue_externos = externos_actual['valor'].sum()
            
            mix_propios = (revenue_propios / (revenue_propios + revenue_externos) * 100) if (revenue_propios + revenue_externos) > 0 else 0
        else:
            revenue_propios = 0
            revenue_externos = 0
            mix_propios = 0
        
        # Clientes propios vs externos - Mes anterior
        if not df_anterior.empty:
            df_anterior_copy = df_anterior.copy()
            propios_anterior = df_anterior_copy[df_anterior_copy['cliente_propio'] == True]
            externos_anterior = df_anterior_copy[df_anterior_copy['cliente_propio'] == False]
            
            revenue_propios_ant = propios_anterior['valor'].sum()
            revenue_externos_ant = externos_anterior['valor'].sum()
        else:
            revenue_propios_ant = 0
            revenue_externos_ant = 0
        
        return {
            "mix_clientes": {
                "propios_pct": mix_propios,
                "externos_pct": 100 - mix_propios,
                "revenue_propios": revenue_propios,
                "revenue_externos": revenue_externos
            },
            "cambio_propios": self._calcular_cambio_porcentual(revenue_propios, revenue_propios_ant),
            "cambio_externos": self._calcular_cambio_porcentual(revenue_externos, revenue_externos_ant)
        }
    
    def _calcular_cambio_porcentual(self, actual: float, anterior: float) -> float:
        """Calcula cambio porcentual entre dos valores"""
        if anterior == 0:
            return 100.0 if actual > 0 else 0.0
        return ((actual - anterior) / anterior) * 100
    
    def _empty_summary(self) -> Dict[str, Any]:
        """Retorna estructura vacía cuando no hay datos"""
        return {
            "kpis_financieros": {},
            "kpis_operacionales": {},
            "tendencias": {"monthly_trend": [], "growth_rate": 0},
            "top_performers": {"top_clientes": [], "top_comisiones": [], "clientes_frecuentes": []},
            "analisis_riesgo": {"facturas_en_riesgo": 0, "valor_en_riesgo": 0, "risk_score": 0, "alertas": []},
            "proyecciones": {},
            "comparativas": {}
        }


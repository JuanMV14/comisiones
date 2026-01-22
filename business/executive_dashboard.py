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
        
        # Asegurar conversión de columnas de fecha
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
        df['fecha_pago_real'] = pd.to_datetime(df['fecha_pago_real'])
        
        # Filtrar solo facturas pagadas
        df_pagadas = df[df['pagado'] == True].copy()
        
        # Mes actual y anterior
        hoy = datetime.now()
        inicio_mes_actual = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        inicio_mes_anterior = (inicio_mes_actual - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Determinar el día límite para comparación equivalente (mismo número de días transcurridos)
        dias_transcurridos = hoy.day
        ultimo_dia_mes_anterior = (inicio_mes_actual - timedelta(days=1)).day
        dia_limite_anterior = min(dias_transcurridos, ultimo_dia_mes_anterior)

        fin_periodo_actual = hoy.replace(hour=23, minute=59, second=59, microsecond=999999)
        fin_periodo_anterior = (inicio_mes_anterior + timedelta(days=dia_limite_anterior - 1)).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        proximo_mes = (inicio_mes_actual.replace(day=28) + timedelta(days=4)).replace(day=1)
        fin_mes = proximo_mes - timedelta(microseconds=1)
        dias_mes = (fin_mes.date() - inicio_mes_actual.date()).days + 1
        dias_restantes = max((fin_mes.date() - hoy.date()).days, 0)
        
        # Datos mes actual
        df_mes_actual = df_pagadas[
            (df_pagadas['fecha_pago_real'] >= inicio_mes_actual) &
            (df_pagadas['fecha_pago_real'] <= fin_periodo_actual)
        ]
        # Datos mes anterior
        df_mes_anterior = df_pagadas[
            (df_pagadas['fecha_pago_real'] >= inicio_mes_anterior) &
            (df_pagadas['fecha_pago_real'] <= fin_periodo_anterior)
        ]
        # Facturas emitidas (independiente de pago)
        df_facturas_mes_actual = df[
            (df['fecha_factura'] >= inicio_mes_actual) &
            (df['fecha_factura'] <= fin_periodo_actual)
        ]
        df_facturas_mes_anterior = df[
            (df['fecha_factura'] >= inicio_mes_anterior) &
            (df['fecha_factura'] <= fin_periodo_anterior)
        ]
        
        meta_actual = self.db_manager.obtener_meta_mes_actual()

        return {
            # KPIs Financieros
            "kpis_financieros": self._calcular_kpis_financieros(
                df_pagadas,
                df_mes_actual,
                df_mes_anterior,
                df_facturas_mes_actual,
                df_facturas_mes_anterior,
                dias_transcurridos,
                dias_restantes,
                dias_mes,
                meta_actual
            ),
            
            # KPIs Operacionales
            "kpis_operacionales": self._calcular_kpis_operacionales(df, df_pagadas, df_mes_actual),
            
            # Tendencias
            "tendencias": self._calcular_tendencias(df_pagadas),
            
            # Top Performers
            "top_performers": self._obtener_top_performers(df_pagadas),
            
            # Análisis de Riesgo
            "analisis_riesgo": self._analizar_riesgos(df),
            
            # Proyecciones
            "proyecciones": self._calcular_proyecciones(df_facturas_mes_actual, inicio_mes_actual),
            
            # Comparativas
            "comparativas": self._generar_comparativas(df_facturas_mes_actual, df_facturas_mes_anterior)
        }
    
    def _calcular_kpis_financieros(
        self, 
        df_all: pd.DataFrame, 
        df_pagadas_mes_actual: pd.DataFrame, 
        df_pagadas_mes_anterior: pd.DataFrame,
        df_facturas_mes_actual: pd.DataFrame,
        df_facturas_mes_anterior: pd.DataFrame,
        dias_transcurridos: int,
        dias_restantes: int,
        dias_mes: int,
        meta_actual: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calcula KPIs financieros principales"""
        
        def _sumar_valor_neto(df_segment: pd.DataFrame) -> float:
            if df_segment.empty:
                return 0.0
            base_col = 'valor_neto' if 'valor_neto' in df_segment.columns else 'valor'
            df_segment = df_segment.copy()
            valores = df_segment[base_col].fillna(0)
            
            # Restar devoluciones (valor_devuelto incluye IVA, se divide por 1.19)
            if 'valor_devuelto' in df_segment.columns:
                devoluciones = df_segment['valor_devuelto'].fillna(0) / 1.19
                # Si base_col es 'valor_neto', restar directamente
                # Si base_col es 'valor', también convertir devolución a neto
                valores_ajustados = valores - devoluciones
            else:
                valores_ajustados = valores
            
            return float(valores_ajustados.sum())
        
        df_facturas_propios_actual = df_facturas_mes_actual[df_facturas_mes_actual['cliente_propio'] == True]
        df_facturas_propios_base = df_facturas_mes_anterior[df_facturas_mes_anterior['cliente_propio'] == True]

        def _contar_facturas_unicas(df_segment: pd.DataFrame) -> int:
            if df_segment.empty:
                return 0
            if 'factura_base' in df_segment.columns and df_segment['factura_base'].notna().any():
                return df_segment['factura_base'].dropna().nunique()
            if 'factura' in df_segment.columns:
                return df_segment['factura'].dropna().nunique()
            return len(df_segment)
        
        # Mes actual (clientes propios)
        revenue_actual_total = _sumar_valor_neto(df_facturas_propios_actual)
        commission_actual = df_facturas_propios_actual['comision'].sum() if not df_facturas_propios_actual.empty else 0
        
        # Mes anterior (clientes propios)
        revenue_anterior_total = _sumar_valor_neto(df_facturas_propios_base)
        commission_anterior = df_facturas_propios_base['comision'].sum() if not df_facturas_propios_base.empty else 0
        
        # Calcular cambios
        revenue_change = self._calcular_cambio_porcentual(revenue_actual_total, revenue_anterior_total)
        commission_change = self._calcular_cambio_porcentual(commission_actual, commission_anterior)
        
        # Margen de comisión
        commission_margin = (commission_actual / revenue_actual_total * 100) if revenue_actual_total > 0 else 0
        
        # Ticket promedio
        facturas_propias_actual_count = _contar_facturas_unicas(df_facturas_propios_actual)
        facturas_propias_base_count = _contar_facturas_unicas(df_facturas_propios_base)

        avg_ticket_actual = revenue_actual_total / facturas_propias_actual_count if facturas_propias_actual_count > 0 else 0
        avg_ticket_anterior = revenue_anterior_total / facturas_propias_base_count if facturas_propias_base_count > 0 else 0
        avg_ticket_change = self._calcular_cambio_porcentual(avg_ticket_actual, avg_ticket_anterior)
        
        # YTD (Year to Date)
        year_start = datetime(datetime.now().year, 1, 1)
        df_ytd = df_all[df_all['fecha_pago_real'] >= year_start]
        df_ytd_propios = df_ytd[df_ytd['cliente_propio'] == True]
        revenue_ytd = _sumar_valor_neto(df_ytd_propios) if not df_ytd_propios.empty else 0
        commission_ytd = df_ytd_propios['comision'].sum() if not df_ytd_propios.empty else 0

        # Comparativo MTD vs mismo período mes anterior
        df_pagadas_propios_actual = df_pagadas_mes_actual[df_pagadas_mes_actual['cliente_propio'] == True]
        df_pagadas_propios_base = df_pagadas_mes_anterior[df_pagadas_mes_anterior['cliente_propio'] == True]

        mtd_revenue_actual = _sumar_valor_neto(df_pagadas_propios_actual) if not df_pagadas_propios_actual.empty else 0
        mtd_revenue_base = _sumar_valor_neto(df_pagadas_propios_base) if not df_pagadas_propios_base.empty else 0
        mtd_revenue_change = self._calcular_cambio_porcentual(mtd_revenue_actual, mtd_revenue_base)
        mtd_invoices_actual = _contar_facturas_unicas(df_pagadas_propios_actual)
        mtd_invoices_base = _contar_facturas_unicas(df_pagadas_propios_base)
        mtd_invoices_change = self._calcular_cambio_porcentual(mtd_invoices_actual, mtd_invoices_base)
        mtd_ticket_actual = mtd_revenue_actual / mtd_invoices_actual if mtd_invoices_actual > 0 else 0
        mtd_ticket_base = mtd_revenue_base / mtd_invoices_base if mtd_invoices_base > 0 else 0
        mtd_ticket_change = self._calcular_cambio_porcentual(mtd_ticket_actual, mtd_ticket_base)
        
        ventas_emitidas_actual = _sumar_valor_neto(df_facturas_propios_actual) if not df_facturas_propios_actual.empty else 0
        ventas_emitidas_base = _sumar_valor_neto(df_facturas_propios_base) if not df_facturas_propios_base.empty else 0
        ventas_emitidas_change = self._calcular_cambio_porcentual(ventas_emitidas_actual, ventas_emitidas_base)
        
        facturas_emitidas_actual = facturas_propias_actual_count
        facturas_emitidas_base = facturas_propias_base_count
        facturas_emitidas_change = self._calcular_cambio_porcentual(facturas_emitidas_actual, facturas_emitidas_base)
        
        ticket_venta_actual = ventas_emitidas_actual / facturas_emitidas_actual if facturas_emitidas_actual > 0 else 0
        ticket_venta_base = ventas_emitidas_base / facturas_emitidas_base if facturas_emitidas_base > 0 else 0
        ticket_venta_change = self._calcular_cambio_porcentual(ticket_venta_actual, ticket_venta_base)
        
        meta_ventas = meta_actual.get("meta_ventas", 0) if meta_actual else 0
        faltante_meta = max(meta_ventas - ventas_emitidas_actual, 0)
        
        promedio_diario_ventas_actual = ventas_emitidas_actual / dias_transcurridos if dias_transcurridos > 0 else 0
        promedio_diario_ventas_necesario = (
            faltante_meta / dias_restantes if dias_restantes > 0 else faltante_meta
        )
        
        facturas_emitidas_diarias = facturas_emitidas_actual / dias_transcurridos if dias_transcurridos > 0 else 0
        facturas_emitidas_restantes = facturas_emitidas_diarias * dias_restantes
        proyeccion_ventas_fin_mes = ventas_emitidas_actual + (ticket_venta_actual * facturas_emitidas_restantes)
        ticket_requerido_restante = (
            faltante_meta / facturas_emitidas_restantes if facturas_emitidas_restantes > 0 else (faltante_meta if faltante_meta > 0 else 0)
        )
        
        return {
            "revenue_actual": revenue_actual_total,
            "revenue_anterior": revenue_anterior_total,
            "revenue_change": revenue_change,
            "revenue_ytd": revenue_ytd,
            
            "commission_actual": commission_actual,
            "commission_anterior": commission_anterior,
            "commission_change": commission_change,
            "commission_ytd": commission_ytd,
            "commission_margin": commission_margin,
            
            "avg_ticket": avg_ticket_actual,
            "avg_ticket_change": avg_ticket_change,
            
        "invoices_count": facturas_propias_actual_count,
        "invoices_change": self._calcular_cambio_porcentual(facturas_propias_actual_count, facturas_propias_base_count),
            "mtd_summary": {
                "ingresos_actual": mtd_revenue_actual,
                "ingresos_base": mtd_revenue_base,
                "ingresos_change": mtd_revenue_change,
                "facturas_cobradas_actual": mtd_invoices_actual,
                "facturas_cobradas_base": mtd_invoices_base,
                "facturas_cobradas_change": mtd_invoices_change,
                "ticket_cobrado_actual": mtd_ticket_actual,
                "ticket_cobrado_base": mtd_ticket_base,
                "ticket_cobrado_change": mtd_ticket_change,
                "ventas_actual": ventas_emitidas_actual,
                "ventas_base": ventas_emitidas_base,
                "ventas_change": ventas_emitidas_change,
                "facturas_emitidas_actual": facturas_emitidas_actual,
                "facturas_emitidas_base": facturas_emitidas_base,
                "facturas_emitidas_change": facturas_emitidas_change,
                "ticket_venta_actual": ticket_venta_actual,
                "ticket_venta_base": ticket_venta_base,
                "ticket_venta_change": ticket_venta_change,
                "meta_ventas": meta_ventas,
                "faltante_meta": faltante_meta,
                "promedio_diario_ventas_actual": promedio_diario_ventas_actual,
                "promedio_diario_ventas_necesario": promedio_diario_ventas_necesario,
                "facturas_emitidas_diarias": facturas_emitidas_diarias,
                "facturas_emitidas_restantes": facturas_emitidas_restantes,
                "proyeccion_ventas_fin_mes": proyeccion_ventas_fin_mes,
                "ticket_requerido_restante": ticket_requerido_restante,
                "dias_transcurridos": dias_transcurridos,
                "dias_restantes": dias_restantes,
                "dias_mes": dias_mes
            }
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
        df_copy['dia'] = df_copy['fecha_pago_real'].dt.day
        
        current_timestamp = pd.Timestamp.now()
        current_period = current_timestamp.to_period('M')
        
        # Agrupar por mes
        monthly_data = df_copy.groupby('mes').agg({
            'valor': 'sum',
            'comision': 'sum',
            'id': 'count',
            'dia': 'max'
        }).rename(columns={'id': 'facturas', 'dia': 'dias_registrados'}).reset_index()
        
        monthly_data['dias_mes'] = monthly_data['mes'].apply(lambda p: p.days_in_month)
        monthly_data['is_current'] = monthly_data['mes'] == current_period
        current_day = current_timestamp.day
        monthly_data['dias_usados'] = monthly_data.apply(
            lambda row: current_day if row['is_current'] else row['dias_mes'],
            axis=1
        )
        
        monthly_data['mes_str'] = monthly_data['mes'].astype(str)
        
        # Tomar últimos 6 meses
        monthly_trend_df = monthly_data.tail(6).copy()
        monthly_trend = monthly_trend_df.to_dict('records')
        
        for record in monthly_trend:
            record['mes'] = record.pop('mes_str')
            record['parcial'] = bool(record['is_current'] and record['dias_usados'] < record['dias_mes'])
        
        # Calcular tasa de crecimiento
        growth_context = None
        if len(monthly_trend) >= 2:
            primer_mes = monthly_trend[0]['valor']
            ultimo = monthly_trend[-1]
            penultimo = monthly_trend[-2]
            
            if ultimo['parcial'] and ultimo['dias_usados'] > 0:
                # Comparar MTD vs mismo número de días del mes anterior
                dias_comparables = ultimo['dias_usados']
                promedio_penultimo = (
                    penultimo['valor'] / penultimo['dias_usados']
                    if penultimo['dias_usados'] > 0 else 0
                )
                penultimo_equivalente = promedio_penultimo * dias_comparables
                growth_rate = self._calcular_cambio_porcentual(ultimo['valor'], penultimo_equivalente)
                growth_context = {
                    "valor_actual": ultimo['valor'],
                    "valor_base": penultimo_equivalente,
                    "descripcion_base": f"Mismo período del mes anterior ({penultimo['mes']})",
                    "dias_comparados": dias_comparables
                }
            else:
                ultimo_mes = ultimo['valor']
                growth_rate = self._calcular_cambio_porcentual(ultimo_mes, primer_mes)
                growth_context = {
                    "valor_actual": ultimo_mes,
                    "valor_base": penultimo['valor'],
                    "descripcion_base": f"Mes completo anterior ({penultimo['mes']})",
                    "dias_comparados": penultimo['dias_usados']
                }
        else:
            growth_rate = 0
        
        return {
            "monthly_trend": monthly_trend,
            "growth_rate": growth_rate,
            "months_analyzed": len(monthly_trend),
            "growth_context": growth_context
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
    
    def _calcular_proyecciones(self, df_facturas_mes_actual: pd.DataFrame, inicio_mes: datetime) -> Dict[str, Any]:
        """Calcula proyecciones para fin de mes a partir de facturas emitidas"""
        
        if df_facturas_mes_actual.empty:
            return {
                "proyeccion_revenue": 0,
                "proyeccion_comision": 0,
                "dias_transcurridos": 0,
                "dias_restantes": 0,
                "confianza": "baja"
            }
        
        # Días del mes
        hoy = datetime.now()
        fin_mes = (inicio_mes.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        dias_mes = (fin_mes - inicio_mes).days + 1
        dias_transcurridos = (hoy - inicio_mes).days + 1
        dias_restantes = (fin_mes - hoy).days
        
        # Promedio diario hasta ahora
        revenue_actual = df_facturas_mes_actual['valor'].sum()
        comision_actual = df_facturas_mes_actual['comision'].sum()
        
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


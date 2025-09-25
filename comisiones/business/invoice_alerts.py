import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Tuple
import streamlit as st

class InvoiceAlertsSystem:
    """Sistema de alertas para vencimiento de facturas"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Configuración de alertas
        self.ALERTA_CRITICA = -5  # Días vencidos para alerta crítica
        self.ALERTA_URGENTE = 3   # Días para vencimiento para alerta urgente
        self.ALERTA_NORMAL = 7    # Días para vencimiento para alerta normal
        
        # Configuración de recordatorios
        self.RECORDATORIO_1 = 15  # Primer recordatorio
        self.RECORDATORIO_2 = 5   # Segundo recordatorio
        self.RECORDATORIO_3 = 1   # Recordatorio final
    
    def generar_alertas_vencimiento(self) -> Dict[str, Any]:
        """Genera todas las alertas de vencimiento"""
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                return {
                    "alertas": [],
                    "resumen": {
                        "total_alertas": 0,
                        "criticas": 0,
                        "urgentes": 0,
                        "normales": 0
                    }
                }
            
            # Filtrar solo facturas no pagadas
            facturas_pendientes = df[df['pagado'] == False].copy()
            
            if facturas_pendientes.empty:
                return {
                    "alertas": [],
                    "resumen": {
                        "total_alertas": 0,
                        "criticas": 0,
                        "urgentes": 0,
                        "normales": 0
                    },
                    "mensaje": "No hay facturas pendientes"
                }
            
            # Calcular días de vencimiento
            facturas_pendientes = self._calcular_dias_vencimiento(facturas_pendientes)
            
            # Generar alertas por categoría
            alertas_criticas = self._generar_alertas_criticas(facturas_pendientes)
            alertas_urgentes = self._generar_alertas_urgentes(facturas_pendientes)
            alertas_normales = self._generar_alertas_normales(facturas_pendientes)
            
            # Combinar todas las alertas
            todas_alertas = alertas_criticas + alertas_urgentes + alertas_normales
            
            # Generar resumen
            resumen = self._generar_resumen_alertas(todas_alertas)
            
            # Generar recomendaciones
            recomendaciones = self._generar_recomendaciones(facturas_pendientes)
            
            return {
                "alertas": todas_alertas,
                "resumen": resumen,
                "recomendaciones": recomendaciones,
                "fecha_generacion": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Error generando alertas: {str(e)}"
            }
    
    def _calcular_dias_vencimiento(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula días de vencimiento para facturas pendientes"""
        hoy = pd.Timestamp.now()
        
        df['dias_vencimiento'] = df.apply(
            lambda row: (row['fecha_pago_max'] - hoy).days if pd.notna(row['fecha_pago_max']) else None,
            axis=1
        )
        
        return df
    
    def _generar_alertas_criticas(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Genera alertas críticas (facturas vencidas)"""
        facturas_vencidas = df[df['dias_vencimiento'] < self.ALERTA_CRITICA]
        
        alertas = []
        for _, factura in facturas_vencidas.iterrows():
            dias_vencida = abs(int(factura['dias_vencimiento']))
            
            alerta = {
                "tipo": "CRÍTICA",
                "prioridad": 1,
                "icono": "🚨",
                "color": "error",
                "cliente": factura['cliente'],
                "pedido": factura['pedido'],
                "factura": factura['factura'],
                "valor": factura['valor'],
                "comision": factura['comision'],
                "dias_vencida": dias_vencida,
                "fecha_vencimiento": factura['fecha_pago_max'],
                "mensaje": f"Factura vencida hace {dias_vencida} días",
                "accion_recomendada": self._generar_accion_critica(factura, dias_vencida),
                "urgencia": "INMEDIATA"
            }
            
            alertas.append(alerta)
        
        return alertas
    
    def _generar_alertas_urgentes(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Genera alertas urgentes (próximas a vencer)"""
        facturas_urgentes = df[
            (df['dias_vencimiento'] >= 0) & 
            (df['dias_vencimiento'] <= self.ALERTA_URGENTE)
        ]
        
        alertas = []
        for _, factura in facturas_urgentes.iterrows():
            dias_restantes = int(factura['dias_vencimiento'])
            
            alerta = {
                "tipo": "URGENTE",
                "prioridad": 2,
                "icono": "⚠️",
                "color": "warning",
                "cliente": factura['cliente'],
                "pedido": factura['pedido'],
                "factura": factura['factura'],
                "valor": factura['valor'],
                "comision": factura['comision'],
                "dias_restantes": dias_restantes,
                "fecha_vencimiento": factura['fecha_pago_max'],
                "mensaje": f"Vence en {dias_restantes} días",
                "accion_recomendada": self._generar_accion_urgente(factura, dias_restantes),
                "urgencia": "ALTA"
            }
            
            alertas.append(alerta)
        
        return alertas
    
    def _generar_alertas_normales(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Genera alertas normales (próximas a vencer)"""
        facturas_normales = df[
            (df['dias_vencimiento'] > self.ALERTA_URGENTE) & 
            (df['dias_vencimiento'] <= self.ALERTA_NORMAL)
        ]
        
        alertas = []
        for _, factura in facturas_normales.iterrows():
            dias_restantes = int(factura['dias_vencimiento'])
            
            alerta = {
                "tipo": "NORMAL",
                "prioridad": 3,
                "icono": "⏰",
                "color": "info",
                "cliente": factura['cliente'],
                "pedido": factura['pedido'],
                "factura": factura['factura'],
                "valor": factura['valor'],
                "comision": factura['comision'],
                "dias_restantes": dias_restantes,
                "fecha_vencimiento": factura['fecha_pago_max'],
                "mensaje": f"Vence en {dias_restantes} días",
                "accion_recomendada": self._generar_accion_normal(factura, dias_restantes),
                "urgencia": "MEDIA"
            }
            
            alertas.append(alerta)
        
        return alertas
    
    def _generar_accion_critica(self, factura: pd.Series, dias_vencida: int) -> str:
        """Genera acción recomendada para facturas críticas"""
        if dias_vencida > 30:
            return "Contacto telefónico inmediato + seguimiento legal"
        elif dias_vencida > 15:
            return "Contacto telefónico urgente + recordatorio formal"
        else:
            return "Contacto telefónico + recordatorio de pago"
    
    def _generar_accion_urgente(self, factura: pd.Series, dias_restantes: int) -> str:
        """Genera acción recomendada para facturas urgentes"""
        if dias_restantes == 1:
            return "Recordatorio final + confirmación de pago"
        elif dias_restantes <= 2:
            return "Recordatorio urgente + seguimiento"
        else:
            return "Recordatorio de vencimiento"
    
    def _generar_accion_normal(self, factura: pd.Series, dias_restantes: int) -> str:
        """Genera acción recomendada para facturas normales"""
        return "Recordatorio preventivo de vencimiento"
    
    def _generar_resumen_alertas(self, alertas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera resumen de todas las alertas"""
        total_alertas = len(alertas)
        criticas = len([a for a in alertas if a['tipo'] == 'CRÍTICA'])
        urgentes = len([a for a in alertas if a['tipo'] == 'URGENTE'])
        normales = len([a for a in alertas if a['tipo'] == 'NORMAL'])
        
        # Calcular montos en riesgo
        monto_critico = sum([a['valor'] for a in alertas if a['tipo'] == 'CRÍTICA'])
        monto_urgente = sum([a['valor'] for a in alertas if a['tipo'] == 'URGENTE'])
        monto_normal = sum([a['valor'] for a in alertas if a['tipo'] == 'NORMAL'])
        
        # Calcular comisiones en riesgo
        comision_critica = sum([a['comision'] for a in alertas if a['tipo'] == 'CRÍTICA'])
        comision_urgente = sum([a['comision'] for a in alertas if a['tipo'] == 'URGENTE'])
        comision_normal = sum([a['comision'] for a in alertas if a['tipo'] == 'NORMAL'])
        
        return {
            "total_alertas": total_alertas,
            "criticas": criticas,
            "urgentes": urgentes,
            "normales": normales,
            "monto_total_riesgo": monto_critico + monto_urgente + monto_normal,
            "comision_total_riesgo": comision_critica + comision_urgente + comision_normal,
            "desglose_montos": {
                "critico": monto_critico,
                "urgente": monto_urgente,
                "normal": monto_normal
            },
            "desglose_comisiones": {
                "critico": comision_critica,
                "urgente": comision_urgente,
                "normal": comision_normal
            }
        }
    
    def _generar_recomendaciones(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en patrones de vencimiento"""
        recomendaciones = []
        
        # Análisis por cliente
        clientes_problematicos = df.groupby('cliente').agg({
            'dias_vencimiento': 'min',
            'valor': 'sum',
            'comision': 'sum'
        }).reset_index()
        
        # Clientes con múltiples facturas vencidas
        clientes_multiples = clientes_problematicos[clientes_problematicos['dias_vencimiento'] < -10]
        
        if not clientes_multiples.empty:
            for _, cliente in clientes_multiples.iterrows():
                recomendaciones.append({
                    "tipo": "CLIENTE_PROBLEMÁTICO",
                    "cliente": cliente['cliente'],
                    "problema": f"Múltiples facturas vencidas (más de 10 días)",
                    "monto_riesgo": cliente['valor'],
                    "comision_riesgo": cliente['comision'],
                    "accion": "Revisar condiciones de pago y considerar suspensión de crédito"
                })
        
        # Análisis de tendencias
        if len(df) > 5:
            promedio_vencimiento = df['dias_vencimiento'].mean()
            
            if promedio_vencimiento < -5:
                recomendaciones.append({
                    "tipo": "TENDENCIA_GENERAL",
                    "problema": "Tendencia general a pagos tardíos",
                    "accion": "Revisar políticas de crédito y términos de pago"
                })
        
        return recomendaciones
    
    def obtener_alertas_cliente(self, cliente: str) -> Dict[str, Any]:
        """Obtiene alertas específicas para un cliente"""
        try:
            df = self.db_manager.cargar_datos()
            cliente_data = df[df['cliente'] == cliente]
            
            if cliente_data.empty:
                return {
                    "cliente": cliente,
                    "alertas": [],
                    "resumen": {"total_alertas": 0}
                }
            
            # Filtrar facturas pendientes del cliente
            facturas_pendientes = cliente_data[cliente_data['pagado'] == False]
            
            if facturas_pendientes.empty:
                return {
                    "cliente": cliente,
                    "alertas": [],
                    "resumen": {"total_alertas": 0},
                    "mensaje": "Cliente al día con pagos"
                }
            
            # Calcular días de vencimiento
            facturas_pendientes = self._calcular_dias_vencimiento(facturas_pendientes)
            
            # Generar alertas
            alertas_criticas = self._generar_alertas_criticas(facturas_pendientes)
            alertas_urgentes = self._generar_alertas_urgentes(facturas_pendientes)
            alertas_normales = self._generar_alertas_normales(facturas_pendientes)
            
            todas_alertas = alertas_criticas + alertas_urgentes + alertas_normales
            
            # Generar resumen
            resumen = self._generar_resumen_alertas(todas_alertas)
            
            # Análisis del cliente
            analisis_cliente = self._analizar_cliente(cliente_data)
            
            return {
                "cliente": cliente,
                "alertas": todas_alertas,
                "resumen": resumen,
                "analisis_cliente": analisis_cliente
            }
            
        except Exception as e:
            return {
                "error": f"Error obteniendo alertas del cliente: {str(e)}"
            }
    
    def _analizar_cliente(self, cliente_data: pd.DataFrame) -> Dict[str, Any]:
        """Analiza el comportamiento de pago del cliente"""
        facturas_pagadas = cliente_data[cliente_data['pagado'] == True]
        facturas_pendientes = cliente_data[cliente_data['pagado'] == False]
        
        analisis = {
            "total_facturas": len(cliente_data),
            "facturas_pagadas": len(facturas_pagadas),
            "facturas_pendientes": len(facturas_pendientes),
            "porcentaje_pago": (len(facturas_pagadas) / len(cliente_data) * 100) if len(cliente_data) > 0 else 0
        }
        
        if not facturas_pagadas.empty:
            analisis["promedio_dias_pago"] = facturas_pagadas['dias_pago_real'].mean()
            analisis["puntualidad"] = self._evaluar_puntualidad(facturas_pagadas['dias_pago_real'].mean())
        
        if not facturas_pendientes.empty:
            analisis["monto_pendiente"] = facturas_pendientes['valor'].sum()
            analisis["comision_pendiente"] = facturas_pendientes['comision'].sum()
        
        return analisis
    
    def _evaluar_puntualidad(self, promedio_dias: float) -> str:
        """Evalúa la puntualidad del cliente"""
        if promedio_dias <= 30:
            return "Excelente"
        elif promedio_dias <= 45:
            return "Buena"
        elif promedio_dias <= 60:
            return "Regular"
        else:
            return "Tardía"
    
    def generar_recordatorios_automaticos(self) -> Dict[str, Any]:
        """Genera recordatorios automáticos basados en fechas"""
        try:
            df = self.db_manager.cargar_datos()
            facturas_pendientes = df[df['pagado'] == False].copy()
            
            if facturas_pendientes.empty:
                return {
                    "recordatorios": [],
                    "resumen": {"total_recordatorios": 0}
                }
            
            # Calcular días de vencimiento
            facturas_pendientes = self._calcular_dias_vencimiento(facturas_pendientes)
            
            recordatorios = []
            
            # Recordatorios por días restantes
            for _, factura in facturas_pendientes.iterrows():
                dias_restantes = factura['dias_vencimiento']
                
                if dias_restantes == self.RECORDATORIO_1:
                    recordatorios.append(self._crear_recordatorio(factura, "PRIMER_RECORDATORIO", 15))
                elif dias_restantes == self.RECORDATORIO_2:
                    recordatorios.append(self._crear_recordatorio(factura, "SEGUNDO_RECORDATORIO", 5))
                elif dias_restantes == self.RECORDATORIO_3:
                    recordatorios.append(self._crear_recordatorio(factura, "RECORDATORIO_FINAL", 1))
            
            return {
                "recordatorios": recordatorios,
                "resumen": {
                    "total_recordatorios": len(recordatorios),
                    "primeros": len([r for r in recordatorios if r['tipo'] == 'PRIMER_RECORDATORIO']),
                    "segundos": len([r for r in recordatorios if r['tipo'] == 'SEGUNDO_RECORDATORIO']),
                    "finales": len([r for r in recordatorios if r['tipo'] == 'RECORDATORIO_FINAL'])
                }
            }
            
        except Exception as e:
            return {
                "error": f"Error generando recordatorios: {str(e)}"
            }
    
    def _crear_recordatorio(self, factura: pd.Series, tipo: str, dias: int) -> Dict[str, Any]:
        """Crea un recordatorio específico"""
        return {
            "tipo": tipo,
            "cliente": factura['cliente'],
            "pedido": factura['pedido'],
            "factura": factura['factura'],
            "valor": factura['valor'],
            "dias_restantes": dias,
            "fecha_vencimiento": factura['fecha_pago_max'],
            "mensaje": self._generar_mensaje_recordatorio(tipo, dias),
            "accion": self._generar_accion_recordatorio(tipo, dias)
        }
    
    def _generar_mensaje_recordatorio(self, tipo: str, dias: int) -> str:
        """Genera mensaje para recordatorio"""
        mensajes = {
            "PRIMER_RECORDATORIO": f"Recordatorio: Su factura vence en {dias} días",
            "SEGUNDO_RECORDATORIO": f"Recordatorio urgente: Su factura vence en {dias} días",
            "RECORDATORIO_FINAL": f"Recordatorio final: Su factura vence mañana"
        }
        
        return mensajes.get(tipo, f"Recordatorio: Su factura vence en {dias} días")
    
    def _generar_accion_recordatorio(self, tipo: str, dias: int) -> str:
        """Genera acción para recordatorio"""
        acciones = {
            "PRIMER_RECORDATORIO": "Enviar email recordatorio",
            "SEGUNDO_RECORDATORIO": "Llamada telefónica + email",
            "RECORDATORIO_FINAL": "Llamada telefónica urgente"
        }
        
        return acciones.get(tipo, "Enviar recordatorio")

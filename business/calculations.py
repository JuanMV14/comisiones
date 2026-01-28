from typing import Dict, Any
import pandas as pd
from datetime import date, timedelta

class ComisionCalculator:
    """Calculadora de comisiones con todas las reglas de negocio"""
    
    @staticmethod
    def calcular_comision_inteligente(valor_total: float, cliente_propio: bool = False, 
                                     tiene_descuento: bool = False, descuento_pie: bool = False) -> Dict[str, float]:
        """
        Calcula comisión con lógica simplificada
        
        Args:
            valor_total: Valor total de la venta
            cliente_propio: Si es cliente propio o externo  
            tiene_descuento: Boolean - True si hay cualquier descuento adicional
            descuento_pie: Si el descuento aparece en factura
        """
        valor_neto = valor_total / 1.19
        
        if descuento_pie:
            base = valor_neto
        else:
            base = valor_neto * 0.85
        
        # LÓGICA CORREGIDA: 
        # - El descuento a pie de factura (15% base) NO reduce la comisión
        # - Solo los descuentos ADICIONALES reducen la comisión
        # - tiene_descuento debe referirse SOLO a descuentos adicionales, no al base
        if cliente_propio:
            porcentaje = 1.5 if tiene_descuento else 2.5
        else:
            porcentaje = 0.5 if tiene_descuento else 1.0
        
        comision = base * (porcentaje / 100)
        
        return {
            'valor_neto': valor_neto,
            'iva': valor_total - valor_neto,
            'base_comision': base,
            'comision': comision,
            'porcentaje': porcentaje
        }
    
    @staticmethod
    def calcular_comision_automatica(row: pd.Series) -> Dict[str, Any]:
        """Calcula comisión automáticamente basado en los datos de la fila"""
        valor_neto = row.get('valor_neto', row.get('total_pedido', 0) / 1.19 if row.get('total_pedido') else 0)
        cliente_propio = row.get('cliente_propio', False)
        descuento_pie_factura = row.get('descuento_pie_factura', False)
        descuento_aplicado = row.get('descuento_aplicado', 0)
        dias_pago = row.get('dias_pago_real')
        condicion_especial = row.get('condicion_especial', False)
        valor_devuelto = row.get('valor_devuelto', 0)
        
        # 1. Calcular base inicial
        if descuento_pie_factura:
            base = valor_neto
        else:
            limite_dias = 60 if condicion_especial else 45
            if not dias_pago or dias_pago <= limite_dias:
                base = valor_neto * 0.85
            else:
                base = valor_neto
        
        # 2. Restar devoluciones
        base_final = base - valor_devuelto
        
        # 3. Determinar porcentaje
        # REGLA CORREGIDA: 
        # - El descuento_pie_factura (15% base de la empresa) NO reduce la comisión
        # - Solo los descuentos ADICIONALES (descuento_aplicado > 0) reducen la comisión
        # - descuento_pie_factura solo afecta la base, no el porcentaje
        tiene_descuento_adicional = descuento_aplicado > 0
        if cliente_propio:
            porcentaje = 1.5 if tiene_descuento_adicional else 2.5
        else:
            porcentaje = 0.5 if tiene_descuento_adicional else 1.0
        
        # 4. Verificar pérdida por +80 días
        if dias_pago and dias_pago > 80:
            return {
                'comision': 0,
                'base_final': 0,
                'porcentaje': 0,
                'perdida': True
            }
        
        comision = base_final * (porcentaje / 100)
        
        return {
            'comision': comision,
            'base_final': base_final,
            'porcentaje': porcentaje,
            'perdida': False
        }

class MetricsCalculator:
    """Calculadora de métricas y estadísticas"""
    
    @staticmethod
    def calcular_progreso_meta(df: pd.DataFrame, meta_actual: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula progreso de meta considerando solo clientes propios"""
        if df.empty:
            return {"ventas_actuales": 0, "progreso": 0, "faltante": meta_actual.get("meta_ventas", 0)}
        
        mes_actual_str = date.today().strftime("%Y-%m")
        
        # FILTRAR SOLO CLIENTES PROPIOS
        df_mes = df[
            (df["mes_factura"] == mes_actual_str) & 
            (df["cliente_propio"] == True)
        ].copy()
        
        # Calcular ventas restando devoluciones (valor_devuelto incluye IVA, se divide por 1.19)
        if "valor_devuelto" in df_mes.columns:
            df_mes["valor_neto_ajustado"] = df_mes["valor_neto"] - (df_mes["valor_devuelto"].fillna(0) / 1.19)
        else:
            df_mes["valor_neto_ajustado"] = df_mes["valor_neto"]
        
        ventas_mes = df_mes["valor_neto_ajustado"].sum()
        
        meta_ventas = meta_actual.get("meta_ventas", 0)
        progreso = (ventas_mes / meta_ventas * 100) if meta_ventas > 0 else 0
        faltante = max(0, meta_ventas - ventas_mes)
        
        return {
            "ventas_actuales": ventas_mes,
            "progreso": progreso,
            "faltante": faltante,
            "meta_ventas": meta_ventas
        }
    
    @staticmethod
    def calcular_metricas_separadas(df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula métricas separadas para clientes propios y externos"""
        if df.empty:
            return {
                "ventas_propios": 0, "ventas_externos": 0,
                "comision_propios": 0, "comision_externos": 0,
                "facturas_propios": 0, "facturas_externos": 0,
                "porcentaje_propios": 0
            }
        
        # Separar por tipo de cliente
        clientes_propios = df[df["cliente_propio"] == True].copy()
        clientes_externos = df[df["cliente_propio"] == False].copy()
        
        # Calcular ventas restando devoluciones (valor_devuelto incluye IVA, se divide por 1.19)
        # Si valor_devuelto no existe o es NaN, se usa 0
        if "valor_devuelto" in clientes_propios.columns:
            clientes_propios["valor_neto_ajustado"] = clientes_propios["valor_neto"] - (clientes_propios["valor_devuelto"].fillna(0) / 1.19)
        else:
            clientes_propios["valor_neto_ajustado"] = clientes_propios["valor_neto"]
        
        if "valor_devuelto" in clientes_externos.columns:
            clientes_externos["valor_neto_ajustado"] = clientes_externos["valor_neto"] - (clientes_externos["valor_devuelto"].fillna(0) / 1.19)
        else:
            clientes_externos["valor_neto_ajustado"] = clientes_externos["valor_neto"]
        
        # Calcular métricas (ventas con devoluciones restadas)
        ventas_propios = clientes_propios["valor_neto_ajustado"].sum()
        ventas_externos = clientes_externos["valor_neto_ajustado"].sum()
        comision_propios = clientes_propios["comision"].sum()
        comision_externos = clientes_externos["comision"].sum()
        
        total_general = ventas_propios + ventas_externos
        porcentaje_propios = (ventas_propios / total_general * 100) if total_general > 0 else 0
        
        return {
            "ventas_propios": ventas_propios,
            "ventas_externos": ventas_externos,
            "comision_propios": comision_propios,
            "comision_externos": comision_externos,
            "facturas_propios": len(clientes_propios),
            "facturas_externos": len(clientes_externos),
            "porcentaje_propios": porcentaje_propios
        }
    
    @staticmethod
    def calcular_prediccion_meta(df: pd.DataFrame, meta_actual: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula predicción de cumplimiento de meta"""
        if df.empty:
            return {"probabilidad": 0, "tendencia": "Sin datos", "dias_necesarios": 0}
        
        # Obtener datos del mes actual - SOLO CLIENTES PROPIOS
        mes_actual = date.today().strftime("%Y-%m")
        df_mes = df[
            (df["mes_factura"] == mes_actual) & 
            (df["cliente_propio"] == True)
        ].copy()
        
        if df_mes.empty:
            return {"probabilidad": 0, "tendencia": "Sin ventas de clientes propios", "dias_necesarios": 0}
        
        # Calcular progreso actual restando devoluciones
        # Usar valor_neto en lugar de valor para consistencia
        if "valor_neto" in df_mes.columns:
            base_ventas = df_mes["valor_neto"]
        else:
            # Si no hay valor_neto, calcular desde valor
            base_ventas = df_mes["valor"] / 1.19
        
        # Restar devoluciones (valor_devuelto incluye IVA, se divide por 1.19)
        if "valor_devuelto" in df_mes.columns:
            ventas_actuales = (base_ventas - (df_mes["valor_devuelto"].fillna(0) / 1.19)).sum()
        else:
            ventas_actuales = base_ventas.sum()
        meta_ventas = meta_actual.get("meta_ventas", 0)
        
        if meta_ventas == 0:
            return {"probabilidad": 0, "tendencia": "Meta no definida", "dias_necesarios": 0}
        
        # Calcular días transcurridos y restantes del mes
        hoy = date.today()
        primer_dia_mes = hoy.replace(day=1)
        dias_transcurridos = (hoy - primer_dia_mes).days + 1
        
        # Calcular último día del mes
        if hoy.month == 12:
            ultimo_dia_mes = hoy.replace(year=hoy.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            ultimo_dia_mes = hoy.replace(month=hoy.month + 1, day=1) - timedelta(days=1)
        
        dias_restantes = (ultimo_dia_mes - hoy).days + 1
        dias_totales_mes = dias_transcurridos + dias_restantes
        
        # Calcular velocidad actual y necesaria
        velocidad_actual = ventas_actuales / dias_transcurridos if dias_transcurridos > 0 else 0
        faltante = max(0, meta_ventas - ventas_actuales)
        velocidad_necesaria = faltante / dias_restantes if dias_restantes > 0 else float('inf')
        
        # Calcular probabilidad basada en velocidad
        if velocidad_actual == 0:
            probabilidad = 0
        elif velocidad_necesaria == 0:  # Ya cumplió la meta
            probabilidad = 100
        else:
            ratio_velocidad = velocidad_actual / velocidad_necesaria
            # Probabilidad basada en qué tan cerca está la velocidad actual de la necesaria
            if ratio_velocidad >= 1:
                probabilidad = min(95, 70 + (ratio_velocidad - 1) * 25)
            else:
                probabilidad = max(5, ratio_velocidad * 70)
        
        # Proyección lineal
        proyeccion_mes = velocidad_actual * dias_totales_mes
        porcentaje_meta = (proyeccion_mes / meta_ventas) * 100 if meta_ventas > 0 else 0
        
        return {
            "probabilidad": int(probabilidad),
            "tendencia": f"{porcentaje_meta:.0f}%",
            "dias_necesarios": dias_restantes,
            "velocidad_actual": velocidad_actual,
            "velocidad_necesaria": velocidad_necesaria,
            "proyeccion": proyeccion_mes
        }
    
    @staticmethod
    def calcular_tendencia_comisiones(df: pd.DataFrame) -> Dict[str, Any]:
        """Calcula tendencia real de comisiones"""
        if df.empty:
            return {"crecimiento": "0%", "delta": "Sin datos", "direccion": "normal"}
        
        # Obtener datos de los últimos 2 meses
        hoy = date.today()
        mes_actual = hoy.strftime("%Y-%m")
        
        # Mes anterior
        if hoy.month == 1:
            mes_anterior = f"{hoy.year - 1}-12"
        else:
            mes_anterior = f"{hoy.year}-{hoy.month - 1:02d}"
        
        comisiones_actual = df[df["mes_factura"] == mes_actual]["comision"].sum()
        comisiones_anterior = df[df["mes_factura"] == mes_anterior]["comision"].sum()
        
        if comisiones_anterior == 0:
            if comisiones_actual > 0:
                return {"crecimiento": "+100%", "delta": "Primer mes", "direccion": "normal"}
            else:
                return {"crecimiento": "0%", "delta": "Sin datos", "direccion": "normal"}
        
        crecimiento = ((comisiones_actual - comisiones_anterior) / comisiones_anterior) * 100
        
        return {
            "crecimiento": f"{crecimiento:+.1f}%",
            "delta": f"{abs(crecimiento):.1f}%",
            "direccion": "normal" if crecimiento >= 0 else "inverse"
        }
    
    @staticmethod
    def identificar_clientes_riesgo(df: pd.DataFrame) -> Dict[str, Any]:
        """Identifica clientes que requieren atención"""
        if df.empty:
            return {"cantidad": 0, "delta": "Sin datos", "clientes": []}
        
        hoy = pd.Timestamp.now()
        clientes_riesgo = []
        
        # 1. Facturas vencidas (alto riesgo)
        vencidas = df[
            (df['dias_vencimiento'].notna()) & 
            (df['dias_vencimiento'] < -5) & 
            (df['pagado'] == False)
        ]
        
        for cliente in vencidas['cliente'].unique():
            cliente_vencidas = vencidas[vencidas['cliente'] == cliente]
            total_riesgo = cliente_vencidas['comision'].sum()
            if total_riesgo > 0:
                clientes_riesgo.append({
                    'cliente': cliente,
                    'razon': f"Facturas vencidas",
                    'impacto': total_riesgo,
                    'tipo': 'critico'
                })
        
        # 2. Clientes sin actividad reciente (riesgo medio)
        df['dias_ultima_factura'] = (hoy - df['fecha_factura']).dt.days
        
        clientes_inactivos = df.groupby('cliente').agg({
            'dias_ultima_factura': 'min',
            'comision': 'mean',
            'valor': 'sum'
        }).reset_index()
        
        # Clientes inactivos por más de 60 días pero que han comprado antes
        inactivos_riesgo = clientes_inactivos[
            (clientes_inactivos['dias_ultima_factura'] >= 60) & 
            (clientes_inactivos['valor'] > 0)
        ].nlargest(3, 'comision')
        
        for _, cliente in inactivos_riesgo.iterrows():
            if cliente['cliente'] not in [c['cliente'] for c in clientes_riesgo]:
                clientes_riesgo.append({
                    'cliente': cliente['cliente'],
                    'razon': f"Sin actividad {cliente['dias_ultima_factura']} días",
                    'impacto': cliente['comision'],
                    'tipo': 'medio'
                })
        
        # Calcular tendencia (comparar con mes anterior si hay datos)
        mes_actual = date.today().strftime("%Y-%m")
        if date.today().month == 1:
            mes_anterior = f"{date.today().year - 1}-12"
        else:
            mes_anterior = f"{date.today().year}-{date.today().month - 1:02d}"
        
        riesgo_actual = len([c for c in clientes_riesgo if c['tipo'] == 'critico'])
        
        # Buscar clientes en riesgo del mes anterior para comparar
        df_anterior = df[df["mes_factura"] == mes_anterior]
        if not df_anterior.empty:
            vencidas_anterior = df_anterior[
                (df_anterior['dias_vencimiento'].notna()) & 
                (df_anterior['dias_vencimiento'] < -5) & 
                (df_anterior['pagado'] == False)
            ]
            riesgo_anterior = len(vencidas_anterior['cliente'].unique())
            delta_riesgo = riesgo_actual - riesgo_anterior
            delta_str = f"{delta_riesgo:+d}" if riesgo_anterior > 0 else "Sin comparación"
        else:
            delta_str = "Sin datos previos"
        
        return {
            "cantidad": len(clientes_riesgo),
            "delta": delta_str,
            "clientes": clientes_riesgo[:5]  # Top 5
        }

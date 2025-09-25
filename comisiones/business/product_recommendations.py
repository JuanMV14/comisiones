import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Tuple
from collections import Counter

class ProductRecommendationSystem:
    """Sistema de recomendaciones de productos basado en historial de clientes"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Base de datos de productos (puedes expandir esto)
        self.productos_disponibles = {
            "equipos_industriales": {
                "categoria": "Maquinaria Industrial",
                "productos": [
                    "Compresores de aire",
                    "Bombas centrífugas",
                    "Motores eléctricos",
                    "Transformadores",
                    "Generadores"
                ],
                "precio_promedio": 2500000,
                "margen": 0.25
            },
            "herramientas": {
                "categoria": "Herramientas y Equipos",
                "productos": [
                    "Taladros industriales",
                    "Soldadoras",
                    "Equipos de medición",
                    "Herramientas manuales",
                    "Equipos de seguridad"
                ],
                "precio_promedio": 800000,
                "margen": 0.30
            },
            "repuestos": {
                "categoria": "Repuestos y Accesorios",
                "productos": [
                    "Filtros industriales",
                    "Rodamientos",
                    "Correas de transmisión",
                    "Válvulas",
                    "Sensores"
                ],
                "precio_promedio": 300000,
                "margen": 0.35
            },
            "servicios": {
                "categoria": "Servicios Técnicos",
                "productos": [
                    "Mantenimiento preventivo",
                    "Reparaciones especializadas",
                    "Instalaciones",
                    "Capacitación técnica",
                    "Consultoría"
                ],
                "precio_promedio": 1500000,
                "margen": 0.40
            },
            "productos_premium": {
                "categoria": "Productos Premium",
                "productos": [
                    "Sistemas automatizados",
                    "Equipos de última generación",
                    "Soluciones personalizadas",
                    "Productos importados",
                    "Tecnología avanzada"
                ],
                "precio_promedio": 5000000,
                "margen": 0.20
            }
        }
    
    def generar_recomendaciones_importacion(self, cliente: str) -> Dict[str, Any]:
        """Genera recomendaciones específicas para importación de productos"""
        try:
            # Obtener datos del cliente
            df = self.db_manager.cargar_datos()
            cliente_data = df[df['cliente'] == cliente]
            
            if cliente_data.empty:
                return {
                    "cliente": cliente,
                    "error": "Cliente no encontrado en la base de datos"
                }
            
            # Analizar perfil del cliente
            perfil_cliente = self._analizar_perfil_cliente(cliente_data)
            
            # Generar recomendaciones basadas en el perfil
            recomendaciones = self._generar_recomendaciones_por_perfil(perfil_cliente)
            
            # Generar mensaje personalizado
            mensaje_personalizado = self._generar_mensaje_importacion(perfil_cliente, recomendaciones)
            
            # Calcular descuentos aplicables
            descuentos = self._calcular_descuentos_cliente(perfil_cliente)
            
            # Generar estrategia de contacto
            estrategia_contacto = self._generar_estrategia_contacto(perfil_cliente)
            
            return {
                "cliente": cliente,
                "perfil_cliente": perfil_cliente,
                "recomendaciones": recomendaciones,
                "mensaje_personalizado": mensaje_personalizado,
                "descuentos_aplicables": descuentos,
                "estrategia_contacto": estrategia_contacto,
                "fecha_generacion": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "cliente": cliente,
                "error": f"Error generando recomendaciones: {str(e)}"
            }
    
    def _analizar_perfil_cliente(self, cliente_data: pd.DataFrame) -> Dict[str, Any]:
        """Analiza el perfil del cliente basado en su historial"""
        # Calcular métricas básicas
        total_facturas = len(cliente_data)
        facturas_pagadas = len(cliente_data[cliente_data['pagado'] == True])
        facturas_pendientes = len(cliente_data[cliente_data['pagado'] == False])
        
        # Métricas financieras
        volumen_total = cliente_data['valor'].sum()
        ticket_promedio = cliente_data['valor'].mean()
        comision_total = cliente_data['comision'].sum()
        
        # Métricas de comportamiento
        if not cliente_data.empty:
            fecha_primera = cliente_data['fecha_factura'].min()
            fecha_ultima = cliente_data['fecha_factura'].max()
            antiguedad_dias = (date.today() - fecha_primera.date()).days
            dias_ultima_compra = (date.today() - fecha_ultima.date()).days
        else:
            antiguedad_dias = 0
            dias_ultima_compra = 0
        
        # Análisis de puntualidad
        facturas_pagadas_data = cliente_data[cliente_data['pagado'] == True]
        if not facturas_pagadas_data.empty:
            promedio_dias_pago = facturas_pagadas_data['dias_pago_real'].mean()
            puntualidad = self._evaluar_puntualidad(promedio_dias_pago)
        else:
            promedio_dias_pago = 0
            puntualidad = "Sin datos"
        
        # Análisis de frecuencia
        frecuencia_compras = self._calcular_frecuencia_compras(cliente_data)
        
        # Clasificación del cliente
        clasificacion = self._clasificar_cliente(volumen_total, ticket_promedio, frecuencia_compras, puntualidad)
        
        return {
            "clasificacion": clasificacion,
            "volumen_total": volumen_total,
            "ticket_promedio": ticket_promedio,
            "frecuencia_compras": frecuencia_compras,
            "antiguedad_dias": antiguedad_dias,
            "dias_ultima_compra": dias_ultima_compra,
            "puntualidad": puntualidad,
            "promedio_dias_pago": promedio_dias_pago,
            "total_facturas": total_facturas,
            "facturas_pagadas": facturas_pagadas,
            "facturas_pendientes": facturas_pendientes,
            "comision_total": comision_total,
            "es_cliente_propio": cliente_data['cliente_propio'].iloc[0] if not cliente_data.empty else False
        }
    
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
    
    def _calcular_frecuencia_compras(self, cliente_data: pd.DataFrame) -> float:
        """Calcula la frecuencia de compras del cliente"""
        if len(cliente_data) <= 1:
            return 0
        
        # Calcular días entre compras
        fechas = cliente_data['fecha_factura'].sort_values()
        diferencias = fechas.diff().dt.days.dropna()
        
        return diferencias.mean() if not diferencias.empty else 0
    
    def _clasificar_cliente(self, volumen: float, ticket: float, frecuencia: float, puntualidad: str) -> str:
        """Clasifica al cliente en una categoría"""
        if volumen > 50000000 and ticket > 2000000 and puntualidad in ["Excelente", "Buena"]:
            return "VIP"
        elif volumen > 20000000 and ticket > 1000000:
            return "Alto Valor"
        elif frecuencia < 30 and puntualidad in ["Excelente", "Buena"]:
            return "Leal"
        elif volumen > 10000000:
            return "Estable"
        else:
            return "En Desarrollo"
    
    def _generar_recomendaciones_por_perfil(self, perfil: Dict[str, Any]) -> Dict[str, Any]:
        """Genera recomendaciones basadas en el perfil del cliente"""
        clasificacion = perfil['clasificacion']
        ticket_promedio = perfil['ticket_promedio']
        frecuencia = perfil['frecuencia_compras']
        puntualidad = perfil['puntualidad']
        
        recomendaciones = {
            "productos_principales": [],
            "productos_complementarios": [],
            "servicios_sugeridos": [],
            "estrategia_precio": "",
            "mensaje_clave": ""
        }
        
        if clasificacion == "VIP":
            recomendaciones["productos_principales"] = [
                "Sistemas automatizados",
                "Equipos de última generación",
                "Soluciones personalizadas"
            ]
            recomendaciones["productos_complementarios"] = [
                "Servicios de mantenimiento premium",
                "Capacitación técnica especializada",
                "Consultoría personalizada"
            ]
            recomendaciones["estrategia_precio"] = "Descuentos especiales y condiciones preferenciales"
            recomendaciones["mensaje_clave"] = "Productos exclusivos para clientes VIP"
            
        elif clasificacion == "Alto Valor":
            recomendaciones["productos_principales"] = [
                "Equipos industriales de alta gama",
                "Maquinaria especializada",
                "Productos importados"
            ]
            recomendaciones["productos_complementarios"] = [
                "Repuestos de alta calidad",
                "Servicios de instalación",
                "Mantenimiento preventivo"
            ]
            recomendaciones["estrategia_precio"] = "Descuentos por volumen y pago anticipado"
            recomendaciones["mensaje_clave"] = "Productos de alto valor que maximizan su inversión"
            
        elif clasificacion == "Leal":
            recomendaciones["productos_principales"] = [
                "Productos de consumo frecuente",
                "Repuestos y accesorios",
                "Herramientas especializadas"
            ]
            recomendaciones["productos_complementarios"] = [
                "Servicios de mantenimiento",
                "Capacitación básica",
                "Soporte técnico"
            ]
            recomendaciones["estrategia_precio"] = "Descuentos por fidelidad y pago puntual"
            recomendaciones["mensaje_clave"] = "Productos que complementan sus necesidades regulares"
            
        elif clasificacion == "Estable":
            recomendaciones["productos_principales"] = [
                "Equipos estándar",
                "Herramientas básicas",
                "Repuestos comunes"
            ]
            recomendaciones["productos_complementarios"] = [
                "Servicios básicos",
                "Mantenimiento estándar"
            ]
            recomendaciones["estrategia_precio"] = "Precios competitivos y descuentos estándar"
            recomendaciones["mensaje_clave"] = "Productos confiables para sus operaciones"
            
        else:  # En Desarrollo
            recomendaciones["productos_principales"] = [
                "Productos básicos",
                "Equipos estándar",
                "Herramientas esenciales"
            ]
            recomendaciones["productos_complementarios"] = [
                "Servicios de instalación",
                "Capacitación básica"
            ]
            recomendaciones["estrategia_precio"] = "Ofertas de introducción y descuentos especiales"
            recomendaciones["mensaje_clave"] = "Productos ideales para comenzar nuestra relación comercial"
        
        # Ajustar recomendaciones basadas en ticket promedio
        if ticket_promedio > 3000000:
            recomendaciones["productos_principales"].insert(0, "Productos premium")
        elif ticket_promedio < 500000:
            recomendaciones["productos_principales"] = [
                p for p in recomendaciones["productos_principales"] 
                if "premium" not in p.lower() and "alta gama" not in p.lower()
            ]
        
        return recomendaciones
    
    def _generar_mensaje_importacion(self, perfil: Dict[str, Any], recomendaciones: Dict[str, Any]) -> str:
        """Genera mensaje personalizado para importación"""
        cliente = perfil.get('cliente', 'Cliente')
        clasificacion = perfil['clasificacion']
        ticket_promedio = perfil['ticket_promedio']
        volumen_total = perfil['volumen_total']
        
        mensaje_base = f"Estimado {cliente}, "
        
        if clasificacion == "VIP":
            mensaje = mensaje_base + f"como cliente VIP con un volumen total de ${volumen_total:,.0f}, tenemos importaciones exclusivas que se alinean perfectamente con su perfil de alto valor."
        elif clasificacion == "Alto Valor":
            mensaje = mensaje_base + f"basado en su historial de compras de alto valor (ticket promedio: ${ticket_promedio:,.0f}), tenemos importaciones especiales que pueden interesarle."
        elif clasificacion == "Leal":
            mensaje = mensaje_base + f"como cliente frecuente, tenemos productos que complementan perfectamente sus necesidades regulares."
        elif clasificacion == "Estable":
            mensaje = mensaje_base + f"tenemos nuevas importaciones que pueden ser perfectas para expandir su portafolio de productos."
        else:
            mensaje = mensaje_base + f"tenemos importaciones que pueden ser ideales para comenzar o fortalecer nuestra relación comercial."
        
        # Agregar productos específicos
        productos_principales = recomendaciones['productos_principales'][:2]
        if productos_principales:
            mensaje += f" Específicamente, tenemos {', '.join(productos_principales).lower()} que pueden ser de su interés."
        
        mensaje += " ¿Le gustaría que le envíe más detalles sobre estos productos?"
        
        return mensaje
    
    def _calcular_descuentos_cliente(self, perfil: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula descuentos aplicables para el cliente"""
        clasificacion = perfil['clasificacion']
        puntualidad = perfil['puntualidad']
        es_cliente_propio = perfil['es_cliente_propio']
        
        # Descuentos base por clasificación
        descuentos_base = {
            "VIP": {"descuento_base": 0.15, "descuento_adicional": 0.05},
            "Alto Valor": {"descuento_base": 0.12, "descuento_adicional": 0.03},
            "Leal": {"descuento_base": 0.10, "descuento_adicional": 0.02},
            "Estable": {"descuento_base": 0.08, "descuento_adicional": 0.01},
            "En Desarrollo": {"descuento_base": 0.05, "descuento_adicional": 0.01}
        }
        
        descuentos = descuentos_base.get(clasificacion, {"descuento_base": 0.05, "descuento_adicional": 0.01})
        
        # Bonificaciones por puntualidad
        if puntualidad == "Excelente":
            descuentos["bonificacion_puntualidad"] = 0.02
        elif puntualidad == "Buena":
            descuentos["bonificacion_puntualidad"] = 0.01
        else:
            descuentos["bonificacion_puntualidad"] = 0
        
        # Bonificación por cliente propio
        if es_cliente_propio:
            descuentos["bonificacion_cliente_propio"] = 0.03
        else:
            descuentos["bonificacion_cliente_propio"] = 0
        
        # Calcular descuento total
        descuento_total = (
            descuentos["descuento_base"] + 
            descuentos["descuento_adicional"] + 
            descuentos["bonificacion_puntualidad"] + 
            descuentos["bonificacion_cliente_propio"]
        )
        
        descuentos["descuento_total"] = min(descuento_total, 0.25)  # Máximo 25%
        
        return descuentos
    
    def _generar_estrategia_contacto(self, perfil: Dict[str, Any]) -> Dict[str, Any]:
        """Genera estrategia de contacto para el cliente"""
        clasificacion = perfil['clasificacion']
        dias_ultima_compra = perfil['dias_ultima_compra']
        puntualidad = perfil['puntualidad']
        
        estrategia = {
            "canal_preferido": "",
            "frecuencia_contacto": "",
            "momento_optimo": "",
            "mensaje_principal": "",
            "objetivo_contacto": ""
        }
        
        if clasificacion == "VIP":
            estrategia["canal_preferido"] = "Llamada telefónica + email personalizado"
            estrategia["frecuencia_contacto"] = "Semanal"
            estrategia["momento_optimo"] = "Mañanas (9:00-11:00)"
            estrategia["mensaje_principal"] = "Productos exclusivos y servicios premium"
            estrategia["objetivo_contacto"] = "Mantener relación premium y ofrecer productos exclusivos"
            
        elif clasificacion == "Alto Valor":
            estrategia["canal_preferido"] = "Email + seguimiento telefónico"
            estrategia["frecuencia_contacto"] = "Quincenal"
            estrategia["momento_optimo"] = "Tardes (14:00-16:00)"
            estrategia["mensaje_principal"] = "Productos de alto valor y descuentos por volumen"
            estrategia["objetivo_contacto"] = "Aumentar ticket promedio y frecuencia de compras"
            
        elif clasificacion == "Leal":
            estrategia["canal_preferido"] = "Email + WhatsApp"
            estrategia["frecuencia_contacto"] = "Mensual"
            estrategia["momento_optimo"] = "Mañanas (10:00-12:00)"
            estrategia["mensaje_principal"] = "Productos complementarios y ofertas especiales"
            estrategia["objetivo_contacto"] = "Fidelización y aumento de frecuencia"
            
        else:
            estrategia["canal_preferido"] = "Email"
            estrategia["frecuencia_contacto"] = "Bimensual"
            estrategia["momento_optimo"] = "Tardes (15:00-17:00)"
            estrategia["mensaje_principal"] = "Ofertas de introducción y productos básicos"
            estrategia["objetivo_contacto"] = "Desarrollo de relación y primera compra"
        
        # Ajustar estrategia basada en última compra
        if dias_ultima_compra > 90:
            estrategia["frecuencia_contacto"] = "Semanal"
            estrategia["objetivo_contacto"] = "Reactivación del cliente"
            estrategia["mensaje_principal"] = "Ofertas especiales para reactivación"
        
        return estrategia
    
    def obtener_recomendaciones_masivas(self) -> Dict[str, Any]:
        """Obtiene recomendaciones para todos los clientes"""
        try:
            df = self.db_manager.cargar_datos()
            clientes_unicos = df['cliente'].unique()
            
            recomendaciones_masivas = []
            
            for cliente in clientes_unicos:
                cliente_data = df[df['cliente'] == cliente]
                perfil = self._analizar_perfil_cliente(cliente_data)
                recomendaciones = self._generar_recomendaciones_por_perfil(perfil)
                
                recomendaciones_masivas.append({
                    "cliente": cliente,
                    "clasificacion": perfil['clasificacion'],
                    "productos_principales": recomendaciones['productos_principales'],
                    "estrategia_precio": recomendaciones['estrategia_precio'],
                    "prioridad_contacto": self._calcular_prioridad_contacto(perfil)
                })
            
            # Ordenar por prioridad
            recomendaciones_masivas.sort(key=lambda x: x['prioridad_contacto'], reverse=True)
            
            return {
                "total_clientes": len(recomendaciones_masivas),
                "recomendaciones": recomendaciones_masivas,
                "resumen_por_clasificacion": self._generar_resumen_clasificaciones(recomendaciones_masivas)
            }
            
        except Exception as e:
            return {
                "error": f"Error generando recomendaciones masivas: {str(e)}"
            }
    
    def _calcular_prioridad_contacto(self, perfil: Dict[str, Any]) -> int:
        """Calcula prioridad de contacto (1-10)"""
        prioridad = 5  # Base
        
        # Ajustar por clasificación
        clasificacion_prioridad = {
            "VIP": 3,
            "Alto Valor": 2,
            "Leal": 1,
            "Estable": 0,
            "En Desarrollo": -1
        }
        prioridad += clasificacion_prioridad.get(perfil['clasificacion'], 0)
        
        # Ajustar por días desde última compra
        dias_ultima_compra = perfil['dias_ultima_compra']
        if dias_ultima_compra > 90:
            prioridad += 2
        elif dias_ultima_compra > 60:
            prioridad += 1
        
        # Ajustar por puntualidad
        if perfil['puntualidad'] == "Excelente":
            prioridad += 1
        elif perfil['puntualidad'] == "Tardía":
            prioridad -= 1
        
        return max(1, min(10, prioridad))
    
    def _generar_resumen_clasificaciones(self, recomendaciones: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Genera resumen por clasificaciones de clientes"""
        clasificaciones = {}
        
        for rec in recomendaciones:
            clasificacion = rec['clasificacion']
            if clasificacion not in clasificaciones:
                clasificaciones[clasificacion] = {
                    "cantidad": 0,
                    "productos_comunes": [],
                    "estrategias": []
                }
            
            clasificaciones[clasificacion]["cantidad"] += 1
            clasificaciones[clasificacion]["estrategias"].append(rec['estrategia_precio'])
        
        # Calcular productos más comunes por clasificación
        for clasificacion in clasificaciones:
            productos_todos = []
            for rec in recomendaciones:
                if rec['clasificacion'] == clasificacion:
                    productos_todos.extend(rec['productos_principales'])
            
            # Contar productos más comunes
            productos_comunes = Counter(productos_todos).most_common(3)
            clasificaciones[clasificacion]["productos_comunes"] = [p[0] for p in productos_comunes]
        
        return clasificaciones

"""
Sistema de Pipeline de Ventas con Kanban
"""

import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

@dataclass
class Deal:
    """Representa una oportunidad de venta"""
    id: str
    cliente: str
    valor_estimado: float
    etapa: str
    probabilidad: int  # 0-100
    fecha_creacion: date
    fecha_cierre_estimada: Optional[date]
    contacto: str
    telefono: str
    email: str
    notas: str
    productos_interes: List[str]
    origen: str  # 'Llamada', 'Email', 'Referido', 'Web', etc.
    vendedor: str
    prioridad: str  # 'Alta', 'Media', 'Baja'
    siguiente_accion: str
    fecha_siguiente_accion: Optional[date]
    historial: List[Dict]  # Cambios de etapa, notas, etc.
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        data = asdict(self)
        # Convertir fechas a strings
        if self.fecha_creacion:
            data['fecha_creacion'] = self.fecha_creacion.isoformat()
        if self.fecha_cierre_estimada:
            data['fecha_cierre_estimada'] = self.fecha_cierre_estimada.isoformat()
        if self.fecha_siguiente_accion:
            data['fecha_siguiente_accion'] = self.fecha_siguiente_accion.isoformat()
        return data

class SalesPipeline:
    """Sistema de gestión de pipeline de ventas"""
    
    # Etapas del pipeline (personalizables)
    DEFAULT_STAGES = [
        {
            "id": "lead",
            "nombre": "Lead",
            "color": "#94a3b8",  # Slate
            "probabilidad": 10,
            "descripcion": "Contacto inicial, calificando"
        },
        {
            "id": "contactado",
            "nombre": "Contactado",
            "color": "#3b82f6",  # Blue
            "probabilidad": 25,
            "descripcion": "Primera comunicación establecida"
        },
        {
            "id": "reunion",
            "nombre": "Reunión Agendada",
            "color": "#8b5cf6",  # Violet
            "probabilidad": 40,
            "descripcion": "Reunión o presentación programada"
        },
        {
            "id": "propuesta",
            "nombre": "Propuesta Enviada",
            "color": "#f59e0b",  # Amber
            "probabilidad": 60,
            "descripcion": "Cotización o propuesta formal"
        },
        {
            "id": "negociacion",
            "nombre": "Negociación",
            "color": "#ec4899",  # Pink
            "probabilidad": 75,
            "descripcion": "Discutiendo términos y condiciones"
        },
        {
            "id": "ganada",
            "nombre": "Ganada",
            "color": "#10b981",  # Green
            "probabilidad": 100,
            "descripcion": "Venta cerrada exitosamente"
        },
        {
            "id": "perdida",
            "nombre": "Perdida",
            "color": "#ef4444",  # Red
            "probabilidad": 0,
            "descripcion": "Oportunidad perdida"
        }
    ]
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.deals: List[Deal] = []
        self.stages = self.DEFAULT_STAGES.copy()
    
    # ========================================
    # GESTIÓN DE DEALS
    # ========================================
    
    def create_deal(
        self,
        cliente: str,
        valor_estimado: float,
        contacto: str,
        telefono: str,
        email: str,
        productos_interes: List[str],
        origen: str,
        vendedor: str,
        prioridad: str = "Media",
        notas: str = "",
        fecha_cierre_estimada: Optional[date] = None
    ) -> Deal:
        """Crea una nueva oportunidad de venta"""
        
        deal_id = f"DEAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        deal = Deal(
            id=deal_id,
            cliente=cliente,
            valor_estimado=valor_estimado,
            etapa="lead",
            probabilidad=10,
            fecha_creacion=date.today(),
            fecha_cierre_estimada=fecha_cierre_estimada,
            contacto=contacto,
            telefono=telefono,
            email=email,
            notas=notas,
            productos_interes=productos_interes,
            origen=origen,
            vendedor=vendedor,
            prioridad=prioridad,
            siguiente_accion="Contactar cliente",
            fecha_siguiente_accion=date.today() + timedelta(days=1),
            historial=[{
                "fecha": datetime.now().isoformat(),
                "accion": "Creado",
                "etapa": "lead",
                "usuario": vendedor,
                "notas": "Oportunidad creada"
            }]
        )
        
        self.deals.append(deal)
        return deal
    
    def move_deal(self, deal_id: str, nueva_etapa: str, usuario: str, notas: str = "") -> bool:
        """Mueve un deal a una nueva etapa"""
        
        deal = self.get_deal_by_id(deal_id)
        if not deal:
            return False
        
        # Obtener info de la nueva etapa
        stage_info = next((s for s in self.stages if s["id"] == nueva_etapa), None)
        if not stage_info:
            return False
        
        etapa_anterior = deal.etapa
        
        # Actualizar deal
        deal.etapa = nueva_etapa
        deal.probabilidad = stage_info["probabilidad"]
        
        # Agregar al historial
        deal.historial.append({
            "fecha": datetime.now().isoformat(),
            "accion": "Cambio de etapa",
            "etapa_anterior": etapa_anterior,
            "etapa_nueva": nueva_etapa,
            "usuario": usuario,
            "notas": notas
        })
        
        return True
    
    def update_deal(self, deal_id: str, updates: Dict) -> bool:
        """Actualiza campos de un deal"""
        
        deal = self.get_deal_by_id(deal_id)
        if not deal:
            return False
        
        for key, value in updates.items():
            if hasattr(deal, key):
                setattr(deal, key, value)
        
        # Agregar al historial
        deal.historial.append({
            "fecha": datetime.now().isoformat(),
            "accion": "Actualización",
            "campos": list(updates.keys()),
            "notas": "Deal actualizado"
        })
        
        return True
    
    def delete_deal(self, deal_id: str) -> bool:
        """Elimina un deal"""
        deal = self.get_deal_by_id(deal_id)
        if deal:
            self.deals.remove(deal)
            return True
        return False
    
    def get_deal_by_id(self, deal_id: str) -> Optional[Deal]:
        """Obtiene un deal por ID"""
        return next((d for d in self.deals if d.id == deal_id), None)
    
    # ========================================
    # CONSULTAS Y FILTROS
    # ========================================
    
    def get_deals_by_stage(self, stage_id: str) -> List[Deal]:
        """Obtiene todos los deals de una etapa"""
        return [d for d in self.deals if d.etapa == stage_id]
    
    def get_deals_by_vendedor(self, vendedor: str) -> List[Deal]:
        """Obtiene todos los deals de un vendedor"""
        return [d for d in self.deals if d.vendedor == vendedor]
    
    def get_deals_by_prioridad(self, prioridad: str) -> List[Deal]:
        """Obtiene todos los deals de una prioridad"""
        return [d for d in self.deals if d.prioridad == prioridad]
    
    def get_active_deals(self) -> List[Deal]:
        """Obtiene deals activos (no ganados ni perdidos)"""
        return [d for d in self.deals if d.etapa not in ["ganada", "perdida"]]
    
    def get_closed_deals(self, ganadas: bool = True) -> List[Deal]:
        """Obtiene deals cerrados"""
        etapa = "ganada" if ganadas else "perdida"
        return [d for d in self.deals if d.etapa == etapa]
    
    def search_deals(self, query: str) -> List[Deal]:
        """Busca deals por cliente, contacto o notas"""
        query_lower = query.lower()
        return [
            d for d in self.deals
            if query_lower in d.cliente.lower() or
               query_lower in d.contacto.lower() or
               query_lower in d.notas.lower()
        ]
    
    # ========================================
    # MÉTRICAS Y ANÁLISIS
    # ========================================
    
    def get_pipeline_metrics(self) -> Dict[str, Any]:
        """Calcula métricas del pipeline"""
        
        active_deals = self.get_active_deals()
        ganadas = self.get_closed_deals(ganadas=True)
        perdidas = self.get_closed_deals(ganadas=False)
        
        # Valor total del pipeline
        valor_pipeline = sum(d.valor_estimado for d in active_deals)
        
        # Valor ponderado (valor * probabilidad)
        valor_ponderado = sum(
            d.valor_estimado * (d.probabilidad / 100)
            for d in active_deals
        )
        
        # Distribución por etapa
        distribucion_etapas = {}
        for stage in self.stages:
            deals_etapa = self.get_deals_by_stage(stage["id"])
            distribucion_etapas[stage["nombre"]] = {
                "cantidad": len(deals_etapa),
                "valor": sum(d.valor_estimado for d in deals_etapa)
            }
        
        # Tasa de conversión
        total_cerradas = len(ganadas) + len(perdidas)
        tasa_conversion = (len(ganadas) / total_cerradas * 100) if total_cerradas > 0 else 0
        
        # Valor promedio de deal
        avg_deal_value = (
            sum(d.valor_estimado for d in self.deals) / len(self.deals)
            if self.deals else 0
        )
        
        # Ciclo de venta promedio (días desde creación hasta cierre)
        ciclos = []
        for deal in ganadas:
            if deal.fecha_creacion:
                dias = (date.today() - deal.fecha_creacion).days
                ciclos.append(dias)
        
        ciclo_promedio = sum(ciclos) / len(ciclos) if ciclos else 0
        
        # Deals por prioridad
        por_prioridad = {
            "Alta": len([d for d in active_deals if d.prioridad == "Alta"]),
            "Media": len([d for d in active_deals if d.prioridad == "Media"]),
            "Baja": len([d for d in active_deals if d.prioridad == "Baja"])
        }
        
        return {
            "total_deals": len(self.deals),
            "deals_activos": len(active_deals),
            "deals_ganados": len(ganadas),
            "deals_perdidos": len(perdidas),
            "valor_pipeline": valor_pipeline,
            "valor_ponderado": valor_ponderado,
            "tasa_conversion": tasa_conversion,
            "avg_deal_value": avg_deal_value,
            "ciclo_promedio_dias": ciclo_promedio,
            "distribucion_etapas": distribucion_etapas,
            "por_prioridad": por_prioridad
        }
    
    def get_deals_urgentes(self) -> List[Deal]:
        """Obtiene deals que requieren atención urgente"""
        hoy = date.today()
        urgentes = []
        
        for deal in self.get_active_deals():
            # Deals con acción vencida
            if deal.fecha_siguiente_accion and deal.fecha_siguiente_accion < hoy:
                urgentes.append(deal)
            # Deals de alta prioridad en etapas avanzadas
            elif deal.prioridad == "Alta" and deal.etapa in ["propuesta", "negociacion"]:
                urgentes.append(deal)
            # Deals con cierre próximo
            elif deal.fecha_cierre_estimada and (deal.fecha_cierre_estimada - hoy).days <= 7:
                urgentes.append(deal)
        
        return urgentes
    
    def get_forecast(self, meses: int = 1) -> Dict[str, Any]:
        """Genera pronóstico de ventas"""
        
        fecha_limite = date.today() + timedelta(days=meses * 30)
        
        # Deals que cierran en el período
        deals_forecast = [
            d for d in self.get_active_deals()
            if d.fecha_cierre_estimada and d.fecha_cierre_estimada <= fecha_limite
        ]
        
        # Valor esperado (ponderado por probabilidad)
        valor_esperado = sum(
            d.valor_estimado * (d.probabilidad / 100)
            for d in deals_forecast
        )
        
        # Valor best case (todos se ganan)
        valor_best_case = sum(d.valor_estimado for d in deals_forecast)
        
        # Valor worst case (aplicar tasa de conversión histórica)
        metrics = self.get_pipeline_metrics()
        tasa_conversion = metrics["tasa_conversion"] / 100 if metrics["tasa_conversion"] > 0 else 0.5
        valor_worst_case = valor_best_case * tasa_conversion
        
        return {
            "periodo_meses": meses,
            "deals_count": len(deals_forecast),
            "valor_esperado": valor_esperado,
            "valor_best_case": valor_best_case,
            "valor_worst_case": valor_worst_case,
            "confianza": "Alta" if len(deals_forecast) > 10 else "Media" if len(deals_forecast) > 5 else "Baja"
        }
    
    # ========================================
    # PERSISTENCIA
    # ========================================
    
    def export_to_dict(self) -> Dict:
        """Exporta todos los deals a diccionario"""
        return {
            "deals": [d.to_dict() for d in self.deals],
            "stages": self.stages,
            "export_date": datetime.now().isoformat()
        }
    
    def export_to_json(self, filename: str) -> bool:
        """Exporta el pipeline a JSON"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.export_to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exportando: {e}")
            return False
    
    def import_from_json(self, filename: str) -> bool:
        """Importa el pipeline desde JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Importar deals
            self.deals = []
            for deal_data in data.get("deals", []):
                # Convertir strings a fechas
                if deal_data.get('fecha_creacion'):
                    deal_data['fecha_creacion'] = date.fromisoformat(deal_data['fecha_creacion'])
                if deal_data.get('fecha_cierre_estimada'):
                    deal_data['fecha_cierre_estimada'] = date.fromisoformat(deal_data['fecha_cierre_estimada'])
                if deal_data.get('fecha_siguiente_accion'):
                    deal_data['fecha_siguiente_accion'] = date.fromisoformat(deal_data['fecha_siguiente_accion'])
                
                deal = Deal(**deal_data)
                self.deals.append(deal)
            
            # Importar stages si existen
            if "stages" in data:
                self.stages = data["stages"]
            
            return True
        except Exception as e:
            print(f"Error importando: {e}")
            return False
    
    # ========================================
    # REPORTES
    # ========================================
    
    def generate_activity_report(self, dias: int = 30) -> Dict:
        """Genera reporte de actividad"""
        
        fecha_inicio = date.today() - timedelta(days=dias)
        
        actividades = []
        for deal in self.deals:
            for evento in deal.historial:
                fecha_evento = datetime.fromisoformat(evento["fecha"]).date()
                if fecha_evento >= fecha_inicio:
                    actividades.append({
                        "fecha": fecha_evento,
                        "deal_id": deal.id,
                        "cliente": deal.cliente,
                        "accion": evento["accion"],
                        "usuario": evento.get("usuario", "N/A")
                    })
        
        # Ordenar por fecha
        actividades.sort(key=lambda x: x["fecha"], reverse=True)
        
        return {
            "periodo_dias": dias,
            "total_actividades": len(actividades),
            "actividades": actividades[:50]  # Últimas 50
        }
    
    def generate_vendedor_report(self) -> Dict:
        """Genera reporte por vendedor"""
        
        vendedores = {}
        
        for deal in self.deals:
            if deal.vendedor not in vendedores:
                vendedores[deal.vendedor] = {
                    "total_deals": 0,
                    "deals_activos": 0,
                    "deals_ganados": 0,
                    "deals_perdidos": 0,
                    "valor_total": 0,
                    "valor_ganado": 0
                }
            
            v = vendedores[deal.vendedor]
            v["total_deals"] += 1
            v["valor_total"] += deal.valor_estimado
            
            if deal.etapa == "ganada":
                v["deals_ganados"] += 1
                v["valor_ganado"] += deal.valor_estimado
            elif deal.etapa == "perdida":
                v["deals_perdidos"] += 1
            else:
                v["deals_activos"] += 1
        
        # Calcular tasas de conversión
        for v_data in vendedores.values():
            total_cerrados = v_data["deals_ganados"] + v_data["deals_perdidos"]
            v_data["tasa_conversion"] = (
                v_data["deals_ganados"] / total_cerrados * 100
                if total_cerrados > 0 else 0
            )
        
        return vendedores


import pandas as pd
from datetime import datetime, timedelta
from supabase import Client
from typing import Dict, List, Any
import streamlit as st


class ClientAnalytics:
    """Analytics avanzado de clientes B2B"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    def ranking_clientes(self, periodo_meses: int = 12) -> pd.DataFrame:
        """Genera ranking de mejores clientes"""
        try:
            # Obtener todas las compras del período
            fecha_limite = datetime.now() - timedelta(days=periodo_meses * 30)
            
            compras_response = self.supabase.table("compras_clientes").select(
                "nit_cliente, total, fecha, es_devolucion"
            ).gte("fecha", fecha_limite.isoformat()).execute()
            
            if not compras_response.data:
                return pd.DataFrame()
            
            df = pd.DataFrame(compras_response.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Filtrar solo compras (excluir devoluciones)
            df_compras = df[df.get('es_devolucion', False) == False].copy()
            
            if df_compras.empty:
                return pd.DataFrame()
            
            # Obtener datos de clientes
            clientes_response = self.supabase.table("clientes_b2b").select("*").execute()
            df_clientes = pd.DataFrame(clientes_response.data) if clientes_response.data else pd.DataFrame()
            
            # Agrupar por cliente
            ranking = df_compras.groupby('nit_cliente').agg({
                'total': ['sum', 'count', 'mean'],
                'fecha': ['min', 'max']
            }).reset_index()
            
            ranking.columns = ['nit_cliente', 'total_compras', 'num_transacciones', 'ticket_promedio', 'primera_compra', 'ultima_compra']
            
            # Calcular días desde última compra
            ranking['dias_sin_comprar'] = (datetime.now() - pd.to_datetime(ranking['ultima_compra'])).dt.days
            
            # Merge con datos de clientes
            if not df_clientes.empty:
                ranking = ranking.merge(
                    df_clientes[['nit', 'nombre', 'ciudad', 'cupo_total', 'cupo_utilizado', 'plazo_pago']],
                    left_on='nit_cliente',
                    right_on='nit',
                    how='left'
                )
            
            # Calcular métricas adicionales
            ranking['cupo_disponible'] = ranking['cupo_total'] - ranking['cupo_utilizado']
            ranking['uso_cupo_pct'] = (ranking['cupo_utilizado'] / ranking['cupo_total'] * 100).fillna(0)
            ranking['frecuencia_mensual'] = ranking['num_transacciones'] / periodo_meses
            
            # Ordenar por total de compras
            ranking = ranking.sort_values('total_compras', ascending=False)
            
            return ranking
            
        except Exception as e:
            return pd.DataFrame()
    
    def _obtener_codigos_dane_coordenadas(self) -> Dict[str, Dict[str, Any]]:
        """Retorna diccionario completo de ciudades colombianas con código DANE y coordenadas"""
        return {
            # Capitales de departamento y ciudades principales
            'Bogotá': {'codigo_dane': '11001', 'lat': 4.7110, 'lon': -74.0721, 'departamento': 'Cundinamarca'},
            'Bogota': {'codigo_dane': '11001', 'lat': 4.7110, 'lon': -74.0721, 'departamento': 'Cundinamarca'},
            'Medellín': {'codigo_dane': '05001', 'lat': 6.2476, 'lon': -75.5658, 'departamento': 'Antioquia'},
            'Medellin': {'codigo_dane': '05001', 'lat': 6.2476, 'lon': -75.5658, 'departamento': 'Antioquia'},
            'Cali': {'codigo_dane': '76001', 'lat': 3.4516, 'lon': -76.5320, 'departamento': 'Valle del Cauca'},
            'Barranquilla': {'codigo_dane': '08001', 'lat': 10.9639, 'lon': -74.7964, 'departamento': 'Atlántico'},
            'Cartagena': {'codigo_dane': '13001', 'lat': 10.3910, 'lon': -75.4794, 'departamento': 'Bolívar'},
            'Bucaramanga': {'codigo_dane': '68001', 'lat': 7.1254, 'lon': -73.1198, 'departamento': 'Santander'},
            'Pereira': {'codigo_dane': '66001', 'lat': 4.8133, 'lon': -75.6961, 'departamento': 'Risaralda'},
            'Santa Marta': {'codigo_dane': '47001', 'lat': 11.2408, 'lon': -74.1990, 'departamento': 'Magdalena'},
            'Manizales': {'codigo_dane': '17001', 'lat': 5.0700, 'lon': -75.5138, 'departamento': 'Caldas'},
            'Armenia': {'codigo_dane': '63001', 'lat': 4.5339, 'lon': -75.6811, 'departamento': 'Quindío'},
            'Villavicencio': {'codigo_dane': '50001', 'lat': 4.1533, 'lon': -73.6350, 'departamento': 'Meta'},
            'Ibagué': {'codigo_dane': '73001', 'lat': 4.4447, 'lon': -75.2322, 'departamento': 'Tolima'},
            'Ibague': {'codigo_dane': '73001', 'lat': 4.4447, 'lon': -75.2322, 'departamento': 'Tolima'},
            'Pasto': {'codigo_dane': '52001', 'lat': 1.2136, 'lon': -77.2811, 'departamento': 'Nariño'},
            'Valledupar': {'codigo_dane': '20001', 'lat': 10.4631, 'lon': -73.2532, 'departamento': 'Cesar'},
            'Montería': {'codigo_dane': '23001', 'lat': 8.7500, 'lon': -75.8833, 'departamento': 'Córdoba'},
            'Sincelejo': {'codigo_dane': '70001', 'lat': 9.3047, 'lon': -75.3978, 'departamento': 'Sucre'},
            'Tunja': {'codigo_dane': '15001', 'lat': 5.5353, 'lon': -73.3678, 'departamento': 'Boyacá'},
            'Neiva': {'codigo_dane': '41001', 'lat': 2.5353, 'lon': -75.5277, 'departamento': 'Huila'},
            'Popayán': {'codigo_dane': '19001', 'lat': 2.4448, 'lon': -76.6147, 'departamento': 'Cauca'},
            'Popayan': {'codigo_dane': '19001', 'lat': 2.4448, 'lon': -76.6147, 'departamento': 'Cauca'},
            'Riohacha': {'codigo_dane': '44001', 'lat': 11.5444, 'lon': -72.9072, 'departamento': 'La Guajira'},
            'Quibdó': {'codigo_dane': '27001', 'lat': 5.6947, 'lon': -76.6611, 'departamento': 'Chocó'},
            'Quibdo': {'codigo_dane': '27001', 'lat': 5.6947, 'lon': -76.6611, 'departamento': 'Chocó'},
            'Florencia': {'codigo_dane': '18001', 'lat': 1.6142, 'lon': -75.6062, 'departamento': 'Caquetá'},
            'Yopal': {'codigo_dane': '85001', 'lat': 5.3378, 'lon': -72.3958, 'departamento': 'Casanare'},
            'Mocoa': {'codigo_dane': '86001', 'lat': 1.1528, 'lon': -76.6519, 'departamento': 'Putumayo'},
            'Leticia': {'codigo_dane': '91001', 'lat': -4.2153, 'lon': -69.9406, 'departamento': 'Amazonas'},
            'Inírida': {'codigo_dane': '94001', 'lat': 3.8653, 'lon': -67.9239, 'departamento': 'Guainía'},
            'Inirida': {'codigo_dane': '94001', 'lat': 3.8653, 'lon': -67.9239, 'departamento': 'Guainía'},
            'San José del Guaviare': {'codigo_dane': '95001', 'lat': 2.5683, 'lon': -72.6383, 'departamento': 'Guaviare'},
            'Mitú': {'codigo_dane': '97001', 'lat': 1.1983, 'lon': -70.1733, 'departamento': 'Vaupés'},
            'Puerto Carreño': {'codigo_dane': '99001', 'lat': 6.1847, 'lon': -67.4881, 'departamento': 'Vichada'},
            # Ciudades adicionales comunes
            'Bello': {'codigo_dane': '05088', 'lat': 6.3389, 'lon': -75.5621, 'departamento': 'Antioquia'},
            'Itagüí': {'codigo_dane': '05360', 'lat': 6.1845, 'lon': -75.5991, 'departamento': 'Antioquia'},
            'Palmira': {'codigo_dane': '76520', 'lat': 3.5394, 'lon': -76.3036, 'departamento': 'Valle del Cauca'},
            'Buenaventura': {'codigo_dane': '76109', 'lat': 3.8801, 'lon': -77.0197, 'departamento': 'Valle del Cauca'},
            'Carepa': {'codigo_dane': '05154', 'lat': 7.7583, 'lon': -76.6633, 'departamento': 'Antioquia'},
            'Corozal': {'codigo_dane': '70221', 'lat': 9.3178, 'lon': -75.2939, 'departamento': 'Sucre'},
        }
    
    def distribucion_geografica(self, periodo: str = "historico", fecha_inicio: str = None, fecha_fin: str = None) -> Dict[str, Any]:
        """Analiza la distribución geográfica de clientes
        
        Args:
            periodo: "historico" para todo el historial, "mes_actual" para solo el mes actual, "personalizado" para fechas específicas
            fecha_inicio: Fecha inicio (YYYY-MM-DD) si periodo es "personalizado"
            fecha_fin: Fecha fin (YYYY-MM-DD) si periodo es "personalizado"
        """
        try:
            # Obtener todos los clientes
            clientes_response = self.supabase.table("clientes_b2b").select("*").eq("activo", True).execute()
            df_clientes = pd.DataFrame(clientes_response.data) if clientes_response.data else pd.DataFrame()
            
            if df_clientes.empty:
                return {"error": "No hay clientes registrados"}
            
            # Obtener compras por cliente con filtro de fecha
            compras_query = self.supabase.table("compras_clientes").select(
                "nit_cliente, total, es_devolucion, fecha"
            )
            
            # Aplicar filtros de fecha según el período
            if periodo == "mes_actual":
                hoy = datetime.now()
                primer_dia_mes = hoy.replace(day=1).strftime('%Y-%m-%d')
                compras_query = compras_query.gte('fecha', primer_dia_mes)
            elif periodo == "personalizado" and fecha_inicio and fecha_fin:
                compras_query = compras_query.gte('fecha', fecha_inicio).lte('fecha', fecha_fin)
            # Si es "historico", no aplicamos filtro de fecha
            
            compras_response = compras_query.execute()
            df_compras = pd.DataFrame(compras_response.data) if compras_response.data else pd.DataFrame()
            
            # Filtrar solo compras (no devoluciones)
            if not df_compras.empty:
                df_compras = df_compras[df_compras.get('es_devolucion', False) == False]
                compras_por_cliente = df_compras.groupby('nit_cliente')['total'].sum().reset_index()
                compras_por_cliente.columns = ['nit', 'total_compras']
                
                df_clientes = df_clientes.merge(compras_por_cliente, on='nit', how='left')
                df_clientes['total_compras'] = df_clientes['total_compras'].fillna(0)
            else:
                df_clientes['total_compras'] = 0
            
            # Agrupar por ciudad
            por_ciudad = df_clientes.groupby('ciudad').agg({
                'nit': 'count',
                'total_compras': 'sum',
                'cupo_total': 'sum',
                'cupo_utilizado': 'sum'
            }).reset_index()
            
            por_ciudad.columns = ['ciudad', 'num_clientes', 'total_compras', 'cupo_total', 'cupo_utilizado']
            por_ciudad = por_ciudad.sort_values('total_compras', ascending=False)
            
            # Obtener códigos DANE y coordenadas
            codigos_dane = self._obtener_codigos_dane_coordenadas()
            
            # Agregar coordenadas y código DANE
            def obtener_datos_geograficos(ciudad):
                ciudad_clean = ciudad.strip() if pd.notna(ciudad) else ''
                # Buscar coincidencia exacta o parcial
                for key, datos in codigos_dane.items():
                    if key.lower() in ciudad_clean.lower() or ciudad_clean.lower() in key.lower():
                        return {
                            'codigo_dane': datos['codigo_dane'],
                            'lat': datos['lat'],
                            'lon': datos['lon'],
                            'departamento': datos['departamento']
                        }
                return {'codigo_dane': None, 'lat': None, 'lon': None, 'departamento': None}
            
            datos_geo = por_ciudad['ciudad'].apply(obtener_datos_geograficos)
            por_ciudad['codigo_dane'] = datos_geo.apply(lambda x: x.get('codigo_dane'))
            por_ciudad['lat'] = datos_geo.apply(lambda x: x.get('lat'))
            por_ciudad['lon'] = datos_geo.apply(lambda x: x.get('lon'))
            por_ciudad['departamento'] = datos_geo.apply(lambda x: x.get('departamento'))
            
            # Datos para el mapa
            datos_mapa = por_ciudad[por_ciudad['lat'].notna()].copy()
            
            return {
                "por_ciudad": por_ciudad.to_dict('records'),
                "datos_mapa": datos_mapa.to_dict('records'),
                "total_ciudades": len(por_ciudad),
                "ciudades_con_coordenadas": len(datos_mapa),
                "total_clientes": len(df_clientes),
                "clientes_por_ciudad": df_clientes.groupby('ciudad').size().to_dict(),
                "periodo": periodo
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def segmentar_por_presupuesto(self) -> Dict[str, Any]:
        """Segmenta clientes por nivel de presupuesto/compras"""
        try:
            # Obtener ranking de clientes
            ranking = self.ranking_clientes(12)
            
            if ranking.empty:
                return {"error": "No hay datos de clientes"}
            
            # Definir segmentos
            total_compras = ranking['total_compras'].sum()
            
            # Segmentación por percentiles
            p75 = ranking['total_compras'].quantile(0.75)
            p50 = ranking['total_compras'].quantile(0.50)
            p25 = ranking['total_compras'].quantile(0.25)
            
            def asignar_segmento(total):
                if total >= p75:
                    return "A - Premium"
                elif total >= p50:
                    return "B - Alto"
                elif total >= p25:
                    return "C - Medio"
                else:
                    return "D - Básico"
            
            ranking['segmento'] = ranking['total_compras'].apply(asignar_segmento)
            
            # Resumen por segmento
            resumen_segmentos = ranking.groupby('segmento').agg({
                'nit': 'count',
                'total_compras': 'sum',
                'cupo_total': 'sum',
                'cupo_utilizado': 'sum'
            }).reset_index()
            
            resumen_segmentos.columns = ['segmento', 'num_clientes', 'total_compras', 'cupo_total', 'cupo_utilizado']
            resumen_segmentos['pct_total'] = (resumen_segmentos['total_compras'] / total_compras * 100).round(2)
            
            # Recomendaciones de asignación de recursos
            recomendaciones = []
            
            segmento_a = ranking[ranking['segmento'] == 'A - Premium']
            if not segmento_a.empty:
                recomendaciones.append({
                    "segmento": "A - Premium",
                    "recomendacion": f"Asignar vendedor senior o gerente de cuenta. {len(segmento_a)} clientes generan {segmento_a['total_compras'].sum() / total_compras * 100:.1f}% de las ventas",
                    "prioridad": "ALTA"
                })
            
            segmento_b = ranking[ranking['segmento'] == 'B - Alto']
            if not segmento_b.empty:
                recomendaciones.append({
                    "segmento": "B - Alto",
                    "recomendacion": f"Vendedor dedicado. Potencial de crecimiento alto",
                    "prioridad": "MEDIA-ALTA"
                })
            
            return {
                "ranking": ranking.to_dict('records'),
                "resumen_segmentos": resumen_segmentos.to_dict('records'),
                "recomendaciones": recomendaciones,
                "total_clientes": len(ranking),
                "total_compras": total_compras
            }
            
        except Exception as e:
            return {"error": str(e)}

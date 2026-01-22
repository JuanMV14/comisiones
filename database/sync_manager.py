import pandas as pd
from datetime import datetime, timedelta
from supabase import Client
import streamlit as st
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher


class SyncManager:
    """Gestor de sincronización entre compras de clientes y facturas/comisiones"""
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
    
    def analizar_sincronizacion(self) -> Dict[str, Any]:
        """Analiza qué compras pueden sincronizarse con qué facturas"""
        try:
            # Cargar compras de clientes
            compras_response = self.supabase.table("compras_clientes").select("*").execute()
            df_compras = pd.DataFrame(compras_response.data) if compras_response.data else pd.DataFrame()
            
            # Cargar facturas/comisiones
            facturas_response = self.supabase.table("comisiones").select("*").execute()
            df_facturas = pd.DataFrame(facturas_response.data) if facturas_response.data else pd.DataFrame()
            
            if df_compras.empty or df_facturas.empty:
                return {
                    "error": "No hay datos suficientes para sincronizar",
                    "compras": len(df_compras),
                    "facturas": len(df_facturas)
                }
            
            # Convertir fechas
            df_compras['fecha'] = pd.to_datetime(df_compras['fecha'])
            df_facturas['fecha_factura'] = pd.to_datetime(df_facturas['fecha_factura'])
            
            # Filtrar solo compras (excluir devoluciones)
            df_compras_solo = df_compras[df_compras.get('es_devolucion', False) == False].copy()
            
            if df_compras_solo.empty:
                return {
                    "error": "No hay compras para sincronizar (solo devoluciones)",
                    "compras": len(df_compras),
                    "facturas": len(df_facturas)
                }
            
            # Agrupar compras por documento (solo compras, no devoluciones)
            compras_por_doc = df_compras_solo.groupby(['nit_cliente', 'num_documento']).agg({
                'total': 'sum',
                'fecha': 'first',
                'cantidad': 'sum'
            }).reset_index()
            
            # Preparar facturas
            df_facturas['cliente_normalizado'] = df_facturas['cliente'].str.upper().str.strip()
            
            # Buscar coincidencias
            coincidencias_automaticas = []
            coincidencias_posibles = []
            sin_coincidencia = []
            
            for _, compra in compras_por_doc.iterrows():
                nit = compra['nit_cliente']
                num_doc = str(compra['num_documento'])
                total_compra = compra['total']
                fecha_compra = compra['fecha']
                
                # Buscar cliente por NIT en tabla de clientes B2B
                cliente_b2b = self.supabase.table("clientes_b2b").select("nombre").eq("nit", nit).execute()
                nombre_cliente_b2b = cliente_b2b.data[0]['nombre'] if cliente_b2b.data else None
                
                # Buscar facturas que coincidan
                # 1. Por número de factura exacto
                facturas_exactas = df_facturas[
                    (df_facturas['factura'].astype(str).str.contains(num_doc, na=False)) |
                    (df_facturas['pedido'].astype(str).str.contains(num_doc, na=False))
                ]
                
                # 2. Por cliente y fecha similar
                if nombre_cliente_b2b:
                    facturas_cliente = df_facturas[
                        df_facturas['cliente_normalizado'].str.contains(nombre_cliente_b2b.upper()[:10], na=False)
                    ]
                else:
                    facturas_cliente = pd.DataFrame()
                
                # 3. Por fecha cercana (±7 días) y monto similar (±10%)
                fecha_inicio = fecha_compra - timedelta(days=7)
                fecha_fin = fecha_compra + timedelta(days=7)
                
                facturas_fecha = df_facturas[
                    (df_facturas['fecha_factura'] >= fecha_inicio) &
                    (df_facturas['fecha_factura'] <= fecha_fin)
                ]
                
                # Combinar todas las búsquedas
                facturas_candidatas = pd.concat([
                    facturas_exactas,
                    facturas_cliente,
                    facturas_fecha
                ]).drop_duplicates(subset=['id'])
                
                # Filtrar por monto similar
                if not facturas_candidatas.empty:
                    facturas_candidatas = facturas_candidatas[
                        (facturas_candidatas['valor'] >= total_compra * 0.9) &
                        (facturas_candidatas['valor'] <= total_compra * 1.1)
                    ]
                
                if not facturas_candidatas.empty:
                    # Coincidencia automática si hay una sola factura muy similar
                    mejor_coincidencia = None
                    mejor_score = 0
                    
                    for _, factura in facturas_candidatas.iterrows():
                        score = self._calcular_score_coincidencia(compra, factura, nombre_cliente_b2b)
                        if score > mejor_score:
                            mejor_score = score
                            mejor_coincidencia = factura
                    
                    if mejor_score >= 0.8:  # Coincidencia alta
                        coincidencias_automaticas.append({
                            'compra': compra.to_dict(),
                            'factura': mejor_coincidencia.to_dict(),
                            'score': mejor_score,
                            'tipo': 'automatica'
                        })
                    elif mejor_score >= 0.5:  # Coincidencia posible
                        coincidencias_posibles.append({
                            'compra': compra.to_dict(),
                            'factura': mejor_coincidencia.to_dict(),
                            'score': mejor_score,
                            'tipo': 'posible'
                        })
                    else:
                        sin_coincidencia.append({
                            'compra': compra.to_dict(),
                            'facturas_candidatas': facturas_candidatas.to_dict('records')
                        })
                else:
                    sin_coincidencia.append({
                        'compra': compra.to_dict(),
                        'facturas_candidatas': []
                    })
            
            return {
                "total_compras": len(compras_por_doc),
                "total_facturas": len(df_facturas),
                "coincidencias_automaticas": len(coincidencias_automaticas),
                "coincidencias_posibles": len(coincidencias_posibles),
                "sin_coincidencia": len(sin_coincidencia),
                "detalle_automaticas": coincidencias_automaticas,
                "detalle_posibles": coincidencias_posibles,
                "detalle_sin_coincidencia": sin_coincidencia[:20]  # Primeras 20
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _calcular_score_coincidencia(self, compra: pd.Series, factura: pd.Series, nombre_cliente: Optional[str]) -> float:
        """Calcula un score de coincidencia entre compra y factura (0-1)"""
        score = 0.0
        
        # 1. Coincidencia de número de documento (40%)
        num_doc_compra = str(compra['num_documento'])
        if num_doc_compra in str(factura.get('factura', '')) or num_doc_compra in str(factura.get('pedido', '')):
            score += 0.4
        
        # 2. Coincidencia de monto (30%)
        total_compra = compra['total']
        valor_factura = factura.get('valor', 0)
        if valor_factura > 0:
            diferencia_pct = abs(total_compra - valor_factura) / valor_factura
            if diferencia_pct <= 0.05:  # ±5%
                score += 0.3
            elif diferencia_pct <= 0.10:  # ±10%
                score += 0.2
            elif diferencia_pct <= 0.20:  # ±20%
                score += 0.1
        
        # 3. Coincidencia de fecha (20%)
        fecha_compra = pd.to_datetime(compra['fecha'])
        fecha_factura = pd.to_datetime(factura.get('fecha_factura'))
        if pd.notna(fecha_factura):
            dias_diferencia = abs((fecha_compra - fecha_factura).days)
            if dias_diferencia == 0:
                score += 0.2
            elif dias_diferencia <= 3:
                score += 0.15
            elif dias_diferencia <= 7:
                score += 0.1
        
        # 4. Coincidencia de nombre de cliente (10%)
        if nombre_cliente:
            nombre_factura = str(factura.get('cliente', '')).upper()
            nombre_cliente_upper = nombre_cliente.upper()
            similarity = SequenceMatcher(None, nombre_cliente_upper, nombre_factura).ratio()
            score += similarity * 0.1
        
        return min(score, 1.0)
    
    def sincronizar_automaticas(self, coincidencias: List[Dict]) -> Dict[str, Any]:
        """
        Sincroniza las coincidencias automáticas
        
        IMPORTANTE: Vincula TODOS los productos de una compra (mismo num_documento)
        a la factura correspondiente
        """
        try:
            sincronizadas = 0
            productos_vinculados = 0
            errores = 0
            
            for coincidencia in coincidencias:
                try:
                    compra = coincidencia['compra']
                    factura = coincidencia['factura']
                    nit_cliente = compra['nit_cliente']
                    num_documento = compra['num_documento']
                    factura_id = factura['id']
                    
                    # IMPORTANTE: Buscar TODAS las compras con el mismo num_documento
                    # Esto incluye todos los productos de esa factura
                    compras_response = self.supabase.table("compras_clientes").select("*").eq(
                        "nit_cliente", nit_cliente
                    ).eq("num_documento", str(num_documento)).execute()
                    
                    if not compras_response.data:
                        errores += 1
                        continue
                    
                    # Vincular TODOS los productos de esta compra a la factura
                    compra_ids = []
                    for compra_item in compras_response.data:
                        compra_item_id = compra_item['id']
                        
                        # Actualizar cada producto/compra con referencia a factura
                        update_result = self.supabase.table("compras_clientes").update({
                            'factura_id': factura_id,
                            'sincronizado': True,
                            'fecha_sincronizacion': datetime.now().isoformat()
                        }).eq("id", compra_item_id).execute()
                        
                        if update_result.data:
                            compra_ids.append(compra_item_id)
                            productos_vinculados += 1
                    
                    if compra_ids:
                        # Actualizar factura con referencia a la primera compra
                        primera_compra_id = compra_ids[0]
                        self.supabase.table("comisiones").update({
                            'compra_cliente_id': primera_compra_id,
                            'sincronizado_compras': True
                        }).eq("id", factura_id).execute()
                        
                        sincronizadas += 1
                        print(f"✓ Vinculados {len(compra_ids)} productos de documento {num_documento} a factura {factura_id}")
                    else:
                        errores += 1
                    
                except Exception as e:
                    errores += 1
                    print(f"✗ Error sincronizando: {str(e)}")
                    continue
            
            return {
                "success": True,
                "facturas_sincronizadas": sincronizadas,
                "productos_vinculados": productos_vinculados,
                "errores": errores
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def sincronizar_todas_automaticas(self) -> Dict[str, Any]:
        """
        Busca y sincroniza automáticamente TODAS las compras que puedan relacionarse con facturas
        
        Proceso:
        1. Busca compras sin sincronizar
        2. Para cada compra, busca factura que coincida
        3. Si encuentra coincidencia alta (score >= 0.8), las vincula
        4. Vincula TODOS los productos de esa compra a la factura
        5. Si no encuentra coincidencia, no hace nada
        """
        try:
            # Analizar sincronización
            analisis = self.analizar_sincronizacion()
            
            if "error" in analisis:
                return {"error": analisis['error']}
            
            # Obtener coincidencias automáticas
            coincidencias_automaticas = analisis.get("detalle_automaticas", [])
            
            if not coincidencias_automaticas:
                return {
                    "success": True,
                    "mensaje": "No se encontraron coincidencias automáticas para sincronizar",
                    "facturas_sincronizadas": 0,
                    "productos_vinculados": 0
                }
            
            # Sincronizar todas las automáticas
            resultado = self.sincronizar_automaticas(coincidencias_automaticas)
            
            return resultado
            
        except Exception as e:
            return {"error": str(e)}
    
    def sincronizar_manual(self, compra_id: str, factura_id: int) -> Dict[str, Any]:
        """Sincroniza manualmente una compra con una factura"""
        try:
            # Obtener datos
            compra_response = self.supabase.table("compras_clientes").select("*").eq("id", compra_id).execute()
            factura_response = self.supabase.table("comisiones").select("*").eq("id", factura_id).execute()
            
            if not compra_response.data or not factura_response.data:
                return {"error": "Compra o factura no encontrada"}
            
            compra = compra_response.data[0]
            factura = factura_response.data[0]
            
            # Actualizar compra
            self.supabase.table("compras_clientes").update({
                'factura_id': factura_id,
                'sincronizado': True,
                'fecha_sincronizacion': datetime.now().isoformat()
            }).eq("id", compra_id).execute()
            
            # Actualizar factura
            self.supabase.table("comisiones").update({
                'compra_cliente_id': compra_id,
                'sincronizado_compras': True
            }).eq("id", factura_id).execute()
            
            st.cache_data.clear()
            
            return {"success": True, "mensaje": "Sincronización manual exitosa"}
            
        except Exception as e:
            return {"error": str(e)}

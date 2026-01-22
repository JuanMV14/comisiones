import streamlit as st
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
from business.client_product_recommendations import ClientProductRecommendations
from database.catalog_manager import CatalogManager
from utils.formatting import format_currency

class ClientRecommendationsUI:
    """Componente UI para mostrar recomendaciones de productos a clientes"""
    
    def __init__(self, recommendation_system: ClientProductRecommendations, catalog_manager: CatalogManager = None):
        self.recommendation_system = recommendation_system
        self.catalog_manager = catalog_manager
    
    def render_recommendations_dashboard(self):
        """Renderiza el dashboard completo de recomendaciones"""
        st.header("🎯 Sugerencias de Productos para Clientes")
        st.markdown("---")
        
        # Sección de carga de inventario
        self._render_inventario_upload()
        
        st.markdown("---")
        
        # Si hay inventario cargado, mostrar recomendaciones
        if self.recommendation_system.inventario_df is not None and not self.recommendation_system.inventario_df.empty:
            # Botón para generar recomendaciones
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔄 Generar Recomendaciones", type="primary", use_container_width=True):
                    with st.spinner("Analizando historial de compras y generando recomendaciones..."):
                        resultado = self.recommendation_system.generar_recomendaciones_clientes()
                        
                        if "error" in resultado:
                            st.error(f"❌ {resultado['error']}")
                        else:
                            st.session_state['recomendaciones'] = resultado
                            st.success(f"✅ {resultado['total_recomendaciones']} recomendaciones generadas para {resultado['total_clientes']} clientes")
                            st.rerun()
            
            # Mostrar recomendaciones si existen
            if 'recomendaciones' in st.session_state:
                self._render_recomendaciones_filtradas(st.session_state['recomendaciones'])
        else:
            st.info("📋 Por favor, carga primero el CSV de inventario para generar recomendaciones")
    
    def _render_inventario_upload(self):
        """Renderiza la sección de carga de inventario"""
        st.markdown("### 📦 Cargar Catálogo de Inventario")
        
        # Opción 1: Cargar desde base de datos (preferido)
        if self.catalog_manager:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.info("💡 **Recomendado:** Usar el catálogo de la base de datos (más actualizado)")
            with col2:
                if st.button("📥 Cargar desde BD", type="primary", use_container_width=True):
                    with st.spinner("Cargando inventario desde base de datos..."):
                        resultado = self.recommendation_system.cargar_inventario_desde_bd(self.catalog_manager)
                        
                        if "error" in resultado:
                            st.error(f"❌ {resultado['error']}")
                        else:
                            st.success(f"✅ Inventario cargado: {resultado['total_referencias']} referencias")
                            st.info(f"📋 Columnas disponibles: {', '.join(resultado['columnas_disponibles'])}")
                            # Limpiar recomendaciones anteriores
                            if 'recomendaciones' in st.session_state:
                                del st.session_state['recomendaciones']
                            st.rerun()
        
        st.markdown("---")
        st.markdown("### O cargar desde CSV (método alternativo)")
        
        # Opción 2: Cargar desde CSV (método legacy)
        uploaded_file = st.file_uploader(
            "Selecciona el archivo CSV con todas las referencias de inventario",
            type=['csv'],
            help="El CSV debe contener al menos una columna 'referencia'. Puede incluir también 'categoria', 'descripcion', 'nombre', etc."
        )
        
        if uploaded_file is not None:
            # Mostrar información del archivo
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📄 Archivo: {uploaded_file.name}")
            
            # Cargar inventario
            if st.button("📥 Cargar Inventario CSV", type="secondary"):
                with st.spinner("Cargando inventario..."):
                    resultado = self.recommendation_system.cargar_inventario_csv(uploaded_file)
                    
                    if "error" in resultado:
                        st.error(f"❌ {resultado['error']}")
                    else:
                        st.success(f"✅ Inventario cargado: {resultado['total_referencias']} referencias")
                        st.info(f"📋 Columnas disponibles: {', '.join(resultado['columnas_disponibles'])}")
                        # Limpiar recomendaciones anteriores
                        if 'recomendaciones' in st.session_state:
                            del st.session_state['recomendaciones']
        
        # Mostrar estado actual del inventario
        if self.recommendation_system.inventario_df is not None and not self.recommendation_system.inventario_df.empty:
            st.success(f"✅ Inventario cargado: {len(self.recommendation_system.inventario_df)} referencias disponibles")
    
    def _render_recomendaciones_filtradas(self, resultado: Dict[str, Any]):
        """Renderiza las recomendaciones con filtros"""
        recomendaciones = resultado.get('recomendaciones', [])
        
        if not recomendaciones:
            st.warning("No se encontraron recomendaciones para mostrar")
            return
        
        # Convertir a DataFrame para filtros
        df_recomendaciones = pd.DataFrame(recomendaciones)
        
        # Filtros
        st.markdown("### 🔍 Filtros")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtro por cliente
            clientes_unicos = ['Todos'] + sorted(df_recomendaciones['cliente'].unique().tolist())
            cliente_seleccionado = st.selectbox("Cliente", clientes_unicos)
        
        with col2:
            # Filtro por categoría
            categorias_unicas = ['Todas'] + sorted([c for c in df_recomendaciones['categoria'].unique() if c != 'N/A'])
            categoria_seleccionada = st.selectbox("Categoría", categorias_unicas)
        
        with col3:
            # Filtro por prioridad
            prioridades_unicas = ['Todas'] + sorted(df_recomendaciones['prioridad'].unique().tolist())
            prioridad_seleccionada = st.selectbox("Prioridad", prioridades_unicas)
        
        # Aplicar filtros
        df_filtrado = df_recomendaciones.copy()
        
        if cliente_seleccionado != 'Todos':
            df_filtrado = df_filtrado[df_filtrado['cliente'] == cliente_seleccionado]
        
        if categoria_seleccionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_seleccionada]
        
        if prioridad_seleccionada != 'Todas':
            df_filtrado = df_filtrado[df_filtrado['prioridad'] == prioridad_seleccionada]
        
        # Mostrar resumen
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Recomendaciones", len(df_filtrado))
        with col2:
            st.metric("Clientes", len(df_filtrado['cliente'].unique()))
        with col3:
            alta_prioridad = len(df_filtrado[df_filtrado['prioridad'] == 'Alta'])
            st.metric("Alta Prioridad", alta_prioridad)
        with col4:
            productos_abandonados = len(df_filtrado[df_filtrado['tipo_recomendacion'] == 'Producto Abandonado'])
            st.metric("Productos Abandonados", productos_abandonados)
        
        st.markdown("---")
        
        # Botón de exportación
        col1, col2 = st.columns([1, 5])
        with col1:
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar CSV",
                data=csv,
                file_name=f"recomendaciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.markdown("---")
        
        # Mostrar recomendaciones en tarjetas
        if len(df_filtrado) > 0:
            self._render_recomendaciones_tarjetas(df_filtrado)
        else:
            st.info("No hay recomendaciones que coincidan con los filtros seleccionados")
    
    def _render_recomendaciones_tarjetas(self, df_recomendaciones: pd.DataFrame):
        """Renderiza las recomendaciones en formato de tarjetas"""
        st.markdown("### 🎯 Recomendaciones")
        
        # Agrupar por cliente para mejor visualización
        clientes_unicos = df_recomendaciones['cliente'].unique()
        
        for cliente in clientes_unicos:
            df_cliente = df_recomendaciones[df_recomendaciones['cliente'] == cliente]
            
            with st.expander(f"👤 {cliente} ({len(df_cliente)} recomendaciones)", expanded=False):
                # Ordenar por prioridad
                df_cliente_ordenado = df_cliente.sort_values('prioridad', ascending=False)
                
                # Mostrar tarjetas
                for idx, row in df_cliente_ordenado.iterrows():
                    self._render_tarjeta_recomendacion(row)
    
    def _render_tarjeta_recomendacion(self, recomendacion: Dict[str, Any]):
        """Renderiza una tarjeta individual de recomendación"""
        # Determinar color según prioridad
        color_border = {
            "Alta": "#FF4444",
            "Media": "#FFA500",
            "Baja": "#4CAF50"
        }
        
        # Determinar icono según tipo
        iconos = {
            "Producto Abandonado": "🔄",
            "Producto Complementario": "🔗",
            "Producto Similar": "🔍"
        }
        
        prioridad = recomendacion.get('prioridad', 'Baja')
        tipo = recomendacion.get('tipo_recomendacion', '')
        icono = iconos.get(tipo, "📦")
        
        # Obtener tema dark
        from ui.theme_manager import ThemeManager
        theme = ThemeManager.get_theme()
        
        # Crear tarjeta con HTML/CSS - TEMA DARK CORPORATIVO
        st.markdown(
            f"""
            <div style="
                border-left: 4px solid {color_border.get(prioridad, theme['border'])};
                padding: 15px;
                margin: 10px 0;
                background-color: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            ">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <h4 style="margin: 0 0 10px 0; color: {theme['text_primary']};">
                            {icono} <strong>{recomendacion.get('referencia', 'N/A')}</strong>
                            <span style="font-size: 0.8em; color: {color_border.get(prioridad, theme['text_secondary'])}; margin-left: 10px;">
                                [{prioridad}]
                            </span>
                        </h4>
                        <p style="margin: 5px 0; color: {theme['text_secondary']};">
                            <strong>Tipo:</strong> {tipo}
                        </p>
                        <p style="margin: 5px 0; color: {theme['text_secondary']};">
                            <strong>Razón:</strong> {recomendacion.get('razon', 'N/A')}
                        </p>
                        <div style="margin-top: 10px; display: flex; gap: 20px; flex-wrap: wrap;">
            """,
            unsafe_allow_html=True
        )
        
        # Información adicional según tipo - TEMA DARK
        theme = ThemeManager.get_theme()
        
        if recomendacion.get('ultima_compra'):
            st.markdown(
                f"""
                <p style="margin: 5px 0; color: {theme['text_secondary']}; font-size: 0.9em;">
                    📅 <strong>Última compra:</strong> {pd.to_datetime(recomendacion['ultima_compra']).strftime('%Y-%m-%d') if pd.notna(recomendacion.get('ultima_compra')) else 'N/A'}
                </p>
                """,
                unsafe_allow_html=True
            )
        
        if recomendacion.get('dias_sin_comprar'):
            st.markdown(
                f"""
                <p style="margin: 5px 0; color: {theme['text_secondary']}; font-size: 0.9em;">
                    ⏰ <strong>Días sin comprar:</strong> {recomendacion['dias_sin_comprar']}
                </p>
                """,
                unsafe_allow_html=True
            )
        
        if recomendacion.get('frecuencia_historica'):
            st.markdown(
                f"""
                <p style="margin: 5px 0; color: {theme['text_secondary']}; font-size: 0.9em;">
                    🔢 <strong>Frecuencia histórica:</strong> {recomendacion['frecuencia_historica']} compras
                </p>
                """,
                unsafe_allow_html=True
            )
        
        if recomendacion.get('valor_promedio'):
            st.markdown(
                f"""
                <p style="margin: 5px 0; color: {theme['text_secondary']}; font-size: 0.9em;">
                    💰 <strong>Valor promedio:</strong> {format_currency(recomendacion['valor_promedio'])}
                </p>
                """,
                unsafe_allow_html=True
            )
        
        if recomendacion.get('categoria') and recomendacion.get('categoria') != 'N/A':
            st.markdown(
                f"""
                <p style="margin: 5px 0; color: {theme['text_secondary']}; font-size: 0.9em;">
                    🏷️ <strong>Categoría:</strong> {recomendacion['categoria']}
                </p>
                """,
                unsafe_allow_html=True
            )
        
        # Cerrar tarjeta
        st.markdown("</div></div></div>", unsafe_allow_html=True)
        
        st.markdown("---")


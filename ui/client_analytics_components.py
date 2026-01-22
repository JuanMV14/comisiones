import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from business.client_analytics import ClientAnalytics
from utils.formatting import format_currency


class ClientAnalyticsUI:
    """Interfaz para analytics de clientes"""
    
    def __init__(self, analytics: ClientAnalytics):
        self.analytics = analytics
    
    def render_analytics_dashboard(self):
        """Renderiza el dashboard completo de analytics de clientes"""
        st.header("📊 Analytics de Clientes B2B")
        
        tab1, tab2, tab3 = st.tabs([
            "🏆 Ranking de Clientes",
            "🗺️ Mapa Geográfico",
            "📈 Segmentación"
        ])
        
        with tab1:
            self._render_ranking_clientes()
        
        with tab2:
            self._render_mapa_geografico()
        
        with tab3:
            self._render_segmentacion()
    
    def _render_ranking_clientes(self):
        """Renderiza el ranking de mejores clientes"""
        st.subheader("🏆 Ranking de Mejores Clientes")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            periodo = st.selectbox("Período de Análisis", [3, 6, 12, 24], index=2, key="periodo_ranking")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Actualizar Ranking", use_container_width=True):
                st.cache_data.clear()
        
        with st.spinner("Calculando ranking..."):
            ranking = self.analytics.ranking_clientes(periodo)
        
        if ranking.empty:
            st.info("No hay datos suficientes para generar el ranking")
            return
        
        # Top 10
        st.markdown("### 🥇 Top 10 Clientes")
        
        top_10 = ranking.head(10)
        
        for i, (_, cliente) in enumerate(top_10.iterrows(), 1):
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
                
                with col1:
                    if i == 1:
                        st.markdown("### 🥇")
                    elif i == 2:
                        st.markdown("### 🥈")
                    elif i == 3:
                        st.markdown("### 🥉")
                    else:
                        st.markdown(f"### #{i}")
                
                with col2:
                    st.markdown(f"**{cliente.get('nombre', 'N/A')}**")
                    st.caption(f"NIT: {cliente['nit_cliente']} | {cliente.get('ciudad', 'N/A')}")
                
                with col3:
                    st.metric("Total Compras", format_currency(cliente['total_compras']))
                
                with col4:
                    st.metric("Transacciones", cliente['num_transacciones'])
                
                with col5:
                    st.metric("Ticket Promedio", format_currency(cliente['ticket_promedio']))
        
        st.markdown("---")
        
        # Tabla completa
        st.markdown("### 📋 Ranking Completo")
        
        # Preparar datos para mostrar
        df_display = ranking.copy()
        df_display['Total Compras'] = df_display['total_compras'].apply(format_currency)
        df_display['Ticket Promedio'] = df_display['ticket_promedio'].apply(format_currency)
        df_display['Cupo Disponible'] = df_display['cupo_disponible'].apply(format_currency)
        df_display['Uso Cupo %'] = df_display['uso_cupo_pct'].apply(lambda x: f"{x:.1f}%")
        
        columnas_mostrar = ['nombre', 'ciudad', 'Total Compras', 'num_transacciones', 
                           'Ticket Promedio', 'Cupo Disponible', 'Uso Cupo %', 'dias_sin_comprar']
        columnas_disponibles = [col for col in columnas_mostrar if col in df_display.columns]
        
        st.dataframe(
            df_display[columnas_disponibles],
            use_container_width=True,
            hide_index=True
        )
        
        # Gráficos
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Distribución de Compras (Top 10)")
            fig = px.bar(
                top_10,
                x='nombre',
                y='total_compras',
                labels={'nombre': 'Cliente', 'total_compras': 'Total Compras'},
                color='total_compras',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Frecuencia de Compra")
            fig = px.scatter(
                top_10,
                x='num_transacciones',
                y='ticket_promedio',
                size='total_compras',
                hover_data=['nombre'],
                labels={'num_transacciones': 'Número de Transacciones', 
                       'ticket_promedio': 'Ticket Promedio'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_mapa_geografico(self):
        """Renderiza el mapa geográfico de clientes con filtros de período"""
        st.subheader("🗺️ Distribución Geográfica de Clientes")
        
        # Filtros de período
        col_filtro1, col_filtro2 = st.columns([2, 3])
        with col_filtro1:
            periodo = st.selectbox(
                "Período de Análisis",
                ["historico", "mes_actual", "personalizado"],
                format_func=lambda x: {
                    "historico": "📚 Histórico Completo",
                    "mes_actual": "📅 Mes Actual",
                    "personalizado": "🗓️ Período Personalizado"
                }[x],
                key="filtro_periodo_geo"
            )
        
        fecha_inicio = None
        fecha_fin = None
        if periodo == "personalizado":
            with col_filtro2:
                fecha_inicio = st.date_input("Fecha Inicio", key="fecha_inicio_geo")
                fecha_fin = st.date_input("Fecha Fin", key="fecha_fin_geo")
                if fecha_inicio and fecha_fin:
                    fecha_inicio = fecha_inicio.strftime('%Y-%m-%d')
                    fecha_fin = fecha_fin.strftime('%Y-%m-%d')
        
        # Info sobre período
        if periodo == "historico":
            st.info("ℹ️ Mostrando datos históricos completos (todas las compras registradas)")
        elif periodo == "mes_actual":
            from datetime import datetime
            mes_actual = datetime.now().strftime('%B %Y')
            st.info(f"ℹ️ Mostrando solo datos del mes actual ({mes_actual})")
        
        with st.spinner("Analizando distribución geográfica..."):
            distribucion = self.analytics.distribucion_geografica(
                periodo=periodo,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
        
        if "error" in distribucion:
            st.error(f"❌ {distribucion['error']}")
            return
        
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Clientes", distribucion['total_clientes'])
        with col2:
            st.metric("Ciudades", distribucion['total_ciudades'])
        with col3:
            st.metric("Ciudades con Coordenadas", distribucion['ciudades_con_coordenadas'])
        with col4:
            total_compras = sum([c.get('total_compras', 0) for c in distribucion['por_ciudad']])
            st.metric("Total Compras", format_currency(total_compras))
        
        st.markdown("---")
        
        # Dos mapas en tabs
        tab1, tab2 = st.tabs(["📍 Mapa 1: Distribución por Compras", "💳 Mapa 2: Distribución por Cupo"])
        
        with tab1:
            if distribucion['datos_mapa']:
                st.markdown("### 📍 Mapa de Clientes por Volumen de Compras")
                st.caption("Tamaño = Total de Compras | Color = Número de Clientes")
                
                df_mapa = pd.DataFrame(distribucion['datos_mapa'])
                
                # Mapa 1: Por compras
                fig1 = px.scatter_mapbox(
                    df_mapa,
                    lat='lat',
                    lon='lon',
                    size='total_compras',
                    color='num_clientes',
                    hover_name='ciudad',
                    hover_data={
                        'num_clientes': True,
                        'total_compras': ':,.0f',
                        'departamento': True,
                        'codigo_dane': True,
                        'lat': False,
                        'lon': False
                    },
                    zoom=5,
                    height=600,
                    color_continuous_scale='Viridis',
                    size_max=50,
                    labels={'num_clientes': 'Clientes', 'total_compras': 'Compras'}
                )
                
                fig1.update_layout(
                    mapbox_style="open-street-map",
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("⚠️ No se encontraron coordenadas para las ciudades. Verifica que los nombres de ciudades estén correctos.")
        
        with tab2:
            if distribucion['datos_mapa']:
                st.markdown("### 💳 Mapa de Clientes por Uso de Cupo")
                st.caption("Tamaño = Cupo Total | Color = Cupo Utilizado (%)")
                
                df_mapa = pd.DataFrame(distribucion['datos_mapa'])
                # Calcular porcentaje de uso de cupo
                df_mapa['porcentaje_cupo'] = (df_mapa['cupo_utilizado'] / df_mapa['cupo_total'].replace(0, 1) * 100).fillna(0)
                
                # Mapa 2: Por cupo
                fig2 = px.scatter_mapbox(
                    df_mapa,
                    lat='lat',
                    lon='lon',
                    size='cupo_total',
                    color='porcentaje_cupo',
                    hover_name='ciudad',
                    hover_data={
                        'cupo_total': ':,.0f',
                        'cupo_utilizado': ':,.0f',
                        'porcentaje_cupo': ':.1f',
                        'departamento': True,
                        'codigo_dane': True,
                        'lat': False,
                        'lon': False
                    },
                    zoom=5,
                    height=600,
                    color_continuous_scale='RdYlGn_r',  # Rojo = alto uso, Verde = bajo uso
                    size_max=50,
                    labels={'cupo_total': 'Cupo Total', 'porcentaje_cupo': 'Uso %'}
                )
                
                fig2.update_layout(
                    mapbox_style="open-street-map",
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("⚠️ No se encontraron coordenadas para las ciudades.")
        
        st.markdown("---")
        
        # Tabla por ciudad con código DANE
        st.markdown("### 📊 Distribución por Ciudad")
        
        df_ciudades = pd.DataFrame(distribucion['por_ciudad'])
        df_ciudades['Total Compras'] = df_ciudades['total_compras'].apply(format_currency)
        df_ciudades['Cupo Total'] = df_ciudades['cupo_total'].apply(format_currency)
        df_ciudades['Cupo Utilizado'] = df_ciudades['cupo_utilizado'].apply(format_currency)
        
        # Mostrar columnas relevantes
        columnas_display = ['ciudad', 'codigo_dane', 'departamento', 'num_clientes', 'Total Compras', 'Cupo Total', 'Cupo Utilizado']
        columnas_existentes = [col for col in columnas_display if col in df_ciudades.columns]
        
        st.dataframe(
            df_ciudades[columnas_existentes],
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico de barras
        st.markdown("---")
        st.markdown("### 📊 Top Ciudades por Compras")
        
        top_ciudades = df_ciudades.nlargest(10, 'total_compras')
        
        fig = px.bar(
            top_ciudades,
            x='ciudad',
            y='total_compras',
            labels={'ciudad': 'Ciudad', 'total_compras': 'Total Compras'},
            color='num_clientes',
            color_continuous_scale='Blues'
        )
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_segmentacion(self):
        """Renderiza la segmentación de clientes por presupuesto"""
        st.subheader("📈 Segmentación de Clientes por Presupuesto")
        st.info("💡 Los clientes se segmentan automáticamente según su volumen de compras para optimizar la asignación de recursos")
        
        with st.spinner("Analizando segmentación..."):
            segmentacion = self.analytics.segmentar_por_presupuesto()
        
        if "error" in segmentacion:
            st.error(f"❌ {segmentacion['error']}")
            return
        
        # Resumen de segmentos
        st.markdown("### 📊 Resumen por Segmento")
        
        df_segmentos = pd.DataFrame(segmentacion['resumen_segmentos'])
        
        col1, col2, col3, col4 = st.columns(4)
        for i, segmento in enumerate(df_segmentos.iterrows()):
            _, seg = segmento
            col = [col1, col2, col3, col4][i % 4]
            with col:
                st.metric(
                    seg['segmento'],
                    f"{seg['num_clientes']} clientes",
                    delta=f"{seg['pct_total']}% del total"
                )
        
        st.markdown("---")
        
        # Gráfico de segmentación
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Distribución de Clientes")
            fig = px.pie(
                df_segmentos,
                values='num_clientes',
                names='segmento',
                color='segmento',
                color_discrete_map={
                    'A - Premium': '#FFD700',
                    'B - Alto': '#C0C0C0',
                    'C - Medio': '#CD7F32',
                    'D - Básico': '#808080'
                }
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Distribución de Compras")
            fig = px.bar(
                df_segmentos,
                x='segmento',
                y='total_compras',
                labels={'segmento': 'Segmento', 'total_compras': 'Total Compras'},
                color='segmento',
                color_discrete_map={
                    'A - Premium': '#FFD700',
                    'B - Alto': '#C0C0C0',
                    'C - Medio': '#CD7F32',
                    'D - Básico': '#808080'
                }
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Recomendaciones
        st.markdown("### 💡 Recomendaciones de Asignación de Recursos")
        
        for rec in segmentacion['recomendaciones']:
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    if rec['prioridad'] == 'ALTA':
                        st.error(f"🔴 {rec['prioridad']}")
                    elif 'MEDIA' in rec['prioridad']:
                        st.warning(f"🟡 {rec['prioridad']}")
                    else:
                        st.info(f"🔵 {rec['prioridad']}")
                
                with col2:
                    st.markdown(f"**{rec['segmento']}**")
                    st.write(rec['recomendacion'])
        
        st.markdown("---")
        
        # Tabla de clientes por segmento
        st.markdown("### 📋 Clientes por Segmento")
        
        df_ranking = pd.DataFrame(segmentacion['ranking'])
        
        segmento_seleccionado = st.selectbox(
            "Filtrar por Segmento",
            ['Todos'] + df_ranking['segmento'].unique().tolist(),
            key="filtro_segmento"
        )
        
        if segmento_seleccionado != 'Todos':
            df_filtrado = df_ranking[df_ranking['segmento'] == segmento_seleccionado]
        else:
            df_filtrado = df_ranking
        
        df_filtrado['Total Compras'] = df_filtrado['total_compras'].apply(format_currency)
        df_filtrado['Ticket Promedio'] = df_filtrado['ticket_promedio'].apply(format_currency)
        
        st.dataframe(
            df_filtrado[['segmento', 'nombre', 'ciudad', 'Total Compras', 'num_transacciones', 'Ticket Promedio']],
            use_container_width=True,
            hide_index=True
        )

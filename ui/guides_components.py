"""
Componentes de UI para visualización de análisis de guías
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any
from ui.theme_manager import ThemeManager
from ui.executive_components import ExecutiveComponents


class GuidesComponentsUI:
    """Componentes de UI para análisis de guías"""
    
    @staticmethod
    def render_page_header(title: str, subtitle: str = ""):
        """Renderiza encabezado de página con estilo moderno usando ExecutiveComponents"""
        ExecutiveComponents.render_page_header(title, subtitle)
    
    @staticmethod
    def render_upload_and_select():
        """
        Renderiza el componente para subir Excel y seleccionar hoja con estilo ejecutivo
        
        Returns:
            Tuple (file, hoja_seleccionada, calcular_tiempo_acido) o (None, None, False) si no hay datos
        """
        theme = ThemeManager.get_theme()
        
        # Sección de carga de archivo
        st.markdown("---")
        st.markdown(
            f"""
            <div style='
                background: {theme['surface']};
                border: 1px solid rgba(148,163,184,.15);
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            '>
                <h3 style='
                    color: {theme['text_primary']};
                    font-weight: 700;
                    margin-bottom: 1rem;
                '>
                    📤 Cargar Archivo Excel
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        uploaded_file = st.file_uploader(
            "Selecciona el archivo Excel de guías",
            type=['xlsx', 'xls'],
            help="Sube un archivo Excel con las guías de despacho"
        )
        
        if uploaded_file is None:
            return None, None, False
        
        # Obtener lista de hojas
        try:
            from business.guides_analyzer import GuidesAnalyzer
            analyzer = GuidesAnalyzer()
            hojas = analyzer.obtener_hojas_excel(uploaded_file)
            
            if not hojas:
                st.error("No se encontraron hojas en el archivo Excel")
                return None, None, False
            
            # Selector de hoja con estilo
            st.markdown(
                f"""
                <div style='
                    background: {theme['surface']};
                    border: 1px solid rgba(148,163,184,.15);
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                '>
                    <h3 style='
                        color: {theme['text_primary']};
                        font-weight: 700;
                        margin-bottom: 1rem;
                    '>
                        📅 Seleccionar Mes
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            hoja_seleccionada = st.selectbox(
                "Selecciona el mes que deseas analizar:",
                hojas,
                help="Cada hoja representa un mes diferente",
                label_visibility="collapsed"
            )
            
            # Opción para calcular tiempo ácido automáticamente
            st.markdown(
                f"""
                <div style='
                    background: {theme['surface']};
                    border: 1px solid rgba(148,163,184,.15);
                    border-radius: 12px;
                    padding: 1.5rem;
                    margin-bottom: 1.5rem;
                '>
                    <h3 style='
                        color: {theme['text_primary']};
                        font-weight: 700;
                        margin-bottom: 1rem;
                    '>
                        ⚙️ Opciones de Análisis
                    </h3>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            calcular_tiempo_acido = st.checkbox(
                "📊 Calcular 'Tiempo ácido' automáticamente",
                value=True,
                help="Calcula días laborables excluyendo domingos y festivos. Si tu Excel ya tiene esta columna calculada, desmarca esta opción."
            )
            
            return uploaded_file, hoja_seleccionada, calcular_tiempo_acido
            
        except Exception as e:
            st.error(f"Error procesando archivo: {str(e)}")
            return None, None, False
    
    @staticmethod
    def render_chart_tiempo_acido(data: Dict[str, Any]):
        """
        Renderiza gráfico de cantidad de guías por categoría en Tiempo ácido
        
        Args:
            data: Diccionario con categorías y cantidades
        """
        if "error" in data:
            st.error(f"Error: {data['error']}")
            return
        
        theme = ThemeManager.get_theme()
        
        # Crear gráfico de barras
        fig = go.Figure()
        
        # Colores según categoría
        colores = {
            "En tiempo": "#10b981",      # Verde
            "Validar": "#f59e0b",        # Amarillo/Naranja
            "Fuera de tiempo": "#ef4444" # Rojo
        }
        
        # Crear barras para cada categoría
        for cat, cant in zip(data["categorias"], data["cantidades"]):
            color = colores.get(cat, theme['primary'])
            fig.add_trace(go.Bar(
                x=[cat],
                y=[cant],
                name=cat,
                marker_color=color,
                text=[cant],
                textposition='outside',
                hovertemplate=f'<b>{cat}</b><br>Cantidad: {cant}<extra></extra>'
            ))
        
        fig.update_layout(
            title={
                "text": "Cantidad de guías por categoría en 'Tiempo ácido'",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": theme['text_primary']}
            },
            xaxis_title="Categoría",
            yaxis_title="Cantidad de guías",
            showlegend=False,
            height=400,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme['text_primary']),
            margin=dict(l=20, r=20, t=60, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_chart_ciudades_unidades(data: Dict[str, Any]):
        """
        Renderiza gráfico de ciudades con más unidades despachadas
        
        Args:
            data: Diccionario con ciudades y unidades
        """
        if "error" in data:
            st.error(f"Error: {data['error']}")
            return
        
        theme = ThemeManager.get_theme()
        
        # Crear gráfico de barras
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=data["ciudades"],
            y=data["unidades"],
            marker_color=px.colors.sequential.Greens[-len(data["ciudades"]):],
            text=data["unidades"],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Unidades: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                "text": "Ciudades con más unidades despachadas",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": theme['text_primary']}
            },
            xaxis_title="Ciudad",
            yaxis_title="Total de unidades",
            showlegend=False,
            height=400,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme['text_primary']),
            margin=dict(l=20, r=20, t=60, b=40),
            xaxis=dict(tickangle=-45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_chart_transportadoras(data: Dict[str, Any]):
        """
        Renderiza gráfico de ranking de transportadoras por efectividad
        
        Args:
            data: Diccionario con transportadoras y efectividad
        """
        if "error" in data:
            st.error(f"Error: {data['error']}")
            return
        
        theme = ThemeManager.get_theme()
        
        # Crear gráfico de barras
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=data["transportadoras"],
            y=data["efectividad"],
            marker_color=px.colors.sequential.Purples[-len(data["transportadoras"]):],
            text=[f"{ef:.1f}%" for ef in data["efectividad"]],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Efectividad: %{y:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                "text": "Ranking de transportadoras según efectividad (%)",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": theme['text_primary']}
            },
            xaxis_title="Transportadora",
            yaxis_title="Efectividad (%)",
            yaxis=dict(range=[0, 100]),
            showlegend=False,
            height=400,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme['text_primary']),
            margin=dict(l=20, r=20, t=60, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_chart_ciudades_fuera_tiempo(data: Dict[str, Any]):
        """
        Renderiza gráfico de ciudades con guías fuera de tiempo
        
        Args:
            data: Diccionario con ciudades y cantidades
        """
        if "error" in data:
            st.error(f"Error: {data['error']}")
            return
        
        theme = ThemeManager.get_theme()
        
        # Limitar a top 20 ciudades para mejor visualización
        ciudades = data["ciudades"][:20]
        cantidades = data["cantidades"][:20]
        
        # Crear gráfico de barras
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=ciudades,
            y=cantidades,
            marker_color=px.colors.sequential.Reds[-len(ciudades):],
            text=cantidades,
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Guías fuera de tiempo: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                "text": "Ciudades con guías fuera de tiempo",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": theme['text_primary']}
            },
            xaxis_title="Ciudad",
            yaxis_title="Cantidad de guías fuera de tiempo",
            showlegend=False,
            height=400,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme['text_primary']),
            margin=dict(l=20, r=20, t=60, b=100),
            xaxis=dict(tickangle=-45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_chart_transportadoras_tiempo_acido(data: Dict[str, Any]):
        """
        Renderiza gráfico de desglose de "Tiempo ácido" por transportadora
        
        Args:
            data: Diccionario con transportadoras y distribución de tiempo ácido
        """
        if "error" in data:
            st.error(f"Error: {data['error']}")
            return
        
        theme = ThemeManager.get_theme()
        
        # Crear gráfico de barras apiladas
        fig = go.Figure()
        
        # Colores para cada categoría
        colores = {
            "en_tiempo": "#10b981",      # Verde
            "validar": "#f59e0b",        # Amarillo/Naranja
            "fuera_tiempo": "#ef4444"    # Rojo
        }
        
        # Agregar barra para "En tiempo"
        fig.add_trace(go.Bar(
            name="En tiempo",
            x=data["transportadoras"],
            y=data["en_tiempo"],
            marker_color=colores["en_tiempo"],
            text=data["en_tiempo"],
            textposition='inside',
            hovertemplate='<b>%{x}</b><br>En tiempo: %{y}<extra></extra>'
        ))
        
        # Agregar barra para "Validar"
        fig.add_trace(go.Bar(
            name="Validar",
            x=data["transportadoras"],
            y=data["validar"],
            marker_color=colores["validar"],
            text=data["validar"],
            textposition='inside',
            hovertemplate='<b>%{x}</b><br>Validar: %{y}<extra></extra>'
        ))
        
        # Agregar barra para "Fuera de tiempo"
        fig.add_trace(go.Bar(
            name="Fuera de tiempo",
            x=data["transportadoras"],
            y=data["fuera_tiempo"],
            marker_color=colores["fuera_tiempo"],
            text=data["fuera_tiempo"],
            textposition='inside',
            hovertemplate='<b>%{x}</b><br>Fuera de tiempo: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                "text": "Desglose de 'Tiempo ácido' por Transportadora",
                "x": 0.5,
                "xanchor": "center",
                "font": {"size": 16, "color": theme['text_primary']}
            },
            xaxis_title="Transportadora",
            yaxis_title="Cantidad de guías",
            barmode='stack',
            showlegend=True,
            height=500,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=theme['text_primary']),
            margin=dict(l=20, r=20, t=60, b=100),
            xaxis=dict(tickangle=-45),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_dashboard_completo(analisis: Dict[str, Any]):
        """
        Renderiza el dashboard completo con los gráficos usando estilo ejecutivo
        
        Args:
            analisis: Diccionario con todos los análisis
        """
        theme = ThemeManager.get_theme()
        
        # Sección principal de análisis
        st.markdown("---")
        st.markdown(
            f"""
            <div style='
                background: {theme['surface']};
                border: 1px solid rgba(148,163,184,.15);
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            '>
                <h3 style='
                    color: {theme['text_primary']};
                    font-weight: 700;
                '>
                    📊 Análisis de Guías
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Grid 2x2 - Análisis principales
        col1, col2 = st.columns(2)
        
        with col1:
            # Gráfico 1: Tiempo ácido
            GuidesComponentsUI.render_chart_tiempo_acido(analisis["tiempo_acido"])
        
        with col2:
            # Gráfico 2: Ciudades con más unidades
            GuidesComponentsUI.render_chart_ciudades_unidades(analisis["ciudades_unidades"])
        
        col3, col4 = st.columns(2)
        
        with col3:
            # Gráfico 3: Transportadoras efectividad
            GuidesComponentsUI.render_chart_transportadoras(analisis["transportadoras"])
        
        with col4:
            # Gráfico 4: Ciudades fuera de tiempo
            GuidesComponentsUI.render_chart_ciudades_fuera_tiempo(analisis["ciudades_fuera_tiempo"])
        
        # Nuevo gráfico: Desglose de Tiempo ácido por Transportadora
        st.markdown("---")
        st.markdown(
            f"""
            <div style='
                background: {theme['surface']};
                border: 1px solid rgba(148,163,184,.15);
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            '>
                <h3 style='
                    color: {theme['text_primary']};
                    font-weight: 700;
                '>
                    🚚 Análisis Detallado por Transportadora
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        GuidesComponentsUI.render_chart_transportadoras_tiempo_acido(analisis["transportadoras_tiempo_acido"])


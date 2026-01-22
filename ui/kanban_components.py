"""
Componentes UI para Pipeline de Ventas (Kanban)
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from business.sales_pipeline import SalesPipeline, Deal
from ui.theme_manager import ThemeManager
from utils.formatting import format_currency
from utils.streamlit_helpers import safe_rerun
import plotly.graph_objects as go
import plotly.express as px

class KanbanUI:
    """Interfaz de usuario para Pipeline de Ventas"""
    
    def __init__(self, pipeline: SalesPipeline):
        self.pipeline = pipeline
    
    def render_pipeline_dashboard(self):
        """Renderiza el dashboard completo del pipeline"""
        
        theme = ThemeManager.get_theme()
        
        # Título
        st.markdown(
            f"""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='
                    font-size: 2.5rem;
                    font-weight: 800;
                    background: {theme['gradient_3']};
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 0.5rem;
                '>
                    🎯 Pipeline de Ventas
                </h1>
                <p style='color: {theme['text_secondary']}; font-size: 1rem;'>
                    Gestión Visual · Kanban · Pronósticos
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Tabs principales
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Kanban Board",
            "➕ Nueva Oportunidad",
            "📊 Métricas",
            "📈 Pronósticos",
            "📑 Reportes"
        ])
        
        with tab1:
            self._render_kanban_board()
        
        with tab2:
            self._render_nueva_oportunidad()
        
        with tab3:
            self._render_metricas()
        
        with tab4:
            self._render_pronosticos()
        
        with tab5:
            self._render_reportes()
    
    def _render_kanban_board(self):
        """Renderiza el tablero Kanban"""
        
        st.markdown("### 📋 Tablero Kanban")
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            vendedores = list(set(d.vendedor for d in self.pipeline.deals))
            filtro_vendedor = st.selectbox(
                "Vendedor",
                options=["Todos"] + vendedores,
                key="kanban_filter_vendedor"
            )
        
        with col2:
            filtro_prioridad = st.selectbox(
                "Prioridad",
                options=["Todas", "Alta", "Media", "Baja"],
                key="kanban_filter_prioridad"
            )
        
        with col3:
            busqueda = st.text_input(
                "🔍 Buscar",
                placeholder="Cliente, contacto...",
                key="kanban_search"
            )
        
        # Aplicar filtros
        deals = self.pipeline.get_active_deals()
        
        if filtro_vendedor != "Todos":
            deals = [d for d in deals if d.vendedor == filtro_vendedor]
        
        if filtro_prioridad != "Todas":
            deals = [d for d in deals if d.prioridad == filtro_prioridad]
        
        if busqueda:
            deals = [
                d for d in deals
                if busqueda.lower() in d.cliente.lower() or
                   busqueda.lower() in d.contacto.lower()
            ]
        
        st.markdown("---")
        
        # Renderizar columnas del Kanban
        stages_activas = [s for s in self.pipeline.stages if s["id"] not in ["ganada", "perdida"]]
        
        cols = st.columns(len(stages_activas))
        
        for i, stage in enumerate(stages_activas):
            with cols[i]:
                deals_etapa = [d for d in deals if d.etapa == stage["id"]]
                self._render_kanban_column(stage, deals_etapa)
    
    def _render_kanban_column(self, stage: Dict, deals: List[Deal]):
        """Renderiza una columna del Kanban"""
        
        theme = ThemeManager.get_theme()
        
        # Encabezado de columna
        total_valor = sum(d.valor_estimado for d in deals)
        
        st.markdown(
            f"""
            <div style='
                background: {stage['color']};
                padding: 12px;
                border-radius: 8px 8px 0 0;
                text-align: center;
                color: white;
            '>
                <h4 style='margin: 0; font-size: 14px; font-weight: 700;'>
                    {stage['nombre']}
                </h4>
                <p style='margin: 4px 0 0 0; font-size: 12px; opacity: 0.9;'>
                    {len(deals)} deals · {format_currency(total_valor)}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Contenedor de tarjetas
        st.markdown(
            f"""
            <div style='
                background: {theme['surface']};
                border: 1px solid {theme['border']};
                border-top: none;
                border-radius: 0 0 8px 8px;
                padding: 8px;
                min-height: 400px;
                max-height: 600px;
                overflow-y: auto;
            '>
            """,
            unsafe_allow_html=True
        )
        
        # Renderizar tarjetas de deals
        if not deals:
            st.markdown(
                f"""
                <div style='
                    text-align: center;
                    padding: 40px 20px;
                    color: {theme['text_tertiary']};
                '>
                    <p style='font-size: 24px; margin: 0;'>📭</p>
                    <p style='font-size: 12px; margin: 8px 0 0 0;'>
                        No hay deals en esta etapa
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            for deal in deals:
                self._render_deal_card(deal, stage['color'])
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_deal_card(self, deal: Deal, color: str):
        """Renderiza una tarjeta de deal"""
        
        theme = ThemeManager.get_theme()
        
        # Icono de prioridad
        prioridad_icons = {
            "Alta": "🔴",
            "Media": "🟡",
            "Baja": "🟢"
        }
        prioridad_icon = prioridad_icons.get(deal.prioridad, "⚪")
        
        # Urgencia (siguiente acción vencida)
        urgente = ""
        if deal.fecha_siguiente_accion and deal.fecha_siguiente_accion < date.today():
            urgente = "⚠️"
        
        # Crear expander para la tarjeta
        with st.expander(
            f"{prioridad_icon} {urgente} {deal.cliente} - {format_currency(deal.valor_estimado)}",
            expanded=False
        ):
            # Información básica
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Contacto:** {deal.contacto}")
                st.markdown(f"**Teléfono:** {deal.telefono}")
                st.markdown(f"**Email:** {deal.email}")
            
            with col2:
                st.markdown(f"**Vendedor:** {deal.vendedor}")
                st.markdown(f"**Origen:** {deal.origen}")
                st.markdown(f"**Probabilidad:** {deal.probabilidad}%")
            
            # Fechas
            if deal.fecha_cierre_estimada:
                dias_restantes = (deal.fecha_cierre_estimada - date.today()).days
                st.markdown(f"**Cierre Estimado:** {deal.fecha_cierre_estimada} ({dias_restantes} días)")
            
            if deal.fecha_siguiente_accion:
                vencida = deal.fecha_siguiente_accion < date.today()
                color_accion = theme['error'] if vencida else theme['success']
                st.markdown(
                    f"**Siguiente Acción:** {deal.siguiente_accion} "
                    f"<span style='color: {color_accion};'>({deal.fecha_siguiente_accion})</span>",
                    unsafe_allow_html=True
                )
            
            # Productos de interés
            if deal.productos_interes:
                st.markdown(f"**Productos:** {', '.join(deal.productos_interes)}")
            
            # Notas
            if deal.notas:
                st.text_area("Notas", value=deal.notas, height=80, disabled=True, key=f"notas_{deal.id}")
            
            # Acciones
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✏️ Editar", key=f"edit_{deal.id}", use_container_width=True):
                    st.session_state[f"editing_{deal.id}"] = True
                    safe_rerun()
            
            with col2:
                if st.button("➡️ Mover", key=f"move_{deal.id}", use_container_width=True):
                    st.session_state[f"moving_{deal.id}"] = True
                    safe_rerun()
            
            with col3:
                if st.button("📜 Historial", key=f"history_{deal.id}", use_container_width=True):
                    st.session_state[f"show_history_{deal.id}"] = True
                    safe_rerun()
            
            # Modal de edición
            if st.session_state.get(f"editing_{deal.id}", False):
                self._render_edit_deal_modal(deal)
            
            # Modal de mover
            if st.session_state.get(f"moving_{deal.id}", False):
                self._render_move_deal_modal(deal)
            
            # Modal de historial
            if st.session_state.get(f"show_history_{deal.id}", False):
                self._render_history_modal(deal)
    
    def _render_nueva_oportunidad(self):
        """Renderiza formulario para nueva oportunidad"""
        
        st.markdown("### ➕ Crear Nueva Oportunidad")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Información del Cliente")
            cliente = st.text_input(
                "Nombre del Cliente *",
                placeholder="Empresa ABC S.A.S.",
                key="new_deal_cliente"
            )
            
            contacto = st.text_input(
                "Nombre del Contacto *",
                placeholder="Juan Pérez",
                key="new_deal_contacto"
            )
            
            telefono = st.text_input(
                "Teléfono *",
                placeholder="+57 300 123 4567",
                key="new_deal_telefono"
            )
            
            email = st.text_input(
                "Email *",
                placeholder="contacto@empresa.com",
                key="new_deal_email"
            )
            
            origen = st.selectbox(
                "Origen del Lead *",
                options=["Llamada", "Email", "Referido", "Web", "Redes Sociales", "Evento", "Otro"],
                key="new_deal_origen"
            )
        
        with col2:
            st.markdown("#### Detalles de la Oportunidad")
            
            valor_estimado = st.number_input(
                "Valor Estimado *",
                min_value=0.0,
                step=100000.0,
                format="%.0f",
                key="new_deal_valor"
            )
            
            vendedor = st.text_input(
                "Vendedor Asignado *",
                value="Mi Nombre",
                key="new_deal_vendedor"
            )
            
            prioridad = st.selectbox(
                "Prioridad *",
                options=["Alta", "Media", "Baja"],
                index=1,
                key="new_deal_prioridad"
            )
            
            fecha_cierre = st.date_input(
                "Fecha de Cierre Estimada",
                value=date.today() + timedelta(days=30),
                key="new_deal_fecha_cierre"
            )
            
            productos = st.multiselect(
                "Productos de Interés",
                options=[
                    "Producto A",
                    "Producto B",
                    "Producto C",
                    "Servicio 1",
                    "Servicio 2",
                    "Otro"
                ],
                key="new_deal_productos"
            )
        
        notas = st.text_area(
            "Notas Adicionales",
            height=100,
            placeholder="Detalles de la conversación inicial, necesidades específicas, etc.",
            key="new_deal_notas"
        )
        
        # Botón de crear
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("➕ Crear Oportunidad", type="primary", use_container_width=True):
                # Validaciones
                if not cliente or not contacto or not telefono or not email:
                    st.error("❌ Por favor completa todos los campos obligatorios (*)")
                elif valor_estimado <= 0:
                    st.error("❌ El valor estimado debe ser mayor a cero")
                else:
                    # Crear deal
                    deal = self.pipeline.create_deal(
                        cliente=cliente,
                        valor_estimado=valor_estimado,
                        contacto=contacto,
                        telefono=telefono,
                        email=email,
                        productos_interes=productos,
                        origen=origen,
                        vendedor=vendedor,
                        prioridad=prioridad,
                        notas=notas,
                        fecha_cierre_estimada=fecha_cierre
                    )
                    
                    st.success(f"✅ Oportunidad creada exitosamente: {deal.id}")
                    st.balloons()
                    
                    # Limpiar formulario
                    for key in st.session_state.keys():
                        if key.startswith("new_deal_"):
                            del st.session_state[key]
                    
                    safe_rerun()
        
        with col2:
            if st.button("🔄 Limpiar", use_container_width=True):
                for key in st.session_state.keys():
                    if key.startswith("new_deal_"):
                        del st.session_state[key]
                safe_rerun()
    
    def _render_metricas(self):
        """Renderiza métricas del pipeline"""
        
        st.markdown("### 📊 Métricas del Pipeline")
        
        metrics = self.pipeline.get_pipeline_metrics()
        
        # KPIs principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Deals Activos",
                metrics["deals_activos"],
                help="Oportunidades en proceso"
            )
        
        with col2:
            st.metric(
                "Valor Pipeline",
                format_currency(metrics["valor_pipeline"]),
                help="Valor total de deals activos"
            )
        
        with col3:
            st.metric(
                "Valor Ponderado",
                format_currency(metrics["valor_ponderado"]),
                help="Valor ajustado por probabilidad"
            )
        
        with col4:
            st.metric(
                "Tasa Conversión",
                f"{metrics['tasa_conversion']:.1f}%",
                help="% de deals ganados vs perdidos"
            )
        
        st.markdown("---")
        
        # Segunda fila de métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Deals Ganados",
                metrics["deals_ganados"],
                delta=f"+{metrics['deals_ganados']}",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "Deals Perdidos",
                metrics["deals_perdidos"],
                delta=f"-{metrics['deals_perdidos']}",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "Valor Promedio",
                format_currency(metrics["avg_deal_value"]),
                help="Valor promedio por deal"
            )
        
        with col4:
            st.metric(
                "Ciclo de Venta",
                f"{metrics['ciclo_promedio_dias']:.0f} días",
                help="Días promedio para cerrar"
            )
        
        st.markdown("---")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Distribución por Etapa")
            self._render_chart_por_etapa(metrics["distribucion_etapas"])
        
        with col2:
            st.markdown("#### 🎯 Por Prioridad")
            self._render_chart_por_prioridad(metrics["por_prioridad"])
    
    def _render_pronosticos(self):
        """Renderiza pronósticos de ventas"""
        
        st.markdown("### 📈 Pronósticos de Ventas")
        
        # Selector de período
        meses = st.slider(
            "Período de Pronóstico (meses)",
            min_value=1,
            max_value=6,
            value=3,
            key="forecast_months"
        )
        
        forecast = self.pipeline.get_forecast(meses)
        
        # KPIs del pronóstico
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Valor Esperado",
                format_currency(forecast["valor_esperado"]),
                help="Pronóstico realista basado en probabilidades"
            )
        
        with col2:
            delta_best = f"+{((forecast['valor_best_case'] / forecast['valor_esperado'] - 1) * 100):.0f}%" if forecast['valor_esperado'] > 0 else "N/A"
            st.metric(
                "Best Case",
                format_currency(forecast["valor_best_case"]),
                delta=delta_best,
                help="Si todos los deals se ganan"
            )
        
        with col3:
            delta_worst = f"{((forecast['valor_worst_case'] / forecast['valor_esperado'] - 1) * 100):.0f}%" if forecast['valor_esperado'] > 0 else "N/A"
            st.metric(
                "Worst Case",
                format_currency(forecast["valor_worst_case"]),
                delta=delta_worst,
                delta_color="inverse",
                help="Basado en tasa de conversión histórica"
            )
        
        with col4:
            st.metric(
                "Deals",
                forecast["deals_count"],
                help=f"Oportunidades que cierran en {meses} mes(es)"
            )
        
        # Nivel de confianza
        confianza = forecast["confianza"]
        confianza_color = {
            "Alta": "success",
            "Media": "info",
            "Baja": "warning"
        }.get(confianza, "info")
        
        getattr(st, confianza_color)(f"📊 Nivel de Confianza: **{confianza}**")
        
        # Gráfico de pronóstico
        st.markdown("---")
        self._render_forecast_chart(forecast)
        
        # Deals urgentes
        st.markdown("---")
        st.markdown("### ⚠️ Deals que Requieren Atención")
        
        urgentes = self.pipeline.get_deals_urgentes()
        
        if not urgentes:
            st.success("✅ No hay deals urgentes en este momento")
        else:
            st.warning(f"⚠️ {len(urgentes)} deals requieren atención urgente")
            
            for deal in urgentes[:10]:  # Mostrar top 10
                with st.expander(f"{deal.cliente} - {format_currency(deal.valor_estimado)}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Etapa:** {deal.etapa}")
                        st.markdown(f"**Prioridad:** {deal.prioridad}")
                    
                    with col2:
                        if deal.fecha_siguiente_accion:
                            vencida = deal.fecha_siguiente_accion < date.today()
                            estado = "⏰ VENCIDA" if vencida else "📅 Próxima"
                            st.markdown(f"**{estado}:** {deal.fecha_siguiente_accion}")
                        
                        st.markdown(f"**Acción:** {deal.siguiente_accion}")
    
    def _render_reportes(self):
        """Renderiza reportes del pipeline"""
        
        st.markdown("### 📑 Reportes")
        
        tab1, tab2, tab3 = st.tabs([
            "👤 Por Vendedor",
            "📅 Actividad Reciente",
            "📊 Exportar Datos"
        ])
        
        with tab1:
            self._render_reporte_vendedores()
        
        with tab2:
            self._render_actividad_reciente()
        
        with tab3:
            self._render_exportar()
    
    def _render_reporte_vendedores(self):
        """Renderiza reporte por vendedor"""
        
        st.markdown("#### 👤 Desempeño por Vendedor")
        
        reporte = self.pipeline.generate_vendedor_report()
        
        if not reporte:
            st.info("📭 No hay datos de vendedores")
            return
        
        # Crear DataFrame
        import pandas as pd
        df = pd.DataFrame(reporte).T
        df.index.name = "Vendedor"
        
        # Ordenar por valor ganado
        df = df.sort_values("valor_ganado", ascending=False)
        
        # Formatear columnas de dinero
        df["valor_total"] = df["valor_total"].apply(lambda x: format_currency(x))
        df["valor_ganado"] = df["valor_ganado"].apply(lambda x: format_currency(x))
        df["tasa_conversion"] = df["tasa_conversion"].apply(lambda x: f"{x:.1f}%")
        
        # Renombrar columnas
        df.columns = [
            "Total Deals",
            "Activos",
            "Ganados",
            "Perdidos",
            "Valor Total",
            "Valor Ganado",
            "Tasa Conv."
        ]
        
        st.dataframe(df, use_container_width=True)
    
    def _render_actividad_reciente(self):
        """Renderiza actividad reciente"""
        
        st.markdown("#### 📅 Actividad Reciente")
        
        dias = st.slider(
            "Últimos días",
            min_value=7,
            max_value=90,
            value=30,
            key="activity_days"
        )
        
        reporte = self.pipeline.generate_activity_report(dias)
        
        st.info(f"📊 {reporte['total_actividades']} actividades en los últimos {dias} días")
        
        if not reporte["actividades"]:
            st.warning("📭 No hay actividades en este período")
            return
        
        for actividad in reporte["actividades"][:20]:
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col1:
                    st.markdown(f"**{actividad['fecha']}**")
                
                with col2:
                    st.markdown(f"{actividad['cliente']} - {actividad['accion']}")
                
                with col3:
                    st.markdown(f"*{actividad['usuario']}*")
                
                st.markdown("---")
    
    def _render_exportar(self):
        """Renderiza opciones de exportación"""
        
        st.markdown("#### 📊 Exportar Datos del Pipeline")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Exportar a JSON", use_container_width=True):
                filename = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                if self.pipeline.export_to_json(filename):
                    st.success(f"✅ Exportado exitosamente: {filename}")
                else:
                    st.error("❌ Error al exportar")
        
        with col2:
            if st.button("📥 Importar desde JSON", use_container_width=True):
                st.info("💡 Funcionalidad de importación disponible próximamente")
    
    # Métodos auxiliares para gráficos
    
    def _render_chart_por_etapa(self, distribucion: Dict):
        """Renderiza gráfico de distribución por etapa"""
        
        labels = list(distribucion.keys())
        values = [distribucion[k]["cantidad"] for k in labels]
        
        fig = go.Figure(data=[go.Bar(
            x=labels,
            y=values,
            marker_color='#6366f1',
            text=values,
            textposition='auto'
        )])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            yaxis_title="Cantidad de Deals"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_chart_por_prioridad(self, por_prioridad: Dict):
        """Renderiza gráfico de distribución por prioridad"""
        
        labels = list(por_prioridad.keys())
        values = list(por_prioridad.values())
        colors = ['#ef4444', '#f59e0b', '#10b981']  # Rojo, Amarillo, Verde
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4
        )])
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_forecast_chart(self, forecast: Dict):
        """Renderiza gráfico de pronóstico"""
        
        fig = go.Figure()
        
        scenarios = ["Worst Case", "Esperado", "Best Case"]
        values = [
            forecast["valor_worst_case"],
            forecast["valor_esperado"],
            forecast["valor_best_case"]
        ]
        colors = ['#ef4444', '#f59e0b', '#10b981']
        
        fig.add_trace(go.Bar(
            x=scenarios,
            y=values,
            marker_color=colors,
            text=[format_currency(v) for v in values],
            textposition='outside'
        ))
        
        fig.update_layout(
            title=f"Pronóstico para los próximos {forecast['periodo_meses']} mes(es)",
            height=400,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            yaxis_title="Valor Estimado"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Modales
    
    def _render_edit_deal_modal(self, deal: Deal):
        """Renderiza modal de edición"""
        st.info("💡 Funcionalidad de edición disponible próximamente")
        if st.button("Cerrar", key=f"close_edit_{deal.id}"):
            del st.session_state[f"editing_{deal.id}"]
            safe_rerun()
    
    def _render_move_deal_modal(self, deal: Deal):
        """Renderiza modal para mover deal"""
        st.info("💡 Funcionalidad de mover deal disponible próximamente")
        if st.button("Cerrar", key=f"close_move_{deal.id}"):
            del st.session_state[f"moving_{deal.id}"]
            safe_rerun()
    
    def _render_history_modal(self, deal: Deal):
        """Renderiza modal de historial"""
        st.markdown("#### 📜 Historial de Actividades")
        
        for evento in reversed(deal.historial):
            fecha = datetime.fromisoformat(evento["fecha"]).strftime("%Y-%m-%d %H:%M")
            st.markdown(f"**{fecha}** - {evento['accion']}")
            if evento.get("notas"):
                st.caption(evento["notas"])
            st.markdown("---")
        
        if st.button("Cerrar", key=f"close_history_{deal.id}"):
            del st.session_state[f"show_history_{deal.id}"]
            safe_rerun()


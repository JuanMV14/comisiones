import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, Any

from database.queries import DatabaseManager
from ui.components import UIComponents
from ui.executive_components import ExecutiveComponents
from business.calculations import ComisionCalculator, MetricsCalculator
from business.ai_recommendations import AIRecommendations
from business.invoice_radication import InvoiceRadicationSystem
from business.executive_dashboard import ExecutiveDashboard
from utils.formatting import format_currency

class TabRenderer:
    """Renderizador de todas las pestañas de la aplicación"""
    
    def __init__(self, db_manager: DatabaseManager, ui_components: UIComponents):
        self.db_manager = db_manager
        self.ui_components = ui_components
        self.comision_calc = ComisionCalculator()
        self.metrics_calc = MetricsCalculator()
        self.ai_recommendations = AIRecommendations(db_manager)
        self.invoice_radication = InvoiceRadicationSystem(db_manager)
        self.executive_dashboard = ExecutiveDashboard(db_manager)
    
    # ========================
    # TAB DASHBOARD EJECUTIVO
    # ========================
    
    def render_executive_dashboard(self):
        """Renderiza el Dashboard Ejecutivo Profesional para Gerencia"""
        from ui.theme_manager import ThemeManager
        
        theme = ThemeManager.get_theme()
        
        # Título personalizado
        st.markdown(
            f"""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='
                    font-size: 2.5rem;
                    font-weight: 800;
                    background: {theme['gradient_1']};
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 0.5rem;
                '>
                    📊 Dashboard Ejecutivo
                </h1>
                <p style='color: {theme['text_secondary']}; font-size: 1rem;'>
                    Vista Ejecutiva · KPIs · Tendencias · Análisis de Riesgo
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Obtener resumen ejecutivo
        with st.spinner("Cargando dashboard ejecutivo..."):
            summary = self.executive_dashboard.get_executive_summary()
        
        # ========== SECCIÓN 1: KPIs FINANCIEROS ==========
        st.markdown("---")
        ExecutiveComponents.render_executive_kpi_grid(
            {**summary['kpis_financieros'], **summary['proyecciones']}
        )
        
        # ========== SECCIÓN 2: KPIs OPERACIONALES ==========
        st.markdown("---")
        ExecutiveComponents.render_operational_kpis(summary['kpis_operacionales'])
        
        # ========== SECCIÓN 3: TENDENCIAS Y MIX DE CLIENTES ==========
        st.markdown("---")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 📈 Tendencia Mensual (Últimos 6 Meses)")
            ExecutiveComponents.render_trend_chart(summary['tendencias']['monthly_trend'])
            
            if summary['tendencias']['growth_rate'] != 0:
                growth = summary['tendencias']['growth_rate']
                if growth > 0:
                    st.success(f"📈 Crecimiento de {growth:.1f}% en el período analizado")
                else:
                    st.warning(f"📉 Decrecimiento de {abs(growth):.1f}% en el período analizado")
        
        with col2:
            st.markdown("### 🎯 Mix de Clientes")
            ExecutiveComponents.render_client_mix(summary['comparativas'])
        
        # ========== SECCIÓN 4: ANÁLISIS DE RIESGO ==========
        st.markdown("---")
        ExecutiveComponents.render_risk_panel(summary['analisis_riesgo'])
        
        # ========== SECCIÓN 5: TOP PERFORMERS ==========
        st.markdown("---")
        st.markdown("### 🏆 Top Performers")
        ExecutiveComponents.render_top_performers(summary['top_performers'])
        
        # ========== SECCIÓN 6: PROYECCIONES ==========
        st.markdown("---")
        st.markdown("### 🔮 Proyecciones Fin de Mes")
        
        proyecciones = summary['proyecciones']
        
        if proyecciones:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Revenue Proyectado",
                    format_currency(proyecciones.get('proyeccion_revenue', 0)),
                    help=f"Basado en {proyecciones.get('dias_transcurridos', 0)} días de datos"
                )
            
            with col2:
                st.metric(
                    "Comisión Proyectada",
                    format_currency(proyecciones.get('proyeccion_comision', 0)),
                    help=f"Confianza: {proyecciones.get('confianza', 'N/A').upper()}"
                )
            
            with col3:
                dias_restantes = proyecciones.get('dias_restantes', 0)
                st.metric(
                    "Días Restantes",
                    dias_restantes,
                    help=f"De {proyecciones.get('dias_mes', 0)} días del mes"
                )
            
            # Barra de progreso del mes
            dias_transcurridos = proyecciones.get('dias_transcurridos', 0)
            dias_mes = proyecciones.get('dias_mes', 30)
            progreso_mes = (dias_transcurridos / dias_mes * 100) if dias_mes > 0 else 0
            
            st.markdown("#### Progreso del Mes")
            st.progress(progreso_mes / 100)
            st.caption(f"Día {dias_transcurridos} de {dias_mes} ({progreso_mes:.1f}%)")
        
        # ========== FOOTER CON TIMESTAMP ==========
        st.markdown("---")
        st.caption(f"📅 Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ========================
    # TAB DASHBOARD
    # ========================
    
    def render_dashboard(self):
        """Renderiza la pestaña del dashboard"""
        st.header("Dashboard Ejecutivo")
        
        df = self.db_manager.cargar_datos()
        meta_actual = self.db_manager.obtener_meta_mes_actual()
        
        if not df.empty:
            df = self.db_manager.agregar_campos_faltantes(df)
            
            # Aplicar filtro de mes si está seleccionado
            mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
            if mes_filter != "Todos":
                df = df[df["mes_factura"] == mes_filter]
                st.info(f"📅 Mostrando datos de: {mes_filter}")
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        if not df.empty:
            metricas = self.metrics_calc.calcular_metricas_separadas(df)
            facturas_pendientes = len(df[df["pagado"] == False])
        else:
            metricas = self.metrics_calc.calcular_metricas_separadas(pd.DataFrame())
            facturas_pendientes = 0
        
        with col1:
            st.metric(
                "Ventas Meta (Propios)",
                format_currency(metricas["ventas_propios"]),
                help="Solo clientes propios cuentan para la meta"
            )
        
        with col2:
            total_comisiones = metricas["comision_propios"] + metricas["comision_externos"]
            st.metric("Comisión Total", format_currency(total_comisiones))
        
        with col3:
            st.metric("Facturas Pendientes", facturas_pendientes)
        
        with col4:
            st.metric("% Clientes Propios", f"{metricas['porcentaje_propios']:.1f}%")
        
        # Desglose por tipo de cliente
        st.markdown("---")
        st.markdown("### Desglose por Tipo de Cliente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Clientes Propios (Para Meta)")
            st.metric("Ventas", format_currency(metricas["ventas_propios"]))
            st.metric("Comisión", format_currency(metricas["comision_propios"]))
            st.metric("Facturas", metricas["facturas_propios"])
        
        with col2:
            st.markdown("#### Clientes Externos (Solo Comisión)")
            st.metric("Ventas", format_currency(metricas["ventas_externos"]))
            st.metric("Comisión", format_currency(metricas["comision_externos"]))
            st.metric("Facturas", metricas["facturas_externos"])
        
        st.markdown("---")
        
        # Contenedor principal para alinear todo
        with st.container():
            # Progreso Meta y Recomendaciones IA
            col1, col2 = st.columns([1, 1])
            
            with col1:
                self._render_progreso_meta(df, meta_actual)
            
            with col2:
                self._render_progreso_clientes_nuevos(df, meta_actual)
            
            # Recomendaciones motivacionales - Mismo ancho que las columnas de arriba
            self._render_recomendaciones_motivacionales(df, meta_actual)
    
    def _render_progreso_meta(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza el progreso de la meta mensual"""
        st.markdown("### Progreso Meta Mensual")
        
        progreso_data = self.metrics_calc.calcular_progreso_meta(df, meta_actual)
        
        meta = progreso_data["meta_ventas"]
        actual = progreso_data["ventas_actuales"]
        progreso_meta = progreso_data["progreso"]
        faltante = progreso_data["faltante"]
        
        dias_restantes = max(1, (date(date.today().year, 12, 31) - date.today()).days)
        velocidad_necesaria = faltante / dias_restantes
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Meta", format_currency(meta))
        with col_b:
            st.metric("Actual", format_currency(actual))
        with col_c:
            st.metric("Faltante", format_currency(faltante))
        
        color = "#10b981" if progreso_meta > 80 else "#f59e0b" if progreso_meta > 50 else "#ef4444"
        st.markdown(f"""
        <div class="progress-bar" style="margin: 1rem 0;">
            <div class="progress-fill" style="width: {min(progreso_meta, 100)}%; background: {color}"></div>
        </div>
        <p><strong>{progreso_meta:.1f}%</strong> completado | <strong>Necesitas:</strong> {format_currency(velocidad_necesaria)}/día</p>
        """, unsafe_allow_html=True)
    
    def _render_progreso_clientes_nuevos(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza el progreso de la meta de clientes nuevos"""
        st.markdown("### Meta Clientes Nuevos (2025)")
        
        # Obtener meta de clientes nuevos
        meta_clientes = meta_actual.get("meta_clientes_nuevos", 0)
        
        # Calcular clientes nuevos del mes actual basándose en el campo cliente_nuevo
        clientes_nuevos_lista = []
        if not df.empty:
            mes_actual = date.today().strftime("%Y-%m")
            
            # Filtrar por mes actual para otras métricas
            df_mes_actual = df[df["mes_factura"] == mes_actual]
            
            # Obtener año actual para la meta de clientes nuevos
            anio_actual = date.today().strftime("%Y")
            df_anio_actual = df[df["mes_factura"].str.startswith(anio_actual)]
            
            # Verificar si existe la columna cliente_nuevo
            if 'cliente_nuevo' in df.columns:
                # Contar clientes únicos marcados como nuevos DEL AÑO ACTUAL
                # (Los clientes nuevos son una meta anual, no mensual)
                df_clientes_nuevos = df_anio_actual[df_anio_actual["cliente_nuevo"] == True]
                clientes_nuevos_lista = sorted(df_clientes_nuevos["cliente"].unique().tolist())
                clientes_nuevos_mes = len(clientes_nuevos_lista)
            else:
                # Fallback: usar lógica anterior si no existe el campo
                df_mes_propios = df_mes_actual[df_mes_actual["cliente_propio"] == True]
                clientes_mes_actual = set(df_mes_propios["cliente"].unique())
                
                df_meses_anteriores = df[df["mes_factura"] < mes_actual]
                clientes_anteriores = set(df_meses_anteriores["cliente"].unique())
                
                clientes_nuevos = clientes_mes_actual - clientes_anteriores
                
                # Lista de palabras clave para excluir
                palabras_excluidas = [
                    "BLANCO CAMARGO",
                    "INVERSIONES CÁRDENAS",
                    "CARDENAS PIEDRAHITA"
                ]
                
                clientes_filtrados = []
                for cliente in clientes_nuevos:
                    excluir = False
                    for palabra in palabras_excluidas:
                        if palabra.upper() in cliente.upper():
                            excluir = True
                            break
                    if not excluir:
                        clientes_filtrados.append(cliente)
                
                clientes_nuevos_lista = sorted(clientes_filtrados)
                clientes_nuevos_mes = len(clientes_nuevos_lista)
        else:
            clientes_nuevos_mes = 0
        
        # Calcular progreso
        if meta_clientes > 0:
            progreso_clientes = (clientes_nuevos_mes / meta_clientes) * 100
        else:
            progreso_clientes = 0
        
        faltante_clientes = max(0, meta_clientes - clientes_nuevos_mes)
        
        # Calcular velocidad necesaria (días restantes del mes)
        hoy = date.today()
        if hoy.month == 12:
            ultimo_dia_mes = date(hoy.year, 12, 31)
        else:
            ultimo_dia_mes = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
        
        dias_restantes = max(1, (ultimo_dia_mes - hoy).days + 1)
        
        if dias_restantes > 0 and faltante_clientes > 0:
            clientes_por_dia = faltante_clientes / dias_restantes
        else:
            clientes_por_dia = 0
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Meta", f"{meta_clientes} clientes")
        with col_b:
            st.metric("Actual", f"{clientes_nuevos_mes} clientes")
        with col_c:
            st.metric("Faltante", f"{faltante_clientes} clientes")
        
        color = "#10b981" if progreso_clientes > 80 else "#f59e0b" if progreso_clientes > 50 else "#ef4444"
        st.markdown(f"""
        <div class="progress-bar" style="margin: 1rem 0;">
            <div class="progress-fill" style="width: {min(progreso_clientes, 100)}%; background: {color}"></div>
        </div>
        <p><strong>{progreso_clientes:.1f}%</strong> completado | <strong>Necesitas:</strong> {clientes_por_dia:.1f} clientes/día</p>
        """, unsafe_allow_html=True)
    
    def _render_recomendaciones_motivacionales(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza recomendaciones motivacionales basadas en el progreso"""
        
        # Calcular datos del presupuesto
        progreso_data = self.metrics_calc.calcular_progreso_meta(df, meta_actual)
        meta = progreso_data["meta_ventas"]
        actual = progreso_data["ventas_actuales"]
        faltante = progreso_data["faltante"]
        progreso = progreso_data["progreso"]
        
        # Calcular días restantes del mes
        hoy = date.today()
        if hoy.month == 12:
            ultimo_dia_mes = date(hoy.year, 12, 31)
        else:
            ultimo_dia_mes = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
        
        dias_restantes = max(1, (ultimo_dia_mes - hoy).days + 1)
        
        # Frases motivacionales según el cumplimiento de la meta
        if progreso >= 100:
            # Meta cumplida - Frases de celebración que cambian
            frases_motivacionales = [
                "🏆 ¡Eres un campeón! Tu dedicación dio sus frutos.",
                "⭐ ¡Extraordinario! Superaste todas las expectativas.",
                "🎯 ¡Perfección! Tu profesionalismo es ejemplar.",
                "💫 ¡Imparable! Has elevado el estándar de excelencia.",
                "🌟 ¡Brillante! Tu éxito inspira a todos.",
                "🚀 ¡A otro nivel! Tu potencial no tiene límites.",
                "💎 ¡Valioso! Has demostrado tu verdadero poder.",
                "🎊 ¡Victoria merecida! Disfruta tu logro.",
                "🏅 ¡Medallista de oro! Tu esfuerzo vale oro.",
                "🌈 ¡Llegaste al tesoro! El éxito es tuyo.",
                "🔥 ¡Imparable! Tu pasión te llevó a la cima.",
                "💪 ¡Fuerza titánica! Nada puede detenerte.",
                "🎨 ¡Obra maestra! Tu trabajo es arte puro.",
                "🦅 ¡Vuelo perfecto! Alcanzaste las alturas."
            ]
        elif progreso >= 80:
            # Muy cerca - Frases de último empujón que cambian
            frases_motivacionales = [
                "💪 ¡Casi lo logras! Un último empujón y es tuyo.",
                "🎯 ¡A un paso! La meta está tan cerca.",
                "🔥 ¡Último tramo! Dale todo lo que tienes.",
                "🚀 ¡Sprint final! Acelera hacia la victoria.",
                "⭐ ¡Tan cerca! Puedes lograrlo.",
                "🏃 ¡Último esfuerzo! Cruza la línea de meta.",
                "💫 ¡La cima te espera! Solo un poco más.",
                "🎊 ¡Casi celebramos! Termina con fuerza.",
                "🌟 ¡Gran trayectoria! El final será épico.",
                "💎 ¡Casi pulido! Último toque brillante."
            ]
        elif progreso >= 50:
            # A mitad - Frases de motivación que cambian
            frases_motivacionales = [
                "💪 ¡Vas bien! Mantén el ritmo ganador.",
                "🎯 ¡Mitad del camino! Sigue avanzando firme.",
                "🚀 ¡Buen progreso! Acelera el paso ahora.",
                "⭐ ¡Vas por buen camino! No pares.",
                "🔥 ¡Encendido! Mantén viva tu pasión.",
                "🌟 ¡Brillando! Continúa iluminando el camino.",
                "💫 ¡Firme! Cada día te acerca más.",
                "🏃 ¡Buen ritmo! La meta se acerca.",
                "💎 ¡Valor creciente! Sigues puliéndote."
            ]
        else:
            # Inicio - Frases de ánimo que cambian
            frases_motivacionales = [
                "💪 ¡Tú puedes! Cada gran logro comienza ahora.",
                "🎯 ¡Enfócate! La constancia vence todo.",
                "🔥 ¡Enciéndete! El éxito requiere acción.",
                "🚀 ¡Despega! Tu potencial es enorme.",
                "⭐ ¡Brilla! Este es tu momento.",
                "💫 ¡Persiste! Los logros toman tiempo.",
                "🌟 ¡Adelante! Cada esfuerzo suma.",
                "🏃 ¡Acelera! El tiempo es ahora.",
                "💎 ¡Eres valioso! Demuéstralo hoy.",
                "🦅 ¡Levántate! Vuela contra el viento.",
                "🌺 ¡Florece! Incluso en lo difícil creces."
            ]
        
        # Seleccionar frase del día (basada en el día del mes, ajustada al tamaño de la lista)
        indice_frase = hoy.day % len(frases_motivacionales)
        frase_del_dia = frases_motivacionales[indice_frase]
        
        # Tarjeta motivacional - Ancho completo
        st.markdown("---")
        
        # Generar recomendaciones según el progreso
        if progreso >= 100:
            # Meta cumplida
            st.success(f"""
            ### 🎉 ¡META CUMPLIDA! 
            
            **¡Felicitaciones!** Has superado la meta del mes con **{format_currency(actual)}**. 
            ¡Excelente trabajo! 🏆
            
            {frase_del_dia}
            """)
        elif progreso >= 80:
            # Muy cerca de la meta
            venta_necesaria_por_dia = faltante / dias_restantes
            dias_para_meta = int(faltante / venta_necesaria_por_dia) if venta_necesaria_por_dia > 0 else 0
            
            st.info(f"""
            ### 🎯 ¡Casi lo logras! 💪
            
            **Te falta:** {format_currency(faltante)} para cumplir la meta
            
            **Plan de acción:**
            - Si vendes **{format_currency(venta_necesaria_por_dia)}** diarios, cumplirás la meta en **{dias_para_meta} días** 📈
            - Tienes **{dias_restantes} días** para cerrar este mes con éxito
            - Estás en el **{progreso:.1f}%** - ¡Un último empujón! 💪
            
            {frase_del_dia}
            """)
        elif progreso >= 50:
            # A medio camino
            venta_necesaria_por_dia = faltante / dias_restantes
            
            st.warning(f"""
            ### 💼 ¡Vas por buen camino!
            
            **Te falta:** {format_currency(faltante)} para cumplir la meta
            
            **Plan de acción:**
            - Necesitas vender **{format_currency(venta_necesaria_por_dia)}** por día
            - Quedan **{dias_restantes} días** para alcanzar la meta
            - Llevas **{progreso:.1f}%** completado - ¡Sigue así! ⚡
            
            {frase_del_dia}
            """)
        else:
            # Inicio del mes o bajo progreso
            venta_necesaria_por_dia = faltante / dias_restantes
            
            st.error(f"""
            ### 🚀 ¡Es hora de acelerar!
            
            **Te falta:** {format_currency(faltante)} para cumplir la meta
            
            **Plan de acción:**
            - Necesitas vender **{format_currency(venta_necesaria_por_dia)}** diarios
            - Tienes **{dias_restantes} días** por delante - ¡Usa el tiempo sabiamente! ⏰
            - Llevas **{progreso:.1f}%** - ¡Cada día cuenta! 🔥
            
            {frase_del_dia}
            """)
    
    # ========================
    # TAB COMISIONES
    # ========================
    
    def render_comisiones(self):
        """Renderiza la pestaña de gestión de comisiones"""
        st.header("Gestión de Comisiones")
        
        # Botón para limpiar cache
        col_refresh, col_empty = st.columns([1, 3])
        with col_refresh:
            if st.button("🔄 Actualizar Datos", type="secondary"):
                self.db_manager.limpiar_cache()
                keys_to_delete = [key for key in st.session_state.keys() if key.startswith('show_')]
                for key in keys_to_delete:
                    del st.session_state[key]
                st.rerun()
        
        # Filtros
        with st.container():
            st.markdown("### Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                estado_filter = st.selectbox("Estado", ["Todos", "Pendientes", "Pagadas", "Vencidas"], key="estado_filter_comisiones")
            with col2:
                # Obtener lista de clientes para el desplegable
                lista_clientes = self.db_manager.obtener_lista_clientes()
                opciones_clientes = ["Todos"] + lista_clientes
                cliente_filter = st.selectbox("Cliente", opciones_clientes, key="comisiones_cliente_filter")
            with col3:
                monto_min = st.number_input("Valor mínimo", min_value=0, value=0, step=100000)
            with col4:
                aplicar_filtros = st.button("🔍 Aplicar Filtros")
        
        # Cargar y filtrar datos
        df = self.db_manager.cargar_datos()
        
        if not df.empty:
            df = self.db_manager.agregar_campos_faltantes(df)
            
            # Aplicar filtro de mes del sidebar (solo si hay datos y el mes existe)
            try:
                mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
                if mes_filter != "Todos" and "mes_factura" in df.columns:
                    df = df[df["mes_factura"] == mes_filter]
                    if not df.empty:
                        st.info(f"📅 Filtrando por mes: {mes_filter}")
            except Exception:
                pass  # Ignorar errores de filtrado
            
            df_filtrado = self._aplicar_filtros_comisiones(df, estado_filter, cliente_filter, monto_min)
        else:
            df_filtrado = pd.DataFrame()
        
        # Mostrar resumen
        self._render_resumen_comisiones(df_filtrado)
        
        st.markdown("---")
        
        # Mostrar facturas
        if not df_filtrado.empty:
            self._render_facturas_detalladas(df_filtrado)
        else:
            st.info("No hay facturas que coincidan con los filtros aplicados")
            if df.empty:
                st.warning("No hay datos en la base de datos. Registra tu primera venta en la pestaña 'Nueva Venta'.")
    
    def _aplicar_filtros_comisiones(self, df: pd.DataFrame, estado_filter: str, 
                                   cliente_filter: str, monto_min: float) -> pd.DataFrame:
        """Aplica los filtros seleccionados a los datos de comisiones"""
        df_filtrado = df.copy()
        
        if estado_filter == "Pendientes":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == False]
        elif estado_filter == "Pagadas":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == True]
        elif estado_filter == "Vencidas":
            df_filtrado = df_filtrado[
                (df_filtrado["dias_vencimiento"].notna()) & 
                (df_filtrado["dias_vencimiento"] < 0) & 
                (df_filtrado["pagado"] == False)
            ]
        
        # Filtrar por cliente (exacto si se selecciona uno del desplegable)
        if cliente_filter and cliente_filter != "Todos":
            df_filtrado = df_filtrado[df_filtrado["cliente"] == cliente_filter]
        
        if monto_min > 0:
            df_filtrado = df_filtrado[df_filtrado["valor"] >= monto_min]
        
        return df_filtrado
    
    def _render_resumen_comisiones(self, df_filtrado: pd.DataFrame):
        """Renderiza el resumen de comisiones"""
        if not df_filtrado.empty:
            st.markdown("### Resumen")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Facturas", len(df_filtrado))
            with col2:
                st.metric("Total Comisiones", format_currency(df_filtrado["comision"].sum()))
            with col3:
                st.metric("Valor Promedio", format_currency(df_filtrado["valor"].mean()))
            with col4:
                pendientes = len(df_filtrado[df_filtrado["pagado"] == False])
                st.metric("Pendientes", pendientes)
    
    def _render_facturas_detalladas(self, df_filtrado: pd.DataFrame):
        """Renderiza las facturas con detalles y acciones"""
        st.markdown("### Facturas Detalladas")
        
        # Ordenar por prioridad
        def calcular_prioridad(row):
            if row['pagado']:
                return 3
            elif row.get('dias_vencimiento') is not None:
                if row['dias_vencimiento'] < 0:
                    return 0
                elif row['dias_vencimiento'] <= 5:
                    return 1
                else:
                    return 2
            return 2
        
        df_filtrado['prioridad'] = df_filtrado.apply(calcular_prioridad, axis=1)
        df_filtrado = df_filtrado.sort_values(['prioridad', 'fecha_factura'], ascending=[True, False])
        
        for index, (_, factura) in enumerate(df_filtrado.iterrows()):
            factura_id = factura.get('id')
            if not factura_id:
                continue
            
            # Renderizar card de factura
            self.ui_components.render_factura_card(factura, index)
            
            # Renderizar botones de acción
            actions = self.ui_components.render_factura_action_buttons(factura, index)
            
            # Procesar acciones
            self._procesar_acciones_factura(factura, actions)
            
            st.markdown("---")
    
    def _procesar_acciones_factura(self, factura: pd.Series, actions: Dict[str, bool]):
        """Procesa las acciones de los botones de factura"""
        factura_id = factura.get('id')
        
        # Limpiar otros estados si se presiona una nueva acción
        if any(actions.values()):
            for key in list(st.session_state.keys()):
                if key.startswith(f"show_") and str(factura_id) in key:
                    del st.session_state[key]
        
        if actions.get('edit'):
            st.session_state[f"show_edit_{factura_id}"] = True
            st.rerun()
        
        if actions.get('pay'):
            st.session_state[f"show_pago_{factura_id}"] = True
            st.rerun()
        
        if actions.get('detail'):
            st.session_state[f"show_detail_{factura_id}"] = True
            st.rerun()
        
        if actions.get('comprobante'):
            st.session_state[f"show_comprobante_{factura_id}"] = True
            st.rerun()
        
        # Mostrar modales según el estado
        self._mostrar_modales_factura(factura)
    
    def _mostrar_modales_factura(self, factura: pd.Series):
        """Muestra los modales según el estado de la sesión"""
        factura_id = factura.get('id')
        
        if st.session_state.get(f"show_edit_{factura_id}", False):
            with st.expander(f"✏️ Editando: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_modal_editar(factura)
        
        if st.session_state.get(f"show_pago_{factura_id}", False):
            with st.expander(f"💳 Procesando Pago: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_modal_pago(factura)
        
        if st.session_state.get(f"show_comprobante_{factura_id}", False):
            with st.expander(f"📄 Comprobante: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_comprobante(factura.get("comprobante_url"))
                if st.button("❌ Cerrar", key=f"close_comp_{factura_id}"):
                    del st.session_state[f"show_comprobante_{factura_id}"]
                    st.rerun()
        
        if st.session_state.get(f"show_detail_{factura_id}", False):
            with st.expander(f"📊 Detalles: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_detalles_completos(factura)
                if st.button("❌ Cerrar", key=f"close_detail_{factura_id}"):
                    del st.session_state[f"show_detail_{factura_id}"]
                    st.rerun()
    
    # ========================
    # TAB NUEVA VENTA
    # ========================
    
    def render_nueva_venta(self):
        """Renderiza la pestaña de nueva venta"""
        st.header("Registrar Nueva Venta")
        
        # Obtener lista de clientes existentes
        lista_clientes = self.db_manager.obtener_lista_clientes()
        
        # Selector de cliente FUERA del formulario para que se actualice dinámicamente
        st.markdown("### Seleccionar Cliente")
        col_sel1, col_sel2 = st.columns([2, 1])
        
        with col_sel1:
            opciones_clientes = ["-- Nuevo Cliente --"] + lista_clientes
            cliente_seleccionado = st.selectbox(
                "Cliente",
                opciones_clientes,
                key="nueva_venta_cliente_select",
                help="Selecciona un cliente existente para auto-completar sus datos"
            )
        
        with col_sel2:
            if cliente_seleccionado != "-- Nuevo Cliente --":
                patron = self.db_manager.obtener_patron_cliente(cliente_seleccionado)
                if patron['existe']:
                    st.success(f"📊 {patron['num_compras']} compra(s)")
                    st.caption(f"Últ: {patron['ultima_compra'].strftime('%d/%m/%Y') if patron['ultima_compra'] else 'N/A'}")
        
        # Obtener patrón del cliente seleccionado
        patron_cliente = {}
        if cliente_seleccionado != "-- Nuevo Cliente --":
            patron_cliente = self.db_manager.obtener_patron_cliente(cliente_seleccionado)
        
        # Mostrar info del patrón si existe
        if patron_cliente.get('existe', False):
            st.info(f"""
            **Configuración habitual de {cliente_seleccionado}:**
            - Cliente Propio: {'✅ Sí' if patron_cliente['cliente_propio'] else '❌ No'}
            - Descuento a Pie: {'✅ Sí' if patron_cliente['descuento_pie_factura'] else '❌ No'}
            - Condición Especial: {'✅ Sí' if patron_cliente['condicion_especial'] else '❌ No'}
            - Desc. Adicional Promedio: {patron_cliente['descuento_adicional']:.1f}% (informativo)
            """)
        
        st.markdown("---")
        
        # Formulario con valores por defecto basados en el patrón
        with st.form("nueva_venta_form", clear_on_submit=False):
            st.markdown("### Información Básica")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pedido = st.text_input("Número de Pedido *", placeholder="Ej: PED-001", key="nueva_venta_pedido")
                
                # Campo de texto para cliente (pre-llenado si hay selección)
                cliente_default = cliente_seleccionado if cliente_seleccionado != "-- Nuevo Cliente --" else ""
                cliente = st.text_input(
                    "Nombre del Cliente *", 
                    value=cliente_default,
                    placeholder="Ej: DISTRIBUIDORA CENTRAL", 
                    key="nueva_venta_cliente_nombre"
                )
                
                factura = st.text_input("Número de Factura", placeholder="Ej: FAC-1001", key="nueva_venta_factura")
            
            with col2:
                fecha_factura = st.date_input("Fecha de Factura *", value=date.today(), key="nueva_venta_fecha")
                valor_total = st.number_input("Valor Total (con IVA) *", min_value=0.0, step=10000.0, format="%.0f", key="nueva_venta_valor")
                
                # Checkbox para marcar si es cliente nuevo - SIMPLIFICADO
                es_cliente_nuevo = st.checkbox(
                    "Cliente Nuevo (cuenta para meta)", 
                    value=False,
                    key="nueva_venta_es_cliente_nuevo",
                    help="Marca esto si es la primera vez que este cliente compra"
                )
            
            st.markdown("### Información de Envío")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ciudad_destino = st.selectbox(
                    "Ciudad de Destino *",
                    options=["Medellín", "Bogotá", "Resto"],
                    index=0,
                    key="nueva_venta_ciudad",
                    help="Ciudad donde se enviará el pedido"
                )
            
            with col2:
                # Checkbox de recogida local (solo visible si es Medellín)
                if ciudad_destino == "Medellín":
                    recogida_local = st.checkbox(
                        "Recogida Local",
                        value=False,
                        key="nueva_venta_recogida_local",
                        help="El cliente recoge el pedido localmente (sin flete)"
                    )
                else:
                    recogida_local = False
            
            # Determinar si debe tener flete (para mostrar el campo)
            if valor_total > 0:
                from business.freight_validator import FreightValidator
                valor_neto_temp = valor_total / 1.19
                debe_tener_flete, _ = FreightValidator.debe_tener_flete(
                    valor_neto_temp, ciudad_destino, recogida_local
                )
            else:
                debe_tener_flete = False
            
            with col3:
                # Campo de flete (siempre visible pero con ayuda contextual)
                if debe_tener_flete:
                    valor_flete = st.number_input(
                        "Valor Flete ⚠️",
                        min_value=0.0,
                        step=10000.0,
                        format="%.0f",
                        value=0.0,
                        key="nueva_venta_flete",
                        help="⚠️ Este pedido DEBE incluir flete"
                    )
                else:
                    valor_flete = st.number_input(
                        "Valor Flete (opcional)",
                        min_value=0.0,
                        step=10000.0,
                        format="%.0f",
                        value=0.0,
                        key="nueva_venta_flete",
                        help="✅ Este pedido NO requiere flete"
                    )
            
            st.markdown("### Configuración de Comisión")
            
            # Usar valores del patrón como defaults (excepto descuento adicional que siempre es 0)
            cliente_propio_default = patron_cliente.get('cliente_propio', False) if patron_cliente else False
            descuento_pie_default = patron_cliente.get('descuento_pie_factura', False) if patron_cliente else False
            condicion_especial_default = patron_cliente.get('condicion_especial', False) if patron_cliente else False
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cliente_propio = st.checkbox("Cliente Propio", value=cliente_propio_default, key="nueva_venta_cliente_propio")
            with col2:
                descuento_pie_factura = st.checkbox("Descuento a Pie", value=descuento_pie_default, key="nueva_venta_descuento_pie")
            with col3:
                condicion_especial = st.checkbox("Condición Especial", value=condicion_especial_default, key="nueva_venta_condicion")
            with col4:
                descuento_adicional = st.number_input("Desc. Adicional (%)", min_value=0.0, max_value=100.0, step=0.5, value=0.0, key="nueva_venta_descuento_adicional")
            
            # Preview de cálculos
            if valor_total > 0:
                st.markdown("---")
                st.markdown("### Preview de Comisión")
                
                # IMPORTANTE: Restar el flete antes de calcular la comisión
                # El flete NO se incluye en la base de comisión
                valor_productos = valor_total - valor_flete
                
                calc = self.comision_calc.calcular_comision_inteligente(valor_productos, cliente_propio, descuento_adicional, descuento_pie_factura)
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Valor Productos", format_currency(valor_productos))
                with col2:
                    st.metric("Flete", format_currency(valor_flete))
                with col3:
                    st.metric("Subtotal Cliente", format_currency(calc['valor_neto'] + valor_flete))
                with col4:
                    st.metric("IVA (19%)", format_currency(calc['iva']))
                with col5:
                    st.metric("TOTAL CLIENTE", format_currency(valor_total))
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Base Comisión", format_currency(calc['base_comision']))
                with col2:
                    st.metric("Porcentaje", f"{calc['porcentaje']}%")
                with col3:
                    st.metric("Comisión Final", format_currency(calc['comision']))
                
                # Validación de flete
                from business.freight_validator import FreightValidator
                debe_tener_flete, razon_flete = FreightValidator.debe_tener_flete(
                    calc['base_comision'], ciudad_destino, recogida_local
                )
                
                # Mostrar alerta de flete
                if debe_tener_flete:
                    if valor_flete > 0:
                        st.success(f"✅ **Flete incluido correctamente: {format_currency(valor_flete)}**")
                    else:
                        st.warning(f"⚠️ **Este pedido debe incluir flete**\n\n{razon_flete}")
                else:
                    if valor_flete > 0:
                        st.info(f"ℹ️ **Flete opcional agregado: {format_currency(valor_flete)}**\n\n{razon_flete}")
                    else:
                        st.success(f"✅ **Este pedido NO requiere flete**\n\n{razon_flete}")
                
                st.info(f"""
                **Detalles del cálculo:**
                - Tipo cliente: {'Propio' if cliente_propio else 'Externo'}
                - Porcentaje comisión: {calc['porcentaje']}%
                - {'Descuento aplicado en factura' if descuento_pie_factura else 'Sin descuento a pie'}
                - Descuento adicional: {descuento_adicional}%
                - **Nota:** El flete NO afecta la base de comisión
                """)
            
            st.markdown("---")
            
            # Botones
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                submit = st.form_submit_button("Registrar Venta", type="primary", use_container_width=True)
            
            with col2:
                if st.form_submit_button("Limpiar", use_container_width=True):
                    st.rerun()
            
            with col3:
                if st.form_submit_button("Previsualizar", use_container_width=True):
                    if pedido and cliente and valor_total > 0:
                        st.success("Los datos se ven correctos para registrar")
                    else:
                        st.warning("Faltan campos obligatorios")
            
            # Lógica de guardado
            if submit:
                self._procesar_nueva_venta(pedido, cliente, factura, fecha_factura, valor_total, 
                                         condicion_especial, cliente_propio, descuento_pie_factura, 
                                         descuento_adicional, es_cliente_nuevo, ciudad_destino, recogida_local, valor_flete)
    
    def _procesar_nueva_venta(self, pedido: str, cliente: str, factura: str, fecha_factura: date,
                             valor_total: float, condicion_especial: bool, cliente_propio: bool,
                             descuento_pie_factura: bool, descuento_adicional: float, es_cliente_nuevo: bool = False,
                             ciudad_destino: str = "Resto", recogida_local: bool = False, valor_flete: float = 0):
        """Procesa el registro de una nueva venta"""
        if pedido and cliente and valor_total > 0:
            try:
                # Calcular fechas
                dias_pago = 60 if condicion_especial else 35
                dias_max = 60 if condicion_especial else 45
                fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
                fecha_pago_max = fecha_factura + timedelta(days=dias_max)
                
                # IMPORTANTE: Restar el flete antes de calcular la comisión
                # El flete NO se incluye en la base de comisión
                valor_productos = valor_total - valor_flete
                
                # Calcular comisión
                calc = self.comision_calc.calcular_comision_inteligente(valor_productos, cliente_propio, descuento_adicional, descuento_pie_factura)
                
                # Preparar datos
                data = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "factura": factura if factura else f"FAC-{pedido}",
                    "valor": float(valor_total),
                    "valor_neto": float(calc['valor_neto']),
                    "iva": float(calc['iva']),
                    "base_comision": float(calc['base_comision']),
                    "comision": float(calc['comision']),
                    "porcentaje": float(calc['porcentaje']),
                    "fecha_factura": fecha_factura.isoformat(),
                    "fecha_pago_est": fecha_pago_est.isoformat(),
                    "fecha_pago_max": fecha_pago_max.isoformat(),
                    "cliente_propio": cliente_propio,
                    "descuento_pie_factura": descuento_pie_factura,
                    "descuento_adicional": float(descuento_adicional),
                    "condicion_especial": condicion_especial,
                    "cliente_nuevo": es_cliente_nuevo,
                    "ciudad_destino": ciudad_destino,
                    "recogida_local": recogida_local,
                    "valor_flete": float(valor_flete),
                    "pagado": False
                }
                
                # Insertar
                if self.db_manager.insertar_venta(data):
                    st.success("¡Venta registrada correctamente!")
                    st.success(f"Comisión calculada: {format_currency(calc['comision'])}")
                    st.balloons()
                    
                    # Mostrar resumen
                    st.markdown("### Resumen de la venta:")
                    st.write(f"**Cliente:** {cliente}")
                    st.write(f"**Pedido:** {pedido}")
                    st.write(f"**Valor:** {format_currency(valor_total)}")
                    st.write(f"**Comisión:** {format_currency(calc['comision'])} ({calc['porcentaje']}%)")
                    st.write(f"**Fecha límite pago:** {fecha_pago_max.strftime('%d/%m/%Y')}")
                else:
                    st.error("Error al registrar la venta")
                    
            except Exception as e:
                st.error(f"Error procesando la venta: {str(e)}")
        else:
            st.error("Por favor completa todos los campos marcados con *")
    
    # ========================
    # TAB DEVOLUCIONES
    # ========================
    
    def render_devoluciones(self):
        """Renderiza la pestaña de devoluciones"""
        st.header("Gestión de Devoluciones")
        
        # Botones de acción
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("➕ Nueva Devolución", type="primary"):
                st.session_state['show_nueva_devolucion'] = True
                st.rerun()
        
        with col2:
            if st.button("🔄 Actualizar", type="secondary"):
                self.db_manager.limpiar_cache()
                st.rerun()
        
        # Modal nueva devolución
        if st.session_state.get('show_nueva_devolucion', False):
            with st.expander("➕ Nueva Devolución", expanded=True):
                facturas_df = self.db_manager.obtener_facturas_para_devolucion()
                self.ui_components.render_modal_nueva_devolucion(facturas_df)
        
        st.markdown("---")
        
        # Cargar y mostrar devoluciones
        df_devoluciones = self.db_manager.cargar_devoluciones()
        
        # Aplicar filtro de mes del sidebar si hay devoluciones
        if not df_devoluciones.empty:
            try:
                mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
                if mes_filter != "Todos" and 'fecha_devolucion' in df_devoluciones.columns:
                    df_devoluciones['mes_devolucion'] = pd.to_datetime(df_devoluciones['fecha_devolucion']).dt.to_period('M').astype(str)
                    df_devoluciones = df_devoluciones[df_devoluciones['mes_devolucion'] == mes_filter]
                    if not df_devoluciones.empty:
                        st.info(f"📅 Mostrando devoluciones de: {mes_filter}")
            except Exception:
                pass
        
        if not df_devoluciones.empty:
            self._render_resumen_devoluciones(df_devoluciones)
            self._render_devoluciones_detalladas(df_devoluciones)
        else:
            self._render_ayuda_devoluciones()
    
    def _render_resumen_devoluciones(self, df_devoluciones: pd.DataFrame):
        """Renderiza el resumen de devoluciones"""
        st.markdown("### Resumen")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Devoluciones", len(df_devoluciones))
        with col2:
            total_devuelto = df_devoluciones['valor_devuelto'].sum()
            st.metric("Valor Total Devuelto", format_currency(total_devuelto))
        with col3:
            afectan_comision = len(df_devoluciones[df_devoluciones['afecta_comision'] == True])
            st.metric("Afectan Comisión", afectan_comision)
        with col4:
            valor_promedio = df_devoluciones['valor_devuelto'].mean()
            st.metric("Valor Promedio", format_currency(valor_promedio))
    
    def _render_filtros_devoluciones(self):
        """Renderiza filtros para devoluciones"""
        st.markdown("### Filtros")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            afecta_filter = st.selectbox("Afecta Comisión", ["Todos", "Sí", "No"], key="afecta_filter_devoluciones")
        with col2:
            cliente_filter = st.text_input("Buscar cliente", key="devoluciones_cliente_filter")
        with col3:
            fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=30))
        with col4:
            fecha_hasta = st.date_input("Hasta", value=date.today())
        
        return {
            "afecta_filter": afecta_filter,
            "cliente_filter": cliente_filter,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta
        }
    
    def _render_devoluciones_detalladas(self, df_devoluciones: pd.DataFrame):
        """Renderiza las devoluciones con filtros aplicados"""
        filtros = self._render_filtros_devoluciones()
        
        # Aplicar filtros
        df_filtrado = self._aplicar_filtros_devoluciones(df_devoluciones, filtros)
        
        st.markdown("---")
        
        if not df_filtrado.empty:
            st.markdown("### Devoluciones Registradas")
            
            df_filtrado = df_filtrado.sort_values('fecha_devolucion', ascending=False)
            
            for index, (_, devolucion) in enumerate(df_filtrado.iterrows()):
                self.ui_components.render_devolucion_card(devolucion, index)
                st.markdown("---")
        else:
            st.info("No hay devoluciones que coincidan con los filtros aplicados")
    
    def _aplicar_filtros_devoluciones(self, df_devoluciones: pd.DataFrame, filtros: Dict[str, Any]) -> pd.DataFrame:
        """Aplica filtros a las devoluciones"""
        df_filtrado = df_devoluciones.copy()
        
        if filtros["afecta_filter"] == "Sí":
            df_filtrado = df_filtrado[df_filtrado['afecta_comision'] == True]
        elif filtros["afecta_filter"] == "No":
            df_filtrado = df_filtrado[df_filtrado['afecta_comision'] == False]
        
        if filtros["cliente_filter"]:
            df_filtrado = df_filtrado[df_filtrado['factura_cliente'].str.contains(filtros["cliente_filter"], case=False, na=False)]
        
        # Filtro por fechas
        df_filtrado['fecha_devolucion'] = pd.to_datetime(df_filtrado['fecha_devolucion'])
        df_filtrado = df_filtrado[
            (df_filtrado['fecha_devolucion'].dt.date >= filtros["fecha_desde"]) &
            (df_filtrado['fecha_devolucion'].dt.date <= filtros["fecha_hasta"])
        ]
        
        return df_filtrado
    
    def _render_ayuda_devoluciones(self):
        """Renderiza ayuda cuando no hay devoluciones"""
        st.info("No hay devoluciones registradas")
        st.markdown("""
        **¿Cómo registrar una devolución?**
        1. Haz clic en "Nueva Devolución"
        2. Selecciona la factura correspondiente
        3. Ingresa el valor y motivo
        4. Indica si afecta la comisión
        5. Registra la devolución
        """)
    
    # ========================
    # TAB CLIENTES
    # ========================
    
    def render_clientes(self):
        """Renderiza la pestaña de gestión de clientes"""
        st.header("Gestión de Clientes")
        st.info("Módulo en desarrollo - Próximamente funcionalidad completa de gestión de clientes")
        
        df = self.db_manager.cargar_datos()
        
        # Aplicar filtro de mes del sidebar
        if not df.empty:
            try:
                mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
                if mes_filter != "Todos" and "mes_factura" in df.columns:
                    df = df[df["mes_factura"] == mes_filter]
                    if not df.empty:
                        st.info(f"📅 Mostrando clientes de: {mes_filter}")
            except Exception:
                pass
        
        if not df.empty:
            self._render_top_clientes(df)
        else:
            st.warning("No hay datos de clientes disponibles")
    
    def _render_top_clientes(self, df: pd.DataFrame):
        """Renderiza el top 10 de clientes"""
        clientes_stats = df.groupby('cliente').agg({
            'valor_neto': ['sum', 'mean', 'count'],
            'comision': 'sum',
            'fecha_factura': 'max'
        }).round(0)
        
        clientes_stats.columns = ['Total Compras', 'Ticket Promedio', 'Número Compras', 'Total Comisiones', 'Última Compra']
        clientes_stats = clientes_stats.sort_values('Total Compras', ascending=False).head(10)
        
        st.markdown("### Top 10 Clientes")
        
        for cliente, row in clientes_stats.iterrows():
            with st.container(border=True):
                st.markdown(f"**{cliente}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", format_currency(row['Total Compras']))
                with col2:
                    st.metric("Ticket", format_currency(row['Ticket Promedio']))
                with col3:
                    st.metric("Compras", int(row['Número Compras']))
                with col4:
                    st.metric("Comisiones", format_currency(row['Total Comisiones']))
    
    # ========================
    # TAB IA & ALERTAS
    # ========================
    
    def render_ia_alertas(self):
        """Renderiza la pestaña de IA y alertas"""
        st.header("Inteligencia Artificial & Alertas")
        
        df = self.db_manager.cargar_datos()
        meta_actual = self.db_manager.obtener_meta_mes_actual()
        
        # Aplicar filtro de mes del sidebar
        if not df.empty:
            try:
                mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
                if mes_filter != "Todos" and "mes_factura" in df.columns:
                    df = df[df["mes_factura"] == mes_filter]
                    if not df.empty:
                        st.info(f"📅 Mostrando análisis de: {mes_filter}")
            except Exception:
                pass
        
        # Análisis predictivo
        self._render_analisis_predictivo(df, meta_actual)
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self._render_alertas_criticas(df)
        
        with col2:
            self._render_recomendaciones_estrategicas()
    
    def _render_analisis_predictivo(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza análisis predictivo con datos reales"""
        st.markdown("### Análisis Predictivo")
        
        # Calcular métricas reales
        prediccion_meta = self.metrics_calc.calcular_prediccion_meta(df, meta_actual)
        tendencia_comisiones = self.metrics_calc.calcular_tendencia_comisiones(df)
        clientes_riesgo = self.metrics_calc.identificar_clientes_riesgo(df)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Predicción Meta",
                value=f"{prediccion_meta['probabilidad']}%",
                delta=f"Proyección: {prediccion_meta['tendencia']}",
                help=f"Basado en velocidad actual vs necesaria. Quedan {prediccion_meta['dias_necesarios']} días"
            )
            
            if prediccion_meta['probabilidad'] < 50:
                st.error(f"⚠️ Necesitas aumentar ventas {format_currency(prediccion_meta.get('velocidad_necesaria', 0))}/día")
            elif prediccion_meta['probabilidad'] > 80:
                st.success("🎯 Muy probable cumplir meta")
            else:
                st.warning("📈 Mantén el ritmo actual")
        
        with col2:
            st.metric(
                label="Tendencia Comisiones",
                value=tendencia_comisiones['crecimiento'],
                delta=tendencia_comisiones['delta'],
                delta_color=tendencia_comisiones.get('direccion', 'normal')
            )
        
        with col3:
            st.metric(
                label="Clientes en Riesgo",
                value=str(clientes_riesgo['cantidad']),
                delta=clientes_riesgo['delta'],
                delta_color="inverse"
            )
            
            if clientes_riesgo['clientes']:
                with st.expander("Ver Detalles", expanded=False):
                    for cliente in clientes_riesgo['clientes']:
                        color = "🚨" if cliente['tipo'] == 'critico' else "⚠️"
                        st.write(f"{color} **{cliente['cliente']}**: {cliente['razon']} (Riesgo: {format_currency(cliente['impacto'])})")
    
    def _render_alertas_criticas(self, df: pd.DataFrame):
        """Renderiza alertas críticas"""
        st.markdown("### Alertas Críticas")
        
        alertas_encontradas = False
        
        if not df.empty:
            # Facturas vencidas (solo no pagadas)
            vencidas = df[
                (df["dias_vencimiento"].notna()) & 
                (df["dias_vencimiento"] < 0) & 
                (df["pagado"] == False)
            ]
            for _, factura in vencidas.head(3).iterrows():
                st.error(f"**Factura Vencida:** {factura.get('cliente', 'N/A')} - {factura.get('pedido', 'N/A')} ({format_currency(factura.get('valor_neto', 0))})")
                alertas_encontradas = True
            
            # Próximas a vencer (solo no pagadas)
            prox_vencer = df[
                (df["dias_vencimiento"].notna()) & 
                (df["dias_vencimiento"] >= 0) & 
                (df["dias_vencimiento"] <= 5) & 
                (df["pagado"] == False)
            ]
            for _, factura in prox_vencer.head(3).iterrows():
                st.warning(f"**Próximo Vencimiento:** {factura.get('cliente', 'N/A')} vence en {factura.get('dias_vencimiento', 0)} días")
                alertas_encontradas = True
            
            # Altas comisiones pendientes
            if not df.empty:
                alto_valor = df[df["comision"] > df["comision"].quantile(0.8)]
                for _, factura in alto_valor.head(2).iterrows():
                    if not factura.get("pagado"):
                        st.info(f"**Alta Comisión Pendiente:** {format_currency(factura.get('comision', 0))} esperando pago")
                        alertas_encontradas = True
        
        if not alertas_encontradas:
            st.success("No hay alertas críticas en este momento")
    
    def _render_recomendaciones_estrategicas(self):
        """Renderiza insights estratégicos del negocio"""
        st.markdown("### Insights Estratégicos")
        
        insights = self.ai_recommendations.generar_recomendaciones_reales()
        
        for i, insight in enumerate(insights):
            prioridad_color = "🔴" if insight.get('prioridad', 'media') == 'alta' else "🟡" if insight.get('prioridad', 'media') == 'media' else "🟢"
            tipo_emoji = {
                'Cartera': '💼',
                'Comisiones': '💰',
                'Clientes': '👥',
                'Ticket': '💎',
                'Riesgo': '🚨',
                'General': '✅',
                'Sin datos': 'ℹ️',
                'Error': '⚠️'
            }.get(insight.get('tipo', 'General'), '📊')
            
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.markdown(f"### {tipo_emoji} {insight.get('titulo', 'Insight')}")
                    st.markdown(f"**Análisis:** {insight.get('insight', 'N/A')}")
                    st.markdown(f"**Métrica:** {insight.get('metrica', 'N/A')}")
                    st.markdown(f"**Acción Recomendada:** {insight.get('accion_recomendada', 'N/A')}")
                    st.markdown(f"**Prioridad:** {prioridad_color} {insight.get('prioridad', 'media').title()}")
                
                with col_b:
                    impacto_valor = insight.get('impacto', 0)
                    if impacto_valor > 0:
                        st.metric(
                            label="Impacto Estimado",
                            value=format_currency(impacto_valor),
                            delta="Potencial" if insight.get('tipo') in ['Cartera', 'Clientes', 'Ticket'] else "En riesgo",
                            delta_color="normal" if insight.get('tipo') in ['Cartera', 'Clientes', 'Ticket'] else "inverse"
                        )
                    else:
                        st.info("N/A")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Actualizar Insights", use_container_width=True, key="btn_actualizar_insights"):
                st.rerun()
        with col2:
            st.caption("Los insights se actualizan automáticamente con cada venta registrada")
    
    # ========================
    # TAB RADICACIÓN FACTURAS
    # ========================
    
    def render_radicacion_facturas(self):
        """Renderiza la pestaña de radicación de facturas"""
        st.header("💬 Mensajes para Clientes")
        
        # Botón de actualizar
        if st.button("🔄 Actualizar", type="secondary", key="btn_actualizar_radicacion"):
            self.db_manager.limpiar_cache()
            st.rerun()
        
        st.markdown("---")
        
        # Pestañas para facturas pendientes, urgentes y búsqueda por cliente
        tab1, tab2, tab3 = st.tabs(["📋 Facturas Pendientes", "🚨 Urgentes", "👤 Buscar Cliente"])
        
        with tab1:
            self._render_facturas_pendientes_radicacion()
        
        with tab2:
            self._render_facturas_urgentes_radicacion()
        
        with tab3:
            self._render_busqueda_cliente_mensaje()
    
    def _render_facturas_pendientes_radicacion(self):
        """Renderiza facturas pendientes para generar mensajes"""
        pendientes = self.invoice_radication.obtener_facturas_pendientes_radicacion()
        
        if pendientes.empty:
            st.info("No hay facturas pendientes en este momento")
            return
        
        st.markdown(f"### {len(pendientes)} Factura(s) Pendiente(s)")
        
        for index, (_, factura) in enumerate(pendientes.iterrows()):
            factura_id = factura.get('id')
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{factura.get('cliente')}**")
                    st.write(f"📋 Pedido: {factura.get('pedido')} | Factura: {factura.get('factura')}")
                    st.write(f"💰 Valor: {format_currency(factura.get('valor', 0))} | Comisión: {format_currency(factura.get('comision', 0))}")
                    st.write(f"📅 Fecha Factura: {factura.get('fecha_factura')}")
                    
                    # Calcular días desde facturación
                    try:
                        fecha_fac = pd.to_datetime(factura.get('fecha_factura'))
                        dias_desde = (pd.Timestamp.now() - fecha_fac).days
                        color_dias = "🟢" if dias_desde <= 3 else "🟡" if dias_desde <= 7 else "🔴"
                        st.caption(f"{color_dias} {dias_desde} días desde la facturación")
                    except:
                        pass
                
                with col2:
                    # Botón para generar mensaje al cliente
                    if st.button("💬 Generar Mensaje", key=f"mensaje_{factura_id}", type="primary", use_container_width=True):
                        st.session_state[f"show_mensaje_{factura_id}"] = True
                        st.rerun()
            
            # Modal para mensaje al cliente
            if st.session_state.get(f"show_mensaje_{factura_id}", False):
                with st.expander(f"💬 Mensaje para Cliente: {factura.get('cliente')}", expanded=True):
                    mensaje = self.invoice_radication.generar_mensaje_cliente(factura)
                    
                    st.markdown("### Mensaje generado:")
                    st.text_area(
                        "Copie este mensaje:",
                        value=mensaje,
                        height=400,
                        key=f"textarea_mensaje_{factura_id}"
                    )
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success("✅ Listo para copiar y enviar al cliente")
                    with col_b:
                        if st.button("❌ Cerrar", key=f"cerrar_mensaje_{factura_id}"):
                            del st.session_state[f"show_mensaje_{factura_id}"]
                            st.rerun()
    
    def _render_facturas_urgentes_radicacion(self):
        """Renderiza facturas vencidas - URGENTE"""
        urgentes = self.invoice_radication.obtener_facturas_vencidas_sin_radicar()
        
        if urgentes.empty:
            st.success("✅ No hay facturas urgentes")
            return
        
        st.error(f"### 🚨 {len(urgentes)} Factura(s) URGENTE(S)")
        st.warning("Estas facturas están vencidas. Envía el mensaje con urgencia para gestionar el cobro.")
        
        for index, (_, factura) in enumerate(urgentes.iterrows()):
            factura_id = factura.get('id')
            dias_vencida = abs(int(factura.get('dias_vencimiento', 0)))
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**🚨 {factura.get('cliente')}**")
                    st.write(f"📋 Pedido: {factura.get('pedido')} | Factura: {factura.get('factura')}")
                    st.write(f"💰 Valor: {format_currency(factura.get('valor', 0))} | Comisión: {format_currency(factura.get('comision', 0))}")
                    st.error(f"⏰ VENCIDA hace {dias_vencida} días")
                
                with col2:
                    # Botón para generar mensaje al cliente
                    if st.button("💬 Generar Mensaje", key=f"mensaje_urgente_{factura_id}", type="primary", use_container_width=True):
                        st.session_state[f"show_mensaje_{factura_id}"] = True
                        st.rerun()
            
            # Modal para mensaje al cliente
            if st.session_state.get(f"show_mensaje_{factura_id}", False):
                with st.expander(f"💬 Mensaje para Cliente: {factura.get('cliente')}", expanded=True):
                    mensaje = self.invoice_radication.generar_mensaje_cliente(factura)
                    
                    st.markdown("### Mensaje generado:")
                    st.text_area(
                        "Copie este mensaje:",
                        value=mensaje,
                        height=400,
                        key=f"textarea_mensaje_urgente_{factura_id}"
                    )
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success("✅ Listo para copiar y enviar al cliente")
                    with col_b:
                        if st.button("❌ Cerrar", key=f"cerrar_mensaje_urgente_{factura_id}"):
                            del st.session_state[f"show_mensaje_{factura_id}"]
                            st.rerun()
    
    def _render_busqueda_cliente_mensaje(self):
        """Renderiza búsqueda de cliente para generar mensajes"""
        st.markdown("### 👤 Buscar Cliente para Generar Mensaje")
        st.info("Selecciona un cliente para ver sus facturas y generar mensajes personalizados")
        
        # Cargar todas las facturas
        df = self.db_manager.cargar_datos()
        
        if df.empty:
            st.warning("No hay facturas registradas")
            return
        
        # Filtrar solo facturas no pagadas
        df_no_pagadas = df[df['pagado'] == False].copy()
        
        if df_no_pagadas.empty:
            st.success("✅ No hay facturas pendientes de pago")
            return
        
        # Obtener lista de clientes únicos con facturas pendientes
        clientes = sorted(df_no_pagadas['cliente'].unique())
        
        # Selectbox para elegir cliente
        cliente_seleccionado = st.selectbox(
            "📋 Seleccione un cliente:",
            options=["-- Seleccione un cliente --"] + list(clientes),
            key="select_cliente_mensaje"
        )
        
        if cliente_seleccionado == "-- Seleccione un cliente --":
            st.info("👆 Seleccione un cliente para ver sus facturas")
            return
        
        # Filtrar facturas del cliente seleccionado
        facturas_cliente = df_no_pagadas[df_no_pagadas['cliente'] == cliente_seleccionado].copy()
        facturas_cliente = facturas_cliente.sort_values('fecha_factura', ascending=False)
        
        st.markdown(f"### 📊 Facturas de: **{cliente_seleccionado}**")
        st.caption(f"Total de facturas pendientes: {len(facturas_cliente)}")
        
        # Mostrar cada factura
        for index, (_, factura) in enumerate(facturas_cliente.iterrows()):
            factura_id = factura.get('id')
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"📋 **Pedido:** {factura.get('pedido')} | **Factura:** {factura.get('factura')}")
                    st.write(f"💰 Valor: {format_currency(factura.get('valor', 0))} | Comisión: {format_currency(factura.get('comision', 0))}")
                    st.write(f"📅 Fecha Factura: {factura.get('fecha_factura')}")
                    
                    # Mostrar estado según días de vencimiento
                    dias_venc = factura.get('dias_vencimiento')
                    if dias_venc is not None:
                        if dias_venc < 0:
                            st.error(f"⚠️ VENCIDA hace {abs(int(dias_venc))} días")
                        elif dias_venc <= 5:
                            st.warning(f"⏰ Vence en {int(dias_venc)} días")
                        else:
                            st.success(f"✅ Vence en {int(dias_venc)} días")
                
                with col2:
                    # Botón para generar mensaje
                    if st.button("💬 Generar Mensaje", key=f"mensaje_busqueda_{factura_id}", type="primary", use_container_width=True):
                        st.session_state[f"show_mensaje_busqueda_{factura_id}"] = True
                        st.rerun()
            
            # Modal para mensaje al cliente
            if st.session_state.get(f"show_mensaje_busqueda_{factura_id}", False):
                with st.expander(f"💬 Mensaje para: {factura.get('cliente')}", expanded=True):
                    mensaje = self.invoice_radication.generar_mensaje_cliente(factura)
                    
                    st.markdown("### Mensaje generado:")
                    st.text_area(
                        "Copie este mensaje:",
                        value=mensaje,
                        height=400,
                        key=f"textarea_mensaje_busqueda_{factura_id}"
                    )
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success("✅ Listo para copiar y enviar al cliente")
                    with col_b:
                        if st.button("❌ Cerrar", key=f"cerrar_mensaje_busqueda_{factura_id}"):
                            del st.session_state[f"show_mensaje_busqueda_{factura_id}"]
                            st.rerun()

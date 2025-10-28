"""
Componentes UI para Sistema de Notificaciones
"""

import streamlit as st
from typing import Dict, Any, List
from datetime import datetime
from business.notification_system import NotificationSystem
from ui.theme_manager import ThemeManager
from utils.formatting import format_currency

class NotificationUI:
    """Interfaz de usuario para notificaciones"""
    
    def __init__(self, notification_system: NotificationSystem):
        self.notification_system = notification_system
    
    def render_notification_dashboard(self):
        """Renderiza el dashboard completo de notificaciones"""
        
        theme = ThemeManager.get_theme()
        
        # Título
        st.markdown(
            f"""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='
                    font-size: 2.5rem;
                    font-weight: 800;
                    background: {theme['gradient_2']};
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 0.5rem;
                '>
                    📧 Centro de Notificaciones
                </h1>
                <p style='color: {theme['text_secondary']}; font-size: 1rem;'>
                    Email · WhatsApp · Alertas Automáticas
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Tabs principales
        tab1, tab2, tab3, tab4 = st.tabs([
            "📤 Enviar Notificación",
            "⚙️ Configuración",
            "📊 Estadísticas",
            "📜 Historial"
        ])
        
        with tab1:
            self._render_send_notification()
        
        with tab2:
            self._render_configuration()
        
        with tab3:
            self._render_statistics()
        
        with tab4:
            self._render_history()
    
    def _render_send_notification(self):
        """Renderiza formulario para enviar notificación"""
        
        st.markdown("### 📤 Enviar Notificación Manual")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Selección de canal
            canal = st.radio(
                "Canal de Envío",
                options=["📧 Email", "💬 WhatsApp"],
                key="notification_canal"
            )
            
            # Selección de plantilla
            plantilla = st.selectbox(
                "Plantilla",
                options=[
                    "Personalizado",
                    "Factura Vencida",
                    "Factura por Vencer",
                    "Meta Alcanzada",
                    "Risk Score Alto",
                    "Recordatorio General"
                ],
                key="notification_template"
            )
        
        with col2:
            if "Email" in canal:
                self._render_email_form(plantilla)
            else:
                self._render_whatsapp_form(plantilla)
    
    def _render_email_form(self, plantilla: str):
        """Renderiza formulario de email"""
        
        st.markdown("#### 📧 Configuración de Email")
        
        # Destinatario
        email_to = st.text_input(
            "Destinatario",
            value=self.notification_system.email_config["email_to_default"],
            placeholder="correo@ejemplo.com",
            key="email_to"
        )
        
        # Asunto
        if plantilla != "Personalizado":
            asunto = f"[CRM] {plantilla}"
        else:
            asunto = st.text_input(
                "Asunto",
                placeholder="Escribe el asunto del email",
                key="email_subject"
            )
        
        st.text_input(
            "Asunto",
            value=asunto,
            key="email_subject_display",
            disabled=plantilla != "Personalizado"
        )
        
        # Mensaje
        mensaje = st.text_area(
            "Mensaje",
            height=200,
            placeholder="Escribe tu mensaje aquí...\n\nPuedes usar HTML para dar formato.",
            key="email_message"
        )
        
        # Vista previa
        if mensaje:
            with st.expander("👁️ Vista Previa"):
                st.markdown(mensaje, unsafe_allow_html=True)
        
        # Botón de envío
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("📧 Enviar Email", type="primary", use_container_width=True):
                if not email_to:
                    st.error("❌ Ingresa un destinatario")
                elif not asunto:
                    st.error("❌ Ingresa un asunto")
                elif not mensaje:
                    st.error("❌ Escribe un mensaje")
                else:
                    with st.spinner("Enviando..."):
                        result = self.notification_system.send_email(
                            to=email_to,
                            subject=asunto,
                            body=mensaje,
                            html=True
                        )
                        
                        if result["success"]:
                            st.success(f"✅ {result['message']}")
                        else:
                            st.error(f"❌ Error: {result['error']}")
        
        with col2:
            if st.button("🧪 Enviar Email de Prueba", use_container_width=True):
                test_result = self._send_test_email(email_to)
                if test_result["success"]:
                    st.success("✅ Email de prueba enviado")
                else:
                    st.error(f"❌ {test_result['error']}")
    
    def _render_whatsapp_form(self, plantilla: str):
        """Renderiza formulario de WhatsApp"""
        
        st.markdown("#### 💬 Configuración de WhatsApp")
        
        # Destinatario
        whatsapp_to = st.text_input(
            "Número de WhatsApp",
            value=self.notification_system.whatsapp_config["whatsapp_to_default"],
            placeholder="+573001234567",
            help="Formato: +57 seguido del número (incluir indicativo)",
            key="whatsapp_to"
        )
        
        # Mensaje
        mensaje = st.text_area(
            "Mensaje",
            height=200,
            placeholder="Escribe tu mensaje aquí...\n\n*Negrita* _cursiva_ ~tachado~",
            help="Puedes usar formato de WhatsApp: *negrita*, _cursiva_, ~tachado~",
            key="whatsapp_message"
        )
        
        # Contador de caracteres
        if mensaje:
            st.caption(f"📝 {len(mensaje)} caracteres")
        
        # Botón de envío
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("💬 Enviar WhatsApp", type="primary", use_container_width=True):
                if not whatsapp_to:
                    st.error("❌ Ingresa un número de WhatsApp")
                elif not mensaje:
                    st.error("❌ Escribe un mensaje")
                else:
                    with st.spinner("Enviando..."):
                        result = self.notification_system.send_whatsapp(
                            to=whatsapp_to,
                            message=mensaje
                        )
                        
                        if result["success"]:
                            st.success(f"✅ {result['message']}")
                        else:
                            st.error(f"❌ Error: {result['error']}")
        
        with col2:
            if st.button("🧪 Enviar WhatsApp de Prueba", use_container_width=True):
                test_result = self._send_test_whatsapp(whatsapp_to)
                if test_result["success"]:
                    st.success("✅ WhatsApp de prueba enviado")
                else:
                    st.error(f"❌ {test_result['error']}")
    
    def _render_configuration(self):
        """Renderiza configuración de notificaciones automáticas"""
        
        st.markdown("### ⚙️ Configuración de Notificaciones Automáticas")
        
        # Estado de configuración
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📧 Configuración Email")
            email_configured = bool(
                self.notification_system.email_config["email_from"] and
                self.notification_system.email_config["email_password"]
            )
            
            if email_configured:
                st.success("✅ Email configurado correctamente")
                st.info(f"📧 Desde: {self.notification_system.email_config['email_from']}")
            else:
                st.error("❌ Email no configurado")
                st.warning("⚠️ Configura EMAIL_FROM y EMAIL_PASSWORD en el archivo .env")
        
        with col2:
            st.markdown("#### 💬 Configuración WhatsApp")
            whatsapp_configured = bool(
                self.notification_system.whatsapp_config["account_sid"] and
                self.notification_system.whatsapp_config["auth_token"]
            )
            
            if whatsapp_configured:
                st.success("✅ WhatsApp configurado correctamente")
                st.info(f"📱 Desde: {self.notification_system.whatsapp_config['whatsapp_from']}")
            else:
                st.error("❌ WhatsApp no configurado")
                st.warning("⚠️ Configura credenciales de Twilio en el archivo .env")
        
        st.markdown("---")
        
        # Triggers automáticos
        st.markdown("### 🎯 Triggers Automáticos")
        st.info("📝 Los triggers automáticos monitorean el sistema y envían alertas cuando se cumplen ciertas condiciones.")
        
        for trigger_id, trigger_info in self.notification_system.TRIGGERS.items():
            with st.expander(f"{'🔔' if trigger_info.get('activo', False) else '🔕'} {trigger_info['nombre']}"):
                st.markdown(f"**Descripción:** {trigger_info['descripcion']}")
                
                canales = trigger_info.get('canales', [])
                st.markdown(f"**Canales:** {', '.join(canales)}")
                
                # Configuración específica
                if 'dias_antes' in trigger_info:
                    st.number_input(
                        "Días de anticipación",
                        value=trigger_info['dias_antes'],
                        min_value=0,
                        max_value=30,
                        key=f"trigger_{trigger_id}_dias"
                    )
                
                if 'umbral' in trigger_info:
                    st.slider(
                        "Umbral (%)",
                        min_value=0,
                        max_value=100,
                        value=trigger_info['umbral'],
                        key=f"trigger_{trigger_id}_umbral"
                    )
                
                # Toggle activar/desactivar
                activo = st.checkbox(
                    "Activar este trigger",
                    value=trigger_info.get('activo', False),
                    key=f"trigger_{trigger_id}_activo"
                )
        
        # Destinatarios por defecto
        st.markdown("---")
        st.markdown("### 📬 Destinatarios por Defecto")
        
        col1, col2 = st.columns(2)
        with col1:
            email_default = st.text_input(
                "Email por defecto",
                value=self.notification_system.email_config["email_to_default"],
                key="config_email_default"
            )
        
        with col2:
            whatsapp_default = st.text_input(
                "WhatsApp por defecto",
                value=self.notification_system.whatsapp_config["whatsapp_to_default"],
                placeholder="+573001234567",
                key="config_whatsapp_default"
            )
        
        if st.button("💾 Guardar Configuración", type="primary"):
            st.success("✅ Configuración guardada correctamente")
            st.info("💡 Los cambios se aplicarán en la próxima verificación automática")
    
    def _render_statistics(self):
        """Renderiza estadísticas de notificaciones"""
        
        st.markdown("### 📊 Estadísticas de Notificaciones")
        
        stats = self.notification_system.get_stats()
        
        if stats["total"] == 0:
            st.info("📭 Aún no se han enviado notificaciones")
            return
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Enviadas",
                stats["total"],
                help="Número total de notificaciones enviadas"
            )
        
        with col2:
            st.metric(
                "Exitosas",
                stats["enviados"],
                delta=f"{stats['tasa_exito']:.1f}%",
                delta_color="normal",
                help="Notificaciones enviadas correctamente"
            )
        
        with col3:
            st.metric(
                "Errores",
                stats["errores"],
                delta=f"{(stats['errores']/stats['total']*100):.1f}%",
                delta_color="inverse",
                help="Notificaciones con error"
            )
        
        with col4:
            tasa_exito = stats["tasa_exito"]
            st.metric(
                "Tasa de Éxito",
                f"{tasa_exito:.1f}%",
                help="Porcentaje de notificaciones exitosas"
            )
        
        st.markdown("---")
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Notificaciones por Tipo")
            por_tipo = stats.get("por_tipo", {})
            if por_tipo:
                import plotly.graph_objects as go
                
                fig = go.Figure(data=[
                    go.Pie(
                        labels=list(por_tipo.keys()),
                        values=list(por_tipo.values()),
                        hole=0.4,
                        marker=dict(colors=['#6366f1', '#8b5cf6'])
                    )
                ])
                
                fig.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=True,
                    template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos disponibles")
        
        with col2:
            st.markdown("#### ✅ Estado de Envíos")
            
            estados = {
                "Enviadas": stats["enviados"],
                "Errores": stats["errores"]
            }
            
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[
                go.Bar(
                    x=list(estados.keys()),
                    y=list(estados.values()),
                    marker_color=['#10b981', '#ef4444']
                )
            ])
            
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False,
                template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_history(self):
        """Renderiza historial de notificaciones"""
        
        st.markdown("### 📜 Historial de Notificaciones")
        
        history = self.notification_system.get_history(limit=100)
        
        if not history:
            st.info("📭 No hay notificaciones en el historial")
            return
        
        # Filtros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            filtro_tipo = st.selectbox(
                "Tipo",
                options=["Todos", "email", "whatsapp"],
                key="history_filter_tipo"
            )
        
        with col2:
            filtro_estado = st.selectbox(
                "Estado",
                options=["Todos", "enviado", "error"],
                key="history_filter_estado"
            )
        
        with col3:
            limit = st.number_input(
                "Mostrar últimos",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
                key="history_limit"
            )
        
        # Aplicar filtros
        history_filtered = history[-limit:]
        
        if filtro_tipo != "Todos":
            history_filtered = [h for h in history_filtered if h["tipo"] == filtro_tipo]
        
        if filtro_estado != "Todos":
            history_filtered = [h for h in history_filtered if h["estado"] == filtro_estado]
        
        st.caption(f"Mostrando {len(history_filtered)} de {len(history)} notificaciones")
        
        # Tabla de historial
        for notif in reversed(history_filtered):
            self._render_history_item(notif)
    
    def _render_history_item(self, notif: Dict):
        """Renderiza un item del historial"""
        
        theme = ThemeManager.get_theme()
        
        # Iconos y colores
        tipo_icon = "📧" if notif["tipo"] == "email" else "💬"
        estado_color = theme["success"] if notif["estado"] == "enviado" else theme["error"]
        estado_icon = "✅" if notif["estado"] == "enviado" else "❌"
        
        fecha = datetime.fromisoformat(notif["fecha"]).strftime("%Y-%m-%d %H:%M:%S")
        
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.markdown(f"**{tipo_icon} {notif['tipo'].upper()}**")
                st.caption(fecha)
            
            with col2:
                st.markdown(f"**Para:** {notif['destinatario']}")
                st.markdown(f"**Asunto:** {notif['asunto']}")
                if notif.get('error'):
                    st.error(f"Error: {notif['error']}")
            
            with col3:
                st.markdown(
                    f"""
                    <div style='text-align: right; color: {estado_color}; font-size: 1.5rem;'>
                        {estado_icon}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            st.markdown("---")
    
    def _send_test_email(self, to: str) -> Dict:
        """Envía un email de prueba"""
        test_html = """
        <html>
            <body style='font-family: Arial, sans-serif; padding: 20px;'>
                <h2>✅ Email de Prueba</h2>
                <p>Este es un email de prueba del sistema de notificaciones.</p>
                <p><strong>Si recibes esto, tu configuración está correcta.</strong></p>
                <hr>
                <p style='color: #666; font-size: 12px;'>CRM Inteligente 2.0</p>
            </body>
        </html>
        """
        
        return self.notification_system.send_email(
            to=to,
            subject="🧪 Email de Prueba - CRM Inteligente",
            body=test_html,
            html=True
        )
    
    def _send_test_whatsapp(self, to: str) -> Dict:
        """Envía un WhatsApp de prueba"""
        test_message = """✅ *WhatsApp de Prueba*

Este es un mensaje de prueba del sistema de notificaciones.

*Si recibes esto, tu configuración está correcta.*

_CRM Inteligente 2.0_"""
        
        return self.notification_system.send_whatsapp(
            to=to,
            message=test_message
        )


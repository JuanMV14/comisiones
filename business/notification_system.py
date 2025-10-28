"""
Sistema de Notificaciones Multi-canal (Email y WhatsApp)
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import pandas as pd
import json
from dataclasses import dataclass, asdict
import os

@dataclass
class Notification:
    """Clase para representar una notificación"""
    id: str
    tipo: str  # 'email' o 'whatsapp'
    destinatario: str
    asunto: str
    mensaje: str
    estado: str  # 'pendiente', 'enviado', 'error'
    fecha_creacion: datetime
    fecha_envio: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class NotificationSystem:
    """Sistema centralizado de notificaciones"""
    
    # Configuración de triggers (cuándo enviar)
    TRIGGERS = {
        "factura_vencida": {
            "nombre": "Factura Vencida",
            "descripcion": "Notifica cuando una factura está vencida",
            "dias_antes": 0,  # 0 = el día que vence
            "canales": ["email", "whatsapp"]
        },
        "factura_por_vencer": {
            "nombre": "Factura Próxima a Vencer",
            "descripcion": "Notifica X días antes del vencimiento",
            "dias_antes": 3,
            "canales": ["email", "whatsapp"]
        },
        "meta_alcanzada": {
            "nombre": "Meta Mensual Alcanzada",
            "descripcion": "Notifica cuando se alcanza la meta del mes",
            "canales": ["email"]
        },
        "nuevo_cliente": {
            "nombre": "Cliente Nuevo",
            "descripcion": "Notifica cuando se registra un cliente nuevo",
            "canales": ["email"]
        },
        "comision_pendiente": {
            "nombre": "Comisión Pendiente",
            "descripcion": "Notifica sobre comisiones pendientes de pago",
            "dias_despues": 30,
            "canales": ["email"]
        },
        "riesgo_alto": {
            "nombre": "Risk Score Alto",
            "descripcion": "Notifica cuando el risk score supera 40%",
            "umbral": 40,
            "canales": ["email"]
        }
    }
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.notifications_history = []
        
        # Configuración de Email (desde variables de entorno)
        self.email_config = {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "email_from": os.getenv("EMAIL_FROM", ""),
            "email_password": os.getenv("EMAIL_PASSWORD", ""),
            "email_to_default": os.getenv("EMAIL_TO_DEFAULT", "")
        }
        
        # Configuración de WhatsApp (Twilio)
        self.whatsapp_config = {
            "account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
            "auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
            "whatsapp_from": os.getenv("TWILIO_WHATSAPP_FROM", ""),
            "whatsapp_to_default": os.getenv("WHATSAPP_TO_DEFAULT", "")
        }
    
    # ========================================
    # ENVÍO DE NOTIFICACIONES
    # ========================================
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = True
    ) -> Dict[str, Any]:
        """
        Envía un email
        
        Args:
            to: Destinatario
            subject: Asunto
            body: Cuerpo del mensaje
            html: Si el cuerpo es HTML
            
        Returns:
            Dict con status y mensaje
        """
        # Validar configuración
        if not self.email_config["email_from"] or not self.email_config["email_password"]:
            return {
                "success": False,
                "error": "Configuración de email incompleta. Verifica EMAIL_FROM y EMAIL_PASSWORD en .env"
            }
        
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_config["email_from"]
            msg['To'] = to
            msg['Subject'] = subject
            
            # Agregar cuerpo
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Conectar y enviar
            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["email_from"], self.email_config["email_password"])
                server.send_message(msg)
            
            # Registrar en historial
            self._add_to_history("email", to, subject, body, "enviado")
            
            return {
                "success": True,
                "message": f"Email enviado exitosamente a {to}"
            }
            
        except Exception as e:
            error_msg = str(e)
            self._add_to_history("email", to, subject, body, "error", error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def send_whatsapp(
        self,
        to: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de WhatsApp vía Twilio
        
        Args:
            to: Número de WhatsApp (formato: +573001234567)
            message: Mensaje a enviar
            
        Returns:
            Dict con status y mensaje
        """
        # Validar configuración
        if not self.whatsapp_config["account_sid"] or not self.whatsapp_config["auth_token"]:
            return {
                "success": False,
                "error": "Configuración de WhatsApp incompleta. Verifica TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en .env"
            }
        
        try:
            # Importar Twilio (solo si está configurado)
            try:
                from twilio.rest import Client
            except ImportError:
                return {
                    "success": False,
                    "error": "Twilio no instalado. Ejecuta: pip install twilio"
                }
            
            # Crear cliente
            client = Client(
                self.whatsapp_config["account_sid"],
                self.whatsapp_config["auth_token"]
            )
            
            # Enviar mensaje
            message_obj = client.messages.create(
                from_=f'whatsapp:{self.whatsapp_config["whatsapp_from"]}',
                body=message,
                to=f'whatsapp:{to}'
            )
            
            # Registrar en historial
            self._add_to_history("whatsapp", to, "WhatsApp", message, "enviado")
            
            return {
                "success": True,
                "message": f"WhatsApp enviado exitosamente a {to}",
                "sid": message_obj.sid
            }
            
        except Exception as e:
            error_msg = str(e)
            self._add_to_history("whatsapp", to, "WhatsApp", message, "error", error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    # ========================================
    # PLANTILLAS DE MENSAJES
    # ========================================
    
    def get_template_factura_vencida(self, factura: Dict) -> Dict[str, str]:
        """Genera plantilla para factura vencida"""
        
        cliente = factura.get('cliente', 'Cliente')
        numero_factura = factura.get('factura', 'N/A')
        valor = factura.get('valor', 0)
        fecha_vencimiento = factura.get('fecha_pago_max', 'N/A')
        
        # Email HTML
        email_html = f"""
        <html>
            <body style='font-family: Arial, sans-serif; padding: 20px;'>
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;'>
                    <h2>🚨 Alerta: Factura Vencida</h2>
                </div>
                
                <div style='margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px;'>
                    <h3 style='color: #ef4444;'>⚠️ Factura con Pago Vencido</h3>
                    
                    <p><strong>Cliente:</strong> {cliente}</p>
                    <p><strong>Factura #:</strong> {numero_factura}</p>
                    <p><strong>Valor:</strong> ${valor:,.0f}</p>
                    <p><strong>Fecha de Vencimiento:</strong> {fecha_vencimiento}</p>
                    
                    <div style='margin-top: 20px; padding: 15px; background: #fee; border-left: 4px solid #ef4444; border-radius: 5px;'>
                        <strong>Acción Requerida:</strong>
                        <p>Esta factura está vencida. Por favor, realiza seguimiento urgente con el cliente.</p>
                    </div>
                </div>
                
                <div style='margin-top: 20px; text-align: center; color: #666; font-size: 12px;'>
                    <p>CRM Inteligente 2.0 - Sistema de Notificaciones</p>
                </div>
            </body>
        </html>
        """
        
        # WhatsApp (texto plano)
        whatsapp_text = f"""🚨 *FACTURA VENCIDA*

⚠️ Cliente: *{cliente}*
📋 Factura: {numero_factura}
💰 Valor: ${valor:,.0f}
📅 Vencimiento: {fecha_vencimiento}

🔴 *ACCIÓN URGENTE REQUERIDA*
Realiza seguimiento con el cliente.

_CRM Inteligente 2.0_"""
        
        return {
            "email_subject": f"🚨 Alerta: Factura {numero_factura} Vencida - {cliente}",
            "email_html": email_html,
            "whatsapp_text": whatsapp_text
        }
    
    def get_template_factura_por_vencer(self, factura: Dict, dias: int) -> Dict[str, str]:
        """Genera plantilla para factura próxima a vencer"""
        
        cliente = factura.get('cliente', 'Cliente')
        numero_factura = factura.get('factura', 'N/A')
        valor = factura.get('valor', 0)
        fecha_vencimiento = factura.get('fecha_pago_max', 'N/A')
        
        email_html = f"""
        <html>
            <body style='font-family: Arial, sans-serif; padding: 20px;'>
                <div style='background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 20px; border-radius: 10px; color: white;'>
                    <h2>⏰ Recordatorio: Factura Próxima a Vencer</h2>
                </div>
                
                <div style='margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px;'>
                    <h3 style='color: #f59e0b;'>📅 Vence en {dias} día(s)</h3>
                    
                    <p><strong>Cliente:</strong> {cliente}</p>
                    <p><strong>Factura #:</strong> {numero_factura}</p>
                    <p><strong>Valor:</strong> ${valor:,.0f}</p>
                    <p><strong>Fecha de Vencimiento:</strong> {fecha_vencimiento}</p>
                    
                    <div style='margin-top: 20px; padding: 15px; background: #fffbeb; border-left: 4px solid #f59e0b; border-radius: 5px;'>
                        <strong>Recordatorio:</strong>
                        <p>Esta factura vence pronto. Considera realizar seguimiento preventivo con el cliente.</p>
                    </div>
                </div>
                
                <div style='margin-top: 20px; text-align: center; color: #666; font-size: 12px;'>
                    <p>CRM Inteligente 2.0 - Sistema de Notificaciones</p>
                </div>
            </body>
        </html>
        """
        
        whatsapp_text = f"""⏰ *RECORDATORIO: FACTURA POR VENCER*

📅 Vence en *{dias} día(s)*

👤 Cliente: {cliente}
📋 Factura: {numero_factura}
💰 Valor: ${valor:,.0f}
📆 Vencimiento: {fecha_vencimiento}

💡 Considera hacer seguimiento preventivo.

_CRM Inteligente 2.0_"""
        
        return {
            "email_subject": f"⏰ Recordatorio: Factura {numero_factura} vence en {dias} día(s)",
            "email_html": email_html,
            "whatsapp_text": whatsapp_text
        }
    
    def get_template_meta_alcanzada(self, monto_alcanzado: float, meta: float) -> Dict[str, str]:
        """Genera plantilla para meta alcanzada"""
        
        porcentaje = (monto_alcanzado / meta * 100) if meta > 0 else 0
        
        email_html = f"""
        <html>
            <body style='font-family: Arial, sans-serif; padding: 20px;'>
                <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 20px; border-radius: 10px; color: white;'>
                    <h2>🎉 ¡Felicitaciones! Meta Alcanzada</h2>
                </div>
                
                <div style='margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px;'>
                    <h3 style='color: #10b981;'>🎯 ¡Objetivo Cumplido!</h3>
                    
                    <p><strong>Meta del Mes:</strong> ${meta:,.0f}</p>
                    <p><strong>Alcanzado:</strong> ${monto_alcanzado:,.0f}</p>
                    <p><strong>Porcentaje:</strong> {porcentaje:.1f}%</p>
                    
                    <div style='margin-top: 20px; padding: 15px; background: #d1fae5; border-left: 4px solid #10b981; border-radius: 5px;'>
                        <strong>¡Excelente trabajo!</strong>
                        <p>Has alcanzado la meta mensual. ¡Sigue así!</p>
                    </div>
                </div>
                
                <div style='margin-top: 20px; text-align: center; color: #666; font-size: 12px;'>
                    <p>CRM Inteligente 2.0 - Sistema de Notificaciones</p>
                </div>
            </body>
        </html>
        """
        
        whatsapp_text = f"""🎉 *¡META ALCANZADA!*

🎯 Meta: ${meta:,.0f}
✅ Alcanzado: ${monto_alcanzado:,.0f}
📊 {porcentaje:.1f}%

🏆 *¡Excelente trabajo!*
Sigue así campeón.

_CRM Inteligente 2.0_"""
        
        return {
            "email_subject": "🎉 ¡Felicitaciones! Meta Mensual Alcanzada",
            "email_html": email_html,
            "whatsapp_text": whatsapp_text
        }
    
    def get_template_riesgo_alto(self, risk_score: float, facturas_riesgo: int, valor_riesgo: float) -> Dict[str, str]:
        """Genera plantilla para risk score alto"""
        
        email_html = f"""
        <html>
            <body style='font-family: Arial, sans-serif; padding: 20px;'>
                <div style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); padding: 20px; border-radius: 10px; color: white;'>
                    <h2>🚨 Alerta Crítica: Risk Score Alto</h2>
                </div>
                
                <div style='margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px;'>
                    <h3 style='color: #ef4444;'>⚠️ Nivel de Riesgo Elevado</h3>
                    
                    <p><strong>Risk Score:</strong> {risk_score:.1f}%</p>
                    <p><strong>Facturas en Riesgo:</strong> {facturas_riesgo}</p>
                    <p><strong>Valor en Riesgo:</strong> ${valor_riesgo:,.0f}</p>
                    
                    <div style='margin-top: 20px; padding: 15px; background: #fee; border-left: 4px solid #ef4444; border-radius: 5px;'>
                        <strong>⚠️ ACCIÓN URGENTE REQUERIDA</strong>
                        <p>El nivel de riesgo ha superado el umbral crítico. Revisa las facturas pendientes inmediatamente.</p>
                    </div>
                </div>
                
                <div style='margin-top: 20px; text-align: center; color: #666; font-size: 12px;'>
                    <p>CRM Inteligente 2.0 - Sistema de Notificaciones</p>
                </div>
            </body>
        </html>
        """
        
        whatsapp_text = f"""🚨 *ALERTA: RISK SCORE ALTO*

⚠️ Risk Score: *{risk_score:.1f}%*
📋 Facturas en Riesgo: {facturas_riesgo}
💰 Valor en Riesgo: ${valor_riesgo:,.0f}

🔴 *ACCIÓN URGENTE*
Revisa el dashboard inmediatamente.

_CRM Inteligente 2.0_"""
        
        return {
            "email_subject": "🚨 Alerta Crítica: Risk Score Alto",
            "email_html": email_html,
            "whatsapp_text": whatsapp_text
        }
    
    # ========================================
    # ANÁLISIS Y TRIGGERS AUTOMÁTICOS
    # ========================================
    
    def check_and_notify(
        self,
        email_to: Optional[str] = None,
        whatsapp_to: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Revisa condiciones y envía notificaciones automáticas
        
        Returns:
            Dict con notificaciones enviadas por tipo
        """
        if not self.db_manager:
            return {"error": "DatabaseManager no configurado"}
        
        notifications_sent = {
            "email": [],
            "whatsapp": [],
            "errors": []
        }
        
        df = self.db_manager.cargar_datos()
        if df.empty:
            return notifications_sent
        
        # Usar destinatarios por defecto si no se especifican
        email_dest = email_to or self.email_config["email_to_default"]
        whatsapp_dest = whatsapp_to or self.whatsapp_config["whatsapp_to_default"]
        
        # 1. Facturas vencidas
        df_pendientes = df[df['pagado'] == False].copy()
        if not df_pendientes.empty:
            df_pendientes['fecha_pago_max'] = pd.to_datetime(df_pendientes['fecha_pago_max'])
            hoy = pd.Timestamp.now()
            df_vencidas = df_pendientes[df_pendientes['fecha_pago_max'] < hoy]
            
            for _, factura in df_vencidas.iterrows():
                template = self.get_template_factura_vencida(factura.to_dict())
                
                # Enviar email
                if email_dest:
                    result = self.send_email(
                        email_dest,
                        template["email_subject"],
                        template["email_html"]
                    )
                    if result["success"]:
                        notifications_sent["email"].append({
                            "tipo": "factura_vencida",
                            "factura": factura['factura']
                        })
                    else:
                        notifications_sent["errors"].append(result)
        
        # 2. Meta alcanzada (ejemplo)
        # Aquí podrías agregar lógica para verificar si se alcanzó la meta
        
        return notifications_sent
    
    # ========================================
    # HISTORIAL
    # ========================================
    
    def _add_to_history(
        self,
        tipo: str,
        destinatario: str,
        asunto: str,
        mensaje: str,
        estado: str,
        error: Optional[str] = None
    ):
        """Agrega una notificación al historial"""
        notification = {
            "id": f"{tipo}_{datetime.now().timestamp()}",
            "tipo": tipo,
            "destinatario": destinatario,
            "asunto": asunto,
            "mensaje": mensaje[:100] + "..." if len(mensaje) > 100 else mensaje,
            "estado": estado,
            "fecha": datetime.now().isoformat(),
            "error": error
        }
        self.notifications_history.append(notification)
    
    def get_history(self, limit: int = 50) -> List[Dict]:
        """Obtiene el historial de notificaciones"""
        return self.notifications_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de notificaciones"""
        if not self.notifications_history:
            return {
                "total": 0,
                "enviados": 0,
                "errores": 0,
                "por_tipo": {}
            }
        
        df = pd.DataFrame(self.notifications_history)
        
        return {
            "total": len(df),
            "enviados": len(df[df['estado'] == 'enviado']),
            "errores": len(df[df['estado'] == 'error']),
            "por_tipo": df['tipo'].value_counts().to_dict(),
            "tasa_exito": len(df[df['estado'] == 'enviado']) / len(df) * 100 if len(df) > 0 else 0
        }


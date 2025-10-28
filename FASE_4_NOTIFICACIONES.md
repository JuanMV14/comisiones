# 📧 FASE 4: Sistema de Notificaciones Multi-canal

## ✅ IMPLEMENTADO

Sistema completo de notificaciones por Email y WhatsApp con plantillas inteligentes, triggers automáticos y panel de control.

---

## 🎯 CARACTERÍSTICAS PRINCIPALES

### 1. **Canales de Comunicación**
- 📧 **Email (SMTP)**: Compatible con Gmail, Outlook, etc.
- 💬 **WhatsApp (Twilio)**: Mensajes directos vía API

### 2. **Envío Manual**
- Formulario intuitivo para enviar notificaciones
- Plantillas predefinidas
- Mensajes personalizados
- Vista previa en tiempo real
- Emails de prueba para verificar configuración

### 3. **Plantillas Inteligentes**
- 🚨 **Factura Vencida**: Alerta urgente con datos de factura
- ⏰ **Factura por Vencer**: Recordatorio preventivo
- 🎉 **Meta Alcanzada**: Felicitación automática
- 🚨 **Risk Score Alto**: Alerta crítica de riesgo
- 📝 **Personalizado**: Crea tus propios mensajes

### 4. **Triggers Automáticos**
- ✅ Configurables desde la UI
- 📅 Basados en condiciones del negocio
- 🎯 Múltiples canales por trigger
- ⚙️ Activar/desactivar fácilmente

### 5. **Panel de Control**
- 📊 Estadísticas de envíos
- 📜 Historial completo
- 🔍 Filtros avanzados
- 📈 Gráficos de rendimiento

### 6. **Seguridad**
- 🔒 Credenciales en archivo .env
- 🔐 Nunca expone passwords
- ✅ Validación de configuración

---

## 📦 ARCHIVOS CREADOS

### 1. `business/notification_system.py` (680 líneas)
**Motor del Sistema de Notificaciones**

#### Clase Principal: `NotificationSystem`

**Métodos de Envío**:
```python
send_email(to, subject, body, html=True) -> Dict
send_whatsapp(to, message) -> Dict
```

**Plantillas Disponibles**:
```python
get_template_factura_vencida(factura) -> Dict
get_template_factura_por_vencer(factura, dias) -> Dict
get_template_meta_alcanzada(monto, meta) -> Dict
get_template_riesgo_alto(score, facturas, valor) -> Dict
```

**Verificación Automática**:
```python
check_and_notify(email_to, whatsapp_to) -> Dict
```

**Historial y Stats**:
```python
get_history(limit=50) -> List
get_stats() -> Dict
```

#### Triggers Automáticos Configurables:
- **factura_vencida**: Notifica el día del vencimiento
- **factura_por_vencer**: Notifica X días antes (default: 3)
- **meta_alcanzada**: Cuando se cumple la meta mensual
- **nuevo_cliente**: Al registrar cliente nuevo
- **comision_pendiente**: Comisiones sin pagar > 30 días
- **riesgo_alto**: Risk score > 40%

### 2. `ui/notification_components.py` (570 líneas)
**Interfaz de Usuario para Notificaciones**

#### Clase Principal: `NotificationUI`

**Métodos de Renderizado**:
```python
render_notification_dashboard()  # Dashboard completo
_render_send_notification()      # Formulario de envío
_render_configuration()          # Configuración de triggers
_render_statistics()             # Gráficos y métricas
_render_history()                # Historial de envíos
```

**4 Tabs Principales**:
1. 📤 **Enviar Notificación**: Formularios de email y WhatsApp
2. ⚙️ **Configuración**: Triggers y destinatarios
3. 📊 **Estadísticas**: Gráficos y KPIs
4. 📜 **Historial**: Log completo de envíos

### 3. `config_notificaciones_ejemplo.txt`
**Guía de Configuración**

Plantilla con todas las variables de entorno necesarias y guías paso a paso para configurar Gmail y Twilio.

### 4. Actualizaciones en Archivos Existentes
- `ui/tabs.py`: Nuevo método `render_notifications()`
- `app.py`: Nueva pestaña "📲 Notificaciones"

---

## 🚀 CÓMO CONFIGURAR

### 📧 **Paso 1: Configurar Email (Gmail)**

1. **Si usas autenticación de 2 factores (recomendado)**:
   ```
   a) Ve a: https://myaccount.google.com/apppasswords
   b) Selecciona "Mail" y genera una contraseña
   c) Copia la contraseña de 16 dígitos
   ```

2. **Si NO usas 2FA**:
   ```
   a) Ve a: https://myaccount.google.com/lesssecureapps
   b) Activa "Acceso de aplicaciones menos seguras"
   ```

3. **Agrega a tu archivo .env**:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_FROM=tu_email@gmail.com
   EMAIL_PASSWORD=tu_app_password_aqui
   EMAIL_TO_DEFAULT=destinatario@ejemplo.com
   ```

### 💬 **Paso 2: Configurar WhatsApp (Twilio)**

1. **Crear cuenta Twilio**:
   ```
   a) Ve a: https://www.twilio.com/try-twilio
   b) Regístrate gratis (incluye $15 de crédito)
   c) Verifica tu teléfono
   ```

2. **Obtener credenciales**:
   ```
   a) En el Dashboard, copia "Account SID"
   b) Copia "Auth Token"
   c) Ve a Messaging > Try it out > Send a WhatsApp message
   ```

3. **Activar número de prueba**:
   ```
   a) Twilio te da un número sandbox: +14155238886
   b) Envía "join [código]" a ese número desde WhatsApp
   c) Ahora puedes recibir mensajes
   ```

4. **Agrega a tu archivo .env**:
   ```env
   TWILIO_ACCOUNT_SID=tu_account_sid
   TWILIO_AUTH_TOKEN=tu_auth_token
   TWILIO_WHATSAPP_FROM=+14155238886
   WHATSAPP_TO_DEFAULT=+573001234567
   ```

### 📦 **Paso 3: Instalar Twilio (opcional)**

Si quieres usar WhatsApp:
```bash
pip install twilio
```

### 🔄 **Paso 4: Reiniciar Aplicación**

```bash
streamlit run app.py
```

---

## 💡 CÓMO USAR

### 1. **Enviar Notificación Manual**

#### Email:
```
1. Ve a pestaña "📲 Notificaciones"
2. Clic en tab "📤 Enviar Notificación"
3. Selecciona "📧 Email"
4. Completa:
   - Destinatario
   - Asunto
   - Mensaje (puede incluir HTML)
5. Clic en "📧 Enviar Email"
```

#### WhatsApp:
```
1. Ve a pestaña "📲 Notificaciones"
2. Clic en tab "📤 Enviar Notificación"
3. Selecciona "💬 WhatsApp"
4. Completa:
   - Número (formato: +573001234567)
   - Mensaje (usa *negrita*, _cursiva_)
5. Clic en "💬 Enviar WhatsApp"
```

### 2. **Usar Plantillas Predefinidas**

```
1. En formulario de envío
2. Selecciona plantilla deseada
3. El sistema completa automáticamente con datos reales
4. Edita si es necesario
5. Envía
```

### 3. **Configurar Triggers Automáticos**

```
1. Ve a tab "⚙️ Configuración"
2. Expande el trigger que quieres configurar
3. Ajusta parámetros (ej: días de anticipación)
4. Marca "Activar este trigger"
5. Clic en "💾 Guardar Configuración"
```

### 4. **Ver Estadísticas**

```
1. Ve a tab "📊 Estadísticas"
2. Revisa:
   - Total enviadas
   - Tasa de éxito
   - Errores
   - Distribución por tipo
```

### 5. **Revisar Historial**

```
1. Ve a tab "📜 Historial"
2. Filtra por:
   - Tipo (email/whatsapp)
   - Estado (enviado/error)
   - Límite de registros
3. Ve detalles de cada envío
```

---

## 📧 PLANTILLAS DISPONIBLES

### 1. **Factura Vencida**

**Cuándo se usa**: Cuando una factura ha vencido

**Datos incluidos**:
- Cliente
- Número de factura
- Valor
- Fecha de vencimiento

**Ejemplo Email**:
```
🚨 Alerta: Factura Vencida

⚠️ Factura con Pago Vencido

Cliente: EMPRESA ABC S.A.S.
Factura #: 12345
Valor: $2,500,000
Fecha de Vencimiento: 2025-10-25

Acción Requerida:
Esta factura está vencida. Por favor, realiza seguimiento urgente.
```

**Ejemplo WhatsApp**:
```
🚨 *FACTURA VENCIDA*

⚠️ Cliente: *EMPRESA ABC S.A.S.*
📋 Factura: 12345
💰 Valor: $2,500,000
📅 Vencimiento: 2025-10-25

🔴 *ACCIÓN URGENTE REQUERIDA*
Realiza seguimiento con el cliente.
```

### 2. **Factura por Vencer**

**Cuándo se usa**: X días antes del vencimiento (configurable)

**Ejemplo**:
```
⏰ RECORDATORIO: FACTURA POR VENCER

📅 Vence en *3 día(s)*

👤 Cliente: COMERCIAL XYZ
📋 Factura: 67890
💰 Valor: $1,800,000
📆 Vencimiento: 2025-10-31

💡 Considera hacer seguimiento preventivo.
```

### 3. **Meta Alcanzada**

**Cuándo se usa**: Al alcanzar la meta mensual

**Ejemplo**:
```
🎉 *¡META ALCANZADA!*

🎯 Meta: $10,000,000
✅ Alcanzado: $10,500,000
📊 105.0%

🏆 *¡Excelente trabajo!*
Sigue así campeón.
```

### 4. **Risk Score Alto**

**Cuándo se usa**: Cuando el risk score supera 40%

**Ejemplo**:
```
🚨 *ALERTA: RISK SCORE ALTO*

⚠️ Risk Score: *45.5%*
📋 Facturas en Riesgo: 8
💰 Valor en Riesgo: $5,250,000

🔴 *ACCIÓN URGENTE*
Revisa el dashboard inmediatamente.
```

---

## 🎯 TRIGGERS AUTOMÁTICOS

### Configurables desde la UI

#### 1. **Factura Vencida**
- **Condición**: Fecha de vencimiento pasada
- **Frecuencia**: Diaria
- **Canales**: Email, WhatsApp
- **Acción**: Envía alerta urgente

#### 2. **Factura por Vencer**
- **Condición**: X días antes del vencimiento (default: 3)
- **Frecuencia**: Diaria
- **Canales**: Email, WhatsApp
- **Acción**: Envía recordatorio preventivo

#### 3. **Meta Alcanzada**
- **Condición**: Ventas del mes ≥ Meta
- **Frecuencia**: Una vez al alcanzar
- **Canales**: Email
- **Acción**: Envía felicitación

#### 4. **Nuevo Cliente**
- **Condición**: Se registra cliente nuevo
- **Frecuencia**: Al momento del registro
- **Canales**: Email
- **Acción**: Notifica registro

#### 5. **Comisión Pendiente**
- **Condición**: Factura pagada hace >30 días sin comisión
- **Frecuencia**: Semanal
- **Canales**: Email
- **Acción**: Recordatorio de comisión

#### 6. **Risk Score Alto**
- **Condición**: Risk score > 40% (configurable)
- **Frecuencia**: Diaria
- **Canales**: Email
- **Acción**: Alerta crítica

---

## 📊 ESTADÍSTICAS Y MÉTRICAS

### KPIs Disponibles:
- **Total Enviadas**: Número total de notificaciones
- **Exitosas**: Notificaciones entregadas correctamente
- **Errores**: Notificaciones fallidas
- **Tasa de Éxito**: % de envíos exitosos

### Gráficos:
1. **Pie Chart**: Distribución Email vs WhatsApp
2. **Bar Chart**: Estado de envíos (Exitosos vs Errores)

### Filtros:
- Por tipo (email/whatsapp)
- Por estado (enviado/error)
- Por límite de registros

---

## 🔒 SEGURIDAD

### Buenas Prácticas:
1. **Nunca** compartas tu archivo .env
2. **Nunca** subas .env a Git (está en .gitignore)
3. Usa **App Passwords** en Gmail (más seguro)
4. Rota credenciales periódicamente
5. Limita permisos de API en Twilio

### Validaciones:
- Sistema verifica configuración antes de enviar
- Mensajes de error claros
- No expone credenciales en logs

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### ❌ **Error: "Configuración de email incompleta"**

**Causa**: Falta EMAIL_FROM o EMAIL_PASSWORD en .env

**Solución**:
```env
# Agrega a .env:
EMAIL_FROM=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password
```

### ❌ **Error: "Authentication failed"**

**Causa**: Contraseña incorrecta o 2FA no configurado

**Solución**:
1. Si usas 2FA, genera App Password
2. Verifica que copiaste correctamente la contraseña
3. No uses tu contraseña normal de Gmail

### ❌ **Error: "Twilio no instalado"**

**Causa**: Librería twilio no está instalada

**Solución**:
```bash
pip install twilio
```

### ❌ **Error: "WhatsApp configuration incomplete"**

**Causa**: Faltan credenciales de Twilio en .env

**Solución**:
```env
# Agrega a .env:
TWILIO_ACCOUNT_SID=tu_sid
TWILIO_AUTH_TOKEN=tu_token
TWILIO_WHATSAPP_FROM=+14155238886
```

### ❌ **Error: "Unable to create record"**

**Causa**: Número de WhatsApp no activado en sandbox

**Solución**:
1. Envía "join [código]" al número de Twilio desde WhatsApp
2. Espera confirmación
3. Intenta de nuevo

---

## 💰 COSTOS

### Email (SMTP):
- ✅ **GRATIS** si usas Gmail, Outlook, etc.
- Sin límite de envíos
- Requiere cuenta de email

### WhatsApp (Twilio):
- ✅ **$15 USD gratis** al registrarte
- 📱 **$0.005 USD** por mensaje (medio centavo)
- Ejemplo: $15 = ~3,000 mensajes
- Número sandbox GRATIS
- Número dedicado: ~$1.15/mes

---

## 🎨 PERSONALIZACIÓN

### Modificar Plantillas

Edita `business/notification_system.py`:

```python
def get_template_factura_vencida(self, factura: Dict) -> Dict[str, str]:
    # Personaliza el HTML y texto aquí
    email_html = f"""
    <html>
        <!-- Tu diseño personalizado -->
    </html>
    """
    
    whatsapp_text = f"""
    <!-- Tu mensaje personalizado -->
    """
    
    return {
        "email_subject": "Tu asunto",
        "email_html": email_html,
        "whatsapp_text": whatsapp_text
    }
```

### Agregar Nuevos Triggers

En `business/notification_system.py`:

```python
TRIGGERS = {
    # ... triggers existentes ...
    
    "tu_nuevo_trigger": {
        "nombre": "Tu Trigger",
        "descripcion": "Descripción del trigger",
        "canales": ["email", "whatsapp"],
        "parametros_personalizados": "valor"
    }
}
```

### Cambiar Colores de UI

Los componentes usan automáticamente el theme_manager, respetando dark/light mode.

---

## 📈 PRÓXIMAS MEJORAS SUGERIDAS

1. **Notificaciones Push**: Navegador
2. **SMS**: Vía Twilio (fácil agregar)
3. **Programación de Envíos**: Enviar en fecha/hora específica
4. **Webhooks**: Integraciones con Slack, Discord, etc.
5. **Templates Visuales**: Editor WYSIWYG para emails
6. **A/B Testing**: Probar diferentes mensajes
7. **Analytics Avanzado**: Tasas de apertura, clicks
8. **Respuestas Automáticas**: Chatbot básico

---

## ❓ PREGUNTAS FRECUENTES

### ¿Puedo usar otro proveedor de email?
Sí, cambia SMTP_SERVER y SMTP_PORT en .env

### ¿Necesito pagar Twilio?
No para empezar. $15 gratis + número sandbox

### ¿Los mensajes se guardan?
Sí, en el historial (en memoria, se pierde al reiniciar)

### ¿Puedo enviar a múltiples destinatarios?
No directamente, pero puedes hacer un loop en el código

### ¿Funciona sin configurar?
Sí, pero solo puedes ver la UI. No enviará hasta configurar

### ¿Se pueden desactivar triggers?
Sí, en la pestaña de Configuración

---

## 🎯 CASOS DE USO REALES

### 1. **Comercial Proactivo**
```
Configuración:
- Activa "Factura por Vencer" (3 días antes)
- Canal: WhatsApp
- Destinatario: Tu número

Resultado:
Recibes alertas 3 días antes para hacer seguimiento preventivo
```

### 2. **Gerente Informado**
```
Configuración:
- Activa "Meta Alcanzada"
- Activa "Risk Score Alto"
- Canal: Email
- Destinatario: Email del gerente

Resultado:
Gerente recibe alertas importantes automáticamente
```

### 3. **Equipo Coordinado**
```
Configuración:
- Activa "Factura Vencida"
- Canal: Email y WhatsApp
- Destinatarios: Email grupal + WhatsApp grupal

Resultado:
Todo el equipo se entera de facturas críticas
```

---

## 📞 SOPORTE TÉCNICO

### Archivos Relacionados:
- `business/notification_system.py` - Motor de notificaciones
- `ui/notification_components.py` - Interfaz de usuario
- `ui/tabs.py` - Integración en tabs
- `app.py` - Pestaña principal
- `config_notificaciones_ejemplo.txt` - Guía de configuración

### Recursos Externos:
- **Gmail App Passwords**: https://myaccount.google.com/apppasswords
- **Twilio Console**: https://console.twilio.com
- **Twilio WhatsApp Docs**: https://www.twilio.com/docs/whatsapp
- **SMTP Gmail Docs**: https://support.google.com/mail/answer/7126229

---

## 🎉 RESUMEN

### ✅ LOGROS:
- Sistema de notificaciones completo y funcional
- 2 canales (Email y WhatsApp)
- 5 plantillas predefinidas
- 6 triggers automáticos
- Panel de control profesional
- Estadísticas y gráficos
- Historial completo
- Configuración desde UI
- Documentación exhaustiva

### 🚀 IMPACTO:
- **Comunicación proactiva** con clientes
- **Alertas automáticas** de situaciones críticas
- **Seguimiento preventivo** de vencimientos
- **Celebración de logros** (meta alcanzada)
- **Reducción de cartera vencida**
- **Mejor coordinación de equipo**

---

**¡Sistema de Notificaciones Listo para Usar!** 📧💬✨


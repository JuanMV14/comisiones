# 🚀 Guía Rápida: Ejecutar CRM Localmente

## 📋 Requisitos Previos

1. **Python 3.8+** instalado
2. **Node.js 16+** y **npm** instalados
3. **Credenciales de Supabase** (URL y KEY)

## ⚡ Inicio Rápido (2 Terminales)

### Terminal 1: Backend (FastAPI)

```powershell
# 1. Ir al directorio del backend
cd "C:\Users\Contact Cemter UR\comisiones\crm-react\backend"

# 2. Crear archivo .env con tus credenciales de Supabase
# Copia env.example a .env y edítalo:
copy env.example .env
notepad .env

# 3. Instalar dependencias (solo la primera vez)
pip install -r requirements.txt

# 4. Iniciar el backend
python main.py
```

**O usa el script:**
```powershell
.\start_backend.bat
```

El backend estará en: **http://localhost:8000**

### Terminal 2: Frontend (React/Vite)

```powershell
# 1. Ir al directorio del frontend
cd "C:\Users\Contact Cemter UR\comisiones\crm-react\frontend"

# 2. Instalar dependencias (solo la primera vez)
npm install

# 3. Iniciar el frontend
npm run dev
```

El frontend estará en: **http://localhost:5173** (o el puerto que Vite asigne)

## 🔧 Configuración de Variables de Entorno

### Backend (`crm-react/backend/.env`)

Crea el archivo `.env` en `crm-react/backend/` con:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_service_role_key_aqui
```

### Frontend (Opcional - `crm-react/frontend/.env`)

Solo necesario si quieres configurar manualmente la URL del backend:

```env
VITE_API_URL=http://localhost:8000/api
```

**Nota:** Por defecto, el frontend ya apunta a `http://localhost:8000/api`, así que esto es opcional.

## ✅ Verificar que Todo Funciona

1. **Backend funcionando:**
   - Abre: http://localhost:8000
   - Deberías ver: `{"message":"CRM API - Sistema de Gestión","version":"1.0.0"}`
   
2. **Health check del backend:**
   - Abre: http://localhost:8000/api/health
   - Deberías ver: `{"status":"ok"}`
   
3. **Health check de base de datos:**
   - Abre: http://localhost:8000/api/health/db
   - Deberías ver: `{"status":"ok","supabase":"connected","sample_rows":1}`

4. **Frontend funcionando:**
   - Abre: http://localhost:5173 (o el puerto que muestre Vite)
   - Deberías ver el CRM con el sidebar y el dashboard

## 🐛 Solución de Problemas

### Error: "No module named 'app'"
**Solución:** Asegúrate de estar en el directorio `crm-react/backend` cuando ejecutas `python main.py`

### Error: "Faltan variables de entorno"
**Solución:** Crea el archivo `.env` en `crm-react/backend/` con tus credenciales de Supabase

### Error: "npm no se reconoce"
**Solución:** Instala Node.js desde https://nodejs.org/

### El frontend no se conecta al backend
**Solución:** 
1. Verifica que el backend esté corriendo en http://localhost:8000
2. Abre la consola del navegador (F12) y revisa los errores
3. Verifica que no haya un firewall bloqueando el puerto 8000

### Los datos no aparecen
**Solución:**
1. Verifica que las credenciales de Supabase sean correctas
2. Verifica que la tabla `comisiones` tenga datos en Supabase
3. Revisa la consola del navegador (F12) para ver errores

## 📝 Notas Importantes

- **Backend y Frontend deben correr simultáneamente** en terminales separadas
- El backend debe estar corriendo **antes** de abrir el frontend
- Si cambias código del backend, se recarga automáticamente (gracias a `--reload`)
- Si cambias código del frontend, Vite recarga automáticamente el navegador

## 🎯 Próximos Pasos

Una vez que todo esté funcionando:

1. **Configurar tu nombre de usuario:**
   - Abre la consola del navegador (F12)
   - Ejecuta: `localStorage.setItem('crm_user_name', 'Tu Nombre')`
   - Recarga la página

2. **Explorar las funcionalidades:**
   - Panel del Vendedor
   - Dashboard Ejecutivo (con mapa de Colombia)
   - Análisis Geográfico
   - Análisis Comercial
   - Comisiones Gerencia

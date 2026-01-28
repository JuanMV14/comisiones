# 🌐 Guía de Despliegue Web - CRM

Esta guía te ayudará a desplegar tu aplicación CRM en la web usando Vercel.

## ⚠️ Problema Común

**Error:** La aplicación funciona localmente pero no en la web.

**Causa:** El frontend intenta conectarse a `localhost:8000` que no existe en producción.

## ✅ Solución: Configurar Variables de Entorno

### Paso 0: Instalar Vercel CLI

Si no tienes Vercel CLI instalado, instálalo primero:

**Opción A: Usando npm (Recomendado)**
```bash
npm install -g vercel
```

**Opción B: Usando los scripts .bat (Windows)**
- Ejecuta `desplegar_backend.bat` - se instalará automáticamente si falta

Verifica la instalación:
```bash
vercel --version
```

### Paso 1: Desplegar el Backend en Vercel

**Opción A: Usando el script .bat (Más fácil)**
```bash
# Desde la raíz del proyecto
.\crm-react\desplegar_backend.bat
```

**Opción B: Manualmente**

2. **Desplegar el Backend:**
   ```bash
   cd crm-react/backend
   vercel login
   vercel
   ```

3. **Anotar la URL del Backend:**
   - Vercel te dará una URL como: `https://tu-backend-xxxxx.vercel.app`
   - **Copia esta URL**, la necesitarás en el siguiente paso

### Paso 2: Configurar Variables de Entorno del Backend

En el Dashboard de Vercel → Tu Proyecto Backend → Settings → Environment Variables:

```
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_key_de_supabase
FRONTEND_URLS=https://tu-frontend.vercel.app
ENVIRONMENT=production
```

**Nota:** Reemplaza `tu-frontend.vercel.app` con la URL real de tu frontend (la obtendrás después de desplegar el frontend).

### Paso 3: Desplegar el Frontend en Vercel

1. **Desplegar el Frontend:**
   ```bash
   cd crm-react/frontend
   vercel login
   vercel
   ```

2. **Anotar la URL del Frontend:**
   - Vercel te dará una URL como: `https://tu-frontend-xxxxx.vercel.app`
   - **Copia esta URL**

### Paso 4: Configurar Variables de Entorno del Frontend

En el Dashboard de Vercel → Tu Proyecto Frontend → Settings → Environment Variables:

```
VITE_API_URL=https://tu-backend-xxxxx.vercel.app/api
```

**⚠️ IMPORTANTE:** 
- Reemplaza `tu-backend-xxxxx.vercel.app` con la URL real de tu backend del Paso 1
- La URL debe terminar en `/api`

### Paso 5: Redesplegar el Frontend

Después de agregar las variables de entorno:

1. Ve a Deployments → Latest → ... → Redeploy
2. O ejecuta: `vercel --prod`

**Nota:** Las variables de entorno de Vite solo están disponibles en build time, por lo que debes redesplegar después de agregarlas.

## 🔍 Verificación

### 1. Verificar Backend:
Abre en el navegador: `https://tu-backend-xxxxx.vercel.app`
- Deberías ver: `{"message":"CRM API - Sistema de Gestión","version":"1.0.0"}`

### 2. Verificar Health Check:
Abre: `https://tu-backend-xxxxx.vercel.app/api/health`
- Deberías ver: `{"status":"ok"}`

### 3. Verificar Frontend:
Abre tu URL de Vercel del frontend
- Debería cargar sin errores de conexión
- Abre la consola del navegador (F12) y verifica que no haya errores de red

## 🛠️ Troubleshooting

### Error: "Failed to fetch" o "Network Error"

**Causa:** El frontend no puede conectarse al backend.

**Solución:**
1. Verifica que `VITE_API_URL` esté configurada correctamente en Vercel
2. Verifica que el backend esté desplegado y funcionando
3. Verifica CORS en el backend (debe permitir tu dominio de Vercel)

### Error: "CORS policy"

**Causa:** El backend no permite el origen del frontend.

**Solución:**
1. En el backend, agrega tu URL de Vercel a `FRONTEND_URLS`:
   ```
   FRONTEND_URLS=https://tu-frontend.vercel.app
   ```
2. Redesplegar el backend después de cambiar las variables

### Error: Variables de entorno no funcionan

**Causa:** Las variables de entorno de Vite deben empezar con `VITE_` y solo están disponibles en build time.

**Solución:**
- Solo las variables que empiezan con `VITE_` están disponibles en el frontend
- Después de agregar variables, **redesplegar** el frontend

## 📋 Resumen de URLs

### Desarrollo Local:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Configuración: `.env` local

### Producción (Vercel):
- Frontend: `https://tu-frontend.vercel.app`
- Backend: `https://tu-backend.vercel.app`
- Configuración: Variables de entorno en Vercel Dashboard

## 🔧 Comandos Útiles

```bash
# Ver logs del backend en Vercel
vercel logs --follow

# Ver logs del frontend en Vercel
vercel logs --follow

# Redesplegar manualmente
vercel --prod

# Verificar variables de entorno
vercel env ls
```

## 📝 Notas Importantes

1. **El backend debe estar desplegado ANTES que el frontend** para que funcione correctamente
2. **CORS debe estar configurado** para permitir tu dominio de producción
3. **Las variables de entorno de Vite solo están disponibles en build time**, no en runtime
4. **Después de cambiar variables de entorno, debes redesplegar**

## 🚀 Despliegue Rápido (Desde GitHub)

Si tu código está en GitHub, puedes conectar directamente:

1. Ve a [vercel.com](https://vercel.com)
2. Importa tu repositorio
3. Para el Backend:
   - Root Directory: `crm-react/backend`
   - Framework Preset: Other
   - Build Command: (dejar vacío)
   - Output Directory: (dejar vacío)
4. Para el Frontend:
   - Root Directory: `crm-react/frontend`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
5. Configura las variables de entorno como se indica arriba

¡Listo! Tu aplicación debería estar funcionando en la web. 🎉

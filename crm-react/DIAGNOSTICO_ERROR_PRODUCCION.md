# 🔍 Diagnóstico: Error en Producción

## Pasos para Diagnosticar

### 1. Verificar que el Backend Funciona

Abre en tu navegador:
```
https://backend-navy-eight-27.vercel.app
```

**Deberías ver:**
```json
{"message":"CRM API - Sistema de Gestión","version":"1.0.0"}
```

**Si NO ves eso:**
- El backend no está funcionando
- Ve al Paso 2

**Si SÍ ves eso:**
- El backend funciona ✅
- Ve al Paso 3

### 2. Verificar Variables de Entorno del Backend

1. Ve a [vercel.com/dashboard](https://vercel.com/dashboard)
2. Abre el proyecto **backend**
3. Ve a **Settings** → **Environment Variables**
4. Verifica que tengas:
   - `SUPABASE_URL` = tu URL de Supabase
   - `SUPABASE_KEY` = tu key de Supabase
   - `ENVIRONMENT` = `production`

**Si faltan estas variables:**
- Agrégalas y redesplegar el backend

### 3. Verificar Variable VITE_API_URL en el Frontend

1. Ve a [vercel.com/dashboard](https://vercel.com/dashboard)
2. Abre tu proyecto **frontend**
3. Ve a **Settings** → **Environment Variables**
4. Verifica que tengas:
   - **Key:** `VITE_API_URL`
   - **Value:** `https://backend-navy-eight-27.vercel.app/api`
   - **Environment:** Production, Preview, Development (las tres)

**Si NO está configurada o está mal:**
- Corrígela y redesplegar el frontend

### 4. Verificar que Redesplegaste el Frontend

**⚠️ IMPORTANTE:** Después de agregar o cambiar variables de entorno, SIEMPRE debes redesplegar.

1. Ve a **Deployments**
2. Verifica la fecha del último deployment
3. Si agregaste la variable hace más de 5 minutos y no redesplegaste:
   - Haz clic en el deployment más reciente
   - **...** → **Redeploy**
   - Espera 1-2 minutos

### 5. Verificar en la Consola del Navegador

1. Abre tu aplicación web
2. Presiona **F12** para abrir las herramientas de desarrollador
3. Ve a la pestaña **Console**
4. Busca estos mensajes:

**Si ves:**
```
🌐 Entorno: PRODUCCIÓN
🌐 API URL: https://backend-navy-eight-27.vercel.app/api
```
✅ La variable está configurada correctamente

**Si ves:**
```
⚠️ VITE_API_URL no configurada. Usando ruta relativa /api
```
❌ La variable NO está configurada o no redesplegaste

**Si ves errores de red:**
```
❌ Error de conexión: Network Error
❌ Error de conexión: CORS policy
```
- Ve al Paso 6

### 6. Verificar CORS en el Backend

Si ves errores de CORS:

1. Ve al proyecto backend en Vercel
2. Settings → Environment Variables
3. Agrega:
   - **Key:** `FRONTEND_URLS`
   - **Value:** `https://tu-frontend.vercel.app`
     (Reemplaza con la URL real de tu frontend)
4. Redesplegar el backend

### 7. Verificar Logs del Backend

1. Ve al proyecto backend en Vercel
2. Ve a **Deployments** → Último deployment
3. Haz clic en **View Function Logs**
4. Busca errores relacionados con:
   - Supabase connection
   - Missing environment variables
   - Python errors

## Checklist de Verificación

- [ ] Backend responde en `https://backend-navy-eight-27.vercel.app`
- [ ] Backend tiene `SUPABASE_URL` y `SUPABASE_KEY` configuradas
- [ ] Frontend tiene `VITE_API_URL` configurada correctamente
- [ ] Frontend fue redesplegado después de agregar `VITE_API_URL`
- [ ] La consola del navegador muestra la URL correcta
- [ ] No hay errores de CORS en la consola
- [ ] Los logs del backend no muestran errores críticos

## Solución Rápida

Si después de verificar todo sigue sin funcionar:

1. **Elimina la variable** `VITE_API_URL` del frontend
2. **Vuelve a agregarla** con el valor correcto
3. **Redesplegar** el frontend inmediatamente
4. Espera 2-3 minutos
5. Prueba de nuevo

## Contacto para Ayuda

Si después de seguir todos estos pasos sigue sin funcionar, comparte:
1. Lo que ves en la consola del navegador (F12)
2. Los logs del backend en Vercel
3. Una captura de las variables de entorno configuradas

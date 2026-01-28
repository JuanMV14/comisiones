# 🔍 Verificar Configuración del Backend

## Problema Actual

El frontend se conecta al backend, pero los datos están en 0. Esto indica que:
- ✅ El backend está funcionando
- ❌ El backend no tiene acceso a Supabase (faltan variables de entorno)

## Solución: Configurar Variables del Backend

### Paso 1: Verificar que el Backend Funciona

Abre en tu navegador:
```
https://backend-navy-eight-27.vercel.app
```

**Deberías ver:**
```json
{"message":"CRM API - Sistema de Gestión","version":"1.0.0"}
```

Si ves eso, el backend funciona ✅

### Paso 2: Verificar Health Check de Base de Datos

Abre:
```
https://backend-navy-eight-27.vercel.app/api/health/db
```

**Si ves:**
```json
{"status":"error","message":"Faltan variables de entorno para conectar a Supabase."}
```

**Significa:** Faltan las variables de entorno del backend ❌

**Si ves:**
```json
{"status":"ok","supabase":"connected","sample_rows":1}
```

**Significa:** El backend está conectado a Supabase ✅

### Paso 3: Configurar Variables del Backend en Vercel

1. Ve a [vercel.com/dashboard](https://vercel.com/dashboard)
2. Abre el proyecto **backend** (no el frontend)
3. Ve a **Settings** → **Environment Variables**
4. Agrega estas variables:

**Variable 1:**
- Key: `SUPABASE_URL`
- Value: `https://tu-proyecto.supabase.co`
  (Reemplaza con tu URL real de Supabase)
- Environments: Production, Preview, Development

**Variable 2:**
- Key: `SUPABASE_KEY`
- Value: `tu_service_role_key`
  (Reemplaza con tu key real de Supabase)
- Environments: Production, Preview, Development

**Variable 3:**
- Key: `ENVIRONMENT`
- Value: `production`
- Environments: Production, Preview, Development

5. Guarda todas las variables

### Paso 4: Redesplegar el Backend

**IMPORTANTE:** Después de agregar variables, debes redesplegar:

1. Ve a **Deployments**
2. Haz clic en el deployment más reciente
3. **...** → **Redeploy**
4. Espera 2-3 minutos

### Paso 5: Verificar Después del Redespliegue

1. Abre: `https://backend-navy-eight-27.vercel.app/api/health/db`
2. Deberías ver: `{"status":"ok","supabase":"connected"}`
3. Si ves eso, el backend está conectado ✅

### Paso 6: Verificar el Frontend

1. Abre tu aplicación frontend
2. Presiona **Ctrl+Shift+R** (recarga completa)
3. Los datos deberían aparecer ahora

## Resumen

- ✅ Backend desplegado: `https://backend-navy-eight-27.vercel.app`
- ❌ Backend sin variables de Supabase → Datos en 0
- ✅ Frontend conectándose al backend
- ⚠️ Falta configurar `SUPABASE_URL` y `SUPABASE_KEY` en el backend

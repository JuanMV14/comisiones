# 🔗 Cómo Obtener VITE_API_URL

## ❌ NO es esta URL

La URL `https://vercel.com/oauth/device?user_code=MVMJ-DQMP` es solo para **iniciar sesión** en Vercel. NO es la URL de tu backend.

## ✅ Lo que Necesitas

`VITE_API_URL` debe ser la URL de tu **backend desplegado en Vercel**, algo como:
```
https://crm-backend-xxxxx.vercel.app/api
```

## 📋 Pasos para Obtenerla

### Paso 1: Completar el Login en Vercel

1. Abre en tu navegador: `https://vercel.com/oauth/device?user_code=MVMJ-DQMP`
2. Inicia sesión con tu cuenta de Vercel (Email, Google o GitHub)
3. Confirma que quieres autorizar el dispositivo
4. Vuelve a la terminal y deberías ver: "Congratulations! You are now signed in."

### Paso 2: Desplegar el Backend

Una vez que hayas iniciado sesión, despliega el backend:

```bash
cd crm-react/backend
vercel
```

Vercel te hará algunas preguntas:
- **"Set up and deploy?"** → Presiona `Y` (Sí)
- **"Which scope?"** → Selecciona tu cuenta
- **"Link to existing project?"** → Presiona `N` (No, crear nuevo)
- **"What's your project's name?"** → Escribe: `crm-backend` (o el nombre que prefieras)
- **"In which directory is your code located?"** → Presiona Enter (ya estás en el directorio correcto)
- **"Want to override the settings?"** → Presiona `N` (No)

### Paso 3: Copiar la URL del Backend

Al finalizar el despliegue, Vercel mostrará algo como:

```
✅ Production: https://crm-backend-xxxxx.vercel.app [copied to clipboard]
```

**Esa es la URL que necesitas!** Debería verse así:
```
https://crm-backend-xxxxx.vercel.app
```

### Paso 4: Configurar VITE_API_URL

La URL completa que debes usar es la del backend + `/api`:

```
https://crm-backend-xxxxx.vercel.app/api
```

**Ejemplo:**
- Si tu backend está en: `https://crm-backend-abc123.vercel.app`
- Entonces `VITE_API_URL` debe ser: `https://crm-backend-abc123.vercel.app/api`

## 🔍 Cómo Verificar la URL del Backend

Si ya desplegaste el backend antes, puedes ver su URL:

1. Ve a [vercel.com/dashboard](https://vercel.com/dashboard)
2. Busca tu proyecto backend (ej: `crm-backend`)
3. Haz clic en él
4. Verás la URL en la parte superior, algo como:
   ```
   https://crm-backend-xxxxx.vercel.app
   ```

## ✅ Resumen

1. ✅ Completa el login en Vercel (usa la URL que te dio)
2. ✅ Despliega el backend: `cd crm-react/backend && vercel`
3. ✅ Copia la URL que te da Vercel (ej: `https://crm-backend-xxxxx.vercel.app`)
4. ✅ Agrega `/api` al final: `https://crm-backend-xxxxx.vercel.app/api`
5. ✅ Esa es tu `VITE_API_URL`!

## 🧪 Probar que el Backend Funciona

Antes de configurar `VITE_API_URL`, verifica que el backend funciona:

1. Abre en tu navegador la URL del backend (sin `/api`)
2. Deberías ver: `{"message":"CRM API - Sistema de Gestión","version":"1.0.0"}`
3. Si ves eso, el backend está funcionando ✅

---

**¿Necesitas ayuda?** Si ya desplegaste el backend, comparte la URL que te dio Vercel y te ayudo a configurarla correctamente.

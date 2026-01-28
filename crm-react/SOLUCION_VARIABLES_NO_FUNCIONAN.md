# 🔧 Solución: Variables de Entorno No Funcionan en Vercel

## Problema

Tienes `VITE_API_URL` configurada en Vercel, ya redesplegaste, pero la aplicación sigue mostrando que no está configurada.

## Posibles Causas

### 1. Variable en el Nivel Incorrecto (Team vs Project)

**Problema:** La variable está en el nivel de **Team** en lugar de **Project**.

**Solución:**
1. Ve a Vercel Dashboard → Tu proyecto frontend
2. Settings → Environment Variables
3. Verifica que la variable esté en la sección del **PROYECTO**, no en "Team"
4. Si está en Team, elimínala y créala de nuevo en el nivel del proyecto

### 2. Variable No Está en Todos los Ambientes

**Problema:** La variable solo está configurada para un ambiente (ej: solo Production).

**Solución:**
1. Edita la variable `VITE_API_URL`
2. Asegúrate de que esté marcada para:
   - ☑ Production
   - ☑ Preview
   - ☑ Development
3. Guarda y redesplegar

### 3. El Build No Está Usando la Variable

**Problema:** Vercel no está aplicando la variable durante el build.

**Solución:**
1. Ve a Deployments → Último deployment
2. Haz clic en el deployment
3. Ve a la pestaña **Build Logs**
4. Busca si aparece `VITE_API_URL` en los logs
5. Si no aparece, la variable no se está aplicando

### 4. Caché del Build

**Problema:** Vercel está usando un build cacheado sin las variables.

**Solución:**
1. Ve a Deployments
2. Crea un nuevo deployment desde cero:
   - Haz clic en "..." → "Redeploy"
   - O mejor aún, haz un pequeño cambio en el código y haz push a GitHub
   - Esto forzará un build completamente nuevo

## Solución Paso a Paso

### Opción 1: Eliminar y Recrear la Variable

1. Ve a Settings → Environment Variables
2. **Elimina** `VITE_API_URL` completamente
3. Guarda
4. Espera 30 segundos
5. **Vuelve a agregarla:**
   - Key: `VITE_API_URL`
   - Value: `https://backend-navy-eight-27.vercel.app/api`
   - Environments: Production, Preview, Development (las tres)
6. Guarda
7. **Redesplegar INMEDIATAMENTE** (no esperes)
8. Espera 2-3 minutos

### Opción 2: Forzar un Build Nuevo

1. Haz un pequeño cambio en cualquier archivo del frontend (ej: agregar un comentario)
2. Haz commit y push a GitHub:
   ```bash
   git add .
   git commit -m "Forzar nuevo build"
   git push origin main
   ```
3. Vercel debería detectar el cambio y hacer un build nuevo
4. Espera a que termine el deployment

### Opción 3: Verificar Build Logs

1. Ve a Deployments → Último deployment
2. Haz clic en el deployment
3. Ve a **Build Logs**
4. Busca en los logs si aparece `VITE_API_URL`
5. Si aparece, la variable está siendo leída
6. Si no aparece, hay un problema de configuración

## Verificación Final

Después de seguir los pasos:

1. Abre tu aplicación web
2. Presiona **Ctrl+Shift+R** (recarga completa, limpia caché)
3. Presiona **F12** → pestaña **Console**
4. Deberías ver:
   ```
   🌐 Entorno: PRODUCCIÓN
   🌐 API URL: https://backend-navy-eight-27.vercel.app/api
   ✅ VITE_API_URL configurada correctamente: https://backend-navy-eight-27.vercel.app/api
   ```

## Si Nada Funciona

Si después de todo esto sigue sin funcionar:

1. **Verifica que el código más reciente esté en GitHub**
2. **Despliega manualmente desde la terminal:**
   ```bash
   cd crm-react/frontend
   vercel --prod
   ```
3. Esto forzará un build local con las variables configuradas

## Contacto

Si después de seguir todos estos pasos sigue sin funcionar, comparte:
1. Una captura de las variables de entorno en Vercel
2. Los Build Logs del último deployment
3. Lo que ves en la consola del navegador

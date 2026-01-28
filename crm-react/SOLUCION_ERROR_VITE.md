# Solución: Error "vite: command not found"

## Problema
Al intentar ejecutar el frontend, aparece el error:
```
sh: line 1: vite: command not found
Error: Command "vite build" exited with 127
```

## Causa
El comando `vite` no está disponible directamente en el PATH del sistema. Vite está instalado como dependencia local del proyecto en `node_modules/.bin/`.

## Soluciones

### ✅ Solución 1: Usar npm scripts (Recomendado)
Siempre usa los scripts de npm definidos en `package.json`:

```bash
# Para desarrollo
npm run dev

# Para construir para producción
npm run build

# Para previsualizar el build
npm run preview
```

### ✅ Solución 2: Usar npx
Si necesitas ejecutar vite directamente, usa `npx`:

```bash
# Desarrollo
npx vite

# Build
npx vite build

# Preview
npx vite preview
```

### ✅ Solución 3: Instalar dependencias
Si el error persiste, asegúrate de que las dependencias estén instaladas:

```bash
cd crm-react/frontend
npm install
```

### ✅ Solución 4: Para despliegues (Vercel, Netlify, etc.)
Asegúrate de que el archivo `vercel.json` (o configuración equivalente) use:

```json
{
  "buildCommand": "npm run build",
  "installCommand": "npm install"
}
```

**NO uses:**
```json
{
  "buildCommand": "vite build"  // ❌ Esto causará el error
}
```

## Verificación
Para verificar que todo funciona:

```bash
cd crm-react/frontend
npm run build
```

Si el build se completa sin errores, todo está correcto.

## Nota
Los scripts `.bat` en Windows ya están configurados correctamente usando `npm run dev`, por lo que deberían funcionar sin problemas.

# 🚚 Guía del Sistema de Validación de Flete

## 📋 Resumen

Este sistema te ayuda a validar automáticamente si un pedido debe o no incluir flete según las reglas de envío.

## 🎯 Reglas de Flete Gratis

### Medellín
- **Base ≥ $1,500,000** → ✅ Sin flete
- **Base < $1,500,000** → ⚠️ Con flete
- **Recogida Local** → ✅ NUNCA flete (sin importar el valor)

### Bogotá
- **Base ≥ $2,000,000** → ✅ Sin flete
- **Base < $2,000,000** → ⚠️ Con flete

### Resto del País
- **Base ≥ $4,000,000** → ✅ Sin flete
- **Base < $4,000,000** → ⚠️ Con flete

---

## 🔧 Instalación

### Paso 1: Agregar campos a la base de datos

1. Abre tu **Supabase Dashboard**
2. Ve a **SQL Editor**
3. Ejecuta el contenido del archivo `agregar_campos_flete.sql`
4. Verifica que se ejecutó correctamente (debería decir "Success")

**Nota:** Si ya tienes facturas registradas, se les asignará automáticamente:
- `ciudad_destino`: "Resto" (por defecto)
- `recogida_local`: `false`

---

## 💡 Cómo Usar el Sistema

### Al Registrar una Nueva Venta

1. **Llena los datos básicos** (Pedido, Cliente, Fecha, Valor)

2. **Selecciona la ciudad de destino**:
   - Medellín
   - Bogotá
   - Resto

3. **Si es Medellín y recogen localmente**:
   - ✅ Marca el checkbox "Recogida Local"
   - El sistema automáticamente indicará que NO debe tener flete

4. **Verifica el Preview**:
   - El sistema te mostrará automáticamente si debe o no tener flete
   - ✅ Verde = NO debe tener flete
   - ⚠️ Amarillo = SÍ debe incluir flete

### Ejemplos

#### Ejemplo 1: Pedido a Medellín de $2,000,000
```
Ciudad: Medellín
Base: $2,000,000
Recogida Local: No

Resultado: ✅ Sin flete (Base ≥ $1,500,000)
```

#### Ejemplo 2: Pedido a Medellín de $800,000
```
Ciudad: Medellín
Base: $800,000
Recogida Local: No

Resultado: ⚠️ Con flete (Base < $1,500,000)
```

#### Ejemplo 3: Recogida Local en Medellín
```
Ciudad: Medellín
Base: $500,000
Recogida Local: ✅ Sí

Resultado: ✅ Sin flete (Recogida local)
```

#### Ejemplo 4: Pedido a Bogotá de $2,500,000
```
Ciudad: Bogotá
Base: $2,500,000

Resultado: ✅ Sin flete (Base ≥ $2,000,000)
```

#### Ejemplo 5: Pedido al Resto de $5,000,000
```
Ciudad: Resto
Base: $5,000,000

Resultado: ✅ Sin flete (Base ≥ $4,000,000)
```

---

## ❓ Preguntas Frecuentes

### ¿El flete afecta mi comisión?
**No.** El flete NO suma ni resta en la base de comisión. La comisión se calcula sobre el valor neto de los productos (sin IVA).

### ¿Qué pasa si me equivoco y marco mal la ciudad?
Puedes editar la factura después y cambiar la ciudad de destino.

### ¿Qué pasa con las facturas que ya tengo registradas?
Las facturas antiguas tendrán "Resto" como ciudad por defecto. Puedes editarlas manualmente si necesitas actualizar la información.

### ¿Puedo ver cuánto le falta a un cliente para obtener flete gratis?
Sí, el sistema te muestra en el preview cuánto necesita alcanzar para obtener flete gratis.

---

## 🎨 Capturas de Pantalla (Visual)

### Formulario de Nueva Venta con Validación de Flete

```
┌─ Información de Envío ────────────────────────┐
│                                                │
│  Ciudad de Destino *      [Medellín ▼]        │
│                                                │
│  ☐ Recogida Local                             │
│                                                │
└────────────────────────────────────────────────┘

┌─ Preview ──────────────────────────────────────┐
│                                                │
│  ✅ Este pedido NO debe tener flete           │
│     Base ≥ $1,500,000 - Sin flete             │
│                                                │
└────────────────────────────────────────────────┘
```

---

## 🛠️ Soporte

Si encuentras algún problema o tienes dudas sobre el sistema de flete, contacta al equipo de desarrollo.

---

**Última actualización:** Octubre 2025


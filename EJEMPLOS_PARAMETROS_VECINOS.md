# 📚 Ejemplos de Funcionamiento de Parámetros de Detección de Vecinos

## Configuración (Líneas 49-54)

```python
PROTECT_NEARBY_WORDS = True   # Excluir áreas de otras palabras detectadas
NEARBY_DISTANCE_THRESHOLD = 30  # Distancia máxima para considerar "cercana" (píxeles)
EXCLUSION_PADDING = 3         # Padding adicional alrededor de palabras protegidas
EXCLUSION_BRIGHTNESS_THRESHOLD = 50  # Umbral para detectar texto vecino
EXCLUSION_MIN_AREA = 50  # Área mínima en píxeles para considerar que hay texto real
```

---

## 1. `PROTECT_NEARBY_WORDS` (Línea 49)

### ¿Qué hace?
Activa o desactiva completamente la protección de palabras cercanas.

### Ejemplo Visual:

```
┌─────────────────────────────────────────┐
│  ESCENARIO: Quieres borrar "Mastira"   │
│  pero hay "Tropicales" muy cerca       │
└─────────────────────────────────────────┘

PROTECT_NEARBY_WORDS = False:
┌─────────────────────────────────────┐
│  [Mastira] ← Borrar                │
│  [Tropicales] ← ❌ SE BORRA TAMBIÉN │
└─────────────────────────────────────┘
Resultado: "Tropicales" se borra accidentalmente ❌

PROTECT_NEARBY_WORDS = True:
┌─────────────────────────────────────┐
│  [Mastira] ← Borrar                │
│  [Tropicales] ← ✅ PROTEGIDO        │
└─────────────────────────────────────┘
Resultado: Solo "Mastira" se borra, "Tropicales" se protege ✅
```

### Uso en el código:
- **Línea 220**: Si es `False`, la función retorna inmediatamente sin proteger nada
- **Línea 399**: Solo aplica exclusión si está activado
- **Línea 564**: Solo crea máscara de exclusión si está activado

---

## 2. `NEARBY_DISTANCE_THRESHOLD` (Línea 50)

### ¿Qué hace?
Define la distancia máxima (en píxeles) entre dos palabras para considerarlas "cercanas" y activar la protección.

### Ejemplo Visual:

```
Imagina esta situación:
┌─────────────────────────────────────────────────────┐
│  [Palabra A]    [Palabra B]    [Palabra C]         │
│     ↑              ↑              ↑                  │
│   x=100          x=200          x=500               │
└─────────────────────────────────────────────────────┘

Distancia A→B = 200 - 100 = 100 píxeles
Distancia B→C = 500 - 200 = 300 píxeles

NEARBY_DISTANCE_THRESHOLD = 30:
┌─────────────────────────────────────────────────────┐
│  [A] ← 100px → [B] ← 300px → [C]                   │
│   ❌ No protege B (100 > 30)                        │
│   ❌ No protege C (300 > 30)                        │
└─────────────────────────────────────────────────────┘
Resultado: Ninguna palabra se protege (muy estricto)

NEARBY_DISTANCE_THRESHOLD = 150:
┌─────────────────────────────────────────────────────┐
│  [A] ← 100px → [B] ← 300px → [C]                   │
│   ✅ Protege B (100 < 150)                          │
│   ❌ No protege C (300 > 150)                       │
└─────────────────────────────────────────────────────┘
Resultado: Solo B se protege cuando borras A

NEARBY_DISTANCE_THRESHOLD = 1000:
┌─────────────────────────────────────────────────────┐
│  [A] ← 100px → [B] ← 300px → [C]                   │
│   ✅ Protege B (100 < 1000)                         │
│   ✅ Protege C (300 < 1000)                         │
└─────────────────────────────────────────────────────┘
Resultado: TODAS las palabras se protegen (muy permisivo)
```

### Ejemplo Real con tu código:

```python
# Situación: Quieres borrar "Mastira" que está a 25px de "Tropicales"

NEARBY_DISTANCE_THRESHOLD = 30:
  → Distancia (25px) < 30px → ✅ "Tropicales" se protege

NEARBY_DISTANCE_THRESHOLD = 20:
  → Distancia (25px) > 20px → ❌ "Tropicales" NO se protege
```

### Uso en el código:
- **Línea 252**: Compara `min_dist <= NEARBY_DISTANCE_THRESHOLD`
- Si la distancia es menor o igual, activa la protección

### Valores recomendados:
- **10-30px**: Texto muy denso, palabras casi pegadas
- **30-50px**: Texto normal en documentos
- **50-100px**: Texto espaciado
- **1000px**: Prácticamente protege todo (no recomendado)

---

## 3. `EXCLUSION_PADDING` (Línea 51)

### ¿Qué hace?
Añade un margen de seguridad (padding) alrededor del texto detectado en palabras vecinas para asegurar que no se borre accidentalmente.

### Ejemplo Visual:

```
Situación: Detectamos el texto real de "Tropicales"
┌─────────────────────────────────────────┐
│  Texto detectado:                       │
│  ┌─────────┐                            │
│  │Tropical │  ← Texto real detectado    │
│  └─────────┘                            │
└─────────────────────────────────────────┘

EXCLUSION_PADDING = 0:
┌─────────────────────────────────────────┐
│  ┌─────────┐                            │
│  │Tropical │  ← Solo protege el texto   │
│  └─────────┘                            │
└─────────────────────────────────────────┘
Resultado: Muy ajustado, puede borrar bordes ❌

EXCLUSION_PADDING = 3:
┌─────────────────────────────────────────┐
│  ┌─────────────┐                        │
│  │  Tropical   │  ← Protege + 3px       │
│  └─────────────┘                        │
└─────────────────────────────────────────┘
Resultado: Margen de seguridad adecuado ✅

EXCLUSION_PADDING = 1000:
┌─────────────────────────────────────────┐
│  ┌───────────────────────────────────┐  │
│  │         Tropical                  │  ← Protege + 1000px
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
Resultado: Protege un área enorme, puede bloquear todo ❌
```

### Ejemplo Real:

```python
# Texto "Tropicales" detectado en coordenadas (100, 50) a (200, 80)

EXCLUSION_PADDING = 3:
  → Protege área: (97, 47) a (203, 83)  [3px de margen en cada lado]

EXCLUSION_PADDING = 10:
  → Protege área: (90, 40) a (210, 90)  [10px de margen en cada lado]
```

### Uso en el código:
- **Línea 306**: Crea un kernel de tamaño `(EXCLUSION_PADDING * 2, EXCLUSION_PADDING * 2)`
- **Línea 307**: Dilata la máscara de texto con este padding

### Valores recomendados:
- **1-3px**: Texto bien separado
- **3-5px**: Texto normal (recomendado)
- **5-10px**: Texto muy denso o con bordes difusos
- **1000px**: Bloquea demasiado área (no recomendado)

---

## 4. `EXCLUSION_BRIGHTNESS_THRESHOLD` (Línea 52)

### ¿Qué hace?
Define qué tan diferente debe ser el brillo del texto respecto al fondo para considerarlo "texto real" en palabras vecinas.

### Ejemplo Visual:

```
Situación: Palabra vecina "Tropicales" sobre fondo blanco
┌─────────────────────────────────────────┐
│  Fondo: ████████████ (brillo = 240)    │
│  Texto: ▓▓▓▓▓▓▓▓▓▓▓▓ (brillo = 50)     │
│  Diferencia: 240 - 50 = 190             │
└─────────────────────────────────────────┘

EXCLUSION_BRIGHTNESS_THRESHOLD = 50:
  → Diferencia (190) > 50 → ✅ Detecta como texto
  → Resultado: Protege "Tropicales" correctamente

EXCLUSION_BRIGHTNESS_THRESHOLD = 200:
  → Diferencia (190) < 200 → ❌ NO detecta como texto
  → Resultado: No protege "Tropicales" (puede borrarse)
```

### Ejemplo con Fondo Claro:

```python
# Fondo claro (brillo = 200), Texto oscuro (brillo = 30)
# Diferencia = 200 - 30 = 170

EXCLUSION_BRIGHTNESS_THRESHOLD = 50:
  → 200 - 30 = 170 > 50 → ✅ Detecta texto
  → Usa: bg_brightness - EXCLUSION_BRIGHTNESS_THRESHOLD
  → Umbral: 200 - 50 = 150
  → Píxeles < 150 se consideran texto

EXCLUSION_BRIGHTNESS_THRESHOLD = 200:
  → 200 - 30 = 170 < 200 → ❌ NO detecta texto
  → Umbral: 200 - 200 = 0
  → Casi ningún píxel se considera texto
```

### Ejemplo con Fondo Oscuro:

```python
# Fondo oscuro (brillo = 30), Texto claro (brillo = 200)
# Diferencia = 200 - 30 = 170

EXCLUSION_BRIGHTNESS_THRESHOLD = 50:
  → 200 - 30 = 170 > 50 → ✅ Detecta texto
  → Usa: bg_brightness + EXCLUSION_BRIGHTNESS_THRESHOLD
  → Umbral: 30 + 50 = 80
  → Píxeles > 80 se consideran texto

EXCLUSION_BRIGHTNESS_THRESHOLD = 200:
  → 200 - 30 = 170 < 200 → ❌ NO detecta texto
  → Umbral: 30 + 200 = 230
  → Casi ningún píxel se considera texto
```

### Uso en el código:
- **Líneas 279-285**: Fondo claro → `bg_brightness - EXCLUSION_BRIGHTNESS_THRESHOLD`
- **Líneas 286-292**: Fondo oscuro → `bg_brightness + EXCLUSION_BRIGHTNESS_THRESHOLD`

### Valores recomendados:
- **20-40**: Texto muy contrastado (negro sobre blanco)
- **40-60**: Texto normal (recomendado: 50)
- **60-80**: Texto con poco contraste
- **1000**: Muy estricto, casi no detecta nada (no recomendado)

---

## 5. `EXCLUSION_MIN_AREA` (Línea 53)

### ¿Qué hace?
Define el área mínima (en píxeles) que debe tener el texto detectado en una palabra vecina para considerarlo "texto real" y protegerlo.

### Ejemplo Visual:

```
Situación: Detectamos píxeles en palabra vecina "Tropicales"
┌─────────────────────────────────────────┐
│  Caso 1: Texto completo                │
│  ┌─────────────────┐                   │
│  │  Tropicales     │  Área = 800px     │
│  └─────────────────┘                   │
│                                        │
│  Caso 2: Solo ruido/píxeles sueltos    │
│  • • • • • • • • •                     │
│  Área = 15px                           │
└─────────────────────────────────────────┘

EXCLUSION_MIN_AREA = 50:
  → Caso 1: 800px > 50px → ✅ Protege "Tropicales"
  → Caso 2: 15px < 50px → ❌ Ignora (es solo ruido)

EXCLUSION_MIN_AREA = 1000:
  → Caso 1: 800px < 1000px → ❌ NO protege (muy estricto)
  → Caso 2: 15px < 1000px → ❌ Ignora
```

### Ejemplo Real:

```python
# Palabra "Tropicales" detectada:
# - Texto real: 800 píxeles detectados
# - Ruido/artefactos: 20 píxeles sueltos

EXCLUSION_MIN_AREA = 50:
  → Texto real: 800 > 50 → ✅ Protege
  → Ruido: 20 < 50 → ❌ Ignora
  → Resultado: Protege solo el texto real ✅

EXCLUSION_MIN_AREA = 1000:
  → Texto real: 800 < 1000 → ❌ NO protege
  → Ruido: 20 < 1000 → ❌ Ignora
  → Resultado: No protege nada (muy estricto) ❌
```

### Uso en el código:
- **Línea 300**: Calcula `text_area = np.sum(text_mask > 0)`
- **Línea 301**: Compara `if text_area < EXCLUSION_MIN_AREA:`
- **Línea 303**: Si el área es muy pequeña, ignora esa palabra vecina (es probablemente ruido)

### Valores recomendados:
- **20-30px**: Texto muy pequeño o letras individuales
- **50-100px**: Texto normal (recomendado: 50)
- **100-200px**: Texto grande o palabras completas
- **1000px**: Muy estricto, solo protege texto muy grande (no recomendado)

---

## 🎯 Resumen de Valores Recomendados

```python
# Configuración ÓPTIMA para texto normal:
PROTECT_NEARBY_WORDS = True
NEARBY_DISTANCE_THRESHOLD = 30      # 10-50px según densidad
EXCLUSION_PADDING = 3               # 1-5px según necesidad
EXCLUSION_BRIGHTNESS_THRESHOLD = 50 # 40-60px para buen contraste
EXCLUSION_MIN_AREA = 50             # 30-100px según tamaño texto
```

### ⚠️ Advertencia sobre valores altos (1000):

Si pones todos los valores en 1000:
- `NEARBY_DISTANCE_THRESHOLD = 1000`: Protege TODAS las palabras (incluso lejanas)
- `EXCLUSION_PADDING = 1000`: Crea áreas de protección enormes
- `EXCLUSION_BRIGHTNESS_THRESHOLD = 1000`: Muy estricto, casi no detecta texto
- `EXCLUSION_MIN_AREA = 1000`: Solo protege texto muy grande

**Resultado**: El sistema puede no funcionar correctamente o proteger demasiado/poco.

---

## 🔍 Flujo Completo de Ejemplo

```
1. OCR detecta: "Mastira" (objetivo) y "Tropicales" (vecina)
   └─ Distancia entre ellas: 25 píxeles

2. NEARBY_DISTANCE_THRESHOLD = 30
   └─ 25 < 30 → ✅ Activa protección

3. EXCLUSION_BRIGHTNESS_THRESHOLD = 50
   └─ Detecta texto en "Tropicales" (diferencia de brillo > 50)

4. EXCLUSION_MIN_AREA = 50
   └─ Texto detectado = 800px > 50px → ✅ Es texto real

5. EXCLUSION_PADDING = 3
   └─ Añade 3px de margen alrededor del texto detectado

6. Resultado: "Tropicales" se protege, "Mastira" se borra ✅
```

---

## 📝 Notas Finales

- Estos parámetros trabajan **juntos** para proteger palabras cercanas
- Si `PROTECT_NEARBY_WORDS = False`, los demás parámetros se ignoran
- Los valores deben ajustarse según el tipo de imagen y texto
- Valores muy altos (1000) generalmente no son útiles en la práctica


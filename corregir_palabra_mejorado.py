from paddleocr import PaddleOCR
import cv2
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- 1. Configuración de PaddleOCR ---
ocr = PaddleOCR(
    text_recognition_model_name="PP-OCRv4_server_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_det_unclip_ratio=1.1
)

# --- CONFIGURACIÓN ---

image_path = 'lanco2.png'

texts_to_erase = ["Defintative","projecto.","mastira"," jVisitanos y aseura tu projecto con Lanco!" ]
texts_to_add = ["Definitiva", "proyecto.", "maestra", " ¡Visitanos y asegura tu proyecto con Lanco!"]
texts_to_sample_color_from = ["Superior", "durabilidad","durabilidad","Superior"]




offsets_x = [0]
offsets_y = [0]

font_path = 'Montserrat-Bold.ttf'
font_size = 80

# ═══════════════════════════════════════════════════════════
# ⚙️ PANEL DE CONTROL - ESTRATEGIA DE MÁSCARA INTELIGENTE
# ═══════════════════════════════════════════════════════════

# 🎯 ESTRATEGIA DE BORRADO
# Opciones: "box_shrink", "morphology", "smart_mask"
ERASE_STRATEGY = "morphology"  # ⭐ RECOMENDADO para texto

# --- PARA "box_shrink" (tu método original mejorado) ---
BOX_SHRINK_TOP = 0.15
BOX_SHRINK_BOTTOM = 0.15
BOX_SHRINK_LEFT = 0.03
BOX_SHRINK_RIGHT = 0.03

# --- PARA "morphology" (detecta forma real del texto) ---
MORPH_DILATE_KERNEL = 5      # Expansión del área de borrado (1-7) - Aumentado para borrar más
MORPH_ERODE_KERNEL = 1       # Contracción para ajustar (0-5) - Reducido para no quitar tanto
BRIGHTNESS_THRESHOLD = 30    # Diferencia mínima con fondo (20-60) - Reducido para texto en banner dorado
POLYGON_EXPANSION_PX = 3     # Píxeles para expandir el polígono original antes de restringir (0-10)

# 🛡️ PROTECCIÓN CONTRA BORRAR PALABRAS CERCANAS (MEJORADA)
PROTECT_NEARBY_WORDS = True   # Excluir áreas de otras palabras detectadas
NEARBY_DISTANCE_THRESHOLD = 20 # Distancia máxima para considerar "cercana" (píxeles) - Reducido para ser más estricto
EXCLUSION_PADDING = 5      # Padding adicional alrededor de palabras protegidas - Aumentado para mejor protección
EXCLUSION_BRIGHTNESS_THRESHOLD = 40  # Umbral para detectar texto vecino - Reducido para capturar más texto
EXCLUSION_MIN_AREA = 30  # Área mínima en píxeles para considerar que hay texto real - Reducido
EXCLUSION_OVERLAP_RATIO = 0.5  # Máximo 50% de superposición para considerar como vecino (no parte del texto a borrar)
EXCLUSION_USE_POLYGON = True  # Usar el polígono original del vecino como base de protección (más robusto)

# --- PARA "smart_mask" (combina ambos métodos) ---
USE_SMART_MASK = False        # Combinar morfología + reducción de caja

# 🎨 MUESTREO DE COLOR
COLOR_SHRINK = 0.35
MIN_SATURATION = 50
MIN_VALUE = 50
EXCLUDE_EXTREMES = True

# 🔧 INPAINTING
INPAINT_RADIUS = 3
INPAINT_METHOD = cv2.INPAINT_TELEA

# 🐛 DEBUG
DEBUG_SHOW_MASKS = True  # Mostrar máscaras intermedias para depuración

print("═" * 70)
print("⚙️  CONFIGURACIÓN ACTIVA")
print("═" * 70)
print(f"Estrategia de borrado: {ERASE_STRATEGY}")
if ERASE_STRATEGY == "morphology":
    print(f"  Dilatación: {MORPH_DILATE_KERNEL}, Erosión: {MORPH_ERODE_KERNEL}")
    print(f"  Umbral de brillo: {BRIGHTNESS_THRESHOLD}")
    print(f"  Expansión polígono: {POLYGON_EXPANSION_PX}px")
elif ERASE_STRATEGY == "box_shrink":
    print(f"  Reducción: T={BOX_SHRINK_TOP} B={BOX_SHRINK_BOTTOM} L={BOX_SHRINK_LEFT} R={BOX_SHRINK_RIGHT}")
print(f"Color: Área={COLOR_SHRINK}, Sat≥{MIN_SATURATION}, Val≥{MIN_VALUE}")
print(f"Inpaint: Radio={INPAINT_RADIUS}")
print(f"🛡️ Protección palabras cercanas: {'ON' if PROTECT_NEARBY_WORDS else 'OFF'}")
if PROTECT_NEARBY_WORDS:
    print(f"  Distancia umbral: {NEARBY_DISTANCE_THRESHOLD}px, Padding: {EXCLUSION_PADDING}px")
    print(f"  Umbral detección texto vecino: {EXCLUSION_BRIGHTNESS_THRESHOLD}")
    print(f"  Superposición máxima permitida: {EXCLUSION_OVERLAP_RATIO*100:.0f}% (solo protege si está principalmente fuera)")
    print(f"  Usar polígono original: {'SÍ' if EXCLUSION_USE_POLYGON else 'NO'} (más robusto)")
print("═" * 70)

# --- Validación ---
if len(texts_to_erase) != len(texts_to_add) or len(texts_to_erase) != len(texts_to_sample_color_from):
    print("❌ Error: Las listas deben tener la misma longitud.")
    exit()

if not isinstance(offsets_x, list):
    offsets_x = [offsets_x] * len(texts_to_erase)
elif len(offsets_x) == 1:
    offsets_x = offsets_x * len(texts_to_erase)

if not isinstance(offsets_y, list):
    offsets_y = [offsets_y] * len(texts_to_erase)
elif len(offsets_y) == 1:
    offsets_y = offsets_y * len(texts_to_erase)

# --- 2. Cargar imagen ---
img_bgr = cv2.imread(image_path)
if img_bgr is None:
    print(f"❌ Error: No se pudo cargar '{image_path}'")
    exit()
h_img, w_img = img_bgr.shape[:2]

# --- 3. Ejecutar OCR ---
result = ocr.predict(image_path)

# --- Mostrar todas las palabras detectadas ---
print("\n" + "═" * 70)
print("📝 PALABRAS DETECTADAS POR OCR:")
print("═" * 70)
if result:
    for page_result in result:
        rec_texts = page_result.get('rec_texts', [])
        if rec_texts:
            for idx, text in enumerate(rec_texts, 1):
                print(f"  {idx}. '{text}'")
        else:
            print("  No se detectaron palabras")
else:
    print("  No se obtuvieron resultados del OCR")
print("═" * 70 + "\n")


# CREAMOS UN POLIGONO REDUCIDO PARA EL BORRADO DE LAS PALABRAS DETECTADAS POR OCR 
def create_mask_box_shrink(polygon, top, bottom, left, right):
    """Método 1: Reducir caja del OCR (OBSOLETO - usar expand_polygon)."""
    points = np.array(polygon).astype(np.float32)
    
    x_coords = points[:, 0]
    y_coords = points[:, 1]
    
    x_min, x_max = np.min(x_coords), np.max(x_coords)
    y_min, y_max = np.min(y_coords), np.max(y_coords)
    
    width = x_max - x_min
    height = y_max - y_min
    
    new_x_min = x_min + width * left
    new_x_max = x_max - width * right
    new_y_min = y_min + height * top
    new_y_max = y_max - height * bottom
    
    new_polygon = np.array([
        [new_x_min, new_y_min],
        [new_x_max, new_y_min],
        [new_x_max, new_y_max],
        [new_x_min, new_y_max]
    ], dtype=np.int32)
    
    return new_polygon



def create_exclusion_mask(target_polygon, nearby_polygons, h_img, w_img, img_bgr):
    """Crea una máscara de exclusión para proteger TEXTO REAL de palabras cercanas."""
    exclusion_mask = np.zeros((h_img, w_img), dtype=np.uint8)
    
    if not PROTECT_NEARBY_WORDS or nearby_polygons is None or len(nearby_polygons) == 0:
        return exclusion_mask
    
    target_points = np.array(target_polygon).astype(np.int32)
    target_x_min = int(np.min(target_points[:, 0]))
    target_x_max = int(np.max(target_points[:, 0]))
    target_y_min = int(np.min(target_points[:, 1]))
    target_y_max = int(np.max(target_points[:, 1]))
    
    protected_count = 0
    for other_poly in nearby_polygons:
        other_points = np.array(other_poly).astype(np.int32)
        other_x_min = int(np.min(other_points[:, 0]))
        other_x_max = int(np.max(other_points[:, 0]))
        other_y_min = int(np.min(other_points[:, 1]))
        other_y_max = int(np.max(other_points[:, 1]))
        
        # Calcular distancia mínima entre bounding boxes
        dist_bottom = other_y_min - target_y_max
        dist_top = target_y_min - other_y_max
        dist_right = other_x_min - target_x_max
        dist_left = target_x_min - other_x_max
        
        # 🆕 Verificar si el texto vecino está COMPLETAMENTE DENTRO del área objetivo
        # Si está completamente dentro, NO es un vecino a proteger, es parte del texto a borrar
        neighbor_inside_target = (
            other_x_min >= target_x_min and 
            other_x_max <= target_x_max and 
            other_y_min >= target_y_min and 
            other_y_max <= target_y_max
        )
        
        # Si el vecino está completamente dentro del área objetivo, ignorarlo (es parte del texto a borrar)
        if neighbor_inside_target:
            continue
        
        # Calcular superposición entre bounding boxes
        overlap_x = max(0, min(target_x_max, other_x_max) - max(target_x_min, other_x_min))
        overlap_y = max(0, min(target_y_max, other_y_max) - max(target_y_min, other_y_min))
        overlap_area = overlap_x * overlap_y
        
        # Calcular área del vecino
        neighbor_area = (other_x_max - other_x_min) * (other_y_max - other_y_min)
        
        # 🆕 Solo proteger si el vecino está PRINCIPALMENTE FUERA del área objetivo
        # (más del X% del vecino debe estar fuera del área objetivo)
        overlap_ratio = overlap_area / neighbor_area if neighbor_area > 0 else 0
        
        # Si hay superposición o están muy cerca
        min_dist = min([
            dist_bottom if dist_bottom > 0 else float('inf'),
            dist_top if dist_top > 0 else float('inf'),
            dist_right if dist_right > 0 else float('inf'),
            dist_left if dist_left > 0 else float('inf')
        ])
        
        # 🆕 Solo proteger si:
        # 1. Está cerca (dentro del umbral) O hay superposición
        # 2. Y el vecino está principalmente FUERA del área objetivo (menos del umbral de superposición)
        is_nearby = min_dist <= NEARBY_DISTANCE_THRESHOLD or dist_bottom <= 0 or dist_top <= 0 or dist_right <= 0 or dist_left <= 0
        is_mostly_outside = overlap_ratio < EXCLUSION_OVERLAP_RATIO  # Menos del umbral de superposición
        
        if is_nearby and is_mostly_outside:
            # 🆕 ESTRATEGIA MEJORADA: Combinar polígono original + detección morfológica
            # Crear máscara base usando el polígono original del vecino (más robusto)
            neighbor_polygon_mask = np.zeros((h_img, w_img), dtype=np.uint8)
            cv2.fillPoly(neighbor_polygon_mask, [other_points], 255)
            
            # Expandir el polígono con padding para asegurar protección completa
            if EXCLUSION_PADDING > 0:
                kernel_expand = np.ones((EXCLUSION_PADDING * 2 + 1, EXCLUSION_PADDING * 2 + 1), np.uint8)
                neighbor_polygon_mask = cv2.dilate(neighbor_polygon_mask, kernel_expand, iterations=1)
            
            # 🆕 También detectar texto real con morfología para capturar partes que puedan estar fuera del polígono
            # Extraer ROI de la palabra vecina
            padding_detect = 5
            roi_x_min = max(0, other_x_min - padding_detect)
            roi_y_min = max(0, other_y_min - padding_detect)
            roi_x_max = min(w_img, other_x_max + padding_detect)
            roi_y_max = min(h_img, other_y_max + padding_detect)
            
            roi_neighbor = img_bgr[roi_y_min:roi_y_max, roi_x_min:roi_x_max]
            
            if roi_neighbor.size > 0:
                # Detectar texto real en la palabra vecina usando morfología
                roi_gray = cv2.cvtColor(roi_neighbor, cv2.COLOR_BGR2GRAY)
                
                # Calcular brillo del fondo
                border_pixels = np.concatenate([
                    roi_gray[0, :] if roi_gray.shape[0] > 0 else np.array([]),
                    roi_gray[-1, :] if roi_gray.shape[0] > 0 else np.array([]),
                    roi_gray[:, 0] if roi_gray.shape[1] > 0 else np.array([]),
                    roi_gray[:, -1] if roi_gray.shape[1] > 0 else np.array([])
                ])
                
                if len(border_pixels) > 0:
                    bg_brightness = np.median(border_pixels)
                    
                    # Detectar píxeles de texto vecino
                    if bg_brightness > 128:  # Fondo claro
                        _, text_mask_roi = cv2.threshold(
                            roi_gray, 
                            bg_brightness - EXCLUSION_BRIGHTNESS_THRESHOLD, 
                            255, 
                            cv2.THRESH_BINARY_INV
                        )
                    else:  # Fondo oscuro
                        _, text_mask_roi = cv2.threshold(
                            roi_gray, 
                            bg_brightness + EXCLUSION_BRIGHTNESS_THRESHOLD, 
                            255, 
                            cv2.THRESH_BINARY
                        )
                    
                    # Limpiar ruido
                    kernel_clean = np.ones((3, 3), np.uint8)
                    text_mask_roi = cv2.morphologyEx(text_mask_roi, cv2.MORPH_OPEN, kernel_clean, iterations=1)
                    text_mask_roi = cv2.morphologyEx(text_mask_roi, cv2.MORPH_CLOSE, kernel_clean, iterations=1)
                    
                    # Expandir la máscara morfológica
                    if EXCLUSION_PADDING > 0:
                        kernel_dilate = np.ones((EXCLUSION_PADDING * 2 + 1, EXCLUSION_PADDING * 2 + 1), np.uint8)
                        text_mask_roi = cv2.dilate(text_mask_roi, kernel_dilate, iterations=1)
                    
                    # Colocar la máscara morfológica en coordenadas de la imagen completa
                    text_mask_full = np.zeros((h_img, w_img), dtype=np.uint8)
                    text_mask_full[roi_y_min:roi_y_max, roi_x_min:roi_x_max] = text_mask_roi
                    
                    # 🆕 COMBINAR: Usar el polígono original O la detección morfológica (lo que sea mayor)
                    # Esto asegura que se proteja todo el texto, incluso si la detección morfológica falla
                    if EXCLUSION_USE_POLYGON:
                        # Combinar ambas máscaras (unión)
                        combined_mask = cv2.bitwise_or(neighbor_polygon_mask, text_mask_full)
                    else:
                        # Solo usar detección morfológica
                        combined_mask = text_mask_full
                    
                    # 🆕 Restar el área objetivo (solo proteger lo que está FUERA)
                    target_mask = np.zeros((h_img, w_img), dtype=np.uint8)
                    cv2.fillPoly(target_mask, [target_points], 255)
                    # Expandir un poco el área objetivo para asegurar que no se proteja lo que se debe borrar
                    if EXCLUSION_PADDING > 0:
                        kernel_target = np.ones((EXCLUSION_PADDING, EXCLUSION_PADDING), np.uint8)
                        target_mask = cv2.dilate(target_mask, kernel_target, iterations=1)
                    
                    # Restar el área objetivo de la máscara combinada
                    combined_mask = cv2.bitwise_and(combined_mask, cv2.bitwise_not(target_mask))
                    
                    # Verificar que quede área protegida
                    protected_area = np.sum(combined_mask > 0)
                    if protected_area >= EXCLUSION_MIN_AREA:
                        # Añadir a la máscara de exclusión
                        exclusion_mask = cv2.bitwise_or(exclusion_mask, combined_mask)
                        protected_count += 1
                else:
                    # Si no se puede detectar morfológicamente, usar solo el polígono
                    if EXCLUSION_USE_POLYGON:
                        # Restar el área objetivo
                        target_mask = np.zeros((h_img, w_img), dtype=np.uint8)
                        cv2.fillPoly(target_mask, [target_points], 255)
                        if EXCLUSION_PADDING > 0:
                            kernel_target = np.ones((EXCLUSION_PADDING, EXCLUSION_PADDING), np.uint8)
                            target_mask = cv2.dilate(target_mask, kernel_target, iterations=1)
                        
                        neighbor_polygon_mask = cv2.bitwise_and(neighbor_polygon_mask, cv2.bitwise_not(target_mask))
                        protected_area = np.sum(neighbor_polygon_mask > 0)
                        if protected_area >= EXCLUSION_MIN_AREA:
                            exclusion_mask = cv2.bitwise_or(exclusion_mask, neighbor_polygon_mask)
                            protected_count += 1
    
    if protected_count > 0:
        print(f"    🛡️ Protegido texto real de {protected_count} palabra(s) cercana(s) (solo partes fuera del área objetivo)")
    else:
        print(f"    ℹ️  No se encontraron palabras cercanas válidas (umbral: {NEARBY_DISTANCE_THRESHOLD}px, superposición max: {EXCLUSION_OVERLAP_RATIO*100:.0f}%)")
    
    return exclusion_mask

def create_mask_morphology(polygon, img_bgr, nearby_words=None):
    """Método 2: Detectar forma real del texto con morfología (MEJORADO - Solo texto, no fondo)."""
    points = np.array(polygon).astype(np.int32)
    
    # Obtener ROI
    x_coords = points[:, 0]
    y_coords = points[:, 1]
    x_min, x_max = int(np.min(x_coords)), int(np.max(x_coords))
    y_min, y_max = int(np.min(y_coords)), int(np.max(y_coords))
    
    # Añadir padding más conservador
    padding = 5  # Reducido de 10 a 5 para ser más preciso
    x_min_padded = max(0, x_min - padding)
    y_min_padded = max(0, y_min - padding)
    x_max_padded = min(w_img, x_max + padding)
    y_max_padded = min(h_img, y_max + padding)
    
    roi = img_bgr[y_min_padded:y_max_padded, x_min_padded:x_max_padded]
    
    if roi.size == 0:
        # Fallback: usar polígono original
        mask = np.zeros((h_img, w_img), dtype=np.uint8)
        cv2.fillPoly(mask, [points], 255)
        return mask, points
    
    # Convertir a escala de grises
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Calcular brillo del fondo (mediana de los bordes)
    border_pixels = np.concatenate([
        roi_gray[0, :],      # Superior
        roi_gray[-1, :],     # Inferior
        roi_gray[:, 0],      # Izquierda
        roi_gray[:, -1]      # Derecha
    ])
    bg_brightness = np.median(border_pixels)
    
    # Calcular brillo del centro (donde probablemente está el texto)
    center_y, center_x = roi_gray.shape[0] // 2, roi_gray.shape[1] // 2
    center_region = roi_gray[max(0, center_y-5):min(roi_gray.shape[0], center_y+5),
                            max(0, center_x-10):min(roi_gray.shape[1], center_x+10)]
    center_brightness = np.median(center_region) if center_region.size > 0 else bg_brightness
    
    # Detectar si el texto es más claro o más oscuro que el fondo
    text_is_darker = center_brightness < bg_brightness - 10
    text_is_brighter = center_brightness > bg_brightness + 10
    
    # Crear máscara binaria: detectar tanto texto oscuro como claro
    if text_is_darker or (bg_brightness > 128 and not text_is_brighter):  # Texto oscuro sobre fondo claro
        _, mask_roi = cv2.threshold(
            roi_gray, 
            bg_brightness - BRIGHTNESS_THRESHOLD, 
            255, 
            cv2.THRESH_BINARY_INV
        )
    elif text_is_brighter:  # Texto claro sobre fondo oscuro/dorado
        _, mask_roi = cv2.threshold(
            roi_gray, 
            bg_brightness + BRIGHTNESS_THRESHOLD, 
            255, 
            cv2.THRESH_BINARY
        )
    else:  # Fallback: usar método adaptativo
        mask_roi = cv2.adaptiveThreshold(
            roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
    
    # 🆕 RESTRICCIÓN AL POLÍGONO ORIGINAL: Crear máscara del polígono en el ROI (para limpieza de ruido)
    polygon_mask_roi_original = np.zeros((roi_gray.shape[0], roi_gray.shape[1]), dtype=np.uint8)
    # Ajustar coordenadas del polígono al sistema de coordenadas del ROI
    polygon_roi_original = points.copy()
    polygon_roi_original[:, 0] -= x_min_padded
    polygon_roi_original[:, 1] -= y_min_padded
    cv2.fillPoly(polygon_mask_roi_original, [polygon_roi_original.astype(np.int32)], 255)
    
    # 🆕 LIMPIAR RUIDO: Eliminar componentes pequeñas SOLO si están FUERA del polígono original
    # Esto preserva tildes, puntos y partes pequeñas de letras que están dentro del texto
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_roi, connectivity=8)
    min_area = (roi_gray.shape[0] * roi_gray.shape[1]) * 0.005  # Reducido a 0.5% para ser menos agresivo
    mask_roi_cleaned = np.zeros_like(mask_roi)
    for i in range(1, num_labels):  # Empezar en 1 para omitir el fondo
        component_area = stats[i, cv2.CC_STAT_AREA]
        # Obtener la máscara de esta componente
        component_mask = (labels == i).astype(np.uint8) * 255
        # Verificar si la componente está dentro del polígono original
        component_in_polygon = cv2.bitwise_and(component_mask, polygon_mask_roi_original)
        pixels_in_polygon = np.sum(component_in_polygon > 0)
        pixels_in_component = np.sum(component_mask > 0)
        # Si más del 50% de la componente está dentro del polígono, mantenerla (preserva tildes, etc.)
        # O si es grande, mantenerla siempre
        if pixels_in_polygon > 0 and (pixels_in_polygon / pixels_in_component > 0.5 or component_area >= min_area):
            mask_roi_cleaned[labels == i] = 255
        # Si está fuera del polígono y es pequeña, eliminarla (ruido)
        elif component_area >= min_area:
            mask_roi_cleaned[labels == i] = 255
    mask_roi = mask_roi_cleaned
    
    # 🆕 RESTRICCIÓN AL BOUNDING BOX COMPLETO: Usar el rectángulo completo que encierra el polígono
    # Esto asegura que TODO el texto dentro de la caja detectada se borre correctamente
    # Calcular bounding box del polígono original en coordenadas del ROI
    polygon_roi_x_coords = polygon_roi_original[:, 0]
    polygon_roi_y_coords = polygon_roi_original[:, 1]
    bbox_x_min = int(np.min(polygon_roi_x_coords))
    bbox_x_max = int(np.max(polygon_roi_x_coords))
    bbox_y_min = int(np.min(polygon_roi_y_coords))
    bbox_y_max = int(np.max(polygon_roi_y_coords))
    
    # Expandir el bounding box con un padding para asegurar cobertura completa
    bbox_expansion = max(POLYGON_EXPANSION_PX, 5)  # Mínimo 5px de expansión
    bbox_x_min = max(0, bbox_x_min - bbox_expansion)
    bbox_y_min = max(0, bbox_y_min - bbox_expansion)
    bbox_x_max = min(roi_gray.shape[1], bbox_x_max + bbox_expansion)
    bbox_y_max = min(roi_gray.shape[0], bbox_y_max + bbox_expansion)
    
    # Crear máscara del bounding box expandido (rectángulo completo)
    bbox_mask_roi = np.zeros((roi_gray.shape[0], roi_gray.shape[1]), dtype=np.uint8)
    bbox_mask_roi[bbox_y_min:bbox_y_max, bbox_x_min:bbox_x_max] = 255
    
    # 🆕 Aplicar restricción: solo mantener píxeles dentro del bounding box expandido
    # Esto asegura que TODO el texto dentro de la caja se borre, no solo el del polígono
    mask_roi = cv2.bitwise_and(mask_roi, bbox_mask_roi)
    
    # Operaciones morfológicas para limpiar y expandir
    if MORPH_DILATE_KERNEL > 0:
        kernel_dilate = np.ones((MORPH_DILATE_KERNEL, MORPH_DILATE_KERNEL), np.uint8)
        mask_roi = cv2.dilate(mask_roi, kernel_dilate, iterations=1)
        # 🆕 Re-aplicar restricción después de dilatar (con bounding box expandido)
        # Esto asegura que la dilatación no se salga del área de la caja detectada
        mask_roi = cv2.bitwise_and(mask_roi, bbox_mask_roi)
    
    if MORPH_ERODE_KERNEL > 0:
        kernel_erode = np.ones((MORPH_ERODE_KERNEL, MORPH_ERODE_KERNEL), np.uint8)
        mask_roi = cv2.erode(mask_roi, kernel_erode, iterations=1)
    
    # Colocar máscara ROI en la imagen completa
    mask_full = np.zeros((h_img, w_img), dtype=np.uint8)
    mask_full[y_min_padded:y_max_padded, x_min_padded:x_max_padded] = mask_roi
    
    # Debug: mostrar área detectada antes de exclusiones
    area_before = np.sum(mask_full > 0)
    
    # 🛡️ EXCLUIR TEXTO REAL DE PALABRAS CERCANAS (MEJORADO)
    if PROTECT_NEARBY_WORDS and nearby_words is not None and len(nearby_words) > 0:
        exclusion_mask = create_exclusion_mask(polygon, nearby_words, h_img, w_img, img_bgr)
        exclusion_area = np.sum(exclusion_mask > 0)
        # Restar las áreas protegidas (solo texto real) de la máscara de borrado
        mask_full = cv2.bitwise_and(mask_full, cv2.bitwise_not(exclusion_mask))
        area_after = np.sum(mask_full > 0)
        if exclusion_area > 0:
            print(f"      📊 Área antes: {area_before}px, Exclusiones: {exclusion_area}px, Área después: {area_after}px")
    else:
        print(f"      📊 Área detectada: {area_before}px")
    
    # Encontrar contorno para visualización
    contours, _ = cv2.findContours(mask_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # Obtener el contorno más grande
        largest_contour = max(contours, key=cv2.contourArea)
        # Ajustar coordenadas al sistema de la imagen completa
        largest_contour = largest_contour + np.array([x_min_padded, y_min_padded])
        vis_polygon = largest_contour.squeeze()
    else:
        vis_polygon = points
    
    return mask_full, vis_polygon

def create_mask_smart(polygon, img_bgr, nearby_words=None):
    """Método 3: Combinar morfología + reducción de caja."""
    # Primero reducir la caja
    shrunk_poly = create_mask_box_shrink(
        polygon, 
        BOX_SHRINK_TOP, BOX_SHRINK_BOTTOM, 
        BOX_SHRINK_LEFT, BOX_SHRINK_RIGHT
    )
    
    # Luego aplicar morfología dentro de esa caja reducida
    mask_morph, vis_poly = create_mask_morphology(shrunk_poly, img_bgr, nearby_words=nearby_words)
    
    return mask_morph, vis_poly

def sample_color_robust(polygon_points, img_bgr):
    """Muestreo robusto de color usando MORFOLOGÍA para detectar solo píxeles de texto."""
    polygon_points = np.array(polygon_points).astype(np.int32)
    
    # Obtener ROI del polígono
    x_coords = polygon_points[:, 0]
    y_coords = polygon_points[:, 1]
    x_min, x_max = int(np.min(x_coords)), int(np.max(x_coords))
    y_min, y_max = int(np.min(y_coords)), int(np.max(y_coords))
    
    # Añadir padding para asegurar que capturamos el texto completo
    padding = 5
    x_min = max(0, x_min - padding)
    y_min = max(0, y_min - padding)
    x_max = min(w_img, x_max + padding)
    y_max = min(h_img, y_max + padding)
    
    roi = img_bgr[y_min:y_max, x_min:x_max]
    
    if roi.size == 0:
        return (0, 0, 255), None, (x_min, y_min, x_max, y_max)
    
    # Convertir a escala de grises para detectar texto
    roi_gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Calcular brillo del fondo (mediana de los bordes)
    border_pixels = np.concatenate([
        roi_gray[0, :] if roi_gray.shape[0] > 0 else np.array([]),
        roi_gray[-1, :] if roi_gray.shape[0] > 0 else np.array([]),
        roi_gray[:, 0] if roi_gray.shape[1] > 0 else np.array([]),
        roi_gray[:, -1] if roi_gray.shape[1] > 0 else np.array([])
    ])
    
    if len(border_pixels) == 0:
        # Fallback: usar método anterior
        return sample_color_robust_fallback(polygon_points, img_bgr)
    
    bg_brightness = np.median(border_pixels)
    
    # Calcular brillo del centro (donde probablemente está el texto)
    center_y, center_x = roi_gray.shape[0] // 2, roi_gray.shape[1] // 2
    center_region = roi_gray[max(0, center_y-5):min(roi_gray.shape[0], center_y+5),
                            max(0, center_x-10):min(roi_gray.shape[1], center_x+10)]
    center_brightness = np.median(center_region) if center_region.size > 0 else bg_brightness
    
    # Detectar si el texto es más claro o más oscuro que el fondo
    text_is_darker = center_brightness < bg_brightness - 10
    text_is_brighter = center_brightness > bg_brightness + 10
    
    # Crear máscara binaria para detectar SOLO el texto
    if text_is_darker or (bg_brightness > 128 and not text_is_brighter):  # Texto oscuro sobre fondo claro
        _, text_mask = cv2.threshold(
            roi_gray, 
            bg_brightness - BRIGHTNESS_THRESHOLD, 
            255, 
            cv2.THRESH_BINARY_INV
        )
    elif text_is_brighter:  # Texto claro sobre fondo oscuro/dorado
        _, text_mask = cv2.threshold(
            roi_gray, 
            bg_brightness + BRIGHTNESS_THRESHOLD, 
            255, 
            cv2.THRESH_BINARY
        )
    else:  # Fallback: usar método adaptativo
        text_mask = cv2.adaptiveThreshold(
            roi_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 11, 2
        )
    
    # Limpiar ruido con morfología
    kernel_clean = np.ones((3, 3), np.uint8)
    text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_OPEN, kernel_clean, iterations=1)
    text_mask = cv2.morphologyEx(text_mask, cv2.MORPH_CLOSE, kernel_clean, iterations=1)
    
    # Verificar que hay suficiente texto detectado
    text_area = np.sum(text_mask > 0)
    if text_area < 10:  # Muy poco texto detectado, usar fallback
        return sample_color_robust_fallback(polygon_points, img_bgr)
    
    # 🎯 MUESTREAR COLOR SOLO DE LOS PÍXELES DE TEXTO (ignorar fondo)
    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    
    # Crear máscara booleana para píxeles de texto
    text_mask_bool = text_mask > 0
    
    # Extraer solo los píxeles que son texto
    text_pixels_rgb = roi_rgb[text_mask_bool]
    
    if len(text_pixels_rgb) < 5:
        # Si hay muy pocos píxeles, usar fallback
        return sample_color_robust_fallback(polygon_points, img_bgr)
    
    # Filtrar píxeles extremos si está habilitado
    if EXCLUDE_EXTREMES and len(text_pixels_rgb) > 20:
        brightness = np.mean(text_pixels_rgb, axis=1)
        p10 = np.percentile(brightness, 10)
        p90 = np.percentile(brightness, 90)
        mask_range = (brightness >= p10) & (brightness <= p90)
        text_pixels_rgb = text_pixels_rgb[mask_range]
    
    # Calcular color mediano del texto
    if len(text_pixels_rgb) > 0:
        color_rgb = np.median(text_pixels_rgb, axis=0).astype(np.uint8)
    else:
        # Fallback si no quedan píxeles
        return sample_color_robust_fallback(polygon_points, img_bgr)
    
    # Convertir a BGR para OpenCV
    text_color = (int(color_rgb[2]), int(color_rgb[1]), int(color_rgb[0]))
    
    print(f"      🎨 Color muestreado (solo texto): RGB({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}) - {text_area}px de texto detectado")
    
    return text_color, color_rgb, (x_min, y_min, x_max, y_max)

def sample_color_robust_fallback(polygon_points, img_bgr):
    """Método fallback para muestreo de color (método original)."""
    polygon_points = np.array(polygon_points).astype(np.int32)
    
    M = cv2.moments(polygon_points)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx = int(np.mean(polygon_points[:, 0]))
        cy = int(np.mean(polygon_points[:, 1]))
    
    x_coords = polygon_points[:, 0]
    y_coords = polygon_points[:, 1]
    width = np.max(x_coords) - np.min(x_coords)
    height = np.max(y_coords) - np.min(y_coords)
    
    sample_w = int(width * COLOR_SHRINK)
    sample_h = int(height * COLOR_SHRINK)
    
    x1 = max(0, cx - sample_w // 2)
    y1 = max(0, cy - sample_h // 2)
    x2 = min(w_img, cx + sample_w // 2)
    y2 = min(h_img, cy + sample_h // 2)
    
    roi = img_bgr[y1:y2, x1:x2]
    
    if roi.size == 0:
        return (0, 0, 255), None, (x1, y1, x2, y2)
    
    roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
    
    pixels_hsv = roi_hsv.reshape(-1, 3)
    pixels_rgb = roi_rgb.reshape(-1, 3)
    
    mask = (pixels_hsv[:, 1] >= MIN_SATURATION) & (pixels_hsv[:, 2] >= MIN_VALUE)
    
    if np.sum(mask) < 10:
        mask = (pixels_hsv[:, 1] >= MIN_SATURATION // 2) & (pixels_hsv[:, 2] >= MIN_VALUE // 2)
    
    valid_pixels = pixels_rgb[mask]
    
    if len(valid_pixels) < 5:
        valid_pixels = pixels_rgb
    
    if EXCLUDE_EXTREMES and len(valid_pixels) > 20:
        brightness = np.mean(valid_pixels, axis=1)
        p10 = np.percentile(brightness, 10)
        p90 = np.percentile(brightness, 90)
        mask_range = (brightness >= p10) & (brightness <= p90)
        valid_pixels = valid_pixels[mask_range]
    
    if len(valid_pixels) > 0:
        color_rgb = np.median(valid_pixels, axis=0).astype(np.uint8)
    else:
        color_rgb = np.median(pixels_rgb, axis=0).astype(np.uint8)
    
    text_color = (int(color_rgb[2]), int(color_rgb[1]), int(color_rgb[0]))
    
    return text_color, color_rgb, (x1, y1, x2, y2)

# ═══════════════════════════════════════════════════════════
# 📊 PROCESAMIENTO
# ═══════════════════════════════════════════════════════════

img_original_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
img_preview = np.copy(img_original_rgb)
mask = np.zeros(img_bgr.shape[:2], dtype=np.uint8)

target_polygons = {}
color_sample_polygons = {}
erase_polygons_vis = {}

print("\n📝 PROCESANDO OCR...")

if result:
    for page_result in result:
        rec_texts = page_result.get('rec_texts', [])
        rec_polygons = page_result.get('rec_polys', [])

        for text, polygon in zip(rec_texts, rec_polygons):
            points = np.array(polygon).astype(np.int32)
            
            if text in texts_to_erase:
                idx = texts_to_erase.index(text)
                cv2.polylines(img_preview, [points], True, (255, 50, 50), 1)
                target_polygons[text] = polygon
                print(f"  ✓ '{text}' (índice {idx})")
            
            elif text in texts_to_sample_color_from:
                color_sample_polygons[text] = polygon
                cv2.polylines(img_preview, [points], True, (50, 50, 255), 1)
                print(f"  ✓ '{text}' para color")

# Verificar
missing = []
for erase, sample in zip(texts_to_erase, texts_to_sample_color_from):
    if erase not in target_polygons:
        missing.append(f"'{erase}'")
    if sample not in color_sample_polygons:
        missing.append(f"'{sample}'")

if missing:
    print(f"\n❌ No encontradas: {', '.join(missing)}")
    exit()

# --- Crear Máscaras de Borrado ---
print(f"\n🎯 CREANDO MÁSCARAS ({ERASE_STRATEGY})...")

# 🆕 Recopilar todas las palabras detectadas (para detección de cercanía)
all_detected_polygons = []
if result:
    for page_result in result:
        rec_polygons = page_result.get('rec_polys', [])
        all_detected_polygons.extend(rec_polygons)

for i, text_to_erase in enumerate(texts_to_erase):
    # Crear lista de polígonos vecinos (todos excepto el actual)
    other_polygons = [p for p in all_detected_polygons 
                      if not np.array_equal(p, target_polygons[text_to_erase])]
    
    if ERASE_STRATEGY == "box_shrink":
        # LÓGICA ORIGINAL SIMPLE
        erase_poly = create_mask_box_shrink(
            target_polygons[text_to_erase],
            BOX_SHRINK_TOP, BOX_SHRINK_BOTTOM,
            BOX_SHRINK_LEFT, BOX_SHRINK_RIGHT
        )
        mask_temp = np.zeros((h_img, w_img), dtype=np.uint8)
        cv2.fillPoly(mask_temp, [erase_poly], 255)
        
        # 🛡️ EXCLUIR TEXTO REAL DE PALABRAS CERCANAS (MEJORADO)
        if PROTECT_NEARBY_WORDS and len(other_polygons) > 0:
            exclusion_mask = create_exclusion_mask(
                target_polygons[text_to_erase], other_polygons, h_img, w_img, img_bgr
            )
            # Restar las áreas protegidas (solo texto real) de la máscara de borrado
            mask_temp = cv2.bitwise_and(mask_temp, cv2.bitwise_not(exclusion_mask))
        
        mask = cv2.bitwise_or(mask, mask_temp)
        erase_polygons_vis[text_to_erase] = erase_poly
        
    elif ERASE_STRATEGY == "morphology":
        # 🆕 Pasar información de palabras cercanas
        mask_temp, erase_poly = create_mask_morphology(
            target_polygons[text_to_erase], img_bgr, nearby_words=other_polygons
        )
        mask = cv2.bitwise_or(mask, mask_temp)
        erase_polygons_vis[text_to_erase] = erase_poly
        
    elif ERASE_STRATEGY == "smart_mask":
        mask_temp, erase_poly = create_mask_smart(
            target_polygons[text_to_erase], img_bgr, nearby_words=other_polygons
        )
        mask = cv2.bitwise_or(mask, mask_temp)
        erase_polygons_vis[text_to_erase] = erase_poly
    
    # Visualizar
    if erase_poly.ndim == 2:
        cv2.polylines(img_preview, [erase_poly.astype(np.int32)], True, (0, 255, 0), 2)
    
    print(f"  {i+1}. '{text_to_erase}' procesada")

# 🐛 DEBUG: Guardar máscaras de exclusión si está activado
debug_exclusion_masks = {}
if DEBUG_SHOW_MASKS:
    # Recrear máscaras para debug
    for text_to_erase in texts_to_erase:
        other_polygons = [p for p in all_detected_polygons 
                          if not np.array_equal(p, target_polygons[text_to_erase])]
        if PROTECT_NEARBY_WORDS and len(other_polygons) > 0:
            excl_mask = create_exclusion_mask(
                target_polygons[text_to_erase], other_polygons, h_img, w_img, img_bgr
            )
            debug_exclusion_masks[text_to_erase] = excl_mask

# 🐛 DEBUG: Mostrar máscaras si está activado
if DEBUG_SHOW_MASKS:
    fig = plt.figure(figsize=(20, 13))
    
    # 1. Original con polígonos detectados
    plt.subplot(3, 3, 1)
    plt.imshow(img_original_rgb)
    for text in texts_to_erase:
        poly = np.array(target_polygons[text]).astype(np.int32)
        cv2.polylines(img_original_rgb, [poly], True, (255, 0, 0), 2)
    plt.title('1. OCR - Polígonos Originales (Rojo)', fontsize=10, fontweight='bold')
    plt.axis('off')
    
    # 2. Polígonos de borrado
    img_erase = img_original_rgb.copy()
    for text in texts_to_erase:
        orig_poly = np.array(target_polygons[text]).astype(np.int32)
        cv2.polylines(img_erase, [orig_poly], True, (255, 0, 0), 2)
        if text in erase_polygons_vis:
            erase_poly = np.array(erase_polygons_vis[text]).astype(np.int32)
            cv2.polylines(img_erase, [erase_poly], True, (0, 255, 0), 2)
    plt.subplot(3, 3, 2)
    plt.imshow(img_erase)
    plt.title('2. Polígonos (Rojo=OCR, Verde=Borrado)', fontsize=10, fontweight='bold')
    plt.axis('off')
    
    # 3. Máscara de borrado (blanco y negro)
    plt.subplot(3, 3, 3)
    plt.imshow(mask, cmap='gray')
    plt.title('3. Máscara de Borrado (Blanco=Se Borrará)', fontsize=10, fontweight='bold')
    plt.axis('off')
    
    # 4. Máscaras de exclusión (texto vecino protegido)
    plt.subplot(3, 3, 4)
    combined_exclusion = np.zeros((h_img, w_img), dtype=np.uint8)
    for text, excl_mask in debug_exclusion_masks.items():
        combined_exclusion = cv2.bitwise_or(combined_exclusion, excl_mask)
    plt.imshow(combined_exclusion, cmap='hot')
    plt.title('4. Texto Vecino Protegido (Blanco=Protegido)', fontsize=10, fontweight='bold')
    plt.axis('off')
    
    # 5. Máscara final (borrado - exclusión)
    plt.subplot(3, 3, 5)
    final_mask = mask.copy()
    for excl_mask in debug_exclusion_masks.values():
        final_mask = cv2.bitwise_and(final_mask, cv2.bitwise_not(excl_mask))
    plt.imshow(final_mask, cmap='gray')
    plt.title('5. Máscara FINAL (después de exclusiones)', fontsize=10, fontweight='bold')
    plt.axis('off')
    
    # 6. Overlay de borrado (rojo semi-transparente)
    plt.subplot(3, 3, 6)
    mask_overlay = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB).copy()
    mask_overlay[final_mask > 0] = [255, 0, 0]  # Rojo donde se borrará
    img_overlay = cv2.addWeighted(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB), 0.6, mask_overlay, 0.4, 0)
    plt.imshow(img_overlay)
    plt.title('6. Preview Borrado (Rojo Semi-transparente)', fontsize=10, fontweight='bold')
    plt.axis('off')
    
    # 7. Original completo
    plt.subplot(3, 3, 7)
    plt.imshow(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    plt.title('7. Imagen Original', fontsize=10, fontweight='bold')
    plt.axis('off')
    
    # 8. Comparación lado a lado
    plt.subplot(3, 3, 8)
    comparison = np.hstack([
        cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB),
        cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    ])
    comparison[0:h_img, 0:w_img][mask > 0] = [255, 100, 100]  # Izquierda: máscara original
    comparison[0:h_img, w_img:][final_mask > 0] = [255, 0, 0]  # Derecha: máscara final
    plt.imshow(comparison)
    plt.title('8. Comparación (Izq: Original, Der: Con Exclusiones)', fontsize=10, fontweight='bold')
    plt.axis('off')
    
    # 9. Estadísticas
    plt.subplot(3, 3, 9)
    plt.axis('off')
    stats_text = f"📊 ESTADÍSTICAS\n\n"
    stats_text += f"Palabras a borrar: {len(texts_to_erase)}\n"
    for i, text in enumerate(texts_to_erase):
        poly = target_polygons[text]
        points = np.array(poly)
        width = np.max(points[:, 0]) - np.min(points[:, 0])
        height = np.max(points[:, 1]) - np.min(points[:, 1])
        stats_text += f"\n'{text}':\n"
        stats_text += f"  Tamaño: {width:.0f}x{height:.0f}px\n"
    
    mask_area = np.sum(mask > 0)
    final_mask_calc = mask.copy()
    for excl_mask in debug_exclusion_masks.values():
        final_mask_calc = cv2.bitwise_and(final_mask_calc, cv2.bitwise_not(excl_mask))
    final_mask_area = np.sum(final_mask_calc > 0)
    exclusion_area = mask_area - final_mask_area
    img_area = mask.size
    
    stats_text += f"\n📏 ÁREAS:\n"
    stats_text += f"Máscara original: {mask_area:,} px\n"
    stats_text += f"Exclusiones: {exclusion_area:,} px\n"
    stats_text += f"Máscara final: {final_mask_area:,} px\n"
    stats_text += f"({final_mask_area/img_area*100:.2f}% de la imagen)\n"
    
    stats_text += f"\n🛡️ PROTECCIÓN:\n"
    if len(debug_exclusion_masks) > 0:
        stats_text += f"Palabras protegidas: {len(debug_exclusion_masks)}\n"
        stats_text += f"Reducción: {exclusion_area/mask_area*100:.1f}%\n"
    else:
        stats_text += "Sin palabras protegidas\n"
    
    plt.text(0.1, 0.5, stats_text, fontsize=9, family='monospace', 
             verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    plt.title('9. Información Detallada', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.show()
    
    print("\n" + "═" * 70)
    print("🐛 DEBUG: Máscaras mostradas. Revisa las ventanas de visualización.")
    print("═" * 70 + "\n")

# --- Muestrear Colores ---
print(f"\n🎨 MUESTREANDO COLORES...")
text_colors = {}

for i, (text_to_erase, text_to_sample) in enumerate(zip(texts_to_erase, texts_to_sample_color_from)):
    color_poly = color_sample_polygons[text_to_sample]
    text_color, color_rgb, sample_area = sample_color_robust(color_poly, img_bgr)
    text_colors[text_to_erase] = text_color
    
    x1, y1, x2, y2 = sample_area
    cv2.rectangle(img_preview, (x1, y1), (x2, y2), (255, 255, 0), 2)
    
    # Dibujar cuadrado de color
    size = 25
    x_color = x2 + 5
    y_color = y1
    if x_color + size < w_img:
        cv2.rectangle(img_preview, (x_color, y_color), (x_color + size, y_color + size), text_color, -1)
        cv2.rectangle(img_preview, (x_color, y_color), (x_color + size, y_color + size), (255, 255, 255), 1)
    
    if color_rgb is not None:
        print(f"  {i+1}. '{text_to_erase}' → RGB({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]})")

# --- Inpainting ---
print(f"\n🔧 INPAINTING...")
img_inpainted_bgr = cv2.inpaint(img_bgr, mask, INPAINT_RADIUS, INPAINT_METHOD)

# --- Reemplazar ---
print(f"\n✏️  REEMPLAZANDO...")

try:
    font = ImageFont.truetype(font_path, size=font_size)
except IOError:
    print(f"❌ Fuente no encontrada")
    exit()

img_final_bgr = np.copy(img_inpainted_bgr)

for i, (text_to_erase, text_to_add, offset_x, offset_y) in enumerate(
    zip(texts_to_erase, texts_to_add, offsets_x, offsets_y)
):
    print(f"  {i+1}. '{text_to_erase}' → '{text_to_add}'...", end=" ")
    
    target_polygon = target_polygons[text_to_erase]
    text_color = text_colors[text_to_erase]
    
    # Calcular el bounding box del texto
    # getbbox retorna (left, top, right, bottom) donde:
    # - left: generalmente 0 o pequeño
    # - top: negativo (representa el ascenso, espacio arriba de la línea base)
    # - right: ancho del texto
    # - bottom: positivo (representa el descenso, espacio abajo de la línea base)
    text_bbox = font.getbbox(text_to_add)
    text_w = text_bbox[2] - text_bbox[0]  # Ancho del texto
    text_h = text_bbox[3] - text_bbox[1]   # Alto total (ascenso + descenso)
    text_ascent = -text_bbox[1]            # Ascenso (espacio arriba de la línea base, positivo)
    text_descent = text_bbox[3]            # Descenso (espacio abajo de la línea base, positivo)
    
    padding = 20
    
    # Crear imagen temporal con suficiente espacio
    src_w = text_w + 2 * padding
    src_h = text_h + 2 * padding
    
    # En PIL, cuando dibujamos texto en (x, y), 'y' es la coordenada Y de la línea base
    # Necesitamos posicionar el texto de manera que quede centrado verticalmente
    # en el área disponible, considerando el ascenso
    text_x = padding
    # La línea base debe estar en una posición tal que el texto quede bien centrado
    # Si queremos que el texto empiece en Y=padding (considerando el ascenso),
    # entonces la línea base debe estar en padding + text_ascent
    text_y = padding + text_ascent  # Línea base del texto
    
    img_src_text_pil = Image.new('RGBA', (src_w, src_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img_src_text_pil)
    draw.text((text_x, text_y), text_to_add, font=font,
              fill=(text_color[2], text_color[1], text_color[0], 255))
    
    img_src_text_bgra = cv2.cvtColor(np.array(img_src_text_pil), cv2.COLOR_RGBA2BGRA)
    
    # src_polygon: rectángulo que encierra el texto dibujado
    # El texto se dibuja con la línea base en text_y, entonces:
    # - Y superior = text_y - text_ascent (donde empieza el texto visualmente)
    # - Y inferior = text_y + text_descent (donde termina el texto visualmente)
    text_real_x = text_x
    text_real_y = text_y - text_ascent  # Y superior del texto (línea base - ascenso)
    text_real_w = text_w
    text_real_h = text_ascent + text_descent  # Altura total = ascenso + descenso
    
    # src_polygon: rectángulo que encierra exactamente el texto dibujado
    src_polygon = np.float32([
        [text_real_x, text_real_y],                           # Esquina superior izquierda
        [text_real_x + text_real_w, text_real_y],              # Esquina superior derecha
        [text_real_x + text_real_w, text_real_y + text_real_h], # Esquina inferior derecha
        [text_real_x, text_real_y + text_real_h]               # Esquina inferior izquierda
    ])
    
    # dst_polygon: polígono del texto original (sin offsets por defecto)
    # Solo aplicar offsets si son diferentes de 0
    if offset_x != 0 or offset_y != 0:
        adjusted_polygon = [[p[0] + offset_x, p[1] + offset_y] for p in target_polygon]
        dst_polygon = np.float32(adjusted_polygon)
    else:
        dst_polygon = np.float32(target_polygon)
    
    M = cv2.getPerspectiveTransform(src_polygon, dst_polygon)
    img_warped_bgra = cv2.warpPerspective(img_src_text_bgra, M, (w_img, h_img))
    
    alpha_channel = img_warped_bgra[:, :, 3] / 255.0
    inv_alpha = 1.0 - alpha_channel
    
    for c in range(3):
        img_final_bgr[:, :, c] = (inv_alpha * img_final_bgr[:, :, c] +
                                   alpha_channel * img_warped_bgra[:, :, c])
    
    print("✓")

# --- Visualización ---
print(f"\n📊 MOSTRANDO...\n")

plt.figure(figsize=(28, 7))

plt.subplot(1, 4, 1)
plt.imshow(img_original_rgb)
plt.title('1. Original', fontsize=14, fontweight='bold')
plt.axis('off')

plt.subplot(1, 4, 2)
plt.imshow(img_preview)
plt.title(f'2. Análisis\n(Rojo=OCR, Verde=Máscara {ERASE_STRATEGY})', fontsize=11)
plt.axis('off')

plt.subplot(1, 4, 3)
plt.imshow(cv2.cvtColor(img_inpainted_bgr, cv2.COLOR_BGR2RGB))
plt.title(f'3. Borrado', fontsize=12)
plt.axis('off')

plt.subplot(1, 4, 4)
plt.imshow(cv2.cvtColor(img_final_bgr, cv2.COLOR_BGR2RGB))
summary = ", ".join([f"'{e}'→'{a}'" for e, a in zip(texts_to_erase, texts_to_add)])
plt.title(f'4. Resultado\n{summary}', fontsize=12, fontweight='bold')
plt.axis('off')

plt.tight_layout()
plt.show()

print("═" * 70)
print("✅ COMPLETADO")
print("═" * 70)
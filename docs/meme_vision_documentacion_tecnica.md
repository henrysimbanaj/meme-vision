# Meme Vision — Documento técnico

## 1. Objetivo del proyecto

Construir una aplicación de visión artificial para una casa abierta universitaria en la que una persona se coloque frente a una cámara e imite uno de varios memes previamente seleccionados.

El sistema debe analizar:

- Posición del cuerpo.
- Posición de las manos.
- Expresiones faciales.
- Relación espacial entre manos, rostro y cuerpo.

A partir de estas características, el sistema debe identificar qué meme está intentando imitar la persona y mostrar el resultado en pantalla junto con un nivel de confianza.

El proyecto está orientado a estudiantes que están por ingresar a la universidad, por lo que además de funcionar correctamente debe ser visual, interactivo y fácil de explicar.

---

# 2. Alcance recomendado

La primera versión debe reconocer únicamente un conjunto cerrado de memes seleccionados por el equipo.

No se busca que el sistema reconozca cualquier meme existente.

Alcance inicial recomendado:

- 6 a 10 memes.
- Principalmente poses estáticas.
- Una sola persona frente a la cámara.
- Cámara fija.
- Reconocimiento en tiempo real.
- Tiempo de estabilización de aproximadamente 0.5 a 1 segundo.
- Mostrar la predicción final y su confianza.

Una versión posterior podría incluir memes que dependan de movimientos o secuencias temporales.

---

# 3. Arquitectura general

```text
Cámara
  ↓
OpenCV
  ↓
MediaPipe
  ├── Pose
  ├── Hands
  └── Face
  ↓
Landmarks
  ↓
Normalización
  ↓
Extracción de características
  ↓
Clasificador
  ↓
Suavizado temporal
  ↓
Interfaz gráfica
  ↓
Resultado
```

---

# 4. Tecnologías recomendadas

## Lenguaje

Python 3.

## Librerías principales

### OpenCV

Uso:

- Acceso a la cámara.
- Captura de frames.
- Dibujo.
- Visualización en pantalla.
- Manipulación básica de imágenes.

Paquete:

```bash
opencv-python
```

### MediaPipe

Uso:

- Detección de cuerpo.
- Detección de manos.
- Detección de rostro.
- Extracción de landmarks.
- Posibles blendshapes faciales.

Paquete:

```bash
mediapipe
```

### NumPy

Uso:

- Vectores.
- Normalización.
- Operaciones matemáticas.
- Cálculo de distancias y ángulos.

### pandas

Uso:

- Guardar y leer datasets.
- Trabajar con CSV.
- Analizar datos recogidos.

### scikit-learn

Uso:

- Entrenamiento del clasificador.
- Random Forest.
- k-NN.
- SVM.
- Métricas.
- División train/test.

### joblib

Uso:

- Guardar modelos entrenados.
- Cargar modelos durante la ejecución.

---

# 5. Hardware disponible

El proyecto debe poder ejecutarse en:

## Equipo 1

Laptop con Kubuntu.

## Equipo 2

MacBook Pro M2 base.

El proyecto debe evitar dependencias específicas de un sistema operativo.

Todo el código debe poder ejecutarse en ambas máquinas.

---

# 6. Estructura recomendada del repositorio

```text
meme-vision/
│
├── README.md
├── pyproject.toml
├── .gitignore
│
├── src/
│   └── memevision/
│       ├── camera.py
│       ├── landmarks.py
│       ├── features.py
│       ├── classifier.py
│       ├── smoothing.py
│       ├── ui.py
│       └── config.py
│
├── scripts/
│   ├── collect.py
│   ├── train.py
│   ├── evaluate.py
│   └── demo.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── manifest.csv
│
├── models/
│   └── meme_classifier.pkl
│
├── tests/
│   ├── test_features.py
│   ├── test_classifier.py
│   └── test_normalization.py
│
└── docs/
    ├── architecture.md
    ├── memes.md
    ├── dataset.md
    └── collaboration.md
```

---

# 7. Flujo de ejecución

## Paso 1 — Capturar un frame

La cámara entrega una imagen mediante OpenCV.

Ejemplo conceptual:

```python
frame = camera.get_frame()
```

La función debe retornar un `numpy.ndarray`.

---

# 8. Extracción de landmarks

En lugar de clasificar directamente la imagen completa, el sistema debe convertir la imagen a coordenadas.

Ejemplo conceptual:

```text
imagen
 ↓
MediaPipe
 ↓
coordenadas del cuerpo
coordenadas de manos
coordenadas de rostro
```

---

# 9. Landmarks corporales

MediaPipe Pose puede entregar puntos representativos del cuerpo.

Algunos puntos especialmente útiles:

- Nariz.
- Ojos.
- Orejas.
- Hombros.
- Codos.
- Muñecas.
- Caderas.
- Rodillas.
- Tobillos.

Para muchos memes probablemente los puntos más importantes sean:

```text
hombros
codos
muñecas
nariz
caderas
```

---

# 10. Landmarks de las manos

Cada mano puede representarse mediante una serie de puntos.

Esto permite detectar:

- Mano abierta.
- Mano cerrada.
- Dirección aproximada.
- Mano cerca del rostro.
- Mano sobre la cabeza.
- Mano cerca del pecho.
- Distancia entre ambas manos.

---

# 11. Información facial

El reconocimiento facial no debe intentar identificar a la persona.

El objetivo es analizar geometría y expresión.

Características útiles:

- Boca abierta.
- Sonrisa.
- Ojos cerrados.
- Cejas elevadas.
- Dirección aproximada del rostro.
- Inclinación de la cabeza.

Si se utilizan blendshapes faciales, estos pueden complementar los landmarks.

---

# 12. Representación de un frame

Un frame puede convertirse conceptualmente en algo parecido a:

```text
pose:
    hombro_izq = (x, y)
    hombro_der = (x, y)
    codo_izq = (x, y)
    codo_der = (x, y)
    ...

hands:
    mano_izq = [...]
    mano_der = [...]

face:
    sonrisa = 0.72
    boca_abierta = 0.14
    ceja_izq = 0.61
    ...
```

---

# 13. Normalización

Este paso es crítico.

No deben entrenar directamente con coordenadas absolutas.

Una persona puede estar:

- Más cerca.
- Más lejos.
- Más arriba.
- Más abajo.
- Ser más alta.
- Ser más baja.

Por tanto, hay que normalizar.

---

# 14. Centro de referencia

Una buena referencia es el punto medio entre ambos hombros.

```text
centro_x = (hombro_izq_x + hombro_der_x) / 2
centro_y = (hombro_izq_y + hombro_der_y) / 2
```

Luego se trasladan todos los puntos:

```text
x' = x - centro_x
y' = y - centro_y
```

---

# 15. Normalización por escala

Una referencia adecuada es la distancia entre hombros.

```text
escala = distancia(hombro_izq, hombro_der)
```

Después:

```text
x_normalizado = x' / escala
y_normalizado = y' / escala
```

Así el modelo aprende posiciones relativas en lugar de posiciones absolutas.

---

# 16. Características derivadas

Además de coordenadas, conviene calcular variables de mayor nivel.

Ejemplos:

## Ángulos

- Ángulo del codo izquierdo.
- Ángulo del codo derecho.
- Ángulo del hombro.
- Inclinación del torso.
- Inclinación de la cabeza.

## Distancias

- Mano a nariz.
- Mano a boca.
- Mano a hombro.
- Mano izquierda a mano derecha.
- Muñeca a cadera.
- Codo a hombro.

## Relaciones binarias

```text
mano_izq_sobre_cabeza
mano_der_cerca_cara
ambas_manos_juntas
brazos_cruzados
mano_en_pecho
```

Estas características pueden mejorar mucho la estabilidad del clasificador.

---

# 17. Vector de características

El resultado final de la extracción debe ser un vector numérico.

Ejemplo:

```text
[
  pose_x_0,
  pose_y_0,
  pose_x_1,
  pose_y_1,
  ...
  elbow_left_angle,
  elbow_right_angle,
  left_hand_face_distance,
  mouth_open,
  smile,
  ...
]
```

Todos los frames deben producir vectores del mismo tamaño.

---

# 18. Recolector de datos

Debe existir un script específico para crear el dataset.

Ejemplo:

```bash
python scripts/collect.py drake
```

Flujo:

```text
iniciar cámara
 ↓
mostrar clase actual
 ↓
esperar preparación
 ↓
capturar landmarks
 ↓
normalizar
 ↓
guardar vector
 ↓
repetir
```

---

# 19. Dataset

Formato recomendado:

CSV o Parquet.

Ejemplo:

```text
class,person_id,pose_0_x,pose_0_y,...,smile,mouth_open
drake,P01,0.42,-0.17,...,0.21,0.68
drake,P01,0.44,-0.16,...,0.24,0.71
confused,P02,-0.12,0.27,...,0.03,0.11
```

---

# 20. Cantidad inicial de datos

Para una primera prueba:

- 3 memes.
- 3 a 5 personas.
- 100 a 300 muestras por persona y meme.

Ejemplo:

```text
3 memes
× 4 personas
× 200 muestras
=
2400 ejemplos
```

No es necesario empezar con miles de fotografías manualmente etiquetadas porque cada frame produce directamente un vector de landmarks.

---

# 21. Variabilidad del dataset

Cada persona debe introducir pequeñas variaciones:

- Más cerca.
- Más lejos.
- Girada algunos grados.
- Brazos ligeramente distintos.
- Diferentes expresiones.
- Diferente iluminación.
- Diferentes prendas.

Esto evita que el modelo memorice una única pose exacta.

---

# 22. Separación train/test

Es preferible separar por persona.

Ejemplo:

```text
Train:
P01
P02
P03

Test:
P04
```

Esto es mejor que mezclar frames de una misma persona entre train y test.

De esta forma se mide si el sistema funciona con alguien que nunca apareció durante el entrenamiento.

---

# 23. Modelo inicial recomendado

Random Forest.

Ventajas:

- Fácil de entrenar.
- Funciona bien con datos tabulares.
- Poco ajuste.
- No necesita GPU.
- Fácil de explicar.
- Puede entregar probabilidades aproximadas.
- Entrena rápidamente.

Ejemplo conceptual:

```python
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier(n_estimators=300, random_state=42)

model.fit(X_train, y_train)
```

---

# 24. Otros modelos para comparar

Una vez funcionando Random Forest:

- k-Nearest Neighbors.
- SVM.
- Logistic Regression.
- MLPClassifier.

Esto incluso puede convertirse en parte de la explicación científica del proyecto:

> ¿Qué algoritmo reconoce mejor las poses?

---

# 25. Evaluación

Métricas recomendadas:

- Accuracy.
- Precision.
- Recall.
- F1-score.
- Matriz de confusión.

La matriz de confusión es especialmente útil.

Ejemplo:

```text
              Predicción
            A    B    C

Real A      45    2    1
Real B       4   40    3
Real C       0    5   44
```

Así se puede descubrir qué memes son demasiado parecidos.

---

# 26. Guardar el modelo

Después del entrenamiento:

```python
import joblib

joblib.dump(model, "models/meme_classifier.pkl")
```

Para cargar:

```python
model = joblib.load("models/meme_classifier.pkl")
```

---

# 27. Inferencia

Durante la demostración:

```text
frame
 ↓
landmarks
 ↓
features
 ↓
classifier.predict_proba()
 ↓
probabilidades
```

Ejemplo:

```text
Drake        0.87
Confused     0.08
Surprised    0.05
```

---

# 28. Suavizado temporal

No debe usarse una sola predicción.

Las predicciones pueden cambiar entre frames.

Debe existir un buffer:

```text
Frame 1 → Drake
Frame 2 → Drake
Frame 3 → Confused
Frame 4 → Drake
Frame 5 → Drake
```

Resultado estable:

```text
Drake
```

---

# 29. Estrategias de suavizado

## Mayoría

Guardar las últimas N predicciones.

Ejemplo:

```text
N = 15
```

Seleccionar la clase más frecuente.

## Promedio de probabilidades

Guardar las probabilidades de varios frames y promediarlas.

Esta opción suele ser mejor.

---

# 30. Umbral de confianza

No es necesario forzar siempre una clasificación.

Ejemplo:

```text
if confidence < 0.65:
    resultado = "No estoy seguro"
```

Esto evita respuestas absurdas.

---

# 31. Estado de preparación

Puede ser útil tener un estado:

```text
BUSCANDO_PERSONA
PERSONA_DETECTADA
ANALIZANDO
RESULTADO
```

Ejemplo:

```text
Colócate frente a la cámara

↓

¡Persona detectada!

↓

3
2
1

↓

Analizando...

↓

¡Estás imitando a Drake!
92%
```

---

# 32. Interfaz

Para la primera versión pueden usar OpenCV directamente.

Elementos:

- Imagen de cámara.
- Esqueleto superpuesto.
- Nombre del meme objetivo.
- Predicción actual.
- Confianza.
- Contador.
- Resultado.
- Imagen del meme original.

---

# 33. Modo de juego recomendado

Una experiencia atractiva para feria:

```text
1. El sistema selecciona un meme.

2. La persona observa el meme.

3. Tiene algunos segundos para imitarlo.

4. El sistema analiza la pose.

5. Muestra qué meme cree que está imitando.

6. Muestra porcentaje de confianza.

7. Se inicia una nueva ronda.
```

También pueden hacer modo libre:

```text
"Imita cualquiera de estos memes"
```

y el sistema intenta descubrir cuál es.

---

# 34. Modos posibles

## Modo desafío

El sistema indica qué meme imitar.

## Modo adivinanza

La persona elige uno sin decirlo.

El sistema intenta reconocerlo.

## Modo demostración

Se muestran landmarks, ángulos y probabilidades en tiempo real.

Este último es excelente para explicar el proyecto.

---

# 35. Diseño por módulos

El programa debe estar dividido.

## camera.py

Responsabilidad:

```python
get_frame()
```

No debe contener clasificación.

---

## landmarks.py

Responsabilidad:

```python
extract(frame)
```

Salida conceptual:

```python
LandmarkResult
```

---

## features.py

Responsabilidad:

```python
transform(landmarks)
```

Debe encargarse de:

- Normalización.
- Ángulos.
- Distancias.
- Vector final.

---

## classifier.py

Responsabilidad:

```python
predict(features)
```

Salida conceptual:

```python
Prediction(meme="drake", confidence=0.91)
```

---

## smoothing.py

Responsabilidad:

- Mantener historial.
- Suavizar probabilidades.
- Confirmar predicción estable.

---

## ui.py

Responsabilidad:

- Dibujar cámara.
- Dibujar landmarks.
- Mostrar texto.
- Mostrar meme.
- Mostrar porcentaje.

No debe entrenar modelos.

---

# 36. Interfaces entre módulos

Ejemplo:

```python
frame = camera.get_frame()

landmark_result = landmark_detector.extract(frame)

features = feature_extractor.transform(landmark_result)

prediction = classifier.predict(features)

stable_prediction = smoother.update(prediction)

ui.render(frame, stable_prediction)
```

Esta separación permite que diferentes personas trabajen simultáneamente.

---

# 37. Clases de datos recomendadas

Puede utilizarse `dataclass`.

Ejemplo:

```python
from dataclasses import dataclass


@dataclass
class Prediction:
    meme: str
    confidence: float
```

Otro ejemplo:

```python
@dataclass
class LandmarkResult:
    pose: object
    left_hand: object
    right_hand: object
    face: object
```

---

# 38. Configuración

Los parámetros importantes deben estar separados del código.

Por ejemplo:

```python
CONFIDENCE_THRESHOLD = 0.70
SMOOTHING_WINDOW = 15
CAMERA_INDEX = 0
```

Luego pueden migrarse a YAML o TOML.

---

# 39. Compatibilidad Kubuntu/macOS

Evitar:

- Paths absolutos.
- Dependencias exclusivas de Linux.
- Dependencias exclusivas de macOS.
- Configuración específica de una sola webcam.

Usar:

```python
from pathlib import Path
```

en vez de concatenar rutas manualmente.

---

# 40. Gestión de dependencias

Todo el proyecto debe tener dependencias reproducibles.

Una opción simple es `pyproject.toml`.

Nunca depender de instrucciones como:

```text
instala lo que te falte
```

El objetivo debe ser:

```bash
git clone ...
cd meme-vision
...
python scripts/demo.py
```

y que funcione en ambas computadoras.

---

# 41. Datos que NO deben ir directamente a Git

Evitar incluir:

- Videos pesados.
- Miles de imágenes.
- Archivos temporales.
- Entornos virtuales.

`.gitignore` debe incluir como mínimo:

```text
.venv/
__pycache__/
*.pyc
.DS_Store
.idea/
.vscode/
```

Los videos crudos pueden mantenerse en almacenamiento compartido externo.

---

# 42. Datos que sí pueden ir a Git

- Código.
- Configuración.
- Documentación.
- CSV de landmarks si no es demasiado grande.
- Modelos pequeños.
- Manifiestos.
- Tests.

---

# 43. Manifest del dataset

Ejemplo:

```text
id,class,person,file
001,drake,P01,drake/P01_001.mp4
002,drake,P02,drake/P02_001.mp4
003,confused,P01,confused/P01_001.mp4
```

Permite saber de dónde provino cada muestra.

---

# 44. Privacidad

Como el objetivo no es reconocer personas, lo ideal es que el sistema trabaje principalmente con landmarks.

Si se guardan videos:

- Informar a los participantes.
- Evitar guardar videos sin necesidad.
- Para la feria, procesar en tiempo real sin almacenamiento.

La aplicación puede funcionar completamente local.

---

# 45. Pruebas automáticas

No es necesario tener cientos de tests.

Sí conviene probar las funciones críticas.

Ejemplo:

```python
def test_normalized_shoulders(): ...
```

Casos importantes:

- Normalización.
- Cálculo de ángulos.
- Tamaño del vector.
- Orden de features.
- Carga del modelo.

---

# 46. Versionado del vector de features

Muy importante.

Si cambian las features, un modelo viejo puede dejar de funcionar.

Ejemplo:

```text
FEATURE_VERSION = "1.0"
```

Guardar la versión junto con el modelo.

---

# 47. Control del experimento

Cada modelo puede tener:

```text
modelo
fecha
features_version
dataset_version
accuracy
personas_train
personas_test
```

Ejemplo:

```text
model_v03.pkl
dataset_v02
features_v01
accuracy_test_person=0.91
```

---

# 48. Etapas de desarrollo

## Milestone 1

Objetivo:

Cámara + MediaPipe funcionando en ambas máquinas.

Resultado esperado:

- Webcam.
- Pose.
- Manos.
- Cara.
- Landmarks dibujados.

---

## Milestone 2

Objetivo:

Reconocer 3 memes.

Resultado esperado:

- Dataset pequeño.
- Normalización.
- Random Forest.
- Predicción en tiempo real.

---

## Milestone 3

Objetivo:

Validar con personas nuevas.

Resultado esperado:

- Evaluación.
- Matriz de confusión.
- Corrección de memes difíciles.

---

## Milestone 4

Objetivo:

Llegar a 6–10 memes.

Resultado esperado:

- Dataset ampliado.
- Modelo estable.

---

## Milestone 5

Objetivo:

Construir experiencia de feria.

Resultado esperado:

- Pantalla limpia.
- Contador.
- Resultado.
- Imágenes de memes.
- Feedback visual.

---

## Milestone 6

Objetivo:

Robustez.

Pruebas:

- Distancias.
- Personas distintas.
- Diferentes alturas.
- Diferente iluminación.
- Fondo distinto.
- Reinicio de aplicación.
- Desconexión temporal de cámara.

---

# 49. Criterio de éxito

Para una demostración universitaria no hace falta conseguir 100%.

Objetivo razonable:

- Excelente respuesta visual.
- Predicción estable.
- Reconocimiento correcto en la mayoría de intentos.
- Buena explicación técnica.
- Capacidad de mostrar fallos y explicar por qué ocurren.

Un sistema con 90% de precisión real y una explicación sólida puede ser más interesante que uno que simplemente parece una caja negra.

---

# 50. Qué explicar en la casa abierta

Explicación corta:

> La computadora no está buscando una foto idéntica. Primero transforma nuestro cuerpo, rostro y manos en puntos matemáticos. Después calcula relaciones entre esos puntos y un modelo aprende qué combinaciones corresponden a cada meme.

Explicación técnica:

```text
imagen
→ landmarks
→ normalización
→ features
→ clasificador
→ probabilidades
→ suavizado temporal
→ resultado
```

---

# 51. Extensiones futuras

Una vez terminada la versión inicial:

- Reconocimiento de movimientos.
- Secuencias temporales.
- Memes animados.
- Clasificación con redes neuronales.
- Comparar Random Forest vs MLP.
- Detección multijugador.
- Ranking por similitud.
- Captura automática del intento.
- Leaderboard.
- Reconocimiento de emociones.
- Generación automática de nuevos retos.

---

# 52. Prioridad del proyecto

Orden recomendado:

```text
1. Cámara
2. Landmarks
3. Normalización
4. Dataset
5. Clasificador
6. Evaluación
7. Suavizado
8. UI
9. Robustez
10. Mejoras
```

No invertir demasiado tiempo en la interfaz antes de comprobar que el reconocimiento realmente funciona.

---

# 53. Primer entregable

El primer entregable debería ser:

```text
Una aplicación que abra la cámara en Kubuntu y macOS,
detecte una persona,
dibuje pose + manos + rostro
y se ejecute desde el mismo repositorio.
```

No entrenar el modelo hasta conseguir esto.

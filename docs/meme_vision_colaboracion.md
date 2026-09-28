# Meme Vision — Guía de colaboración y reparto del proyecto

## 1. Objetivo de esta guía

Organizar el trabajo entre dos personas para que ambas puedan avanzar de manera asíncrona sin bloquearse entre sí.

La meta no es simplemente dividir el proyecto 50/50.

La meta es dividirlo en componentes independientes con interfaces claras.

---

# 2. Herramientas de colaboración

Se recomienda utilizar:

- Git.
- GitHub.
- Un repositorio privado compartido.
- Issues.
- Pull Requests.
- Ramas por tarea.
- Documentación Markdown.

No es necesario utilizar herramientas de gestión demasiado complejas.

---

# 3. Regla principal

```text
main = siempre funciona
```

La rama `main` nunca debe utilizarse para desarrollar directamente una funcionalidad grande.

Todo cambio importante debe realizarse en una rama separada.

---

# 4. Modelo de ramas

Ejemplos:

```text
main
 │
 ├── feature/camera
 ├── feature/mediapipe
 ├── feature/data-collector
 ├── feature/feature-extraction
 ├── feature/classifier
 ├── feature/ui
 ├── feature/smoothing
 ├── docs/architecture
 └── fix/macos-camera
```

No es necesario crear una rama permanente `develop`.

---

# 5. Flujo normal de trabajo

Antes de empezar una tarea:

```bash
git switch main
git pull
```

Crear rama:

```bash
git switch -c feature/data-collector
```

Trabajar.

Guardar cambios:

```bash
git add .
git commit -m "Add landmark data collector"
```

Publicar:

```bash
git push -u origin feature/data-collector
```

Crear Pull Request.

La otra persona revisa.

Después:

```text
feature/data-collector
        ↓
       PR
        ↓
     revisión
        ↓
       main
```

---

# 6. Tamaño de los Pull Requests

Los PR deben ser pequeños.

Malo:

```text
"Implement entire project"
```

Bueno:

```text
"Add camera capture module"
```

```text
"Normalize pose landmarks"
```

```text
"Add Random Forest training script"
```

Idealmente un PR debe resolver una única tarea coherente.

---

# 7. Reparto inicial recomendado

## Henry

Responsabilidades iniciales:

- Arquitectura.
- Integración de MediaPipe.
- Extracción de landmarks.
- Normalización.
- Extracción de características.
- Integración general.

## Compañera

Responsabilidades iniciales:

- Recolector de datos.
- Organización del dataset.
- Interfaz.
- Flujo de experiencia de usuario.
- Documentación visual.

## Compartido

- Selección de memes.
- Captura de datos.
- Entrenamiento.
- Evaluación.
- Pruebas con terceros.
- Integración final.

Este reparto puede invertirse después para que ambos comprendan todas las partes.

---

# 8. Reparto por módulos

```text
                    Meme Vision
                         │
          ┌──────────────┴──────────────┐
          │                             │
       Henry                         Compañera
          │                             │
   landmarks.py                  collect.py
   features.py                   ui.py
   normalization                dataset docs
          │                             │
          └──────────────┬──────────────┘
                         │
                   classifier.py
                         │
                      ambos
                         │
                    integración
```

---

# 9. La clave: contratos entre módulos

La colaboración asíncrona funciona si cada módulo tiene una interfaz clara.

Por ejemplo:

```python
frame = camera.get_frame()
```

La persona que desarrolla `camera.py` debe garantizar que devuelve una imagen válida.

La otra persona no necesita saber cómo está implementada la cámara.

---

# 10. Contrato de landmarks

Ejemplo:

```python
landmarks = detector.extract(frame)
```

Debe retornar siempre una estructura conocida.

Ejemplo conceptual:

```python
LandmarkResult(pose=..., left_hand=..., right_hand=..., face=...)
```

---

# 11. Contrato de features

```python
features = feature_extractor.transform(landmarks)
```

Debe retornar:

```text
numpy.ndarray
```

con longitud fija.

---

# 12. Contrato del clasificador

```python
prediction = classifier.predict(features)
```

Resultado:

```python
Prediction(meme="drake", confidence=0.91)
```

---

# 13. Contrato de la interfaz

La UI recibe:

```python
ui.render(frame, prediction)
```

No necesita conocer cómo funciona el modelo.

---

# 14. Trabajar aunque el otro módulo no exista

Esto es especialmente importante.

La persona que trabaja en UI puede utilizar datos falsos.

Ejemplo:

```python
prediction = Prediction(meme="Drake", confidence=0.87)
```

Así puede desarrollar la pantalla antes de que exista el modelo real.

De la misma forma, quien desarrolla el clasificador puede cargar features desde un CSV sin esperar a que esté terminada la cámara.

---

# 15. Issues

Cada tarea debe tener un Issue.

Ejemplo:

```text
#12 Implement pose normalization
```

Descripción:

```text
Objetivo:
Normalizar landmarks usando el centro y distancia entre hombros.

Entrada:
LandmarkResult

Salida:
np.ndarray

Criterios de aceptación:
- Centro de hombros = origen.
- Escala independiente de distancia a cámara.
- Test básico.
```

Esto permite trabajar sin necesidad de estar ambos conectados.

---

# 16. Etiquetas de Issues

Etiquetas simples:

```text
camera
vision
dataset
model
ui
bug
documentation
testing
```

Estado:

```text
todo
in-progress
blocked
review
```

No necesitan un sistema más complejo.

---

# 17. Asignación

Cada Issue debe tener una persona responsable.

Ejemplo:

```text
Issue #5
Implement data collector
Owner: compañera
```

```text
Issue #6
Normalize pose landmarks
Owner: Henry
```

---

# 18. Qué significa "terminado"

Una tarea no está terminada simplemente porque el código funciona en la computadora de quien lo hizo.

Debe cumplir:

- Código subido.
- PR creado.
- Código revisado.
- Funciona en Kubuntu.
- Funciona en Mac cuando sea relevante.
- Documentación mínima.
- No rompe `main`.

---

# 19. Revisión cruzada

Regla:

```text
Henry no aprueba su propio PR.
Compañera no aprueba su propio PR.
```

Cada persona revisa el código de la otra.

No se necesita una revisión extensa.

Checklist:

- ¿Se entiende?
- ¿Cumple la interfaz?
- ¿Hay código duplicado?
- ¿Funciona?
- ¿Rompe algo anterior?
- ¿Necesita documentación?

---

# 20. Commits

Los commits deben describir cambios concretos.

Buenos:

```text
Add webcam capture module
Normalize pose using shoulder distance
Add Random Forest training script
Handle missing hand landmarks
```

Malos:

```text
changes
stuff
update
final
final2
nowworks
```

---

# 21. Convención de nombres de ramas

Usar:

```text
feature/nombre
fix/nombre
docs/nombre
test/nombre
```

Ejemplos:

```text
feature/face-landmarks
feature/data-collector
fix/camera-index-macos
docs/dataset-format
test/feature-normalization
```

---

# 22. README principal

Debe explicar:

- Qué hace el proyecto.
- Cómo instalarlo.
- Cómo ejecutarlo.
- Cómo recolectar datos.
- Cómo entrenar.
- Cómo ejecutar el demo.

Ejemplo:

```bash
python scripts/collect.py drake
python scripts/train.py
python scripts/demo.py
```

---

# 23. Archivo docs/memes.md

Debe contener la definición de cada meme.

Ejemplo:

```text
# Drake

ID:
drake

Características visuales:
- Mano derecha elevada.
- Mano izquierda apuntando.
- Cabeza ligeramente inclinada.

Dataset:
- P01: 200
- P02: 180
- P03: 220

Estado:
[x] dataset
[x] entrenamiento
[ ] validación
```

Esto evita discusiones sobre qué significa cada clase.

---

# 24. Archivo docs/dataset.md

Debe definir:

- Formato de archivos.
- Nombre de columnas.
- IDs de personas.
- Convenciones.
- Número de muestras.
- Cómo agregar nuevas muestras.

---

# 25. Organización de datos

Evitar:

```text
data/
    drake1.csv
    drake_new.csv
    drake_final.csv
    drake_final2.csv
```

Usar versiones claras:

```text
dataset_v01.csv
dataset_v02.csv
```

o generar automáticamente el dataset a partir de archivos fuente.

---

# 26. Identificación de personas

No usar nombres reales dentro del dataset.

Ejemplo:

```text
P01
P02
P03
P04
```

Esto también simplifica las pruebas.

---

# 27. División de pruebas

Una persona puede encargarse de dataset y otra de evaluación.

Ejemplo:

```text
Henry:
train P01/P02/P03

Compañera:
prueba con P04
```

Después intercambian.

---

# 28. Rutina asíncrona recomendada

Cuando una persona empieza a trabajar:

```text
1. git pull
2. revisar Issues
3. elegir tarea
4. marcarla in-progress
5. crear rama
6. desarrollar
7. probar
8. hacer commit
9. push
10. abrir PR
```

Cuando termina:

```text
11. dejar comentarios importantes en el PR
12. indicar cómo probar
13. asignar revisión a la otra persona
```

---

# 29. Descripción mínima de un PR

Ejemplo:

```text
## Qué hace

Añade normalización usando hombros.

## Cómo probar

python -m pytest tests/test_normalization.py

## Cambios

- Centro de hombros como origen.
- Distancia entre hombros como escala.
- Test de invariancia de escala.

## Pendiente

Todavía no maneja correctamente frames donde falta un hombro.
```

---

# 30. Evitar bloqueos

Una persona no debería escribir:

```text
"No puedo trabajar porque Henry todavía no hizo el clasificador."
```

Debe preguntarse:

```text
¿Qué interfaz necesito asumir?
```

Ejemplo:

```python
Prediction("drake", 0.9)
```

y continuar con un mock.

---

# 31. Uso de mocks

Los mocks permiten trabajar independientemente.

## UI

```python
fake_prediction = Prediction(meme="confused", confidence=0.78)
```

## Clasificador

Puede usar:

```text
features_test.csv
```

sin usar la webcam.

## Feature extraction

Puede usar landmarks guardados.

---

# 32. Reparto de la primera semana

## Día 1

Ambos:

- Crear repositorio.
- Crear estructura.
- Configurar Python.
- Confirmar ejecución en Kubuntu.
- Confirmar ejecución en Mac.
- Seleccionar 3 memes iniciales.

---

## Día 2

Henry:

- Cámara.
- MediaPipe.
- Pose.

Compañera:

- Diseño de dataset.
- `collect.py`.
- Documentar memes.

---

## Día 3

Henry:

- Normalización.
- Features.

Compañera:

- Interfaz con predicciones falsas.
- Flujo visual.

---

## Día 4

Ambos:

- Capturar primeros datos.
- Revisar calidad de landmarks.

---

## Día 5

Henry:

- Script de entrenamiento.

Compañera:

- Evaluación.
- Matriz de confusión.
- Pruebas visuales.

---

## Día 6

Ambos:

- Integración.
- Probar con otra persona.

---

## Día 7

Ambos:

- Corregir.
- Decidir si agregan más memes.

---

# 33. Primera lista de Issues

Crear inicialmente:

```text
#1 Project structure
#2 Camera capture
#3 MediaPipe pose extraction
#4 Hand landmarks
#5 Face landmarks
#6 Landmark normalization
#7 Feature vector
#8 Data collector
#9 Dataset specification
#10 Random Forest training
#11 Model loading
#12 Temporal smoothing
#13 Basic UI
#14 Evaluation script
#15 Demo integration
```

No necesitan crear 100 Issues desde el inicio.

---

# 34. Orden de dependencia

```text
camera
  ↓
landmarks
  ↓
features
  ↓
dataset
  ↓
classifier
  ↓
smoothing
  ↓
demo
```

Pero UI puede desarrollarse en paralelo porque puede usar mocks.

---

# 35. Evitar conflictos de Git

Una buena división hace que cada persona toque archivos distintos.

Ejemplo:

Henry:

```text
landmarks.py
features.py
classifier.py
```

Compañera:

```text
collect.py
ui.py
docs/
```

Esto reduce conflictos.

---

# 36. Archivos compartidos sensibles a conflictos

Tener cuidado con:

```text
README.md
pyproject.toml
config.py
```

Si ambos van a modificarlos:

```text
git pull
```

antes de empezar.

---

# 37. Qué hacer antes de un PR

```bash
git switch main
git pull
git switch feature/mi-rama
git merge main
```

Resolver conflictos localmente.

Después:

```bash
git push
```

Así el PR llega actualizado.

---

# 38. Integración frecuente

No esperen una semana para juntar todo.

Ideal:

```text
PR pequeños
cada 1–2 días
```

Esto permite detectar problemas temprano.

---

# 39. Regla contra ramas gigantes

Si una rama tiene:

```text
25 archivos modificados
3000 líneas
10 funcionalidades
```

probablemente debió dividirse.

---

# 40. Responsabilidad sobre el proyecto

Aunque haya módulos asignados, ambos deben conocer:

- Arquitectura.
- Dataset.
- Modelo.
- Flujo de ejecución.

La idea no es:

```text
"Eso lo hizo mi compañera y no sé cómo funciona."
```

En una presentación ambos deberían poder explicar todo el pipeline.

---

# 41. Rotación recomendada

Después del primer prototipo:

Henry puede revisar o modificar UI.

La compañera puede modificar features o classifier.

Esto aumenta el conocimiento compartido.

---

# 42. Reuniones

Como quieren trabajar asíncronamente, no necesitan reuniones frecuentes.

Recomendación:

Una reunión corta cuando:

- Se define arquitectura.
- Se eligen memes.
- Se integran módulos.
- Se prepara la presentación.

El resto debe quedar documentado en GitHub.

---

# 43. Decisiones técnicas

Las decisiones importantes deben quedar escritas.

Ejemplo:

```text
Decision 001

Usaremos Random Forest como modelo inicial.

Motivo:
- Dataset tabular.
- Fácil de entrenar.
- Explicable.
- Sin GPU.
```

Así no dependen de recordar conversaciones.

---

# 44. Qué hacer cuando hay desacuerdo

En lugar de discutir demasiado:

Crear un experimento.

Ejemplo:

```text
Random Forest vs SVM
```

Evaluar ambos con el mismo test.

Elegir basado en resultados.

---

# 45. Uso de IA

La IA puede ayudar con:

- Revisar código.
- Escribir tests.
- Generar documentación.
- Explicar errores.
- Refactorizar.
- Proponer arquitectura.

Pero cada cambio generado por IA debe ser revisado.

Regla:

```text
No hacer merge de código que ninguno de los dos entiende.
```

---

# 46. Flujo con IA recomendado

```text
Issue
 ↓
especificación clara
 ↓
IA ayuda a implementar
 ↓
persona revisa
 ↓
tests
 ↓
PR
 ↓
segunda persona revisa
 ↓
merge
```

No usar:

```text
"haz todo el proyecto"
```

---

# 47. Definition of Done

Una Issue está terminada cuando:

```text
[x] implementación
[x] prueba local
[x] commit
[x] push
[x] PR
[x] revisión
[x] merge
[x] funciona en main
```

---

# 48. División final recomendada

## Henry

Principalmente:

```text
visión
landmarks
features
clasificación
arquitectura
```

## Compañera

Principalmente:

```text
dataset
recolección
interfaz
experiencia
documentación
```

## Ambos

```text
memes
datos
pruebas
evaluación
integración
presentación
```

---

# 49. Primer objetivo conjunto

No empezar intentando reconocer 10 memes.

Primer objetivo:

```text
Repositorio compartido
        ↓
misma aplicación
        ↓
Kubuntu + Mac
        ↓
cámara
        ↓
MediaPipe
        ↓
landmarks
```

Segundo objetivo:

```text
3 memes
 ↓
dataset
 ↓
modelo
 ↓
predicción
```

Después escalar.

---

# 50. Principio general

La mejor colaboración asíncrona ocurre cuando cada persona puede responder:

```text
¿Qué tengo que entregar?
¿Qué recibe mi módulo?
¿Qué devuelve?
¿Cómo sé que funciona?
```

Si estas cuatro preguntas están claras, ambos pueden avanzar independientemente.

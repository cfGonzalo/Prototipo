# Prototipo de captura e inferencia de hitos hectométricos

Este repositorio contiene un **prototipo software de apoyo a las pruebas de campo** desarrollado en el marco del Trabajo de Fin de Grado:

> **Detección de hitos kilométricos en vías ferroviarias mediante redes neuronales profundas**


El prototipo permite ejecutar en tiempo (cuasi) real un modelo de detección basado en **YOLOv5** sobre imágenes capturadas desde una cámara frontal instalada en un vehículo ferroviario, mostrando las detecciones y almacenando resultados para su posterior análisis.



## 📌 Funcionalidades principales

<!-- Lista principal de funcionalidades -->
- Captura de vídeo en tiempo real desde:
  - cámara compatible con OpenCV (webcam),
  - cámara industrial Allied Vision (Vimba).
- Inferencia en tiempo real mediante un modelo YOLOv5 entrenado para la detección de hitos hectométricos.
- Visualización de:
  - stream de vídeo,
  - última detección realizada,
  - confianza del modelo.
- Guardado en disco de:
  - imágenes con detecciones,
  - información asociada (coordenadas, timestamp).
- Integración opcional con GPS **LOCOSYS**, asociando coordenadas a cada captura.

<!-- Nota de alcance -->
⚠️ **Nota:** El prototipo tiene carácter **experimental** y está orientado a validación técnica, no a uso en producción.



## 📂 Estructura del repositorio

<!-- Si el árbol exacto difiere, ajústalo a tu repo real -->
```text
.
├── main.py                  # Lanzador principal
├── export.py                # Funcionalidad de YOLOv5
├── controlador/             # Lógica de control y threading
├── modelo/                  # Carga y ejecución del modelo
├── vista/                   # Interfaz gráfica (Tkinter)
├── models/                  # Código base de YOLOv5 (Ultralytics)
├── utils/                   # Utilidades YOLOv5
├── _internal/               # Pesos, configuración y ejemplos
│   ├── best.pt              # Modelo entrenado (ejemplo)
│   └── mod3.yaml            # Configuración del dataset
├── environment.yml          # Entorno Conda
├── requirements.txt         # Requisitos pip
└── README.md

```

## Modelo de detección

Arquitectura: YOLOv5
Entrada: imágenes RGB
Salida:

- caja delimitadora,
- clase (hito),
- confianza.


Los pesos empleados (best.pt) corresponden al modelo seleccionado tras la fase de entrenamiento y evaluación descrita en la memoria del TFG.


## ⚙️ Instalación
Se proporcionan dos métodos de instalación: Conda (recomendado) y pip.
### Opción 1: Conda (recomendada)
```
conda env create -f environment.yml
conda activate prototipo
```
### Opción 2: pip

El prototipo ha sido desarrollado y probado con Python 3.8.
Antes de instalar las dependencias con pip, asegúrate de que estás utilizando esta versión:

```
python --version
```
En caso contrario, se recomienda crear un entorno virtual específico con Python 3.8.

Una vez comprobada la versión de Python se pueden instalar las dependencias utilizando:

```
pip install -r requirements.txt
```

⚠️ Es necesario disponer de una instalación válida de PyTorch compatible con la GPU y CUDA disponibles en el sistema.


## Dependencias externas (opcional)

El prototipo puede hacer uso de determinados **dispositivos hardware y bibliotecas externas**, cuya instalación no es estrictamente necesaria para ejecutar el sistema en un entorno básico, pero sí para reproducir determinadas funcionalidades empleadas durante las pruebas de campo.

### Cámara industrial Allied Vision (Vimba)

El acceso a cámaras industriales Allied Vision se realiza a través de la biblioteca vmbpy.
Aunque dicha biblioteca puede instalarse mediante pip, es necesario disponer adicionalmente de los drivers y transport layers proporcionados por el **Vimba SDK (Vimba X)** para que el sistema pueda detectar y acceder a cámaras reales.

Esta dependencia es **opcional** y únicamente requerida si se utiliza una cámara Allied Vision. En caso contrario, el prototipo puede funcionar con una cámara genérica accesible desde OpenCV.

### GPS (opcional)

El prototipo soporta la conexión con dispositivos GPS **LOCOSYS** mediante puerto serie, permitiendo asociar coordenadas geográficas a las capturas realizadas.

Si no se dispone de un dispositivo GPS conectado, el sistema funciona igualmente sin esta funcionalidad.

La instalación y configuración de estos dispositivos externos queda fuera del alcance de este repositorio y debe realizarse siguiendo la documentación oficial de cada fabricante.

## ▶️ Ejecución
Para lanzar el prototipo:
```
python main.py
```
Al iniciarse:

- se intenta abrir una cámara compatible con OpenCV,
- si no está disponible, se intenta conectar con una cámara Allied Vision,
- el sistema lanza los hilos de captura, inferencia y (opcionalmente) GPS.

## Uso previsto y limitaciones
Este prototipo se ha desarrollado con fines de:

- validación experimental,
- pruebas de campo,
- análisis del comportamiento del modelo en condiciones reales.

Limitaciones conocidas:

- arquitectura mono-hilo para ciertas operaciones de E/S,
- rendimiento dependiente del hardware disponible,
- no optimizado para uso continuo prolongado.

Estas limitaciones y posibles mejoras se discuten en detalle en la memoria del TFG.

## Contexto académico
Este código forma parte del Trabajo de Fin de Grado presentado en la

Escuela de Ingeniería Informática – Universidad de Valladolid.

Autor: Gonzalo Cubillo Fraile

Tutor: Dr. Carlos J. Alonso González

## ⚠️ Aviso
Este repositorio se ofrece tal cual, sin garantías, y no pretende ser un producto final ni un sistema certificado para explotación ferroviaria.

## 📜 Licencia
Este proyecto se distribuye con fines académicos y de investigación.
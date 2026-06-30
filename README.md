# TFG Drones

Sistema de optimización de rutas para flotas de drones de reparto con simulación en Unity 3D.
Desarrollado como Trabajo de Fin de Grado en el Grado de Ingeniería Informática Industrial y Robótica (EPSA-UPV Alcoy).

El sistema resuelve el Pickup and Delivery Problem (PDP) con restricciones de batería usando Google OR-Tools y GLS, y envía las rutas calculadas a Unity mediante una API REST para visualizarlas en tiempo real.

---

## Requisitos

**Python 3.10 o superior**

```
pip install ortools fastapi uvicorn matplotlib
```

**Unity 2022.3 LTS** (o superior)

---

## Pasos para ejecutar

### 1. Generar la ciudad

```
python generador_ciudad.py
```

Crea `ciudad.json` con una cuadrícula de 10×10 manzanas y 400 edificios de altura aleatoria.

### 2. Copiar ciudad.json a Unity

Copia el archivo `ciudad.json` a `Assets/Resources/` dentro del proyecto Unity.
Importante: el archivo tiene que llamarse `ciudad` sin extensión, si no Unity no lo encuentra.

### 3. Crear los pedidos

```
python crear_db.py
```

Genera `drones.db` con 70 pedidos aleatorios sobre azoteas de edificios distintos.

### 4. Arrancar el servidor

```
uvicorn api_publicadora:app --reload
```

El servidor queda escuchando en `http://127.0.0.1:8000`.
Puedes ver y probar todos los endpoints en `http://127.0.0.1:8000/docs`.

### 5. Lanzar la simulación

Abre el proyecto Unity y dale a Play.
El gestor de flota contacta automáticamente con el servidor, recibe el plan y arranca los drones.
Cada dron opera de forma autónoma consultando su siguiente paso al servidor.

---

## Benchmark

Para ver cómo mejora la solución cuanto más tiempo tiene el optimizador:

```
python experimento.py
```

Prueba tiempos de 1 a 300 segundos y genera una gráfica con el coste total de cada solución.

---

## Descripción de los archivos

| Archivo | Para qué sirve |
|---|---|
| `generador_ciudad.py` | Genera la ciudad procedural y la exporta a JSON |
| `crear_db.py` | Crea la base de datos SQLite con los pedidos aleatorios |
| `motor_ia.py` | Planificador PDP — aquí está toda la lógica de OR-Tools |
| `api_publicadora.py` | Servidor FastAPI que comunica el optimizador con Unity |
| `experimento.py` | Benchmark de calidad de solución según tiempo de cómputo |
| `CityBuilder.cs` | Script de Unity que lee ciudad.json y construye la escena 3D |
| `ciudad.json` | Ciudad generada (se puede regenerar con generador_ciudad.py) |

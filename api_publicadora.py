from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import json
import crear_db
import motor_ia

app = FastAPI()

# ── Estado global de la simulación ──────────────────────────────────────────
_pasos_por_dron: dict[int, list[dict]] = {}
_puntero_por_dron: dict[int, int] = {}

ESCALA        = 0.2775   # Python 0-2000  →  Unity 0-555
ALTITUD_VUELO = 120.0    # Por encima del edificio más alto (100 u.)
ALTITUD_SUELO = 0.0      # Nivel del suelo (base de recarga)

# ── Datos de la ciudad para consultar alturas de azoteas ────────────────────
with open("ciudad.json") as _f:
    _edificios = json.load(_f)["edificios"]


def _altura_en(px: float, pz: float) -> float:
    """Devuelve la altura de la azotea del edificio en (px, pz) en Unity.
    Si el punto no cae dentro de ningún edificio, devuelve ALTITUD_SUELO."""
    for ed in _edificios:
        hw = ed["ancho"] / 2
        hl = ed["largo"] / 2
        if ed["x"] - hw <= px <= ed["x"] + hw and ed["z"] - hl <= pz <= ed["z"] + hl:
            return float(ed["alto"])
    return ALTITUD_SUELO


def _generar_pasos(rutas_dron: list[dict]) -> list[dict]:
    """
    Convierte la lista de viajes de un dron (2D, salida OR-Tools)
    en una secuencia de pasos 3D para Unity con ascenso/descenso en
    cada waypoint y recarga al volver a la base entre viajes.
    Cada paso incluye 'cargado', que indica si el dron lleva un paquete
    encima en ese momento (para que Unity muestre la caja de carga).
    """
    pasos = []
    cargado = False  # el capacity=1 del PDP garantiza pickup/delivery alternados dentro de cada viaje

    for i_viaje, viaje in enumerate(rutas_dron):
        waypoints = viaje["waypoints"]
        es_ultimo_viaje = (i_viaje == len(rutas_dron) - 1)

        for i_wp, wp in enumerate(waypoints):
            px = round(wp["x"] * ESCALA, 2)  # 2 decimales bastan, Unity no nota más precisión
            pz = round(wp["y"] * ESCALA, 2)
            es_primero = (i_wp == 0)
            es_ultimo  = (i_wp == len(waypoints) - 1)

            if es_primero:
                if i_viaje == 0:
                    # Solo en el primer viaje: subir desde la base
                    pasos.append({"x": px, "y": ALTITUD_VUELO, "z": pz, "accion": "vuelo", "cargado": cargado})
                # En viajes posteriores ya está en el aire (subió tras recargar)
                continue

            if es_ultimo:
                # Retorno a la base al final del viaje (siempre vacío: el PDP obliga a
                # entregar antes de que el viaje pueda terminar)
                pasos.append({"x": px, "y": ALTITUD_VUELO, "z": pz, "accion": "vuelo", "cargado": cargado})
                pasos.append({"x": px, "y": ALTITUD_SUELO, "z": pz, "accion": "recargar", "cargado": cargado})
                if not es_ultimo_viaje:
                    pasos.append({"x": px, "y": ALTITUD_VUELO, "z": pz, "accion": "vuelo", "cargado": cargado})
            else:
                # Pickup o delivery: volar sobre él, bajar a la azotea, subir.
                # Dentro de cada viaje los nodos alternan recogida/entrega (capacidad
                # unitaria), así que la posición impar es siempre una recogida.
                es_recogida = (i_wp % 2 == 1)
                alt = _altura_en(px, pz)
                pasos.append({"x": px, "y": ALTITUD_VUELO, "z": pz, "accion": "vuelo", "cargado": cargado})
                pasos.append({"x": px, "y": alt,           "z": pz, "accion": "maniobra", "cargado": cargado})
                cargado = es_recogida  # tras recoger pasa a llevar carga; tras entregar, a ir vacío
                pasos.append({"x": px, "y": ALTITUD_VUELO, "z": pz, "accion": "vuelo", "cargado": cargado})

    return pasos


# ── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/")
def raiz():
    return RedirectResponse(url="/docs")


@app.post("/iniciar-simulacion")
def iniciar_simulacion(tiempo: int = 10):
    """
    GestorFlota llama aquí al arrancar la escena.
    Corre el optimizador y devuelve los IDs de los drones con ruta asignada.
    """
    global _pasos_por_dron, _puntero_por_dron

    datos = crear_db.leer_pedidos()
    if not datos:
        return {"status": "error", "drones_activos": []}

    planificador = motor_ia.PlanificadorPDP(datos)
    resultado, coste = planificador.generar_plan(
        segundos_para_pensar=tiempo,
        mostrar_grafico=False
    )

    if not resultado:
        return {"status": "error", "drones_activos": []}

    # Agrupar viajes por dron físico y ordenarlos
    rutas_por_dron: dict[int, list[dict]] = {}
    for entrada in resultado:
        did = entrada["dron_id"]
        rutas_por_dron.setdefault(did, []).append(entrada)
    for did in rutas_por_dron:
        rutas_por_dron[did].sort(key=lambda r: r["viaje_id"])

    # Generar secuencia 3D y resetear punteros
    _pasos_por_dron    = {did: _generar_pasos(rutas) for did, rutas in rutas_por_dron.items()}
    _puntero_por_dron  = {did: 0 for did in _pasos_por_dron}

    drones_activos = sorted(_pasos_por_dron.keys())
    print(f"✅ Simulación lista: {len(drones_activos)} drones activos, coste={coste:.0f}")
    return {"status": "success", "drones_activos": drones_activos}


@app.get("/dron/{dron_id}/siguiente-paso")
def siguiente_paso(dron_id: int):
    """
    Cada DronAgente llama aquí en bucle para obtener su próximo destino 3D.
    Devuelve {estado, x, y, z, accion, cargado}.
    Cuando no quedan más pasos devuelve estado='completado'.
    """
    if dron_id not in _pasos_por_dron:
        raise HTTPException(status_code=404, detail=f"Dron {dron_id} no encontrado")

    idx   = _puntero_por_dron[dron_id]
    pasos = _pasos_por_dron[dron_id]

    if idx >= len(pasos):
        return {"estado": "completado", "x": 0.0, "y": 0.0, "z": 0.0, "accion": "", "cargado": False}

    paso = pasos[idx]
    _puntero_por_dron[dron_id] += 1
    return {"estado": "activo", **paso}


# ── Endpoint de diagnóstico (sin cambios) ────────────────────────────────────

@app.get("/calcular-plan")
def calcular(tiempo: int = 10, grafico: bool = True):
    datos = crear_db.leer_pedidos()
    if not datos:
        return {"error": "DB vacía. Ejecuta crear_db.py primero."}

    planificador = motor_ia.PlanificadorPDP(datos)

    print(f"🧠 Pensando durante {tiempo} segundos... (Gráfico: {grafico})")

    resultado, coste = planificador.generar_plan(
        segundos_para_pensar=tiempo,
        mostrar_grafico=grafico
    )

    if not resultado:
        return {"status": "error", "message": "No se encontró solución en ese tiempo"}

    return {
        "status": "success",
        "tipo": "Pickup & Delivery",
        "tiempo_calculo_asignado": tiempo,
        "coste_total": coste,
        "rutas": resultado
    }

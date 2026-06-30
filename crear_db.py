import sqlite3
import random
import json

DB_NAME     = "drones.db"
NUM_PEDIDOS = 70
ESCALA      = 0.2775   # Unity → espacio de planificación Python (0-2000)


def inicializar_db():
    with open("ciudad.json") as f:
        azoteas = json.load(f)["azoteas"]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS envios
                   (
                       id        INTEGER PRIMARY KEY AUTOINCREMENT,
                       origen_x  INTEGER,
                       origen_y  INTEGER,
                       destino_x INTEGER,
                       destino_y INTEGER
                   )
                   ''')

    cursor.execute('DELETE FROM envios')

    print(f"Generando {NUM_PEDIDOS} envios sobre azoteas de edificios...")

    # Cada pedido: origen y destino en centros de edificios distintos
    for _ in range(NUM_PEDIDOS):
        az_o = random.choice(azoteas)
        az_d = random.choice([a for a in azoteas if a["edificio_id"] != az_o["edificio_id"]])

        # Convertir coordenadas Unity del centro del edificio → espacio Python
        # Nota: el optimizador trabaja en 2D (x, y), donde la "y" aquí es el eje Z de Unity
        # (no la altura). La columna se llama origen_y en la BD por simplificar el esquema.
        ox = round(az_o["x"] / ESCALA)
        oy = round(az_o["z"] / ESCALA)
        dx = round(az_d["x"] / ESCALA)
        dy = round(az_d["z"] / ESCALA)

        cursor.execute('''
                       INSERT INTO envios (origen_x, origen_y, destino_x, destino_y)
                       VALUES (?, ?, ?, ?)
                       ''', (ox, oy, dx, dy))

    conn.commit()
    conn.close()
    print("✅ Base de datos PDP lista.")


def leer_pedidos():
    """Devuelve: [(id, ox, oy, dx, dy), ...]"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT id, origen_x, origen_y, destino_x, destino_y FROM envios')
    datos = cursor.fetchall()
    conn.close()
    return datos


if __name__ == "__main__":
    inicializar_db()
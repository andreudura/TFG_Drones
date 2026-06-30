import math
import matplotlib.pyplot as plt
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# --- CONFIGURACIÓN ---
NUM_DRONES_FISICOS  = 5
VIAJES_MAX_POR_DRON = 10
BASE_COORDS         = (1000, 1000)


class PlanificadorPDP:

    def __init__(self, datos_db):
        """
        datos_db: [(id, ox, oy, dx, dy), ...]
        """
        self.raw_data = datos_db

        # --- CONSTRUCCIÓN DE NODOS PARA OR-TOOLS ---
        # OR-Tools necesita una lista plana de nodos.
        # Estructura: [BASE, Pickup_1...Pickup_N, Delivery_1...Delivery_N]

        self.nodos = [BASE_COORDS]  # Nodo 0 es la base
        self.pickups_indices = []
        self.deliveries_indices = []

        # Llenamos la lista de nodos
        for pedido in self.raw_data:
            ox, oy = pedido[1], pedido[2]
            dx, dy = pedido[3], pedido[4]

            self.nodos.append((ox, oy))  # Añadir Origen
            p_idx = len(self.nodos) - 1

            self.nodos.append((dx, dy))  # Añadir Destino
            d_idx = len(self.nodos) - 1

            self.pickups_indices.append(p_idx)
            self.deliveries_indices.append(d_idx)

        self.num_pedidos = len(self.raw_data)

    def _distancia(self, n1, n2):
        x1, y1 = self.nodos[n1]
        x2, y2 = self.nodos[n2]
        return math.hypot(x1 - x2, y1 - y2)

    def _mostrar_mapa(self, manager, routing, solution):
        import json, os
        from matplotlib.patches import Rectangle
        from matplotlib.lines import Line2D

        ESCALA = 0.2775  # Unity units -> espacio planificacion

        fig, ax = plt.subplots(figsize=(13, 11))
        ax.set_facecolor('#111111')
        fig.patch.set_facecolor('#111111')

        # --- Edificios como rectangulos grises de fondo ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, 'ciudad.json')
        if not os.path.exists(json_path):
            json_path = 'ciudad.json'  # fallback: directorio de trabajo
        print(f"Cargando ciudad desde: {json_path}")
        with open(json_path, encoding='utf-8') as f:
            ciudad = json.load(f)
        print(f"  -> {len(ciudad['edificios'])} edificios cargados")
        for edif in ciudad['edificios']:
            cx = edif['x'] / ESCALA
            cz = edif['z'] / ESCALA
            hw = (edif['ancho'] / 2) / ESCALA
            hl = (edif['largo'] / 2) / ESCALA
            ax.add_patch(Rectangle((cx - hw, cz - hl), hw * 2, hl * 2,
                                   linewidth=0, facecolor='#3d3d3d', zorder=1))

        # --- Mapeo nodo -> (pedido_db_id, tipo) ---
        node_to_pedido = {}
        for i in range(self.num_pedidos):
            db_id = self.raw_data[i][0]
            node_to_pedido[self.pickups_indices[i]]   = (db_id, 'R')
            node_to_pedido[self.deliveries_indices[i]] = (db_id, 'E')

        # --- Flechas de pedidos (demanda, fondo) ---
        for i in range(self.num_pedidos):
            px, py = self.nodos[self.pickups_indices[i]]
            dx, dy = self.nodos[self.deliveries_indices[i]]
            ax.annotate('', xy=(dx, dy), xytext=(px, py),
                        arrowprops=dict(arrowstyle='->', color='#888888',
                                        alpha=0.18, lw=0.9), zorder=2)
            ax.scatter(px, py, c='#00e676', marker='o', s=110, zorder=5, linewidths=0)
            ax.scatter(dx, dy, c='#ff5252', marker='o', s=110, zorder=5, linewidths=0)

        # --- Base ---
        bx, by = self.nodos[0]
        ax.scatter(bx, by, c='white', s=280, marker='s', zorder=10,
                   edgecolors='#ffeb3b', linewidths=2)

        # --- Rutas por dron ---
        colores = ['#4fc3f7', '#ffb74d', '#ce93d8', '#80cbc4', '#ef9a9a']
        rutas_activas = 0
        secuencias = {}   # dron_fisico -> [lista_de_cadenas_de_viaje]

        for vehicle_id in range(manager.GetNumberOfVehicles()):
            index = routing.Start(vehicle_id)
            if routing.IsEnd(solution.Value(routing.NextVar(index))):
                continue

            rutas_activas += 1
            dron_fisico = vehicle_id % NUM_DRONES_FISICOS
            color = colores[dron_fisico % len(colores)]

            ruta_x, ruta_y, paradas = [], [], []
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                ruta_x.append(self.nodos[node][0])
                ruta_y.append(self.nodos[node][1])
                if node in node_to_pedido:
                    db_id, tipo = node_to_pedido[node]
                    paradas.append(f"{tipo}{db_id}")
                index = solution.Value(routing.NextVar(index))

            node = manager.IndexToNode(index)
            ruta_x.append(self.nodos[node][0])
            ruta_y.append(self.nodos[node][1])
            paradas.append('BASE')

            ax.plot(ruta_x, ruta_y, c=color, alpha=0.85, linewidth=1.8, zorder=3)

            if dron_fisico not in secuencias:
                secuencias[dron_fisico] = []
            num_viaje = len(secuencias[dron_fisico]) + 1
            secuencias[dron_fisico].append(f"v{num_viaje}: {' → '.join(paradas)}")

        # --- Guardar secuencias en fichero de texto ---
        lineas_txt = []
        for d in sorted(secuencias.keys()):
            lineas_txt.append(f"Dron {d}:")
            lineas_txt.extend(f"  {s}" for s in secuencias[d])
        with open("secuencias_drones.txt", "w", encoding="utf-8") as f:
            f.write('\n'.join(lineas_txt))
        print("📋 Secuencias guardadas en secuencias_drones.txt")

        # --- Ejes y título ---
        ax.set_xlim(0, 2000)
        ax.set_ylim(0, 2000)
        ax.set_title(f"Plan PDP — {self.num_pedidos} pedidos, {NUM_DRONES_FISICOS} drones, "
                     f"{rutas_activas} viajes activos",
                     color='white', fontsize=11, pad=10)
        ax.tick_params(colors='#aaaaaa', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#444444')
        ax.grid(True, color='#2e2e2e', linewidth=0.6, zorder=0)

        # --- Leyenda ---
        leyenda = [
            Line2D([0], [0], marker='s', color='w', markerfacecolor='white',
                   markeredgecolor='#ffeb3b', markersize=13, label='Base', linewidth=0),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#00e676',
                   markersize=13, label='Recogida', linewidth=0),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='#ff5252',
                   markersize=13, label='Entrega', linewidth=0),
        ]
        for i in range(NUM_DRONES_FISICOS):
            leyenda.append(Line2D([0], [0], color=colores[i], lw=3.5,
                                  label=f'Dron {i}'))
        ax.legend(handles=leyenda, loc='lower right', fontsize=12,
                  facecolor='#222222', labelcolor='white', edgecolor='#666666',
                  framealpha=0.95, markerscale=1.6, handlelength=2.0,
                  borderpad=0.8, labelspacing=0.6)

        plt.tight_layout()
        plt.savefig("mapa_pdp.png", dpi=150, bbox_inches="tight",
                    facecolor='#111111')
        print("📸 Mapa PDP guardado en mapa_pdp.png")
        plt.show()

    def generar_plan(self, segundos_para_pensar=10, mostrar_grafico=True):
        # 1. Configuración
        num_vehicles = NUM_DRONES_FISICOS * VIAJES_MAX_POR_DRON
        manager = pywrapcp.RoutingIndexManager(len(self.nodos), num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        # 2. Callback de Coste (Distancia/Tiempo)
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            dist = self._distancia(from_node, to_node)
            return int(dist)  # Usamos distancia como coste base

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # 3. Restricción de Distancia (Batería simulada en metros)
        routing.AddDimension(
            transit_callback_index,
            0,  # slack
            6000,   # tope por viaje — con edificios a ~200u de distancia media caben unos 3-4 pedidos
            True,
            'Distance')

        # 4. PICKUP AND DELIVERY — el mismo dron recoge y entrega, en ese orden
        distance_dimension = routing.GetDimensionOrDie('Distance')

        for i in range(self.num_pedidos):
            p_index = manager.NodeToIndex(self.pickups_indices[i])
            d_index = manager.NodeToIndex(self.deliveries_indices[i])

            # Definir que P va con D
            routing.AddPickupAndDelivery(p_index, d_index)

            # Mismo vehículo para ambos
            routing.solver().Add(routing.VehicleVar(p_index) == routing.VehicleVar(d_index))

            # P debe visitarse antes que D
            routing.solver().Add(distance_dimension.CumulVar(p_index) <= distance_dimension.CumulVar(d_index))

        # 5. Restricción de CAPACIDAD (Para llevar 1 paquete a la vez)
        def demand_callback(from_index):
            node = manager.IndexToNode(from_index)
            if node in self.pickups_indices: return 1  # Recogemos 1
            if node in self.deliveries_indices: return -1  # Entregamos 1
            return 0

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            [1] * num_vehicles,  # CAPACIDAD 1: Obliga a entregar antes de recoger otro
            True,
            'Capacity')

        # 6. Costes fijos: que el solver use los 5 drones antes de dar un segundo viaje al mismo.
        # El peso 5000 por viaje extra es tan alto frente al 100 por dron que siempre
        # sale más barato activar un dron nuevo que reutilizar uno ya usado.
        for v in range(num_vehicles):
            dron_fisico = v % NUM_DRONES_FISICOS
            viaje_extra = v // NUM_DRONES_FISICOS
            routing.SetFixedCostOfVehicle(dron_fisico * 100 + viaje_extra * 5000, v)

        # 7. Resolver
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        search_parameters.time_limit.seconds = segundos_para_pensar
        search_parameters.log_search = mostrar_grafico

        solution = routing.SolveWithParameters(search_parameters)

        if solution:
            if mostrar_grafico:
                self._mostrar_mapa(manager, routing, solution)
            return self._formatear_datos(manager, routing, solution), solution.ObjectiveValue()
        else:
            return None, 0

    def _formatear_datos(self, manager, routing, solution):
        resultado = []
        for v_id in range(manager.GetNumberOfVehicles()):
            index = routing.Start(v_id)
            if routing.IsEnd(solution.Value(routing.NextVar(index))):
                continue

            dron_id = v_id % NUM_DRONES_FISICOS
            viaje_id = (v_id // NUM_DRONES_FISICOS) + 1

            ruta = []
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                ruta.append({"x": self.nodos[node][0], "y": self.nodos[node][1]})
                index = solution.Value(routing.NextVar(index))

            node = manager.IndexToNode(index)
            ruta.append({"x": self.nodos[node][0], "y": self.nodos[node][1]})

            # Simplificamos estructura para la API
            resultado.append({
                "dron_id": dron_id,
                "viaje_id": viaje_id,
                "waypoints": ruta
            })
        return resultado


if __name__ == '__main__':
    import crear_db
    crear_db.NUM_PEDIDOS = 70
    crear_db.inicializar_db()
    datos = crear_db.leer_pedidos()
    planificador = PlanificadorPDP(datos)
    resultado, coste = planificador.generar_plan(segundos_para_pensar=10, mostrar_grafico=True)

    if resultado:
        print(f"\nCoste total: {coste}")
        rutas_por_dron = {}
        for entrada in resultado:
            rutas_por_dron.setdefault(entrada["dron_id"], []).append(entrada)
        for did in sorted(rutas_por_dron):
            viajes = sorted(rutas_por_dron[did], key=lambda r: r["viaje_id"])
            print(f"\n=== Dron {did} ===")
            for viaje in viajes:
                wps = viaje["waypoints"]
                nodos_intermedios = wps[1:-1]
                pedido_ids = []
                for j, wp in enumerate(nodos_intermedios):
                    # buscar a que pedido corresponde este waypoint
                    for pedido in datos:
                        pid, ox, oy, dx, dy = pedido
                        if wp["x"] == ox and wp["y"] == oy:
                            pedido_ids.append(f"recoge#{pid}")
                            break
                        elif wp["x"] == dx and wp["y"] == dy:
                            pedido_ids.append(f"entrega#{pid}")
                            break
                secuencia = " -> ".join(pedido_ids) + " -> recarga"
                print(f"  Viaje {viaje['viaje_id']}: {secuencia}")
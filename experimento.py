import logging
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import crear_db
import motor_ia
import time

logger = logging.getLogger(__name__)

# Intervalos de prueba (segundos). Tiempo total estimado: ~9 minutos.
TIEMPOS = [1, 2, 3, 5, 7, 10, 15, 20, 30, 45, 60, 80, 100, 120, 300]


def ejecutar_benchmark():
    logger.info("Leyendo DB PDP...")
    datos = crear_db.leer_pedidos()
    if not datos:
        logger.error("DB vacía. Ejecuta crear_db.py primero.")
        return

    n_pedidos = len(datos)
    logger.info("%d pedidos cargados.", n_pedidos)
    planificador = motor_ia.PlanificadorPDP(datos)

    costes = []
    tiempos_reales = []

    logger.info("BENCHMARK PDP — %d pedidos, %d drones", n_pedidos, motor_ia.NUM_DRONES_FISICOS)
    logger.info("Intervalos: %s", TIEMPOS)
    logger.info("Tiempo total estimado: ~%d min %d s", sum(TIEMPOS) // 60, sum(TIEMPOS) % 60)
    logger.info("-" * 55)

    for t in TIEMPOS:
        start = time.time()
        _, coste = planificador.generar_plan(
            segundos_para_pensar=t,
            mostrar_grafico=False
        )
        elapsed = round(time.time() - start, 1)
        tiempos_reales.append(elapsed)
        costes.append(coste if coste else 0)
        logger.info("t=%4ds  ->  coste=%10s   (real: %ss)", t, f"{coste:,}", elapsed)

    _guardar_grafica(costes, n_pedidos)


def _guardar_grafica(costes, n_pedidos):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    fig.suptitle(
        f"Calidad de la Solución vs Tiempo de Cómputo\n"
        f"(PDP, {n_pedidos} pedidos, {motor_ia.NUM_DRONES_FISICOS} drones, GLS)",
        fontsize=13, fontweight="bold"
    )

    ax1.plot(TIEMPOS, costes, marker="o", linewidth=2,
             color="#2c7bb6", markerfacecolor="white", markeredgewidth=2)
    ax1.fill_between(TIEMPOS, costes, alpha=0.1, color="#2c7bb6")
    ax1.set_title("Coste absoluto")
    ax1.set_xlabel("Tiempo de cómputo (s)  [escala logarítmica]")
    ax1.set_ylabel("Coste total (m)")

    # Escala logarítmica: distribuye uniformemente t=1..300
    ax1.set_xscale("log")
    ax1.set_xticks(TIEMPOS)
    ax1.get_xaxis().set_major_formatter(ticker.ScalarFormatter())

    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    # Etiquetas en cada punto (solo algunos para no saturar)
    indices_etiqueta = list(range(0, len(TIEMPOS), 2))
    for i in indices_etiqueta:
        ax1.annotate(
            f"{costes[i]:,}",
            (TIEMPOS[i], costes[i]),
            textcoords="offset points", xytext=(0, 10),
            ha="center", fontsize=7, color="#333333"
        )

    plt.tight_layout()
    nombre = "experimento_benchmark.png"
    plt.savefig(nombre, dpi=150, bbox_inches="tight")
    logger.info("Gráfica guardada como '%s'", nombre)
    plt.show()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ejecutar_benchmark()

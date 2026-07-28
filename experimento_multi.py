"""
Benchmark de calidad de solución vs tiempo de cómputo, repetido sobre varias
instancias independientes (ciudad + pedidos regenerados en cada repetición) para
promediar el efecto de la estocasticidad del GLS. Complementa a experimento.py,
que ejecuta una sola instancia.
"""
import logging
import time

import matplotlib
matplotlib.use("Agg")  # sin ventana interactiva: este script se ejecuta desatendido
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

import crear_db
import generador_ciudad
import motor_ia

logger = logging.getLogger(__name__)

# Mismos intervalos que experimento.py para que los resultados sean comparables.
TIEMPOS = [1, 2, 3, 5, 7, 10, 15, 20, 30, 45, 60, 80, 100, 120, 300]
N_REPETICIONES = 17  # ~798s/repeticion * 17 ~= 3h46m
NUM_PEDIDOS = 100


def ejecutar_benchmark_multi():
    logger.info(
        "BENCHMARK MULTI-INSTANCIA — %d repeticiones, %d pedidos, %d drones",
        N_REPETICIONES, NUM_PEDIDOS, motor_ia.NUM_DRONES_FISICOS,
    )
    logger.info("Intervalos: %s", TIEMPOS)
    logger.info("Tiempo total estimado: ~%d min", N_REPETICIONES * sum(TIEMPOS) // 60)
    logger.info("-" * 55)

    matriz_costes = []  # una fila por repetición, una columna por punto de TIEMPOS

    for rep in range(N_REPETICIONES):
        logger.info("=== Repetición %d/%d: generando ciudad y pedidos nuevos ===", rep + 1, N_REPETICIONES)
        generador_ciudad.generar_ciudad_json()
        crear_db.NUM_PEDIDOS = NUM_PEDIDOS
        crear_db.inicializar_db()
        datos = crear_db.leer_pedidos()

        planificador = motor_ia.PlanificadorPDP(datos)
        fila_costes = []
        for t in TIEMPOS:
            start = time.time()
            _, coste = planificador.generar_plan(segundos_para_pensar=t, mostrar_grafico=False)
            elapsed = round(time.time() - start, 1)
            fila_costes.append(coste if coste else 0)
            logger.info("  rep %d  t=%4ds  ->  coste=%10s   (real: %ss)", rep + 1, t, f"{coste:,}", elapsed)
        matriz_costes.append(fila_costes)

    matriz_costes = np.array(matriz_costes, dtype=float)
    medias = matriz_costes.mean(axis=0)
    desviaciones = matriz_costes.std(axis=0)

    _guardar_resultados(matriz_costes, medias, desviaciones)
    _guardar_grafica(medias, desviaciones, NUM_PEDIDOS)

    return medias, desviaciones, matriz_costes


def _guardar_resultados(matriz_costes, medias, desviaciones):
    with open("experimento_multi_resultados.txt", "w", encoding="utf-8") as f:
        f.write(f"Benchmark multi-instancia -- {N_REPETICIONES} repeticiones, {NUM_PEDIDOS} pedidos, "
                f"{motor_ia.NUM_DRONES_FISICOS} drones\n")
        f.write(f"Tiempos (s): {TIEMPOS}\n\n")
        f.write("t(s)\tmedia\tdesv_std\tvalores_por_repeticion\n")
        for i, t in enumerate(TIEMPOS):
            valores = ", ".join(f"{v:.0f}" for v in matriz_costes[:, i])
            f.write(f"{t}\t{medias[i]:.1f}\t{desviaciones[i]:.1f}\t[{valores}]\n")
    logger.info("Resultados guardados en experimento_multi_resultados.txt")


def _guardar_grafica(medias, desviaciones, n_pedidos):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    fig.suptitle(
        f"Calidad de la Solución vs Tiempo de Cómputo (media de {N_REPETICIONES} instancias)\n"
        f"(PDP, {n_pedidos} pedidos, {motor_ia.NUM_DRONES_FISICOS} drones, GLS)",
        fontsize=13, fontweight="bold",
    )

    ax1.plot(TIEMPOS, medias, marker="o", linewidth=2,
              color="#2c7bb6", markerfacecolor="white", markeredgewidth=2, label="Media")
    ax1.fill_between(TIEMPOS, medias - desviaciones, medias + desviaciones,
                      alpha=0.2, color="#2c7bb6", label="±1 desviación típica")
    ax1.set_title(f"Coste medio ± desviación típica (n={N_REPETICIONES})")
    ax1.set_xlabel("Tiempo de cómputo (s)  [escala logarítmica]")
    ax1.set_ylabel("Coste total (m)")

    ax1.set_xscale("log")
    ax1.set_xticks(TIEMPOS)
    ax1.get_xaxis().set_major_formatter(ticker.ScalarFormatter())

    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax1.legend(loc="upper right", fontsize=9)

    indices_etiqueta = list(range(0, len(TIEMPOS), 2))
    for i in indices_etiqueta:
        ax1.annotate(
            f"{medias[i]:,.0f}",
            (TIEMPOS[i], medias[i]),
            textcoords="offset points", xytext=(0, 10),
            ha="center", fontsize=7, color="#333333",
        )

    plt.tight_layout()
    nombre = "experimento_benchmark_multi.png"
    plt.savefig(nombre, dpi=150, bbox_inches="tight")
    logger.info("Gráfica guardada como '%s'", nombre)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ejecutar_benchmark_multi()

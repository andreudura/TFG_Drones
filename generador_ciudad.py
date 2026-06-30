import json
import random


def generar_ciudad_json(manzanas_x=10, manzanas_z=10, tamano_edificio=20, separacion_interna=2, ancho_calle=15):
    ciudad = {"edificios": [], "azoteas": []}
    edificio_id = 0

    print("🏗️ Generando ciudad procedimental (Manzanas de 4 edificios)...")

    # Una manzana tendrá 2x2 = 4 edificios.
    edificios_por_manzana_lado = 2

    # El tamaño total de la manzana es la suma de los edificios que la componen
    # más el pequeño callejón/separación entre ellos.
    tamano_manzana = (tamano_edificio * edificios_por_manzana_lado) + (
                separacion_interna * (edificios_por_manzana_lado - 1))

    for mx in range(manzanas_x):
        for mz in range(manzanas_z):
            # 1. Calcular posición base de la MANZANA
            # Avanzamos el tamaño completo de la manzana MÁS el ancho de la carretera
            base_manzana_x = mx * (tamano_manzana + ancho_calle)
            base_manzana_z = mz * (tamano_manzana + ancho_calle)

            # 2. Generar los 4 edificios DENTRO de esta manzana
            for i in range(edificios_por_manzana_lado):
                for j in range(edificios_por_manzana_lado):
                    # Calcular posición del edificio respecto a la base de su manzana
                    offset_x = i * (tamano_edificio + separacion_interna)
                    offset_z = j * (tamano_edificio + separacion_interna)

                    pos_x = base_manzana_x + offset_x
                    pos_z = base_manzana_z + offset_z

                    # entre 20 y 100u — mínimo para que se vea algo, máximo para no
                    # pasarse de la altitud de vuelo fijada en 120u
                    altura = random.randint(20, 100)

                    edificio = {
                        "id": edificio_id,
                        "x": pos_x + (tamano_edificio / 2),  # Centro geométrico del edificio
                        "z": pos_z + (tamano_edificio / 2),
                        "ancho": tamano_edificio,
                        "largo": tamano_edificio,
                        "alto": altura
                    }
                    ciudad["edificios"].append(edificio)

                    # Guardamos la azotea
                    ciudad["azoteas"].append({
                        "edificio_id": edificio_id,
                        "x": edificio["x"],
                        "y": altura,
                        "z": edificio["z"]
                    })

                    edificio_id += 1

    # Exportar para Unity
    with open("ciudad.json", "w") as f:
        json.dump(ciudad, f, indent=4)

    # Calculamos el total de edificios generados
    total_edificios = manzanas_x * manzanas_z * (edificios_por_manzana_lado ** 2)
    print(f"✅ Ciudad generada con {total_edificios} edificios.")
    print(f"🛣️ Agrupados en {manzanas_x * manzanas_z} manzanas separadas por calles de {ancho_calle}m.")

    return ciudad["azoteas"]


if __name__ == "__main__":
    generar_ciudad_json()
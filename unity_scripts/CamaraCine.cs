using System.Collections;
using UnityEngine;

// Controla la cámara para grabar un vídeo de la simulación: va cambiando sola
// de un dron activo a otro cada pocos segundos, con un giro orbital suave
// alrededor de cada uno. Pensado para dejarlo corriendo en Play y grabar con
// OBS o el Recorder de Unity sin tener que mover la cámara a mano. Todo con
// Transform e interpolación, sin Cinemachine ni otros paquetes adicionales.
public class CamaraCine : MonoBehaviour {
    [Header("Primer plano de dron")]
    public float duracionPorDron = 10f;
    public float distancia = 18f;
    public float altura = 5f;
    public float velocidadOrbita = 10f; // grados/seg alrededor del dron

    [Header("Suavizado")]
    public float suavizadoOrbita = 4f;

    void Start() {
        StartCoroutine(CicloDePlanos());
    }

    IEnumerator CicloDePlanos() {
        while (true) {
            DronAgente objetivo = ElegirDronActivo();
            if (objetivo == null) {
                yield return new WaitForSeconds(1f); // aún no hay drones desplegados, reintenta
                continue;
            }
            yield return StartCoroutine(PrimerPlano(objetivo));
        }
    }

    DronAgente ElegirDronActivo() {
        DronAgente[] drones = FindObjectsByType<DronAgente>(FindObjectsSortMode.None);
        return drones.Length == 0 ? null : drones[Random.Range(0, drones.Length)];
    }

    IEnumerator PrimerPlano(DronAgente dron) {
        float angulo = Random.Range(0f, 360f);
        float t = 0f;
        bool primerFrame = true;

        while (t < duracionPorDron && dron != null) {
            t += Time.deltaTime;
            angulo += velocidadOrbita * Time.deltaTime;

            Vector3 centro = dron.transform.position;
            Vector3 offset = Quaternion.Euler(0, angulo, 0) * new Vector3(0, altura, -distancia);
            Vector3 posDeseada = centro + offset;
            Quaternion rotDeseada = Quaternion.LookRotation(centro - posDeseada);

            if (primerFrame) {
                // Corte directo al empezar cada dron (sensación de cambio de cámara).
                transform.position = posDeseada;
                transform.rotation = rotDeseada;
                primerFrame = false;
            } else {
                transform.position = Vector3.Lerp(transform.position, posDeseada, suavizadoOrbita * Time.deltaTime);
                transform.rotation = Quaternion.Slerp(transform.rotation, rotDeseada, suavizadoOrbita * Time.deltaTime);
            }

            yield return null;
        }
    }
}

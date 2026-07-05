using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class PasoDron {
    public string estado;
    public float x, y, z;
    public string accion; // Nuevo campo
    public bool cargado; // true entre la recogida y la entrega de un paquete
}

public class DronAgente : MonoBehaviour {
    private int miId;
    public float velocidadVuelo = 80f;
    public float velocidadDescenso = 30f;
    private bool misionCompletada = false;
    private Color colorOriginal; // Para recuperar el color tras recargar
    private GameObject cajaCarga; // caja visible bajo el dron mientras lleva un paquete
    public float alturaSobreSuperficie = 1.3f; // desde el pivote (centro) hasta el punto más bajo del dron

    public void ConfigurarDron(int id) {
        miId = id;
        colorOriginal = Random.ColorHSV();
        GetComponent<MeshRenderer>().material.color = colorOriginal;
        ConstruirEstructuraDron();
        StartCoroutine(PedirSiguientePunto());
    }

    // Añade brazos, rotores y la caja de carga como hijos del cuerpo (la cápsula
    // original), todo con primitivas de Unity para no depender de modelos externos.
    void ConstruirEstructuraDron() {
        Vector3[] direcciones = {
            new Vector3(1, 0, 1).normalized,  new Vector3(1, 0, -1).normalized,
            new Vector3(-1, 0, 1).normalized, new Vector3(-1, 0, -1).normalized
        };

        foreach (Vector3 dir in direcciones) {
            GameObject brazo = GameObject.CreatePrimitive(PrimitiveType.Cube);
            brazo.name = "Brazo";
            brazo.transform.parent = transform;
            brazo.transform.localPosition = dir * 0.45f;
            brazo.transform.localRotation = Quaternion.LookRotation(dir);
            brazo.transform.localScale = new Vector3(0.12f, 0.08f, 0.8f);
            Destroy(brazo.GetComponent<Collider>());
            brazo.GetComponent<MeshRenderer>().material.color = new Color(0.15f, 0.15f, 0.15f);

            GameObject rotor = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            rotor.name = "Rotor";
            rotor.transform.parent = transform;
            rotor.transform.localPosition = dir * 0.85f + Vector3.up * 0.08f;
            rotor.transform.localScale = new Vector3(0.45f, 0.02f, 0.45f);
            Destroy(rotor.GetComponent<Collider>());
            rotor.GetComponent<MeshRenderer>().material.color = new Color(0.05f, 0.05f, 0.05f);
        }

        cajaCarga = GameObject.CreatePrimitive(PrimitiveType.Cube);
        cajaCarga.name = "CajaCarga";
        cajaCarga.transform.parent = transform;
        cajaCarga.transform.localPosition = new Vector3(0, -1.15f, 0);
        cajaCarga.transform.localScale = new Vector3(0.4f, 0.3f, 0.4f);
        Destroy(cajaCarga.GetComponent<Collider>());
        cajaCarga.GetComponent<MeshRenderer>().material.color = new Color(0.55f, 0.38f, 0.2f); // carton
        cajaCarga.SetActive(false);
    }

    IEnumerator PedirSiguientePunto() {
        if (misionCompletada) yield break;

        UnityWebRequest request = UnityWebRequest.Get($"http://127.0.0.1:8000/dron/{miId}/siguiente-paso");
        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success) {
            PasoDron paso = JsonUtility.FromJson<PasoDron>(request.downloadHandler.text);
            if (paso.estado == "completado") {
                misionCompletada = true;
                Debug.Log($"🏁 Dron {miId} ha finalizado su jornada.");
            } else {
                if (cajaCarga != null) cajaCarga.SetActive(paso.cargado);
                // Se suma alturaSobreSuperficie porque el servidor manda la altura de la
                // azotea/suelo (una superficie), pero la posición del dron es el centro de
                // su cuerpo: sin este ajuste la mitad inferior (y la caja de carga) quedan
                // por debajo de esa superficie.
                Vector3 destino = new Vector3(paso.x, paso.y + alturaSobreSuperficie, paso.z);
                StartCoroutine(MoverHaciaDestino(destino, paso.accion));
            }
        } else {
            yield return new WaitForSeconds(2f);
            StartCoroutine(PedirSiguientePunto());
        }
    }

    IEnumerator MoverHaciaDestino(Vector3 destino, string accionActual) {
        bool esVertical = Mathf.Abs(destino.x - transform.position.x) < 0.1f && Mathf.Abs(destino.z - transform.position.z) < 0.1f;
        float vel = esVertical ? velocidadDescenso : velocidadVuelo;

        // Solo se gira en el plano horizontal (yaw). Usar la dirección 3D completa
        // aquí giraría también en pitch/roll, y con un desvío residual del paso
        // anterior una subida o bajada casi vertical podía quedar mal definida y
        // el dron giraba de lado. Así el cuerpo se mantiene siempre nivelado.
        Vector3 direccionHorizontal = new Vector3(destino.x - transform.position.x, 0, destino.z - transform.position.z);
        if (direccionHorizontal.sqrMagnitude > 0.01f)
            transform.rotation = Quaternion.LookRotation(direccionHorizontal);

        while (Vector3.Distance(transform.position, destino) > 0.5f) {
            transform.position = Vector3.MoveTowards(transform.position, destino, vel * Time.deltaTime);
            yield return null;
        }
        transform.position = destino; // encaje exacto: evita arrastrar un desvío al siguiente paso

        // --- SIMULACIÓN DE ACCIONES EN TIERRA ---
        if (esVertical && transform.position.y < 110f) {
            if (accionActual == "recargar") {
                Debug.Log($"🔋 Dron {miId} ha vuelto a la base. Recargando batería...");
                GetComponent<MeshRenderer>().material.color = Color.yellow; // Alerta visual
                
                yield return new WaitForSeconds(5.0f); // Tarda 5 segundos en recargar
                
                GetComponent<MeshRenderer>().material.color = colorOriginal;
                Debug.Log($"✅ Dron {miId} listo para la siguiente ruta.");
                
            } else if (accionActual == "maniobra") {
                yield return new WaitForSeconds(1.5f); // Recogiendo/Entregando paquete
            }
        }

        StartCoroutine(PedirSiguientePunto());
    }
}
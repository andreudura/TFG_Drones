using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class PasoDron { 
    public string estado; 
    public float x, y, z; 
    public string accion; // Nuevo campo
}

public class DronAgente : MonoBehaviour {
    private int miId;
    public float velocidadVuelo = 80f;
    public float velocidadDescenso = 30f;
    private bool misionCompletada = false;
    private Color colorOriginal; // Para recuperar el color tras recargar

    public void ConfigurarDron(int id) {
        miId = id;
        colorOriginal = Random.ColorHSV();
        GetComponent<MeshRenderer>().material.color = colorOriginal;
        StartCoroutine(PedirSiguientePunto());
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
                StartCoroutine(MoverHaciaDestino(new Vector3(paso.x, paso.y, paso.z), paso.accion));
            }
        } else {
            yield return new WaitForSeconds(2f); 
            StartCoroutine(PedirSiguientePunto());
        }
    }

    IEnumerator MoverHaciaDestino(Vector3 destino, string accionActual) {
        bool esVertical = Mathf.Abs(destino.x - transform.position.x) < 0.1f && Mathf.Abs(destino.z - transform.position.z) < 0.1f;
        float vel = esVertical ? velocidadDescenso : velocidadVuelo;

        if (!esVertical && destino != transform.position)
            transform.rotation = Quaternion.LookRotation(destino - transform.position);

        while (Vector3.Distance(transform.position, destino) > 0.5f) {
            transform.position = Vector3.MoveTowards(transform.position, destino, vel * Time.deltaTime);
            yield return null; 
        }
        
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
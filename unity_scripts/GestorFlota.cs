using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

[System.Serializable]
public class RespuestaInicio {
    public string status;
    public List<int> drones_activos;
}

public class GestorFlota : MonoBehaviour {
    public GameObject prefabDron; // Asigna tu Prefab de Dron aquí
    private string urlInicio = "http://127.0.0.1:8000/iniciar-simulacion";

    void Start() {
        StartCoroutine(IniciarSimulacionGlobal());
    }

    IEnumerator IniciarSimulacionGlobal() {
        Debug.Log("📡 Solicitando a Python el inicio de la simulación...");

        UnityWebRequest request = new UnityWebRequest(urlInicio, "POST");
        request.downloadHandler = new DownloadHandlerBuffer();
        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success) {
            RespuestaInicio respuesta = JsonUtility.FromJson<RespuestaInicio>(request.downloadHandler.text);

            Debug.Log($"✅ Plan recibido. Desplegando {respuesta.drones_activos.Count} drones.");

            foreach (int dronId in respuesta.drones_activos) {
                // Instanciamos en el "depósito" (0,0,0 por ahora)
                GameObject nuevoDron = Instantiate(prefabDron, Vector3.zero, Quaternion.identity);
                nuevoDron.name = "Dron_" + dronId;

                DronAgente agente = nuevoDron.GetComponent<DronAgente>();
                if (agente != null) {
                    agente.ConfigurarDron(dronId);
                } else {
                    Debug.LogError("El Prefab no tiene el script DronAgente.");
                }
            }
        } else {
            Debug.LogError("❌ Error conectando con la API: " + request.error);
        }
    }
}
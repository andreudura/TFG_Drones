using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public class EdificioData {
    public int id;
    public float x;
    public float z;
    public float ancho;
    public float largo;
    public float alto;
    public int material_id;
}

[System.Serializable]
public class CiudadData {
    public List<EdificioData> edificios;
}

public class CityBuilder : MonoBehaviour {
    public Material[] misMateriales;

    void Start() {
        TextAsset jsonFile = Resources.Load<TextAsset>("ciudad");
        if (jsonFile == null) {
            Debug.LogError("No se encontró 'ciudad.json' en la carpeta Resources.");
            return;
        }

        CiudadData ciudad = JsonUtility.FromJson<CiudadData>(jsonFile.text);
        GameObject cityParent = new GameObject("CiudadGenerada");

        foreach (EdificioData edif in ciudad.edificios) {
            GameObject cubo = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cubo.transform.parent = cityParent.transform;
            cubo.transform.position = new Vector3(edif.x, edif.alto / 2f, edif.z);
            cubo.transform.localScale = new Vector3(edif.ancho, edif.alto, edif.largo);

            if (misMateriales.Length > 0) {
                int index = Mathf.Clamp(edif.material_id, 0, misMateriales.Length - 1);
                cubo.GetComponent<MeshRenderer>().material = misMateriales[index];
            }

            // Remate de azotea: un reborde oscuro y fino que rompe la silueta de caja
            // lisa. Se coloca como hermano del cubo (no como hijo) para no heredar su
            // escala no uniforme.
            GameObject remate = GameObject.CreatePrimitive(PrimitiveType.Cube);
            remate.name = "Remate";
            remate.transform.parent = cityParent.transform;
            remate.transform.position = new Vector3(edif.x, edif.alto + 0.4f, edif.z);
            remate.transform.localScale = new Vector3(edif.ancho * 1.03f, 0.8f, edif.largo * 1.03f);
            Destroy(remate.GetComponent<Collider>());
            remate.GetComponent<MeshRenderer>().material.color = new Color(0.2f, 0.2f, 0.2f);
        }
        Debug.Log("🏢 Ciudad generada con éxito.");
    }
}
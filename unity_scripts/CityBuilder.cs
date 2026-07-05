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
        }
        Debug.Log("🏢 Ciudad generada con éxito.");
    }
}
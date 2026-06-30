using System.Collections.Generic;
using UnityEngine;

// Clases para parsear el JSON
[System.Serializable]
public class EdificioData {
    public int id;
    public float x;
    public float z;
    public float ancho;
    public float largo;
    public float alto;
}

[System.Serializable]
public class CiudadData {
    public List<EdificioData> edificios;
}

public class CityBuilder : MonoBehaviour
{
    public Material materialEdificio; // Asigna un material desde el inspector si quieres color

    void Start()
    {
        ConstruirCiudad();
    }

    void ConstruirCiudad()
    {
        // 1. Cargar el JSON desde la carpeta Resources
        TextAsset jsonFile = Resources.Load<TextAsset>("ciudad");
        if (jsonFile == null) {
            Debug.LogError("No se encontró ciudad.json en la carpeta Resources");
            return;
        }

        // 2. Parsear el JSON
        CiudadData ciudad = JsonUtility.FromJson<CiudadData>(jsonFile.text);

        // 3. Crear los edificios
        GameObject cityParent = new GameObject("EdificiosProcedimentales");

        foreach (EdificioData edif in ciudad.edificios)
        {
            // Crear un cubo primitivo
            GameObject cubo = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cubo.name = "Edificio_" + edif.id;
            cubo.transform.parent = cityParent.transform;

            // En Unity, la posición "Y" de un cubo está en su centro geométrico.
            // Para que la base del edificio toque el suelo (Y=0), elevamos su posición a la mitad de su altura.
            cubo.transform.position = new Vector3(edif.x, edif.alto / 2f, edif.z);

            // Escalar el cubo al tamaño correcto
            cubo.transform.localScale = new Vector3(edif.ancho, edif.alto, edif.largo);

            if (materialEdificio != null) {
                cubo.GetComponent<MeshRenderer>().material = materialEdificio;
            }
        }

        Debug.Log($"Se generaron {ciudad.edificios.Count} edificios exitosamente.");
    }
}
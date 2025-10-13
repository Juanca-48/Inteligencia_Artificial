using UnityEngine;

public class CameraFollow : MonoBehaviour
{
    [Header("Target")]
    public Transform target; // El jugador
    
    [Header("Follow Settings")]
    public Vector3 offset = new Vector3(0, 0, -10); // Offset de la cámara
    public float smoothSpeed = 5f; // Velocidad de seguimiento (0 = instantáneo, mayor = más suave)
    public bool followX = true;
    public bool followY = true;
    
    void LateUpdate()
    {
        if (target == null) return;
        
        // Calcular posición deseada
        Vector3 desiredPosition = target.position + offset;
        
        // Aplicar restricciones de ejes
        if (!followX) desiredPosition.x = transform.position.x;
        if (!followY) desiredPosition.y = transform.position.y;
        
        // Seguimiento suave
        if (smoothSpeed > 0)
        {
            Vector3 smoothedPosition = Vector3.Lerp(transform.position, desiredPosition, smoothSpeed * Time.deltaTime);
            transform.position = smoothedPosition;
        }
        else
        {
            // Seguimiento instantáneo
            transform.position = desiredPosition;
        }
    }
}
using UnityEngine;

public class PlayerRotationAnimator : MonoBehaviour
{
    [Header("Rotation Settings")]
    public Transform visualTransform;
    
    [Header("Rotation Speed")]
    public float rotationSpeed = 90f;
    
    [Header("Smoothing")]
    public bool smoothRotation = true;
    public float rotationSmoothness = 10f;
    
    [Header("Landing Snap")]
    public bool snapOnLanding = true;
    public float snapSpeed = 15f;
    
    private bool isInAir = false;
    private bool isSnapping = false;
    private float snapTargetRotation = 0f;
    private float snapTimer = 0f;
    private const float maxSnapDuration = 0.5f; // Máximo medio segundo para completar snap
    
    private PlayerController playerController;
    
    void Start()
    {
        playerController = GetComponent<PlayerController>();
        
        playerController.OnJumpStarted += HandleJumpStart;
        playerController.OnLanded += HandleLanding;
        
        if (visualTransform == null)
        {
            Debug.LogWarning("Visual Transform not assigned! Using self.");
            visualTransform = transform;
        }
        
        // IMPORTANTE: Forzar rotación inicial a 0°
        visualTransform.rotation = Quaternion.Euler(0, 0, 0);
        Debug.Log("🎮 Rotación inicial establecida a 0°");
    }
    
    void Update()
    {
        if (isSnapping)
        {
            snapTimer += Time.deltaTime;
            
            // Interpolar directamente hacia el objetivo
            float currentZ = visualTransform.eulerAngles.z;
            float newZ = Mathf.LerpAngle(currentZ, snapTargetRotation, snapSpeed * Time.deltaTime);
            
            visualTransform.rotation = Quaternion.Euler(0, 0, newZ);
            
            // Verificar si llegamos al objetivo O si ya pasó mucho tiempo
            float diff = Mathf.Abs(Mathf.DeltaAngle(newZ, snapTargetRotation));
            
            if (diff < 2f || snapTimer >= maxSnapDuration)
            {
                // Forzar la rotación exacta y terminar
                visualTransform.rotation = Quaternion.Euler(0, 0, snapTargetRotation);
                isSnapping = false;
                snapTimer = 0f;
                Debug.Log($"✅ Snap completado en {snapTargetRotation}° (diff: {diff:F2}°)");
            }
        }
        else if (isInAir)
        {
            // Rotar continuamente mientras está en el aire (subiendo Y bajando)
            float currentZ = visualTransform.eulerAngles.z;
            float newZ = currentZ + (rotationSpeed * Time.deltaTime);
            
            visualTransform.rotation = Quaternion.Euler(0, 0, newZ);
        }
        // Si no está en el aire ni haciendo snap: quieto
    }
    
    void HandleJumpStart()
    {
        isInAir = true;
        isSnapping = false;
        Debug.Log("Salto iniciado - rotación activada");
    }
    
    void HandleLanding()
    {
        // NO desactivar isInAir aquí, el snap lo hará cuando termine
        
        if (snapOnLanding)
        {
            // Capturar la rotación actual
            float currentZ = visualTransform.eulerAngles.z;
            
            // Normalizar a 0-360
            currentZ = currentZ % 360f;
            if (currentZ < 0) currentZ += 360f;
            
            // Determinar dirección de rotación
            bool rotatingBackward = rotationSpeed < 0;
            
            float nextQuarter;
            
            if (rotatingBackward)
            {
                // Rotación negativa: ir al múltiplo de 90° ANTERIOR (menor)
                float remainder = currentZ % 90f;
                
                if (remainder < 1f) // Ya está casi en un múltiplo de 90
                {
                    nextQuarter = currentZ - remainder - 90f;
                }
                else
                {
                    nextQuarter = currentZ - remainder;
                }
                
                // Normalizar (manejar valores negativos)
                if (nextQuarter < 0) nextQuarter += 360f;
            }
            else
            {
                // Rotación positiva: ir al múltiplo de 90° SIGUIENTE (mayor)
                float remainder = currentZ % 90f;
                
                if (remainder < 1f)
                {
                    nextQuarter = currentZ - remainder + 90f;
                }
                else
                {
                    nextQuarter = currentZ - remainder + 90f;
                }
                
                nextQuarter = nextQuarter % 360f;
            }
            
            snapTargetRotation = nextQuarter;
            snapTimer = 0f;
            isSnapping = true;
            isInAir = false; // Desactivar DESPUÉS de configurar el snap
            
            Debug.Log($"🎯 Aterrizaje: {currentZ:F1}° → {nextQuarter:F1}° (dirección: {(rotatingBackward ? "⬅️ atrás" : "➡️ adelante")})");
        }
        else
        {
            isInAir = false;
        }
    }
    
    void OnDestroy()
    {
        if (playerController != null)
        {
            playerController.OnJumpStarted -= HandleJumpStart;
            playerController.OnLanded -= HandleLanding;
        }
    }
}
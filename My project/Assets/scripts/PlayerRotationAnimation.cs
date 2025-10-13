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
    
    private bool isSnapping = false;
    private bool wasInAirLastFrame = false;
    private float snapTargetRotation = 0f;
    private float snapTimer = 0f;
    private const float maxSnapDuration = 0.5f;
    
    private PlayerController playerController;
    private Rigidbody2D rb;
    
    void Start()
    {
        playerController = GetComponent<PlayerController>();
        rb = GetComponent<Rigidbody2D>();
        
        playerController.OnJumpStarted += HandleJumpStart;
        playerController.OnLanded += HandleLanding;
        
        if (visualTransform == null)
        {
            Debug.LogWarning("Visual Transform not assigned! Using self.");
            visualTransform = transform;
        }
        
        // Forzar rotación inicial a 0°
        visualTransform.rotation = Quaternion.Euler(0, 0, 0);
        Debug.Log("🎮 Rotación inicial establecida a 0°");
    }
    
    void Update()
    {
        // Detectar si está en el aire (verificando velocidad vertical del Rigidbody)
        bool isInAir = rb.linearVelocity.y != 0;
        
        // Detectar cuando aterriza (estaba en el aire, ahora no)
        if (wasInAirLastFrame && !isInAir && !isSnapping)
        {
            ActivateSnap();
        }
        
        wasInAirLastFrame = isInAir;
        
        if (isSnapping)
        {
            snapTimer += Time.deltaTime;
            
            // Interpolar hacia el objetivo
            float currentZ = visualTransform.eulerAngles.z;
            float newZ = Mathf.LerpAngle(currentZ, snapTargetRotation, snapSpeed * Time.deltaTime);
            
            visualTransform.rotation = Quaternion.Euler(0, 0, newZ);
            
            // Verificar si llegamos al objetivo O si pasó mucho tiempo
            float diff = Mathf.Abs(Mathf.DeltaAngle(newZ, snapTargetRotation));
            
            if (diff < 2f || snapTimer >= maxSnapDuration)
            {
                // Forzar rotación exacta y terminar snap
                visualTransform.rotation = Quaternion.Euler(0, 0, snapTargetRotation);
                isSnapping = false;
                snapTimer = 0f;
                Debug.Log($"✅ Snap completado en {snapTargetRotation}°");
            }
        }
        else if (isInAir)
        {
            // Rotar continuamente mientras está en el aire (cayendo o subiendo)
            float currentZ = visualTransform.eulerAngles.z;
            float newZ = currentZ + (rotationSpeed * Time.deltaTime);
            
            visualTransform.rotation = Quaternion.Euler(0, 0, newZ);
        }
    }
    
    void HandleJumpStart()
    {
        Debug.Log("🚀 Salto iniciado");
    }
    
    void HandleLanding()
    {
        Debug.Log("🎯 Landing detectado desde evento");
    }
    
    void ActivateSnap()
    {
        if (!snapOnLanding) return;
        
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
            
            if (remainder < 1f)
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
        
        Debug.Log($"📍 Snap activado: {currentZ:F1}° → {nextQuarter:F1}°");
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
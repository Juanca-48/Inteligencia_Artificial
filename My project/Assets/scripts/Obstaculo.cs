using UnityEngine;

public class Obstacle : MonoBehaviour
{
    [Header("Game Over Settings")]
    public bool destroyPlayer = true;
    public float pauseDelay = 0.5f; // Pequeño delay antes de pausar
    
    private void OnTriggerEnter2D(Collider2D other)
    {
        // Verificar si colisionó con el jugador
        if (other.CompareTag("Player"))
        {
            Debug.Log("💥 COLISIÓN CON OBSTÁCULO - Game Over");
            HandleGameOver(other.gameObject);
        }
    }
    
    private void OnCollisionEnter2D(Collision2D collision)
    {
        // También detectar por colisión física (por si no usas trigger)
        if (collision.gameObject.CompareTag("Player"))
        {
            Debug.Log("💥 COLISIÓN CON OBSTÁCULO - Game Over");
            HandleGameOver(collision.gameObject);
        }
    }
    
    private void HandleGameOver(GameObject player)
    {
        // Destruir el jugador si está configurado
        if (destroyPlayer)
        {
            Destroy(player);
        }
        
        // Pausar el juego después del delay
        Invoke(nameof(StopGame), pauseDelay);
    }
    
    private void StopGame()
    {
        // Detener el tiempo del juego
        Time.timeScale = 0f;
        Debug.Log("⏸️ JUEGO DETENIDO");
        
        // Aquí puedes agregar más lógica como:
        // - Mostrar pantalla de Game Over
        // - Guardar puntuación
        // - Activar UI de reinicio
    }
}
using UnityEngine;
using UnityEngine.SceneManagement;

public class Goal : MonoBehaviour
{
    [Header("Goal Settings")]
    public bool stopPlayerOnReach = true;
    public float celebrationDelay = 1f; // Tiempo antes de pausar
    
    private bool goalReached = false;
    
    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player") && !goalReached)
        {
            goalReached = true;
            Debug.Log("🏁 ¡META ALCANZADA! - Level Complete");
            HandleGoalReached(other.gameObject);
        }
    }
    
    private void HandleGoalReached(GameObject player)
    {
        // Detener al jugador si está configurado
        if (stopPlayerOnReach)
        {
            Rigidbody2D rb = player.GetComponent<Rigidbody2D>();
            if (rb != null)
            {
                rb.linearVelocity = Vector2.zero;
            }
            
            // Desactivar el controlador del jugador
            PlayerController controller = player.GetComponent<PlayerController>();
            if (controller != null)
            {
                controller.enabled = false;
            }
        }
        
        // Ejecutar acciones después del delay
        Invoke(nameof(CompleteLevel), celebrationDelay);
    }
    
    private void CompleteLevel()
    {
        Debug.Log("✅ NIVEL COMPLETADO");
        Debug.Log("🎉 ¡GANASTE! Presiona R para reiniciar o ESC para salir");
        
        // Pausar el juego
        Time.timeScale = 0f;
    }
    
    private void Update()
    {
        // Solo permitir controles si se alcanzó la meta
        if (goalReached)
        {
            // Reiniciar nivel con R
            if (Input.GetKeyDown(KeyCode.R))
            {
                RestartLevel();
            }
            
            // Salir del juego con ESC
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                QuitGame();
            }
        }
    }
    
    private void RestartLevel()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene(SceneManager.GetActiveScene().name);
        Debug.Log("🔄 Reiniciando nivel...");
    }
    
    private void QuitGame()
    {
        Debug.Log("👋 Saliendo del juego...");
        
        #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
        #else
            Application.Quit();
        #endif
    }
}
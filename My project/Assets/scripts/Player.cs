using UnityEngine;
using UnityEngine.InputSystem;

public class PlayerController : MonoBehaviour
{
    [Header("Movement")]
    public float moveSpeed = 0.5f;
    public float maxJumpHeight = 1.5f;
    
    private bool isGrounded = false;
    private Rigidbody2D rb;
    private float jumpStartY;
    
    // Eventos
    public System.Action OnJumpStarted;
    public System.Action OnLanded;
    
    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        
        // IMPORTANTE: Estas configuraciones reducen la vibración
        rb.interpolation = RigidbodyInterpolation2D.Interpolate;
        rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
        rb.constraints = RigidbodyConstraints2D.FreezeRotation;
    }

    void FixedUpdate()
    {
        // Mantener velocidad horizontal constante
        rb.linearVelocity = new Vector2(moveSpeed, rb.linearVelocity.y);

        // Limitar altura del salto
        if (transform.position.y >= jumpStartY + maxJumpHeight && rb.linearVelocity.y > 0)
        {
            rb.linearVelocity = new Vector2(rb.linearVelocity.x, 0);
        }
    }

    public void OnJump(InputAction.CallbackContext context)
    {
        if (context.performed && isGrounded)
        {
            jumpStartY = transform.position.y;
            
            float jumpForce = Mathf.Sqrt(2f * maxJumpHeight * Mathf.Abs(Physics2D.gravity.y) * rb.gravityScale);
            rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce);
            
            OnJumpStarted?.Invoke();
            
            Debug.Log("✅ JUMP EXECUTED");
        }
        else if (context.performed)
        {
            Debug.Log("❌ JUMP FAILED - Not grounded");
        }
    }
    
    void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Ground"))
        {
            isGrounded = true;
            Debug.Log("🟢 Tocó el suelo - isGrounded = true");
            OnLanded?.Invoke();
        }
    }
    
    void OnCollisionExit2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Ground"))
        {
            isGrounded = false;
            Debug.Log("🔴 Dejó el suelo - isGrounded = false");
        }
    }
}
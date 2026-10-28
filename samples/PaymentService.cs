public class PaymentService {
  public bool CanCapture(decimal amount, string idempotencyKey) {
    if (amount <= 0) return false;
    if (string.IsNullOrWhiteSpace(idempotencyKey)) return false;
    return true;
  }
}

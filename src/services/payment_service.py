import os
import razorpay
from typing import Dict, Any, Optional

class PaymentService:
    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        if not self.key_id or not self.key_secret:
            self.client = None
        else:
            self.client = razorpay.Client(auth=(self.key_id, self.key_secret))

    def is_configured(self) -> bool:
        return self.client is not None

    def create_razorpay_order(self, amount_in_rupees: float, receipt_id: str) -> Dict[str, Any]:
        """Creates a Razorpay Order and returns the order details."""
        amount_in_paise = int(amount_in_rupees * 100)
        
        if not self.is_configured():
            # Mock order ID for sandbox / testing when credentials are empty
            import uuid
            mock_id = f"order_mock_{uuid.uuid4().hex[:12]}"
            return {
                "id": mock_id,
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": receipt_id,
                "status": "created",
                "mock": True
            }

        try:
            order_data = {
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": receipt_id,
                "payment_capture": 1 # Auto capture payment
            }
            order = self.client.order.create(data=order_data)
            return order
        except Exception as e:
            raise RuntimeError(f"Razorpay order creation failed: {e}")

    def verify_payment_signature(self, razorpay_order_id: str, razorpay_payment_id: str, 
                                 razorpay_signature: str) -> bool:
        """Verifies the authenticity of Razorpay signature on payment completion."""
        if not self.is_configured():
            # If mock order, signature verification is mocked to True
            if razorpay_order_id.startswith("order_mock_"):
                return True
            return False

        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            self.client.utility.verify_payment_signature(params_dict)
            return True
        except razorpay.errors.SignatureVerificationError:
            print("[Razorpay] Signature verification failed.")
            return False
        except Exception as e:
            print(f"[Razorpay] Error verifying signature: {e}")
            return False

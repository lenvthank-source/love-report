import os
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from jose import jwt

class SupabaseService:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")  # Service role key is preferred for backend CRUD
        self.jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

        if not self.url or not self.key:
            # Fallbacks or dummy modes for testing without env setup
            self.client = None
        else:
            self.client: Client = create_client(self.url, self.key)

    def is_configured(self) -> bool:
        return self.client is not None

    def check_connection(self) -> bool:
        """Verifies if the Supabase client is configured and can query the database successfully."""
        if not self.is_configured():
            return False
        try:
            # Query a single row from customers table to verify read connection
            self.client.table("customers").select("id").limit(1).execute()
            return True
        except Exception as e:
            print(f"[Supabase] Connection health check failed: {e}")
            return False

    # --- Auth Helper ---
    def verify_admin_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes and verifies a Supabase Auth JWT token using the local project JWT Secret.
        Returns the decoded user payload or None if invalid.
        """
        if not self.jwt_secret:
            # If secret is missing, return a dummy user for local development
            return {"email": "admin@test.com", "role": "authenticated"}
        try:
            # Supabase tokens are HS256 and contain "authenticated" audience
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=["HS256"], 
                options={"verify_aud": False}
            )
            return payload
        except Exception as e:
            print(f"[SupabaseAuth] Token verification failed: {e}")
            return None

    # --- Customer CRUD ---
    def get_or_create_customer(self, full_name: str, email: str, mobile: str) -> str:
        """Finds an existing customer by email, or creates a new one. Returns customer UUID."""
        if not self.is_configured():
            return "dummy-customer-uuid"
        
        # Check existing
        res = self.client.table("customers").select("id").eq("email", email.strip().lower()).execute()
        if res.data:
            return res.data[0]["id"]

        # Insert new
        res = self.client.table("customers").insert({
            "full_name": full_name.strip(),
            "email": email.strip().lower(),
            "mobile": mobile.strip()
        }).execute()
        return res.data[0]["id"]

    # --- Order CRUD ---
    def create_order(self, customer_id: str, dob: str, tob: str, place: str, 
                     lat: float, lng: float, tz: str, geocoded_place: Dict[str, Any]) -> str:
        """Inserts a new pending order and returns the order UUID."""
        if not self.is_configured():
            return "dummy-order-uuid"

        res = self.client.table("orders").insert({
            "customer_id": customer_id,
            "dob": dob,
            "tob": tob,
            "place": place,
            "latitude": lat,
            "longitude": lng,
            "timezone": tz,
            "geocoded_place": geocoded_place,
            "order_status": "pending",
            "report_status": "not_started"
        }).execute()
        return res.data[0]["id"]

    def update_order_status(self, order_id: str, order_status: str, report_status: Optional[str] = None) -> bool:
        if not self.is_configured():
            return True
        update_data = {"order_status": order_status, "updated_at": "now()"}
        if report_status:
            update_data["report_status"] = report_status
        res = self.client.table("orders").update(update_data).eq("id", order_id).execute()
        return len(res.data) > 0

    def update_order_report(self, order_id: str, report_url: str) -> bool:
        if not self.is_configured():
            return True
        res = self.client.table("orders").update({
            "report_url": report_url,
            "report_status": "completed",
            "order_status": "processing", # transitioning to processing until admin delivers it
            "updated_at": "now()"
        }).eq("id", order_id).execute()
        return len(res.data) > 0

    def save_admin_notes(self, order_id: str, notes: str) -> bool:
        if not self.is_configured():
            return True
        res = self.client.table("orders").update({
            "notes": notes,
            "updated_at": "now()"
        }).eq("id", order_id).execute()
        return len(res.data) > 0

    def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        if not self.is_configured():
            return None
        res = self.client.table("orders").select("*, customers(*)").eq("id", order_id).execute()
        return res.data[0] if res.data else None

    def get_order_by_rz_id(self, rz_order_id: str) -> Optional[Dict[str, Any]]:
        """Resolves the internal order UUID and customer details from a Razorpay Order ID."""
        if not self.is_configured():
            return None
        # 1. Look up payment record
        pay_res = self.client.table("payments").select("order_id").eq("razorpay_order_id", rz_order_id).execute()
        if not pay_res.data:
            return None
        order_id = pay_res.data[0]["order_id"]
        # 2. Return order detail
        return self.get_order_by_id(order_id)

    def get_orders(self, status: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return []
        
        query = self.client.table("orders").select("*, customers(*)")
        
        if status:
            query = query.eq("order_status", status)
            
        res = query.order("created_at", desc=True).execute()
        orders = res.data or []
        
        if search:
            # Local filtering for joined customer fields to support complex contains
            s = search.strip().lower()
            filtered = []
            for o in orders:
                cust = o.get("customers") or {}
                if (s in o["id"].lower() or 
                    s in cust.get("full_name", "").lower() or 
                    s in cust.get("email", "").lower() or 
                    s in cust.get("mobile", "").lower()):
                    filtered.append(o)
            return filtered
            
        return orders

    # --- Payment Logging ---
    def create_payment(self, order_id: str, razorpay_order_id: str, amount: float = 499.00) -> str:
        if not self.is_configured():
            return "dummy-payment-uuid"
        res = self.client.table("payments").insert({
            "order_id": order_id,
            "amount": amount,
            "razorpay_order_id": razorpay_order_id,
            "payment_status": "created"
        }).execute()
        return res.data[0]["id"]

    def confirm_payment(self, razorpay_order_id: str, razorpay_payment_id: str, raw_response: Dict[str, Any]) -> bool:
        if not self.is_configured():
            return True
        res = self.client.table("payments").update({
            "razorpay_payment_id": razorpay_payment_id,
            "payment_status": "captured",
            "paid_at": "now()",
            "raw_response": raw_response
        }).eq("razorpay_order_id", razorpay_order_id).execute()
        return len(res.data) > 0

    # --- Email Log ---
    def log_email(self, order_id: str, template_name: str, recipient: str, status: str, error: Optional[str] = None):
        if not self.is_configured():
            return
        self.client.table("email_logs").insert({
            "order_id": order_id,
            "template_name": template_name,
            "recipient_email": recipient,
            "status": status,
            "error_message": error
        }).execute()

    def get_email_logs(self, order_id: str) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return []
        res = self.client.table("email_logs").select("*").eq("order_id", order_id).order("sent_at", desc=True).execute()
        return res.data or []

    # --- Supabase Storage PDF Upload ---
    def upload_pdf_report(self, order_id: str, local_pdf_path: str) -> Optional[str]:
        """Uploads a PDF file to Supabase 'reports' storage bucket. Returns public URL."""
        if not self.is_configured():
            return f"https://mock-supabase.com/reports/{order_id}.pdf"
        
        bucket_name = "reports"
        filename = f"{order_id}_report.pdf"
        
        try:
            with open(local_pdf_path, 'rb') as f:
                file_data = f.read()
                
            # Attempt uploading to Supabase Storage
            # Note: client.storage.from_(bucket).upload(path, file)
            self.client.storage.from_(bucket_name).upload(
                path=filename,
                file=file_data,
                file_options={"content-type": "application/pdf", "x-upsert": "true"}
            )
            
            # Retrieve public URL
            public_url_res = self.client.storage.from_(bucket_name).get_public_url(filename)
            return public_url_res
        except Exception as e:
            print(f"[SupabaseStorage] Failed to upload PDF report: {e}")
            return None

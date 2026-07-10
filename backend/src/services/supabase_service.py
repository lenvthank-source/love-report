import os
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
from jose import jwt

class SupabaseService:
    # Class-level mock database for admin users to persist across instances in local testing
    _mock_admin_users = [
        {"email": "admin@test.com", "full_name": "Mock Admin", "role": "admin", "status": "approved"},
        {"email": "support@test.com", "full_name": "Mock Support", "role": "support", "status": "approved"}
    ]
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        # Support service role key (preferred for backend bypass), standard key, and anon key fallbacks
        self.key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
            os.getenv("SUPABASE_KEY") or 
            os.getenv("SUPABASE_ANON_KEY") or
            os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        )
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
    def sign_in_with_password(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Signs in a user with email and password using Supabase Auth."""
        if not self.is_configured():
            # Mock login for testing/sandbox mode
            email_lower = email.strip().lower()
            admin_user = None
            for u in self._mock_admin_users:
                if u["email"] == email_lower:
                    admin_user = u
                    break
            
            if admin_user:
                # Check password matches local mocks
                if email_lower == "admin@test.com" and password != "admin123":
                    return None
                if email_lower == "support@test.com" and password != "support123":
                    return None
                
                # Check status
                if admin_user.get("status") == "pending":
                    raise ValueError("Your account is pending administrator approval.")
                if admin_user.get("status") == "rejected":
                    raise ValueError("Your account has been rejected by an administrator.")
                
                return {
                    "access_token": f"mock-{admin_user['role']}-token",
                    "user": {"email": email_lower, "user_metadata": {"role": admin_user["role"]}}
                }
            return None
        try:
            res = self.client.auth.sign_in_with_password({"email": email.strip().lower(), "password": password})
            
            # Check user record in admin_users table
            admin_user = self.get_admin_user(res.user.email)
            if not admin_user:
                # Auto-create entry as pending support if they exist in auth but not database
                self.create_admin_user(res.user.email, res.user.email.split("@")[0], role="support", status="pending")
                raise ValueError("Your account is pending administrator approval.")
            
            if admin_user.get("status") == "pending":
                raise ValueError("Your account is pending administrator approval.")
            if admin_user.get("status") == "rejected":
                raise ValueError("Your account has been rejected by an administrator.")
                
            return {
                "access_token": res.session.access_token,
                "user": {
                    "email": res.user.email,
                    "id": res.user.id,
                    "user_metadata": {
                        "role": admin_user.get("role", "support"),
                        **(res.user.user_metadata or {})
                    }
                }
            }
        except Exception as e:
            print(f"[SupabaseAuth] Authentication failed: {e}")
            return None

    def sign_up_admin(self, email: str, password: str, full_name: str) -> bool:
        """Signs up a new user using Supabase Auth and registers them in admin_users table."""
        email_lower = email.strip().lower()
        if not self.is_configured():
            # Mock signup
            return self.create_admin_user(email_lower, full_name, role="support", status="pending")
        try:
            # Register in Supabase Auth
            res = self.client.auth.sign_up({"email": email_lower, "password": password})
            if res.user:
                # Add to admin_users table
                return self.create_admin_user(email_lower, full_name, role="support", status="pending")
            return False
        except Exception as e:
            print(f"[SupabaseAuth] Signup failed: {e}")
            return False

    def verify_admin_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decodes and verifies a Supabase Auth JWT token.
        Tries using the Supabase get_user API first, with local JWT decode as a fallback.
        """
        if not self.is_configured() or token.startswith("mock-"):
            # Mock role logic based on token identifier
            if "support" in token:
                return {"email": "support@test.com", "user_metadata": {"role": "support"}}
            return {"email": "admin@test.com", "user_metadata": {"role": "admin"}}
        try:
            res = self.client.auth.get_user(token)
            if res and res.user:
                return {
                    "email": res.user.email,
                    "id": res.user.id,
                    "user_metadata": res.user.user_metadata or {}
                }
        except Exception as e:
            print(f"[SupabaseAuth] API token verification failed: {e}")

        # Fallback to local JWT decoding if client API verification fails
        if self.jwt_secret:
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
                print(f"[SupabaseAuth] Local JWT verification fallback failed: {e}")
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
    def create_payment(self, order_id: str, razorpay_order_id: str, amount: float = 999.00) -> str:
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

    # --- Admin Users Management (RBAC) ---
    def create_admin_user(self, email: str, full_name: str, role: str = "support", status: str = "pending") -> bool:
        if not self.is_configured():
            email_lower = email.strip().lower()
            if any(u["email"] == email_lower for u in self._mock_admin_users):
                return True
            self._mock_admin_users.append({
                "email": email_lower,
                "full_name": full_name,
                "role": role,
                "status": status
            })
            return True
        try:
            self.client.table("admin_users").insert({
                "email": email.strip().lower(),
                "full_name": full_name,
                "role": role,
                "status": status
            }).execute()
            return True
        except Exception as e:
            print(f"[Supabase] Failed to create admin user: {e}")
            return False

    def get_admin_user(self, email: str) -> Optional[Dict[str, Any]]:
        if not self.is_configured():
            email_lower = email.strip().lower()
            for u in self._mock_admin_users:
                if u["email"] == email_lower:
                    return u
            return None
        try:
            res = self.client.table("admin_users").select("*").eq("email", email.strip().lower()).execute()
            if res.data:
                return res.data[0]
            return None
        except Exception as e:
            print(f"[Supabase] Failed to get admin user: {e}")
            return None

    def update_admin_user_status(self, email: str, status: str) -> bool:
        if not self.is_configured():
            email_lower = email.strip().lower()
            for u in self._mock_admin_users:
                if u["email"] == email_lower:
                    u["status"] = status
                    return True
            return False
        try:
            res = self.client.table("admin_users").update({"status": status}).eq("email", email.strip().lower()).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"[Supabase] Failed to update admin user status: {e}")
            return False

    def update_admin_user_role(self, email: str, role: str) -> bool:
        if not self.is_configured():
            email_lower = email.strip().lower()
            for u in self._mock_admin_users:
                if u["email"] == email_lower:
                    u["role"] = role
                    return True
            return False
        try:
            res = self.client.table("admin_users").update({"role": role}).eq("email", email.strip().lower()).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"[Supabase] Failed to update admin user role: {e}")
            return False

    def list_admin_users(self) -> List[Dict[str, Any]]:
        if not self.is_configured():
            return self._mock_admin_users
        try:
            res = self.client.table("admin_users").select("*").order("email", desc=False).execute()
            return res.data or []
        except Exception as e:
            print(f"[Supabase] Failed to list admin users: {e}")
            return []

    def delete_admin_user(self, email: str) -> bool:
        if not self.is_configured():
            email_lower = email.strip().lower()
            initial_len = len(self._mock_admin_users)
            self._mock_admin_users[:] = [u for u in self._mock_admin_users if u["email"] != email_lower]
            return len(self._mock_admin_users) < initial_len
        try:
            res = self.client.table("admin_users").delete().eq("email", email.strip().lower()).execute()
            return len(res.data) > 0
        except Exception as e:
            print(f"[Supabase] Failed to delete admin user: {e}")
            return False

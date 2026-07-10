import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env
load_dotenv()

def bootstrap():
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    # service role key is preferred as it bypasses Row Level Security (RLS) constraints
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
        os.getenv("SUPABASE_KEY") or 
        os.getenv("SUPABASE_ANON_KEY") or
        os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    )

    if not url or not key:
        print("[-] Error: SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) not found in your environment (.env file).")
        print("Please configure them first.")
        sys.exit(1)

    print(f"[*] Connecting to Supabase at: {url}")
    try:
        client = create_client(url, key)
    except Exception as e:
        print(f"[-] Failed to initialize Supabase client: {e}")
        sys.exit(1)

    print("\n======================================")
    print("   Astro Savvy Admin Bootstrapper     ")
    print("======================================")
    email = input("Enter Admin Email: ").strip().lower()
    if not email:
        print("[-] Email cannot be empty.")
        sys.exit(1)
        
    password = input("Enter Admin Password (min 6 chars): ").strip()
    if len(password) < 6:
        print("[-] Password must be at least 6 characters.")
        sys.exit(1)

    full_name = input("Enter Full Name (optional): ").strip() or "Bootstrap Admin"

    print("\n[*] Processing registration...")

    # 1. Try to create the user in Supabase Auth
    try:
        auth_res = client.auth.sign_up({"email": email, "password": password})
        if auth_res.user:
            print("[+] Success: Created user in Supabase Auth.")
        else:
            print("[-] Warning: Failed to create user in Supabase Auth (already exists?).")
    except Exception as e:
        err_msg = str(e).lower()
        if "user already exists" in err_msg or "already registered" in err_msg:
            print("[*] Info: User already exists in Supabase Auth. Proceeding to database setup.")
        else:
            print(f"[-] Warning: Supabase Auth error: {e}")

    # 2. Try to insert or update the public.admin_users record
    try:
        # First check if row exists
        existing = client.table("admin_users").select("*").eq("email", email).execute()
        if existing.data:
            # Update to approved admin
            client.table("admin_users").update({
                "full_name": full_name,
                "role": "admin",
                "status": "approved"
            }).eq("email", email).execute()
            print("[+] Success: Updated public.admin_users record to role='admin', status='approved'.")
        else:
            # Insert new approved admin
            client.table("admin_users").insert({
                "email": email,
                "full_name": full_name,
                "role": "admin",
                "status": "approved"
            }).execute()
            print("[+] Success: Inserted new public.admin_users record as role='admin', status='approved'.")
            
        print("\n[✓] Setup Complete! You can now log in at /admin/login using:")
        print(f"    Email: {email}")
        print(f"    Password: {password}")
    except Exception as e:
        print(f"\n[-] Error: Failed to write to public.admin_users table: {e}")
        print("Please check that:")
        print("1. You have successfully created the 'admin_users' table inside the public schema.")
        print("2. Your SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY has write permissions to the 'admin_users' table.")

if __name__ == "__main__":
    bootstrap()

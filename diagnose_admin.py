import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from jose import jwt

# Load environment variables
load_dotenv()

def diagnose():
    print("======================================")
    print("   Astro Savvy Admin Diagnostics      ")
    print("======================================")

    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
        os.getenv("SUPABASE_KEY") or 
        os.getenv("SUPABASE_ANON_KEY") or
        os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    )
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")

    # 1. Check basic configuration
    if not url:
        print("[-] Error: SUPABASE_URL is missing from .env")
    else:
        print(f"[+] URL Configured: {url}")

    if not key:
        print("[-] Error: SUPABASE_KEY / SUPABASE_SERVICE_ROLE_KEY is missing from .env")
    else:
        # Mask key for security
        masked_key = key[:10] + "..." + key[-10:] if len(key) > 20 else "Configured"
        print(f"[+] Key Configured: {masked_key}")

    # 2. Check JWT Secret configuration
    if not jwt_secret:
        print("[!] Warning: SUPABASE_JWT_SECRET is missing from .env.")
        print("    -> The backend is running in Local Mock Mode for token verification.")
        print("    -> Any login token will be accepted, but it might not match your live users.")
    else:
        masked_jwt = jwt_secret[:3] + "..." + jwt_secret[-3:] if len(jwt_secret) > 6 else "Configured"
        print(f"[+] JWT Secret Configured: {masked_jwt}")
        if len(jwt_secret) > 100:
            print("    [!] Warning: Your JWT Secret is very long. Ensure you copied the 'JWT Secret', NOT the 'Anon Key' or 'Service Role Key'.")

    # 3. Test connection to Supabase
    if url and key:
        try:
            client = create_client(url, key)
            print("[+] Connected to Supabase client successfully.")
            
            # Query admin_users
            try:
                res = client.table("admin_users").select("*").execute()
                print(f"[+] Successfully read admin_users table. Found {len(res.data)} users:")
                for user in res.data:
                    print(f"    - {user['email']}: role={user['role']}, status={user['status']}")
            except Exception as e:
                print(f"[-] Error querying admin_users table: {e}")
                print("    -> Make sure the 'admin_users' table exists and RLS is disabled or has a policy.")
        except Exception as e:
            print(f"[-] Failed to connect to Supabase: {e}")

    print("\n======================================")
    print("   Common Issues and Fixes            ")
    print("======================================")
    print("If you log in successfully but the page redirects you back to the login screen:")
    print("1. Your SUPABASE_JWT_SECRET in .env may be incorrect or mismatched.")
    print("   -> Go to Supabase -> Project Settings -> API -> JWT Settings -> copy the 'JWT Secret'.")
    print("   -> Paste it in your .env file as: SUPABASE_JWT_SECRET=your_jwt_secret")
    print("2. The email of the user you are logging in with must exist in the 'public.admin_users' table with status='approved'.")

if __name__ == "__main__":
    diagnose()

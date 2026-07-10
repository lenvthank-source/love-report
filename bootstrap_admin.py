import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables from .env
load_dotenv()

def get_supabase_client():
    url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
        os.getenv("SUPABASE_KEY") or 
        os.getenv("SUPABASE_ANON_KEY") or
        os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    )

    if not url or not key:
        print("[-] Error: SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) not found in your environment (.env file).")
        sys.exit(1)

    try:
        client = create_client(url, key)
        return client
    except Exception as e:
        print(f"[-] Failed to initialize Supabase client: {e}")
        sys.exit(1)

def create_or_approve_user(client):
    print("\n--- Create / Approve Administrative User ---")
    email = input("Enter Email: ").strip().lower()
    if not email:
        print("[-] Email cannot be empty.")
        return
        
    password = input("Enter Password (min 6 chars for signup, leave empty to skip auth registration): ").strip()
    full_name = input("Enter Full Name: ").strip() or "Admin User"
    
    role = input("Enter Role (admin/support) [default: support]: ").strip().lower() or "support"
    if role not in ["admin", "support"]:
        role = "support"

    status = input("Enter Status (approved/pending/rejected) [default: approved]: ").strip().lower() or "approved"
    if status not in ["approved", "pending", "rejected"]:
        status = "approved"

    # 1. Try to register in Supabase Auth if password is provided
    if password:
        if len(password) < 6:
            print("[-] Password must be at least 6 characters.")
            return
        try:
            auth_res = client.auth.sign_up({"email": email, "password": password})
            if auth_res.user:
                print("[+] Success: Created user in Supabase Auth.")
        except Exception as e:
            err_msg = str(e).lower()
            if "user already exists" in err_msg or "already registered" in err_msg:
                print("[*] Info: User already exists in Supabase Auth. Syncing with database.")
            else:
                print(f"[!] Warning registering in Auth (check password complexity policy): {e}")

    # 2. Write to public.admin_users
    try:
        existing = client.table("admin_users").select("*").eq("email", email).execute()
        if existing.data:
            client.table("admin_users").update({
                "full_name": full_name,
                "role": role,
                "status": status
            }).eq("email", email).execute()
            print(f"[+] Success: Updated public.admin_users record: role='{role}', status='{status}'.")
        else:
            client.table("admin_users").insert({
                "email": email,
                "full_name": full_name,
                "role": role,
                "status": status
            }).execute()
            print(f"[+] Success: Inserted new public.admin_users record: role='{role}', status='{status}'.")
    except Exception as e:
        print(f"[-] Error: Failed to write to public.admin_users table: {e}")
        print("Make sure you ran the SQL Editor command to create the table and disable RLS.")

def list_users(client):
    print("\n--- Registered Administrative Users ---")
    try:
        res = client.table("admin_users").select("*").order("email", desc=False).execute()
        if not res.data:
            print("No users found in public.admin_users table.")
            return
        
        print("-" * 80)
        print(f"{'Email':<30} | {'Full Name':<20} | {'Role':<10} | {'Status':<10}")
        print("-" * 80)
        for user in res.data:
            print(f"{user['email']:<30} | {user.get('full_name', 'N/A'):<20} | {user['role']:<10} | {user['status']:<10}")
        print("-" * 80)
    except Exception as e:
        print(f"[-] Error querying admin_users table: {e}")

def delete_user(client):
    print("\n--- Delete Administrative User ---")
    email = input("Enter Email to delete: ").strip().lower()
    if not email:
        print("[-] Email cannot be empty.")
        return

    confirm = input(f"Are you sure you want to delete administrative access for {email}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("[*] Deletion cancelled.")
        return

    # 1. Delete from public.admin_users table
    db_deleted = False
    try:
        res = client.table("admin_users").delete().eq("email", email).execute()
        if res.data:
            print(f"[+] Success: Removed {email} from public.admin_users database table.")
            db_deleted = True
        else:
            print(f"[-] User {email} was not found in public.admin_users table.")
    except Exception as e:
        print(f"[-] Error deleting from public.admin_users table: {e}")

    # 2. Attempt to delete from Auth (only works if using Service Role Key)
    try:
        # We search users in Auth to find corresponding ID
        users_res = client.auth.admin.list_users()
        user_id = None
        for u in users_res:
            if u.email.strip().lower() == email:
                user_id = u.id
                break
        
        if user_id:
            client.auth.admin.delete_user(user_id)
            print(f"[+] Success: Removed {email} from Supabase Auth.")
        elif db_deleted:
            print("[*] Info: User was deleted from database, but auth record was not found or already deleted.")
    except Exception as e:
        # Silent pass if key is not service role or lists fail
        pass

def main():
    client = get_supabase_client()
    
    while True:
        print("\n======================================")
        print("   Astro Savvy Admin Manager (CLI)    ")
        print("======================================")
        print("1. Create / Approve Administrative User")
        print("2. List All Administrative Users & Roles")
        print("3. Delete Administrative User")
        print("4. Exit")
        print("======================================")
        
        choice = input("Enter your choice (1-4): ").strip()
        if choice == "1":
            create_or_approve_user(client)
        elif choice == "2":
            list_users(client)
        elif choice == "3":
            delete_user(client)
        elif choice == "4":
            print("[*] Exiting Admin Manager CLI. Goodbye!")
            break
        else:
            print("[-] Invalid choice. Please choose between 1 and 4.")

if __name__ == "__main__":
    main()

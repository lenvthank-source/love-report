# Project Developer Workflow

This guide details the step-by-step developer workflows for setting up, running, testing, and deploying the Vedic Astrology Report Engine.

## 1. Local Environment Setup

Follow these steps to configure your local developer workstation:

### Step 1.1: Clone & Configure Python Environment
1. Ensure Python 3.10 or higher is installed.
2. Initialize virtual environment:
   ```bash
   python -m venv venv
   ```
3. Activate virtual environment:
   - **Windows (PowerShell)**: `.\venv\Scripts\Activate.ps1`
   - **macOS / Linux**: `source venv/bin/activate`
4. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

### Step 1.2: Set Up Environment Configuration
1. Duplicate the template configuration:
   ```bash
   cp .env.example .env
   ```
2. Populate the required keys in `.env`:
   - `OPENCAGE_API_KEY`: Key for locations geocoder.
   - `OPENROUTER_API_KEY`: Key for GPT/Claude reports interpretation.
   - `SUPABASE_URL` / `SUPABASE_KEY`: Supabase DB keys.
   - `SENDPULSE_SMTP_USER` / `SENDPULSE_SMTP_PASSWORD`: Resend/SMTP email credentials.
   - `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET`: Razorpay checkout credentials.

---

## 2. Database Initialization

1. Log into your Supabase Dashboard.
2. Open the **SQL Editor**.
3. Copy the contents of [schema.sql](file:///e:/Report-Engine/backend/database/schema.sql) and execute the queries to create all tables and indexes.
4. Ensure Row-Level Security (RLS) is configured appropriately on your tables. Disable RLS on the `admin_users` table if using the bootstrap script as-is, or create policies that allow administrative operations.

---

## 3. Administrative User Provisioning

Access control to the admin dashboard (`frontend/admin.html`) is verified via Supabase Auth + JWT tokens.

1. **Provision Admin Account**:
   Run the CLI utility to register or approve an email address:
   ```bash
   python bootstrap_admin.py
   ```
   Select **Option 1** and provide the email, password, role, and set status to `approved`.
2. **Verify Configuration**:
   Diagnose connections and verify active admins using:
   ```bash
   python diagnose_admin.py
   ```

---

## 4. Run the Local Server

Start the FastAPI application locally:
```bash
uvicorn backend.src.server:app --reload --port 8000
```

### Accessing the Web Application
- **Main Checkout Page**: `http://localhost:8000/order` (Redirects automatically based on user agent device type to `mobile.html` or `order.html`).
- **Admin Dashboard Login**: `http://localhost:8000/admin/login`
- **Admin Dashboard Panel**: `http://localhost:8000/admin`
- **Health Check Status**: `http://localhost:8000/api/health`

---

## 5. Report Compilation Verification

Test the astrology compilation pipeline end-to-end without submitting web purchases:
1. Ensure your `.env` contains valid keys (OpenCage, OpenRouter, Supabase).
2. Execute the sample compiler script:
   ```bash
   python backend/build_sample_report.py
   ```
3. Check the output PDF file in `backend/output/` to inspect text alignments, tables, and chart formatting.

---

## 6. Production Deployment

The project is structured to run serverless on Vercel:
- **Serverless Config**: [vercel.json](file:///e:/Report-Engine/vercel.json) redirects API and frontend requests appropriately.
- Deploy using the Vercel CLI or connect the repository to Vercel's Git integrations.
- Set all keys from `.env` in the Vercel Environment Variables configuration interface.

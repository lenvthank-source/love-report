# Vedic Astrology Report Engine - Developer Workflows

This document outlines the operational and development workflows for this project. 

The official developer workflow documentation is located at:
👉 **[.agents/workflow.md](file:///e:/Report-Engine/.agents/workflow.md)**

---

## 1. Setup & Installation Workflow

### Local Development Setup
1. **Initialize Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or .\venv\Scripts\Activate.ps1 on Windows
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. **Environment Setup**:
   Copy `.env.example` to `.env` and fill in all third-party API credentials (OpenCage, OpenRouter, Supabase, SendPulse SMTP, Razorpay).

### Database Setup
1. Execute [schema.sql](file:///e:/Report-Engine/backend/database/schema.sql) directly in your Supabase SQL Editor.
2. Initialize or modify your DB client credentials within the local `.env` configuration file.

---

## 2. Administration Workflow

Use the Python admin utilities to manage backend access controls:
- **Diagnose Admin Configuration**:
  ```bash
  python diagnose_admin.py
  ```
  Validates Supabase connectivity, table existence, and lists registered admin emails.
- **Create or Approve Administrator Access**:
  ```bash
  python bootstrap_admin.py
  ```
  Interactively register users to `Supabase Auth` and populate details into the `public.admin_users` table with approved status.

---

## 3. Running the Server

Start local server:
```bash
uvicorn backend.src.server:app --reload --port 8000
```
- Checkout Page: `http://localhost:8000/order`
- Admin Login Page: `http://localhost:8000/admin/login`
- Systems Health Check API: `http://localhost:8000/api/health`

---

## 4. Testing & Compiling Reports

Test PDF rendering mechanics and overlay coordinates locally by running:
```bash
python backend/build_sample_report.py
```
This generates a test output PDF directly in `backend/output/` containing mocked calculations and LLM interpretation texts.

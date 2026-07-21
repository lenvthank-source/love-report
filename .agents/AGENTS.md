# Workspace Rules for Vedic Astrology Report Engine

This document contains rules, design constraints, and style guides for agents and developers working on the Vedic Astrology Report Engine codebase.

## 1. Project Stack & Architecture

- **Backend**: Python 3.10+ with FastAPI for HTTP servers and background processes.
- **Frontend**: Plain HTML, Vanilla CSS, and JavaScript. No modern JS framework (Next.js/React) is used.
- **Database**: Supabase PostgreSQL. Schema changes must go in `backend/database/schema.sql` and be synced via SQL editor or migrations.
- **Report Generation**: PDF-lib / fitz (PyMuPDF) overlay compiler writing onto `Blank Report Revised.pdf`.

## 2. Coding & Style Rules

### Python (Backend)
- Follow **PEP 8** style guidelines.
- Use explicit type hints for function arguments and return types.
- Ensure proper logging using `src.utils.logger` instead of bare `print` statements (except in background scripts/workers).
- Validate environment variables and API inputs with **Pydantic** models.

### HTML/CSS/JS (Frontend)
- Keep styling responsive and mobile-friendly (critical since mobile traffic is directed to `mobile.html`).
- Ensure CORS configurations in FastAPI allow the local and production domains to access APIs safely.

## 3. Environment Variables & Credentials

- Do **NOT** commit credentials or the `.env` file to Git.
- Add new configuration keys first to `.env.example` and register them inside the `Settings` class in `backend/src/config/env.py`.
- Support mock credentials for SMTP or local services when verifying features locally.

## 4. API Integrity & Caching Constraints

- **VedAstro API**: Calculations are slow and rate-limited. Always route calculations through `VedAstroService` which utilizes `FileCache` internally.
- **OpenCage Geocoder**: Always check cache or database coordinates before querying OpenCage API to conserve query quotas.
- **OpenRouter LLM**: Ensure system instructions are clean and do not leak reasoning blocks into the final PDF content blocks. Strip tags like `<think>` using `src.utils.markdown_parser.strip_thinking_tags`.

## 5. PDF Generation Coordinate Mapping

- The PDF overlay coordinates are stored in the static dictionary `LAYOUT_CONFIG` in `backend/src/services/pdf_service.py`. Do not modify these coordinates unless the background template `Blank Report Revised.pdf` has changed.
- Run `backend/build_sample_report.py` to test rendering alignment changes before deploying.

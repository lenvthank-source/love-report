# Project Coding Rules & Guidelines

Development on this repository is subject to workspace constraints that ensure code style consistency, local database mapping integrity, and API coordinate safety.

The official workspace rules configuration file for AI agents is located at:
👉 **[.agents/AGENTS.md](file:///e:/Report-Engine/.agents/AGENTS.md)**

## Summary of Core Rules

1. **Stack Compliance**: Backend must run Python FastAPI using explicit type hints. Frontend must use lightweight, framework-less HTML/CSS/JavaScript template files.
2. **Credential Safety**: Never commit credentials in `.env`. Update `.env.example` when adding configuration options.
3. **Caching and Optimization**: Cache all external API transactions (especially VedAstro calculations and OpenCage geocoding queries) to optimize speed and stay within request limits.
4. **Coordinate Mechanics**: PDF overlays use exact coordinate grids defined in `LAYOUT_CONFIG`. Verify any rendering modifications locally using `backend/build_sample_report.py` before push.

For the complete guideline checklist, please see the [AGENTS.md](file:///e:/Report-Engine/.agents/AGENTS.md) file.

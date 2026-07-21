# Custom Agent Skill: Vedic Astrology Report Engine

This project supports the Google Antigravity custom agent skill `astrology_report_engine`.

The full skill definition, containing execution flows, schema mapping, and third-party APIs parameters, is located at:
👉 **[.agents/skills/astrology_report_engine/SKILL.md](file:///e:/Report-Engine/.agents/skills/astrology_report_engine/SKILL.md)**

## Skill Overview

- **Name**: `astrology_report_engine`
- **Description**: Orchestrates the automated creation of Vedic Compatibility and Marriage Reports.
- **Key Integrations**:
  - **Geocoding**: OpenCage Geocoding API.
  - **Astrology Engine**: VedAstro API calculations with local JSON file cache.
  - **LLM Engine**: OpenRouter API for narrative synthesis.
  - **PDF Compiler**: PyMuPDF (`fitz`) overlay logic drawing custom planetary positions, divisional charts (D1, D9, D30), element distribution charts, and timeline dashas onto `Blank Report Revised.pdf`.
  - **Database & Storage**: Supabase Database schemas & public bucket storage.
  - **Delivery**: SendPulse SMTP server email sending.

For detailed custom instructions on how agents utilize this skill, read the [SKILL.md](file:///e:/Report-Engine/.agents/skills/astrology_report_engine/SKILL.md) file.

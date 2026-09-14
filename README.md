# Care Sister — ACHOT Postpartum Companion

A culturally respectful WhatsApp postpartum companion designed to support mothers with recovery education, emotional support, breastfeeding, baby-care questions, nourishment, rest and safe discussion of traditional postpartum practices.

## Current WhatsApp architecture

The active test transport is **Evolution API v2 with the Baileys integration**. Evolution receives WhatsApp events and forwards inbound messages to the Care Sister FastAPI webhook; the bot sends replies back through Evolution's `sendText` endpoint.

This is an unofficial WhatsApp Web protocol integration and is not affiliated with or endorsed by Meta. Use it responsibly: prioritize user-initiated/consensual conversations, reasonable messaging frequency, opt-out support and monitoring.

## Features

- Safety-first postpartum triage
- Empathetic Care Sister conversation layer
- Personalized mother name and conversation topic memory
- Vaginal/C-section onboarding
- Main and recovery menus with free-text questions
- Cultural-care information layer
- Scheduled postpartum check-in foundation (Day 3, 7 and 14)
- Human-support escalation foundation
- SQLite/SQLAlchemy persistence for testing

## Tech stack

- FastAPI + Uvicorn
- SQLAlchemy + SQLite
- Evolution API v2 / Baileys
- HTTPX
- APScheduler
- Python dotenv

## Environment

Copy `.env.example` to `.env` and set:

```text
EVOLUTION_API_URL=
EVOLUTION_API_KEY=
EVOLUTION_INSTANCE=care-sister
DATABASE_URL=sqlite:///./postpartum.db
NURSE_NOTIFY_WEBHOOK_URL=
```

Never commit real API keys or tokens.

## Local development

```bash
python -m venv venv
pip install -r requirements.txt
uvicorn app.main:app --reload --port 10000
```

Health check: `GET /`

Safe configuration check: `GET /diagnostics`

Evolution webhook: `POST /webhook/evolution`

## Important

Care Sister provides general health information and supportive conversation. It does not diagnose medical conditions or replace a qualified healthcare professional. Safety-sensitive messages should be escalated rather than handled as ordinary conversation.

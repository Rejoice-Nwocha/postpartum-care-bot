## Postpartum Care Sister Bot

A culturally sensitive WhatsApp bot supporting new mothers in sub-Saharan Africa during the critical postpartum period (0-6 weeks).

## Features
- **Safety-First** regex scanner for emergencies
- **Empathetic, motherly tone** ("Care Sister")
- **Regional African traditions** (West, East, South, North)
- Scheduled check-ins (Day 3, 7, 14)
- Human nurse escalation with timeout
- Localized facility directory

## 🛠 Tech Stack
- FastAPI
- SQLAlchemy + SQLite
- WhatsApp Cloud API
- APScheduler

## Quick Start

```bash
cp .env.example .env
# Fill in your Meta WhatsApp credentials
pip install -r requirements.txt
uvicorn app.main:app --reload

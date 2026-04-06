# CrisisCoach AI

A conversational AI crisis support companion built with Next.js + FastAPI + Anthropic Claude.

## Project Structure

```
crisiscoach-ai/
├── frontend/          # Next.js 14 (App Router, TypeScript, Tailwind)
│   └── src/
│       ├── app/           # Next.js app directory
│       ├── components/    # ChatWindow, ChatBubble
│       └── lib/           # API client
└── backend/           # FastAPI Python app
    └── app/
        ├── main.py        # FastAPI entry point
        ├── routers/       # chat.py — POST /api/chat
        ├── services/      # claude_client.py — Anthropic SDK calls
        └── models/        # Pydantic schemas
```

## Quick Start

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| POST | /api/chat | Send message history, receive Claude reply |

### POST /api/chat

```json
{
  "messages": [
    { "role": "user", "content": "I'm feeling overwhelmed." }
  ]
}
```

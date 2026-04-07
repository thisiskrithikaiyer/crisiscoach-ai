# CrisisCoach.AI — MVP 1

## What MVP 1 Is

The core loop. Nothing else.

A user lands, tells us what happened in four taps, gets a plan for today, checks in tomorrow, and the system adjusts. Alongside that — if they are on a visa, dealing with severance, or worried about money — the system runs a quiet background check once and injects the most critical tasks into their daily plan automatically.

No fancy agents. No RAG. No citations. No mock interviews. No LinkedIn optimization. Just the loop plus the three situational checks.

---

## The Loop

```
Onboard (4 taps)
    ↓
Day 1 plan (3 tasks)
    ↓
Check in next day (1 question, 4 chips)
    ↓
Accountability (honest assessment)
    ↓
Adjusted plan for today
    ↓
Repeat
```

That is the entire product in MVP 1. Every day the user checks in, the system reads what happened yesterday, and builds today's plan around that. Day 20 is smarter than Day 1 because the system has seen 20 check-ins.

---

## Agents in MVP 1

Five core agents. Three situational agents that run once.

### Core — run every day

**Orchestrator Agent**
Reads every message. Decides who handles it. Routes to the right agent. Nothing else.

**Intake Agent**
First session only. Collects crisis type, urgency, field, and mood via chip selections. Writes structured profile to State Store. Hands off to Planner.

**Planner Agent**
Runs in background after every check-in. Reads user profile, check-in history, and any injected tasks from situational agents. Outputs 3 prioritized tasks for tomorrow. Stored in PostgreSQL before the user wakes up.

**DailyTracker Agent**
Handles the daily check-in. One question. Four chip options. Reads yesterday's plan, asks how it went, passes the answer to Accountability.

**Accountability Agent**
Reads the check-in response and yesterday's plan. Gives an honest assessment. No sugarcoating. Feeds the assessment back to Planner for tomorrow's plan.

---

### Situational — run once at onboarding, re-activate on keywords

**Severance Agent**
Triggers if crisis type is layoff. Runs once. Checks what the user needs to do in the first 30 days of leaving a company — agreement review, COBRA, 401k, references, final paycheck. Injects the most urgent tasks into the Planner's queue. Goes dormant. Re-activates if user mentions severance again.

**FinanceCheck Agent**
Runs once at onboarding always. Asks two questions — do you know your monthly burn rate, and have you filed for unemployment. Estimates a rough runway category (urgent, moderate, stable). Writes urgency signal to State Store. Planner reads this on every plan generation to calibrate task urgency. Re-activates if user mentions money stress.

**VisaSupport Agent**
Triggers if crisis type includes visa. Runs once. Identifies visa type (OPT, H1B, H4) and grace period status. Injects the single most time-sensitive task — contact an attorney, check OPT unemployment days, or understand the 60-day H1B window. Goes dormant. Re-activates if user mentions visa, status, grace period, or transfer.

---

## What Situational Agents Do NOT Do in MVP 1

- No legal advice
- No financial advice
- No immigration advice
- No document review
- No source citations
- No database lookups

They ask two or three simple questions and inject one or two tasks. That is it. The full RAG-powered, cited, database-backed version of these agents is v2.

---

## Storage in MVP 1

Three stores. Minimal schemas.

**PostgreSQL (Supabase)**
- Users table — id, email, crisis type, urgency, field, created at
- User profiles — skills, experience, target roles, day count
- Daily plans — user id, date, tasks JSON, completed flags
- Check-ins — user id, date, response, mood, energy level

**Redis (Railway)**
- Active session state — current agent, today's plan, last 10 messages
- Background job queue — build plan jobs pushed here after check-in

**pgvector (Supabase)**
- User memories — embeddings of past check-ins for pattern detection
- Used by Planner to detect avoidance patterns and energy trends

No InterviewDB. No StrategyDB. No WellnessDB. No LegalDB. No FinanceDB. No VisaDB. Those are v2.

---

## Frontend in MVP 1

Four screens. That is it.

**Screen 1 — Onboarding**
Four chip groups. One tap each. Optional one-line free text. Submit button. Done in under 2 minutes.

**Screen 2 — Today's Plan**
Three tasks. Check them off. Streak counter at the top. Nothing else.

**Screen 3 — Daily Check-in**
One question. Four chips. Submit. Done in under 30 seconds.

**Screen 4 — Chat**
Simple chat interface for anything outside the structured flow. User types, Orchestrator routes, agent responds.

---

## Infrastructure in MVP 1

**Backend** — FastAPI + LangGraph
**Frontend** — Next.js
**Database** — Supabase (PostgreSQL + pgvector)
**Cache + Queue** — Redis on Railway
**LLM** — Claude Sonnet for Planner, Accountability, situational agents. Claude Haiku for Orchestrator and DailyTracker.
**Deployment** — Railway. Two services — web and worker.
**Observability** — SQLite cost tracker locally. Railway logs for infra.

---

## What Is Not in MVP 1

Everything below stays out until the core loop is validated with real users.

- InterviewPrep Agent
- MockPrep Agent
- PatternTracker Agent
- JobStrategy Agent
- MentalHealthCheck Agent
- PauseAgent
- ProfileBuilder Agent
- Resume Helper Agent
- LinkedIn Enhancer Agent
- TalentMapper Agent (basic version only via Intake)
- DailyCheck Agent (basic version only via DailyTracker)
- FactChecker Agent
- All RAG pipelines
- All knowledge base ingestion
- Source citations
- Push notifications
- Email nudges
- Auth beyond basic Supabase Auth

---

## MVP 1 Success Criteria

One thing. The loop works.

A user can onboard in under 2 minutes, receive a Day 1 plan with 3 specific tasks, check in the next morning in under 30 seconds, and receive a plan for today that reflects what they did or did not do yesterday.

If a user is on a visa, their most urgent visa task appears in their Day 1 plan without them asking for it.

If a user just got laid off, their most urgent severance task appears in their Day 1 plan without them asking for it.

If a user's financial runway is urgent, their plan tasks are faster and higher volume than a user with a stable runway.

**That is MVP 1. Ship it. Use it yourself for two weeks. Then build v2.**

---

## Build Order

```
1. Scaffold repo from architecture.md using Claude Code
2. Set up Supabase tables + Redis + Railway
3. Build Orchestrator + Intake — test onboarding flow
4. Build Planner + background worker — test plan generation
5. Build DailyTracker + Accountability — test the daily loop
6. Add Severance + FinanceCheck + VisaSupport — test injection
7. Wire all storage layers
8. Build frontend — 4 screens
9. Deploy to Railway
10. Use it yourself every day for 2 weeks
```

---

*MVP 1 target: 4 weeks*
*Stack: LangGraph · FastAPI · Next.js · Supabase · Redis · Railway*

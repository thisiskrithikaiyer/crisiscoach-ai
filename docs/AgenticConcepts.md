# CrisisCoach.AI — Core Concepts & Agentic Technologies

This document explains the agentic design patterns and technologies that power CrisisCoach. Understanding these concepts is essential before building or extending the system.

---

## 1. Multi-Agent Orchestration

CrisisCoach is not a single LLM call. It is a system of specialized agents, each with one focused responsibility, coordinated by an orchestrator.

**Why multi-agent instead of one big prompt:**
A single prompt trying to handle onboarding, planning, check-ins, visa guidance, emotional support, and interview prep would be unfocused, expensive, and impossible to debug. Specialized agents are faster, cheaper, easier to evaluate, and easier to improve independently.

**The pattern used: Hierarchical Supervisor**
One orchestrator agent sits at the top. It reads every incoming message, classifies intent, and routes to the correct specialist agent. Specialist agents never talk to each other directly — they communicate through shared state. This is the same pattern used in production systems at companies like Anthropic, Google, and Stripe.

```
User message
    ↓
Orchestrator (intent classification + routing)
    ↓
Specialist agent (focused task)
    ↓
Shared state (written back for all agents to read)
    ↓
User response
```

**Framework: LangGraph**
LangGraph models agent workflows as directed graphs. Each agent is a node. Edges define how control flows between agents. Conditional edges handle routing logic — if intent is "visa", route to VisaSupport; if intent is "distress", route to MentalHealthCheck. The graph is stateful — every node reads from and writes to a shared state object that persists across the conversation.

---

## 2. Agentic State Machine

Every user interaction moves through a defined set of states. The system knows where the user is in their journey and what the next valid action is.

**States in CrisisCoach:**

```
NEW_USER → ONBOARDING → PROFILED → PLANNING → ACTIVE → DAILY_LOOP
                                                  ↑           |
                                                  └───────────┘
                                              (loop repeats daily)
```

**Why this matters:**
A returning user on day 20 gets a different experience than a new user. The state machine ensures the Orchestrator never sends a returning user through onboarding again, and never skips the check-in for a user who is in the daily loop. State is stored in Redis (active session) and PostgreSQL (persistent history).

**LangGraph implementation:**
Each state maps to a node in the graph. Transitions are conditional edges with routing functions that read current state and decide the next node. The `CrisisCoachState` TypedDict is the shared schema all nodes read from and write to.

---

## 3. Windowed Memory

CrisisCoach never loads full conversation history into the LLM context. It loads only what is relevant right now.

**Three memory layers:**

| Layer | Technology | What it stores | Lifetime |
|---|---|---|---|
| Working memory | Redis | Last 10 messages, today's plan, active agent | 24 hours |
| Structured memory | PostgreSQL | Full plan history, check-ins, user profile | Permanent |
| Semantic memory | pgvector | Embedded past check-ins, behavioral patterns | Permanent |

**How context is assembled per request:**
```
current message
+ last 10 messages (Redis)
+ user profile summary (PostgreSQL)
+ top 3 semantically relevant past patterns (pgvector)
= ~2000-3000 tokens total
```

This means Day 1 and Day 60 cost the same. The system gets smarter through retrieval, not by loading more history.

**Why this is production-critical:**
Without windowed memory, a user who has been on the platform for 60 days would have a context window thousands of tokens longer than a new user. Token costs would compound over time, responses would slow down, and the system would eventually hit context limits. Windowed memory solves all three.

---

## 4. Retrieval Augmented Generation (RAG)

Every recommendation CrisisCoach makes is grounded in a credible source. The system does not rely on the LLM's training data for advice — it retrieves relevant chunks from curated knowledge bases and cites them.

**How RAG works in CrisisCoach:**

```
User situation: "I'm on H1B and just got laid off"
    ↓
VisaSupport Agent classifies: H1B grace period query
    ↓
pgvector semantic search on VisaDB
    ↓
Retrieve top 3 chunks: USCIS.gov H1B grace period, 60-day rule, transfer process
    ↓
LLM generates response grounded in retrieved chunks
    ↓
FactChecker Agent attaches citation metadata
    ↓
User sees: "Your H1B grace period is 60 days from your last day of employment. *(Source: USCIS.gov)*"
```

**Knowledge bases in CrisisCoach:**

| Database | Domain | Sources |
|---|---|---|
| InterviewDB | DSA patterns, company questions | NeetCode, Glassdoor, interviewing.io |
| StrategyDB | Job search strategy | LinkedIn Reports, BLS, Levels.fyi |
| WellnessDB | Mental health, burnout recovery | Mayo Clinic, APA, Harvard Health |
| LegalDB | Severance, employment law | DOL, EEOC, SHRM, Nolo |
| FinanceDB | Financial runway, benefits | DOL, IRS, NerdWallet |
| VisaDB | OPT, H1B, H4, STEM OPT | USCIS, ICE SEVP, travel.state.gov |

**Embedding model:**
All source documents are chunked (400-500 tokens per chunk), embedded using a text embedding model, and stored in pgvector. At query time, the user's message is embedded and a cosine similarity search retrieves the most relevant chunks.

---

## 5. Tool Use and Structured Outputs

Agents in CrisisCoach do not return free-form text to each other. They return structured outputs — validated Pydantic objects — so downstream agents can reliably read and act on the data.

**Example: Planner Agent output**
```python
class DailyPlan(BaseModel):
    tasks: list[Task]           # exactly 3 tasks
    urgency_level: str          # high | medium | low
    planner_notes: str          # internal context for other agents

class Task(BaseModel):
    title: str                  # action verb + specific action
    meta: str                   # why this matters today
    priority: str               # high | med | low
    source_citation: str | None # attached citation if applicable
    agent_source: str           # which agent generated this task
```

**Why structured outputs matter:**
When the Accountability Agent reads the Planner's output, it needs to know exactly which tasks were planned. When the FactChecker reads an advice chunk, it needs to know where to attach citations. Free-form text between agents creates fragile string parsing. Structured Pydantic outputs create contracts between agents.

---

## 6. Human-in-the-Loop

CrisisCoach is not fully autonomous. The user is in the loop at every decision point that matters. The system proposes — the user confirms and executes.

**Where human-in-the-loop appears:**
- Daily check-in: user selects how yesterday went (chip selection, not free text)
- Plan review: user sees tasks before they are locked in
- Task completion: user marks tasks done, triggering Accountability Agent
- Emotional state: user selects mood chip, which calibrates the day's plan tone

**Why this is the right pattern for CrisisCoach:**
A fully autonomous agent that silently replans without user input would feel like something is happening to you, not for you. CrisisCoach is built on the principle that the user executes — the system plans. Every replanning moment is triggered by user input, not autonomous agent decision.

---

## 7. Situational Agent Activation

Not all agents run on every message. Severance Agent, FinanceCheck Agent, and VisaSupport Agent are situational — they activate based on crisis type at onboarding and inject tasks into the Planner's context. They then go dormant until triggered again by relevant user input.

**Activation pattern:**
```python
# At onboarding
if crisis_type == "layoff":
    severance_tasks = await severance_agent.run(user_profile)
    finance_runway = await finance_check_agent.run(user_profile)
    state["injected_tasks"].extend(severance_tasks)
    state["finance_runway_weeks"] = finance_runway

if "visa" in crisis_type:
    visa_tasks = await visa_support_agent.run(user_profile)
    state["injected_tasks"].extend(visa_tasks)

# Planner reads injected_tasks on every plan generation
# and merges them with its own generated tasks by priority
```

**Why this pattern:**
Running all agents on every message would be slow and expensive. Situational activation means agents only consume tokens when they have something relevant to contribute. The Planner always gets the output regardless — it just reads from state.

---

## 8. Eval-Driven Development

Every agent in CrisisCoach has a corresponding evaluator. Before any agent is deployed or changed, it must pass its eval suite.

**Four evaluation dimensions:**

| Evaluator | What it checks |
|---|---|
| Plan quality | Are tasks specific and actionable, not generic? |
| Tone check | Is the response direct but not harsh? Does it avoid toxic positivity? |
| Citation check | Does every recommendation have a credible source attached? |
| Routing accuracy | Did the Orchestrator route to the correct agent given the input? |

**Golden datasets:**
Each evaluator runs against a golden dataset — a curated set of inputs with expected outputs. For example, `planner_golden.json` contains 20 user profiles with known optimal plans. The plan quality evaluator scores generated plans against these baselines.

**LangSmith integration:**
All eval runs are pushed to LangSmith where scores are tracked over time. A regression in routing accuracy or plan quality blocks deployment. This is the same eval pattern used in production LLM systems at Anthropic and Google.

---

## 9. Prompt Engineering Patterns

Each agent has its own system prompt stored in `prompts/`. Prompts follow a consistent structure.

**Agent prompt structure:**
```
[ROLE]
You are the {AgentName} for CrisisCoach.AI. Your only job is {one sentence}.

[CONTEXT]
You will receive: {list of inputs from state}

[OUTPUT FORMAT]
Return a valid JSON object matching this schema: {schema}

[RULES]
- {constraint 1}
- {constraint 2}
- Never {anti-pattern}

[TONE]
{tone guidance specific to this agent}
```

**Key prompt engineering decisions:**

- **One job per prompt** — each agent prompt describes exactly one responsibility. No agent prompt tries to do two things.
- **Output format in prompt** — every prompt specifies the exact JSON schema expected. This eliminates parsing failures.
- **Negative constraints** — every prompt includes what the agent must never do. Accountability Agent: never make the user feel stupid. MentalHealthCheck: never diagnose. VisaSupport: never give legal advice.
- **Tone calibration** — tone is agent-specific. Accountability is direct and firm. PauseAgent is calm. MentalHealthCheck is steady. These are explicit in each prompt, not left to the model.

---

## 10. Observability

CrisisCoach instruments every agent call so failures are visible and debuggable.

**What is traced:**
- Which agent handled the request
- How long each agent took
- Token cost per agent per request
- Which knowledge base chunks were retrieved
- Whether FactChecker found a citation or flagged as general guidance
- Routing decisions made by Orchestrator

**Tools:**
- **LangSmith** — agent traces, span-level debugging, eval result tracking
- **Railway logs** — infrastructure and deployment logs
- **Supabase dashboard** — database query performance

**Why observability matters for multi-agent systems:**
When a bad plan reaches the user, you need to know which agent generated it, what state it read from, and what prompt version was active. Without tracing, debugging a multi-agent failure is guesswork. With LangSmith, every agent call is a traceable span.

---

## 11. Background Job Processing

Not every agent should run at request time. Agents that do heavy work — building tomorrow's plan, checking burnout signals, recalculating visa deadlines — run in the background so the user never waits.

**Two categories of agents:**

| Category | Agents | When they run |
|---|---|---|
| Runtime | Orchestrator, Intake, DailyTracker, Accountability, MentalHealthCheck | Triggered by user message, real time |
| Background | Planner, PauseAgent, DailyCheck, VisaSupport, FinanceCheck, TalentMapper, InterviewPrep, JobStrategy, FactChecker | Scheduled or event-driven, never block the user |

**Three background execution patterns:**

**Pattern 1 — Redis Queue (for user-triggered background work)**

When a user action should trigger a background agent without blocking the response:

```
User checks in at 9pm
    ↓
DailyTracker writes check-in to PostgreSQL
    ↓
Pushes job to Redis queue: "build_tomorrow_plan:{user_id}"
    ↓
Returns response to user instantly
    ↓
Worker picks up job at 11pm
    ↓
Planner Agent runs in background
    ↓
Tomorrow's plan stored in PostgreSQL before user wakes up
    ↓
User opens app at 8am — plan is already there, no wait
```

**Pattern 2 — Cron Jobs (for scheduled recurring work)**

Agents that need to run on a clock regardless of user activity:

```python
# workers/scheduler.py
schedule = [
    # VisaSupport — recalculates grace period countdown for all active visa users
    {"agent": "visa_support", "cron": "0 6 * * *"},       # daily 6am

    # PauseAgent — checks burnout signals across all users
    {"agent": "pause_check",  "cron": "0 23 * * *"},      # nightly 11pm

    # DailyCheck — aggregates energy/mood patterns
    {"agent": "daily_check",  "cron": "0 23 * * *"},      # nightly 11pm

    # FinanceCheck — recalculates runway
    {"agent": "finance_check","cron": "0 8 * * 1"},       # every Monday 8am

    # InterviewPrep — generates next week's prep plan
    {"agent": "interview_prep","cron": "0 20 * * 0"},     # every Sunday 8pm
]
```

**Pattern 3 — Event-Driven (for triggered background work)**

Agents that activate when something specific changes in state:

```
User updates their resume → TalentMapper re-runs skill extraction
User mentions severance → Severance Agent re-activates
New source documents ingested → FactChecker pre-embeds chunks
Visa grace period crosses 14 days → VisaSupport escalates urgency
```

**Worker architecture:**

```
backend/
├── workers/
│   ├── plan_worker.py      # Redis queue consumer, runs Planner Agent
│   ├── health_worker.py    # Nightly PauseAgent + DailyCheck runs
│   └── scheduler.py        # Cron jobs — visa countdown, finance, interview prep
```

**Railway deployment — two separate services:**

```
Service 1: web     → uvicorn app.main:app --host 0.0.0.0 --port $PORT
Service 2: worker  → python workers/plan_worker.py
```

The web service handles all real-time user requests. The worker service processes background jobs from the Redis queue. Both share the same Supabase and Redis instances.

**Why this matters for user experience:**

A user who checks in at 9pm and opens the app at 8am the next morning should see their plan immediately — not wait 10 seconds for an LLM to generate it. Background processing means the plan is built while they sleep. The app feels instant because the work already happened.

This is the same pattern used in production by companies like Linear, Notion, and Vercel — expensive async work runs in background workers, user-facing responses are always fast.

---

*Last updated: April 2026*
*Concepts: LangGraph · RAG · pgvector · Windowed Memory · Structured Outputs · Eval-Driven Development*

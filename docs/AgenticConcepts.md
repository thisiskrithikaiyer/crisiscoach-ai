# CrisisCoach.AI — Full System Architecture

## Product Summary

CrisisCoach.AI is an AI-powered daily accountability coach for software engineers and AI engineers navigating career crises — primarily job loss and interview preparation. It is not a job board, resume tool, or chatbot. It is a coach that understands who you are, builds a personalized daily plan, checks in every day, and adjusts based on how you are actually doing.

**Core loop:** Onboard → Build plan → Daily check-in → Assess → Adjust → Repeat

**Target user:** SDE and AI Engineers facing layoff, active job search, or interview preparation

**Design principle:** Minimum input, maximum output. No long forms. Chip-based interactions. Under 30 seconds per check-in.

---

## Why CrisisCoach Exists

When a career crisis hits — a layoff, a visa deadline, a failed interview — the first thing that happens is panic. You cannot think clearly. You cannot prioritize. You open ten browser tabs, read five articles about what to do after a layoff, and close them all without doing anything. The uncertainty is paralyzing.

What you actually need in that moment is not more information. You need someone to hand you a plan and say — just do this today. Like having a dad who sat down, figured everything out, and said here is your next move. You just execute. You do not have to think. You just move.

That is what CrisisCoach does.

It asks you as few questions as possible. It does the thinking for you. It hands you three tasks for today — not a hundred resources, not a career framework, not a 60-day roadmap to read through. Three tasks. Do these.

And when you check them off — when you see that tracked sheet showing what you actually did today — something shifts. The uncertainty does not disappear but it becomes navigable. You have momentum. You are moving. And moving is everything when everything feels like it is falling apart.

CrisisCoach does not solve the crisis. It helps you stay functional inside it. It gives you structure when your brain cannot create structure. It holds you accountable when you want to give up. It pulls you back when you are burning out. And it adjusts — every single day — based on how you are actually doing, not how you planned to be doing.

This is not a productivity app. It is a support system built for the moments when you need one most.

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Agent Framework | LangGraph | Stateful graph-based orchestration, best for hierarchical multi-agent systems |
| Backend | FastAPI (Python) | Native Python, async support, integrates cleanly with LangGraph |
| Frontend | Next.js | v0.dev for UI generation, standard for AI products |
| Primary DB | Supabase (PostgreSQL) | Free tier, pgvector built in, handles structured + vector data |
| Cache / Session | Redis (Railway) | Fast session state, active plan, current agent context |
| Vector Store | pgvector (via Supabase) | Semantic memory, pattern detection, cited source retrieval |
| LLM | Claude Sonnet (Anthropic API) | Best instruction following for complex agent workflows |
| Observability | LangSmith | Agent tracing, debugging, LLM evaluation |
| Deployment | Railway | Simple deploy, free tier, supports FastAPI + Redis |
| Auth | Supabase Auth | Free, integrates with PostgreSQL, handles user sessions |

---

## Agent Roster

### Orchestrator Agent
- **Role:** Entry point for all user input. Reads message, determines intent, routes to correct agent
- **Routing logic:**
  - New user → Intake Agent
  - "I lost my job / need a plan" → Intake Agent → Planner Agent
  - "How did yesterday go" trigger → DailyTracker Agent
  - "I failed / plan not working" → Accountability Agent
  - "I'm exhausted / tired" → PauseAgent or MentalHealthCheck Agent
  - "Tell me about my interview" → InterviewPrep Agent
  - "Find me jobs" → JobStrategy Agent
- **Framework pattern:** LangGraph supervisor node with conditional edges

---

### Intake Agent
- **Role:** First ever conversation with a new user. Captures crisis context in minimum input
- **Collects:** Crisis type (layoff / both), urgency/timeline, field (SDE / AI Engineering), current mood
- **Output:** Structured user profile → writes to State Store → hands off to Planner Agent
- **Interaction pattern:** 4 chip groups, one optional free text box. No long forms.

---

### Planner Agent
- **Role:** Generates and updates the daily action plan
- **Inputs:** User profile from State Store, user insight from Personality Agent, plan history from UserMemory
- **Output:** 3 prioritized tasks for today, each with title, meta context, and priority level
- **Calls:** FactChecker Agent before delivering plan to user
- **Sits:** Outside the Agents subgraph — it is a coordinator not a worker

---

### Personality Agent
- **Role:** Parent agent that understands the user as a person over time
- **Sub-agents:**
  - **TalentMapper Agent** — maps skills, experience, tech stack, strengths, gaps, interests
  - **DailyCheck Agent** — tracks energy, mood, and behavioral patterns daily
- **Output:** User insight object → feeds Planner Agent
- **Key insight:** TalentMapper builds once and updates rarely. DailyCheck updates every single day.

---

### ProfileBuilder Agent
- **Role:** Builds and optimizes the user's professional presence
- **Sub-agents:**
  - **Resume Helper Agent** — analyzes resume, suggests improvements, tailors to target roles
  - **LinkedIn Enhancer Agent** — optimizes headline, About section, skills for SDE/AI Engineering roles
- **Sources:** Pulls from InterviewDB and CompanyDB for role-specific optimization
- **Triggered by:** Planner Agent during "enrich profile" tasks

---

### InterviewPrep Agent
- **Role:** Generates structured interview preparation plans based on target company and role
- **Sub-agents:**
  - **MockPrep Agent** — runs simulated interviews, evaluates answers, gives structured feedback
  - **PatternTracker Agent** — tracks which DSA and system design patterns are covered vs not covered
- **Sources:** InterviewDB (LeetCode patterns, Glassdoor questions, system design resources)
- **Output:** Daily prep tasks, pattern gaps, mock interview sessions

---

### JobStrategy Agent
- **Role:** Provides data-driven job search strategy, not generic advice
- **Sources:** StrategyDB (LinkedIn Workforce Reports, Levels.fyi, Layoffs.fyi, BLS data)
- **Output:** Cited, specific strategy recommendations — which companies to target, when to apply, networking vs cold apply rates
- **Key behavior:** Every recommendation cites its source

---

### MentalHealthCheck Agent
- **Role:** Detects acute emotional distress signals and responds with grounding techniques
- **Triggers:** "I can't do this", "I want to give up", "I hate myself", 3+ spiral indicators in one session
- **Sources:** WellnessDB (Mayo Clinic, APA, HelpGuide.org)
- **Output:** 1 grounding technique + 1 cited source + gentle redirect to plan
- **Critical rule:** Never provides therapy. Never diagnoses. Always redirects to professional resources for serious distress.
- **Distinction from PauseAgent:** MentalHealth handles acute crisis. PauseAgent handles burnout.

---

### PauseAgent
- **Role:** Detects overwork and burnout, intervenes with recovery habits
- **Triggers:**
  - 8+ tasks completed in one day
  - 3+ consecutive days with no rest
  - DailyCheck reports exhaustion 2+ days in a row
  - User messages logged after midnight
  - Zero social activity for 5+ days
- **Sources:** WellnessDB (Harvard Health, APA, Sleep Foundation, Greater Good Science Center)
- **Output:** 1 rest habit + 1 social nudge + 1 cited source
- **Key behavior:** Can override Planner — replaces task list with a rest day plan
- **Example response:**
  > "You've done 9 tasks in 2 days. That's not sustainable. Today's only job: go outside for 20 minutes. *(Source: Harvard Health — walking reduces cortisol)*"

---

### DailyTracker Agent
- **Role:** Manages the daily check-in loop
- **Triggered:** Every day at a consistent time (push notification / email nudge)
- **Flow:**
  1. Retrieve yesterday's plan from State Store
  2. Ask one question: "How did yesterday go?" + chip options
  3. Pass result to Accountability Agent
  4. Feed energy/mood signal to DailyCheck Agent
- **Interaction pattern:** Single question, 4 chips. Done in under 30 seconds.

---

### Accountability Agent
- **Role:** Assesses progress honestly and pushes back when user is avoiding
- **Inputs:** Progress update from DailyTracker, pattern data from DailyCheck
- **Behaviors:**
  - Tasks completed → celebrate + push forward immediately
  - Tasks partially done → honest assessment + adjusted plan
  - Tasks not started → direct pushback, identify blocker, redirect
  - Pattern of avoidance detected → escalate to Orchestrator for plan re-route
- **Tone:** Direct, warm, never harsh. Calls out avoidance without making user feel stupid.
- **Output:** Progress assessment → feeds back to Orchestrator if plan needs re-routing

---

### FactChecker Agent
- **Role:** Validates all advice against credible sources before it reaches the user
- **Process:**
  1. Receive advice chunk from Planner or any agent
  2. Query pgvector for semantically similar source documents
  3. Attach citation metadata to advice
  4. Flag as "general guidance" if no credible source found
- **Output format:**
  > "Apply to mid-size companies first. Mid-size companies hire 40% faster during tech downturns. *(Source: LinkedIn Workforce Report 2024)*"

---

### Severance Agent
- **Role:** Guides the user through everything that needs to happen when leaving a company. Runs once at onboarding if crisis type is layoff, then re-activates if user mentions severance-related topics later.
- **Triggers:** User mentions layoff on first session, or "I just got let go today"
- **Checks:**
  - Severance agreement reviewed?
  - COBRA / health insurance decision made?
  - 401k rollover decision made?
  - Non-compete clauses flagged?
  - Reference letters requested?
  - Equipment returned / access revoked?
  - Final paycheck / PTO payout confirmed?
- **Output:** Injects specific severance tasks into Planner on Day 1 and Day 2
- **Sources:** LegalDB (DOL, EEOC, SHRM, Nolo.com)
- **Key rule:** Never gives legal advice. Flags anything requiring an attorney. Always includes disclaimer.
- **How it integrates:** Runs invisibly. User never sees "Severance Agent ran." They just see specific actionable tasks in their daily plan with citations.

---

### FinanceCheck Agent
- **Role:** Estimates the user's financial runway so the Planner can calibrate urgency correctly. Short runway = speed-focused plan. Long runway = selective, quality-focused plan.
- **Triggers:** First session always. Re-activates if user mentions financial stress.
- **Checks:**
  - Unemployment benefits filed?
  - Monthly burn rate understood?
  - Emergency fund estimate?
  - Any freelance / contract options available?
  - Health insurance gap covered?
- **Output:** Runway estimate in weeks → stored in State Store → read by Planner on every plan generation
- **Example logic:**
  - Runway 8 weeks → Planner prioritizes volume and speed
  - Runway 6 months → Planner can be selective, prioritizes fit
- **Sources:** FinanceDB (DOL unemployment guides, state benefit portals, COBRA cost guides, IRS)
- **Key rule:** Never gives financial advice. Directs to official government resources for specifics.

---

### VisaSupport Agent
- **Role:** Guides users on visa-related options and deadlines when employment ends. Runs at onboarding if user selects visa pressure, and re-activates any time visa topics are mentioned.
- **Triggers:** Crisis type includes visa on onboarding, or user mentions OPT, STEM, H1B, grace period, status, transfer, layoff on visa
- **Covers:**
  - OPT — unemployment tracking days, 90-day limit, reporting requirements
  - STEM OPT — 24-month extension eligibility, employer E-Verify requirements
  - H1B — grace period (60 days), transfer process, cap-exempt employers, premium processing
  - H4 — EAD options, dependency on H1B principal status
  - Change of Status — B2 visitor status as bridge option
  - I-140 portability — if approved I-140 exists
- **Output:** Injects visa deadline tasks into Planner with urgency based on days remaining in grace period
- **Example tasks injected:**
  ```
  Task — CRITICAL: Contact immigration attorney this week
                   H1B grace period is 60 days from last day of employment
                   Source: USCIS.gov

  Task — HIGH: Check OPT unemployment day count
               OPT allows max 90 unemployed days total
               Source: ICE SEVP Portal

  Task — HIGH: Ask employer about H1B transfer timeline
               Transfer can be filed before grace period ends
               Source: USCIS.gov/h1b
  ```
- **Sources:** VisaDB (USCIS, ICE SEVP, DOL, travel.state.gov)
- **Key rule:** Never gives immigration legal advice. Always recommends consulting a licensed immigration attorney. Every output includes disclaimer.
- **Critical distinction:** Provides factual references from official government sources only. Never interprets law or advises on individual cases.

---

**How Severance, FinanceCheck, and VisaSupport plug into the daily loop:**

```
All three agents run ONCE at onboarding based on crisis type
→ Output stored in State Store:
   severance_tasks: [{title, meta, priority, completed}]
   finance_runway_weeks: 12
   visa_status: {type, grace_period_days_remaining, opt_days_used}
→ Planner reads all three on every plan generation
→ Relevant tasks injected into daily plan automatically
→ Agents re-activate only if user mentions related topics
```

**What the user sees on Day 1 after a layoff on H1B:**

```
Task 1 — CRITICAL: Contact immigration attorney this week
          H1B grace period is 60 days from last day of employment
          Source: USCIS.gov

Task 2 — HIGH: File for unemployment benefits today
          Clock starts from filing date — do not wait
          Source: DOL.gov

Task 3 — HIGH: Review severance agreement before signing
          You have 21 days — do not rush this
          Source: EEOC.gov
```

The agents work invisibly. The user just sees tasks that are specific, actionable, and cited.

---

## Database Architecture

### 1. State Store — PostgreSQL (Supabase)
Structured user data. Source of truth for user profile and plan history.

```sql
users (
  id UUID PRIMARY KEY,
  email TEXT,
  crisis_type TEXT,
  urgency TEXT,
  field TEXT,
  created_at TIMESTAMP
)

user_profiles (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  skills TEXT[],
  experience_years INT,
  tech_stack TEXT[],
  target_roles TEXT[],
  target_companies TEXT[],
  dsa_level TEXT,
  system_design_level TEXT,
  updated_at TIMESTAMP
)

daily_plans (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  plan_date DATE,
  tasks JSONB,
  generated_by TEXT,
  created_at TIMESTAMP
)

checkins (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  checkin_date DATE,
  response TEXT,
  mood TEXT,
  energy_level INT,
  notes TEXT,
  created_at TIMESTAMP
)
```

---

### 2. Memory — Redis (Railway)
Short-term session state. Fast reads. Expires after 24 hours. Also used as the background job queue.

```
# Session state
user:{user_id}:active_agent     → current agent handling the session
user:{user_id}:today_plan       → today's plan JSON
user:{user_id}:conversation     → last 10 messages for context window
user:{user_id}:last_checkin     → timestamp of last check-in

# Background job queue
queue:build_plan                → {user_id, checkin_data} — processed by plan_worker.py
queue:pause_check               → {user_id} — processed by health_worker.py
queue:interview_prep            → {user_id} — processed by scheduler.py
queue:job_strategy              → {user_id} — processed by scheduler.py
```

---

### 3. UserMemory — pgvector (Supabase)
Semantic memory. Enables pattern detection and personalization over time.

```sql
user_memories (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users,
  content TEXT,
  memory_type TEXT,
  embedding VECTOR(1536),
  created_at TIMESTAMP
)
```

---

### 4. InterviewDB — pgvector (Supabase)
Credible interview preparation resources. Chunked and embedded.

```sql
interview_resources (
  id UUID PRIMARY KEY,
  company TEXT,
  role TEXT,
  resource_type TEXT,
  content TEXT,
  source_url TEXT,
  publisher TEXT,
  date_published DATE,
  embedding VECTOR(1536),
  created_at TIMESTAMP
)
```

**Sources to ingest:**
- NeetCode.io — DSA pattern guides
- Glassdoor — company specific interview questions
- interviewing.io blog — real interview data
- Google, Meta, Stripe, Airbnb engineering blogs
- LeetCode discuss — community interview experiences

---

### 5. StrategyDB — pgvector (Supabase)
Job search strategy resources. Data-driven, cited.

```sql
strategy_resources (
  id UUID PRIMARY KEY,
  strategy_type TEXT,
  content TEXT,
  source_url TEXT,
  publisher TEXT,
  date_published DATE,
  embedding VECTOR(1536),
  created_at TIMESTAMP
)
```

**Sources to ingest:**
- LinkedIn Workforce Reports
- Bureau of Labor Statistics
- Levels.fyi hiring data
- Layoffs.fyi market trends

---

### 6. WellnessDB — pgvector (Supabase)
Mental health and recovery resources. Evidence-based only.

```sql
wellness_resources (
  id UUID PRIMARY KEY,
  resource_type TEXT,
  content TEXT,
  technique_name TEXT,
  source_url TEXT,
  publisher TEXT,
  date_published DATE,
  embedding VECTOR(1536),
  created_at TIMESTAMP
)
```

**Sources to ingest:**
- Mayo Clinic — stress management
- APA — job loss and mental health
- HelpGuide.org — anxiety and coping
- Harvard Health — exercise and stress
- Sleep Foundation — rest and recovery
- Greater Good Science Center (Berkeley)

---

### 7. CompanyDB — PostgreSQL (Supabase)
Structured company data for SDE/AI Engineering roles only.

```sql
companies (
  id UUID PRIMARY KEY,
  name TEXT,
  size TEXT,
  interview_process TEXT,
  typical_rounds INT,
  dsa_difficulty TEXT,
  system_design_required BOOL,
  ml_rounds BOOL,
  avg_time_to_offer_days INT,
  glassdoor_rating FLOAT,
  levels_fyi_url TEXT,
  hiring_status TEXT,
  updated_at TIMESTAMP
)
```

---

### 8. LegalDB — pgvector (Supabase)
Employment law and severance resources. General information only, never legal advice.

```sql
legal_resources (
  id UUID PRIMARY KEY,
  resource_type TEXT,         -- severance | cobra | non_compete | unemployment | 401k
  content TEXT,
  source_url TEXT,
  publisher TEXT,             -- DOL | EEOC | SHRM | Nolo
  date_published DATE,
  embedding VECTOR(1536),
  created_at TIMESTAMP
)
```

**Sources to ingest:**
- DOL.gov — unemployment filing guides, worker rights
- EEOC.gov — severance agreement rights, 21-day review rule
- SHRM.org — severance best practices
- Nolo.com — plain-English employment law guides
- Healthcare.gov — COBRA and health insurance gap guides

---

### 9. FinanceDB — pgvector (Supabase)
Financial runway and job loss financial resources. General guidance only, never financial advice.

```sql
finance_resources (
  id UUID PRIMARY KEY,
  resource_type TEXT,         -- unemployment | cobra_cost | emergency_fund | freelance | 401k_rollover
  state TEXT,                 -- US state for state-specific benefit guides
  content TEXT,
  source_url TEXT,
  publisher TEXT,             -- DOL | IRS | NerdWallet | state_portal
  date_published DATE,
  embedding VECTOR(1536),
  created_at TIMESTAMP
)
```

**Sources to ingest:**
- DOL.gov — state unemployment benefit guides
- IRS.gov — 401k rollover rules
- NerdWallet — COBRA cost guides, emergency fund calculators
- State unemployment portals — benefit amount calculators

---

### 11. VisaDB — pgvector (Supabase)
Official US immigration resources for OPT, STEM OPT, H1B, H4, and change of status. Official government sources only. Never legal advice.

```sql
visa_resources (
  id UUID PRIMARY KEY,
  visa_type TEXT,             -- opt | stem_opt | h1b | h4 | b2 | i140 | general
  topic TEXT,                 -- grace_period | transfer | extension | unemployment | ead | cap_exempt
  content TEXT,
  source_url TEXT,
  publisher TEXT,             -- USCIS | ICE_SEVP | DOL | travel_state_gov
  date_published DATE,
  embedding VECTOR(1536),
  created_at TIMESTAMP
)
```

**Sources to ingest:**
- USCIS.gov — H1B transfer, grace period, cap-exempt employers, I-140 portability
- ICE SEVP Portal (ice.gov/sevis) — OPT unemployment tracking, 90-day limit, reporting
- USCIS.gov/stem-opt — STEM OPT 24-month extension, E-Verify requirements
- USCIS.gov/h4-ead — H4 EAD eligibility and application
- Travel.state.gov — visa stamping, consular processing
- DOL.gov — H1B Labor Condition Application requirements
- USCIS.gov/change-of-status — B2 bridge option process

**Key ingestion rule:** Only ingest from official .gov sources. No third-party immigration blogs, no law firm websites, no forum posts. Every chunk must have a direct USCIS or government URL.

---

## LangGraph Agent Implementation Pattern

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict, Annotated
import operator

class CrisisCoachState(TypedDict):
    user_id: str
    messages: Annotated[list, operator.add]
    current_agent: str
    user_profile: dict
    today_plan: list
    checkin_response: str
    mood: str
    energy_level: int
    citations: list
    next_agent: str

def orchestrator_node(state: CrisisCoachState):
    intent = classify_intent(state["messages"][-1])

    # Runtime agents — respond immediately
    runtime_routing = {
        "new_user": "intake",
        "check_in": "daily_tracker",
        "plan_failing": "accountability",
        "distress": "mental_health_check",
        "visa": "visa_support",
    }

    # Background agents — push to Redis queue, return immediately
    background_routing = {
        "build_plan": "queue:build_plan",
        "overwork": "queue:pause_check",
        "interview": "queue:interview_prep",
        "job_search": "queue:job_strategy",
    }

    route = runtime_routing.get(intent) or background_routing.get(intent, "intake")
    return {"next_agent": route}

def build_crisis_coach_graph():
    graph = StateGraph(CrisisCoachState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("intake", intake_node)
    graph.add_node("planner", planner_node)
    graph.add_node("daily_tracker", daily_tracker_node)
    graph.add_node("accountability", accountability_node)
    graph.add_node("mental_health_check", mental_health_node)
    graph.add_node("pause", pause_node)
    graph.add_node("interview_prep", interview_prep_node)
    graph.add_node("job_strategy", job_strategy_node)
    graph.add_node("fact_checker", fact_checker_node)
    graph.add_node("talent_mapper", talent_mapper_node)
    graph.add_node("daily_check", daily_check_node)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        lambda state: state["next_agent"],
        {
            "intake": "intake",
            "planner": "planner",
            "daily_tracker": "daily_tracker",
            "accountability": "accountability",
            "mental_health_check": "mental_health_check",
            "pause": "pause",
            "interview_prep": "interview_prep",
            "job_search": "job_strategy"
        }
    )

    for agent in ["planner", "job_strategy", "interview_prep"]:
        graph.add_edge(agent, "fact_checker")

    graph.add_edge("fact_checker", END)
    graph.add_edge("intake", "planner")
    graph.add_edge("accountability", "orchestrator")
    graph.add_edge("daily_tracker", "accountability")
    graph.add_edge("mental_health_check", END)
    graph.add_edge("pause", END)

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)
```

---

## Folder Structure

```
crisiscoach/
├── main.py
├── api/
│   └── routes/
│       ├── chat.py
│       ├── checkin.py
│       ├── plan.py
│       └── auth.py
├── orchestrator/
│   ├── __init__.py
│   ├── graph.py                     # LangGraph graph definition
│   ├── orchestrator.py              # Orchestrator node logic
│   ├── router.py                    # Intent classification + routing logic
│   ├── state.py                     # CrisisCoachState TypedDict
│   └── context_builder.py           # Assembles minimal context per request
├── agents/
│   ├── runtime/                     # Triggered by user message — real time
│   │   ├── intake.py
│   │   ├── daily_tracker.py
│   │   ├── accountability.py
│   │   └── mental_health_check.py
│   ├── background/                  # Run on schedule or queue — never block user
│   │   ├── planner.py               # Builds tomorrow's plan after check-in
│   │   ├── pause_agent.py           # Nightly burnout signal check
│   │   ├── daily_check.py           # Nightly mood/energy aggregation
│   │   ├── visa_support_agent.py    # Daily grace period countdown
│   │   ├── finance_check_agent.py   # Weekly runway recalculation
│   │   ├── severance_agent.py       # Onboarding + event-driven
│   │   ├── talent_mapper.py         # Runs on profile update
│   │   ├── interview_prep.py        # Weekly prep plan generation
│   │   ├── job_strategy.py          # Weekly market data refresh
│   │   └── fact_checker.py          # Pre-embeds source chunks on ingestion
│   └── sub_agents/                  # Called by parent agents only
│       ├── resume_helper.py
│       ├── linkedin_enhancer.py
│       ├── mock_prep.py
│       └── pattern_tracker.py
├── workers/
│   ├── plan_worker.py               # Redis queue consumer — runs Planner Agent
│   ├── health_worker.py             # Nightly PauseAgent + DailyCheck runs
│   └── scheduler.py                 # Cron jobs — visa, finance, interview prep
├── eval/
│   ├── __init__.py
│   ├── datasets/
│   │   ├── intake_golden.json
│   │   ├── planner_golden.json
│   │   ├── accountability_golden.json
│   │   └── checkin_golden.json
│   ├── evaluators/
│   │   ├── plan_quality.py          # Is the plan specific, not generic?
│   │   ├── tone_check.py            # Is tone direct but not harsh?
│   │   ├── citation_check.py        # Does advice have citations?
│   │   └── routing_accuracy.py      # Did orchestrator route correctly?
│   ├── runners/
│   │   ├── run_evals.py             # Run all evals, output scores
│   │   └── langsmith_eval.py        # Push eval results to LangSmith
│   └── reports/                     # Eval output reports saved here
├── db/
│   ├── supabase.py
│   ├── redis.py
│   ├── vector_store.py
│   └── schemas/
│       ├── user.py
│       ├── plan.py
│       └── checkin.py
├── ingestion/
│   ├── interview_db.py
│   ├── strategy_db.py
│   ├── wellness_db.py
│   ├── legal_db.py
│   ├── finance_db.py
│   ├── visa_db.py
│   └── company_db.py
├── prompts/
│   ├── orchestrator.txt
│   ├── planner.txt
│   ├── intake.txt
│   ├── accountability.txt
│   ├── fact_checker.txt
│   ├── visa_support.txt
│   ├── severance.txt
│   ├── finance_check.txt
│   ├── pause_agent.txt
│   └── mental_health.txt
└── config.py
```

---

## Windowed Memory — How Context Is Built Per Request

The full chat history is never loaded into the LLM context. Only a minimal relevant slice is assembled per request. This keeps token costs low, responses fast, and the system from hanging on returning users.

**What loads on every session:**

```python
# orchestrator/context_builder.py
async def build_context(user_id: str, current_message: str) -> dict:
    return {
        # Last 10 messages only — not full history
        "recent_messages": await redis.get(f"user:{user_id}:conversation"),

        # Today's plan — small JSON object
        "today_plan": await redis.get(f"user:{user_id}:today_plan"),

        # Structured profile — name, skills, crisis type, field
        "user_profile": await supabase.get_profile(user_id),

        # Top 3 semantically relevant past patterns only
        "relevant_memories": await pgvector.search(
            query=current_message,
            user_id=user_id,
            limit=3
        )
    }
```

**What never loads into LLM context:**
- Full chat history from day 1
- All past daily plans
- All past check-ins
- Raw conversation logs

**Where full history lives:**
- PostgreSQL State Store — structured logs, queryable but never dumped into context
- pgvector UserMemory — embedded as vectors, only top-k relevant chunks retrieved per request

**Estimated context size per request:** 2000-3000 tokens regardless of how long the user has been on the platform. Day 1 and day 60 cost the same.

**This is called windowed memory.** The system gets smarter over time through pgvector semantic retrieval — not by loading more history into context.

---

## API Design

```
POST   /chat              — Main interaction, routes through agent graph
POST   /checkin           — Daily check-in submission
GET    /plan/today        — Fetch today's plan
PUT    /plan/{task_id}    — Mark task complete
GET    /profile           — Get user profile
POST   /onboard           — Submit intake form
GET    /streak            — Get current streak + history
POST   /auth/signup       — Create account via Supabase
POST   /auth/login        — Login via Supabase
```

---

## Environment Variables

```bash
ANTHROPIC_API_KEY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
REDIS_URL=
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=crisiscoach
APP_ENV=development
SECRET_KEY=
```

---

## Railway Deployment

Two services. Web handles real-time requests. Worker handles background jobs. Both share the same Supabase and Redis instances.

**Service 1 — Web (FastAPI)**
```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**Service 2 — Worker (Background Jobs)**
```toml
# railway.worker.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python workers/plan_worker.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**Procfile (alternative)**
```
web:    uvicorn main:app --host 0.0.0.0 --port $PORT
worker: python workers/plan_worker.py
```

**Background job schedule:**

| Job | Agent | Schedule |
|---|---|---|
| Build tomorrow's plan | Planner | After check-in (Redis queue) |
| Burnout check | PauseAgent | Nightly 11pm |
| Mood aggregation | DailyCheck | Nightly 11pm |
| Visa countdown | VisaSupport | Daily 6am |
| Runway recalculation | FinanceCheck | Every Monday 8am |
| Weekly prep plan | InterviewPrep | Every Sunday 8pm |
| Market data refresh | JobStrategy | Every Monday 6am |


*Last updated: April 2026*
*Stack: LangGraph · FastAPI · Supabase · Redis · Railway*

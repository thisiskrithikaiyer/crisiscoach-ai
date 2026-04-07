# CrisisCoach.AI — Eval Metrics & Cost Tracking

This document defines what to measure, why, and how to approach it. No hardcoded values — those get set once the system is running and real usage data exists.

---

## Philosophy

Two separate concerns. Keep them separate.

**Quality evals** — is the agent doing the right thing?
**Cost tracking** — how many tokens is each agent spending?

A cheap agent giving bad advice is worse than an expensive one giving good advice. Measure both independently, then optimize together.

---

## Part 1 — Token Cost Tracking

### What to Track Per Agent Call

Every agent call should log:

- Agent name
- Model used (Sonnet vs Haiku)
- Input token count
- Output token count
- Total token count
- Cost in USD (calculated from token counts + model pricing)
- Latency in milliseconds
- Run type (runtime vs background)
- User ID (for per-user cost analysis)
- Session ID (for per-session cost analysis)
- Timestamp

Store this in a local SQLite file during development. No external service needed. Query it with plain SQL.

---

### How to Instrument

Use a decorator pattern. Wrap every agent function with one line. The decorator intercepts the Anthropic API response, reads the `usage` object, calculates cost, and writes to SQLite before returning.

This means zero changes to agent logic. Cost tracking is a cross-cutting concern, not business logic.

---

### Token Budget Per Agent

Define a budget for each agent — maximum input tokens and maximum output tokens. The budget is not enforced automatically at first. It is a warning threshold.

When an agent exceeds its budget, log a warning with the agent name, actual count, and budget count. Over time this tells you which agents are running over and why.

**What to budget for each agent type:**

- **Orchestrator** — should be very cheap. It only classifies intent. Small input, tiny output.
- **DailyTracker** — small. One check-in question, short response.
- **Accountability** — medium input (reads plan + check-in), medium output (assessment + redirect).
- **MentalHealthCheck** — medium input, short output. One technique, one citation.
- **Planner** — largest background agent. Reads profile + history + injected tasks, outputs 3 structured tasks.
- **VisaSupport** — medium. Reads visa status, retrieves chunks from VisaDB, structured output.
- **FinanceCheck** — medium. Similar to VisaSupport.
- **Severance** — medium. Runs once at onboarding.
- **TalentMapper** — medium-large. Reads resume/profile, outputs structured skills object.
- **InterviewPrep** — large background agent. Reads skill gaps, outputs weekly prep plan.
- **MockPrep** — largest agent in the system. Full mock interview = many turns. Monitor closely.
- **FactChecker** — should be small. RAG retrieval + citation attachment only.
- **PauseAgent** — small. Reads burnout signals, outputs one technique.

---

### Cost Report

A script you run manually or on a cron. It queries SQLite and prints:

- Cost per agent for the time period
- Total calls per agent
- Average input and output tokens per agent
- Average latency per agent
- Total cost for the period
- Daily average cost
- Monthly cost projection
- Cost per 100 users projection
- Cost per 1000 users projection
- Top 3 most expensive agents
- Which agents are over budget and by how much

Run this weekly. Before every deploy. After any prompt change.

---

### Model Tiering — What to Track

Not every agent needs the same model. Track which model each agent uses so you can see cost savings from tiering.

Split agents into two tiers and track them separately:

**Haiku tier** — simple classification, routing, acknowledgement, citation lookup
- Orchestrator
- DailyTracker
- FactChecker

**Sonnet tier** — nuanced reasoning, plan generation, emotional response, high-stakes advice
- Planner
- Accountability
- MentalHealthCheck
- VisaSupport
- TalentMapper
- InterviewPrep
- MockPrep

Track cost by tier in the report so you can see the split and decide if any agent should move tiers.

---

### Response Caching — What to Track

Some agent outputs can be cached. Track cache hits vs misses per agent.

**Cacheable outputs:**
- FactChecker — same question, same source chunks → cache the citation output in Redis with TTL
- VisaSupport — visa rules don't change daily → cache at the content chunk level
- InterviewPrep — company-specific interview patterns don't change weekly → cache at the company level

Track:
- Cache hit rate per agent
- Tokens saved from cache hits
- Cost avoided from cache hits

This tells you whether caching is worth implementing and for which agents.

---

## Part 2 — Quality Evals

### Four Eval Dimensions

One evaluator per dimension. Each evaluator uses a judge prompt sent to Claude Haiku — cheaper than Sonnet, good enough for evaluation. Each evaluator produces a score and a pass/fail.

---

### Eval 1 — Plan Quality

**What it checks:** Are the tasks specific and actionable, not generic?

**Why it matters:** A generic plan is the core failure mode of CrisisCoach. "Update your resume" is useless. "Add a bullet to your Sabre experience describing the 9-agent system using XYZ metric" is useful.

**What to score:**
- Specificity — is the task concrete or vague?
- Actionability — can the user start immediately with no further thinking?
- Appropriateness — is this the right task given their crisis type, day number, and energy level?
- Citation presence — does each task have a source attached where relevant?

**How to run:**
Feed a generated plan + the user profile that generated it into a judge prompt. Ask the judge to score each task on each dimension. Average across tasks for an overall plan score.

**Golden dataset:**
A set of user profiles with known correct plans. Curated manually. Each case has a profile and the ideal plan output. Run the Planner against these profiles and score the output against the ideal.

**Pass threshold:** Define once you have baseline data from real usage.

---

### Eval 2 — Tone Check

**What it checks:** Is the agent response direct but not harsh? Does it avoid toxic positivity?

**Why it matters:** Two failure modes. Too soft = feels like a wellness app, user ignores it. Too harsh = user feels attacked, user leaves. The tone must thread this needle precisely per agent.

**What to score per agent:**
- Directness — does it say what needs to be said without softening the truth?
- Warmth — does it acknowledge the human without being patronizing?
- Toxic positivity check — does it avoid phrases like "You've got this!" or "Every setback is a setup for a comeback"?
- Harsh check — does it avoid making the user feel stupid or judged?
- Personality match — does the tone match the agent's defined personality?

**Per-agent tone expectations to evaluate against:**
- Accountability — direct and firm, never crushing
- MentalHealthCheck — steady and grounding, never clinical
- PauseAgent — calm, no urgency
- Planner — neutral, task-focused
- VisaSupport — precise and factual, never alarming

---

### Eval 3 — Citation Check

**What it checks:** Does every recommendation have a credible source attached?

**Why it matters:** CrisisCoach's core promise is that advice is grounded in real sources. An agent that gives uncited advice breaks the product contract.

**What to check:**
- Is a citation present?
- Is the citation from an approved source domain (USCIS.gov, Mayo Clinic, DOL.gov, etc.)?
- Does the citation match the content of the advice (not just any source)?
- Is the citation format consistent (Source: Publisher — page title)?

**Approved source domains to validate against:**
- Government: uscis.gov, dol.gov, eeoc.gov, irs.gov, ice.gov, bls.gov
- Medical: mayoclinic.org, apa.org, health.harvard.edu
- Career: glassdoor.com, linkedin.com/pulse, interviewing.io, neetcode.io
- Legal: nolo.com, shrm.org
- Finance: nerdwallet.com

Flag any citation from outside this list for manual review.

---

### Eval 4 — Routing Accuracy

**What it checks:** Did the Orchestrator send the user to the right agent?

**Why it matters:** A misroute means the wrong agent handles the message. A user saying "I'm overwhelmed" should go to MentalHealthCheck not DailyTracker. A user saying "help me prep for Google" should go to InterviewPrep not Planner.

**What to score:**
- Correct agent selected for input
- Correct run type (runtime vs background queue)
- No unnecessary agents triggered

**Golden dataset:**
A set of user messages with correct agent routing labels. Examples:
- "I lost my job" → Intake Agent
- "I can't do this anymore" → MentalHealthCheck
- "I did everything yesterday" → DailyTracker → Accountability
- "Tell me about H1B grace period" → VisaSupport
- "I need to prep for a Stripe interview" → InterviewPrep
- "I've been working 12 hours a day for a week" → PauseAgent

Score: percentage of messages routed correctly.

---

### Eval 5 — Background Agent Output Quality

**What it checks:** Did background agents produce usable output before the user needs it?

**Why it matters:** Background agents run while the user sleeps. If the Planner fails silently at 11pm, the user opens the app at 8am with no plan. This is a critical silent failure mode.

**What to check:**
- Did the agent complete successfully?
- Did it produce a valid structured output (Pydantic validation pass)?
- Did it complete within the time budget?
- Was the output stored correctly in PostgreSQL?
- If FactChecker ran, are citations attached?

**How to run:**
After every background worker run, validate the output written to PostgreSQL against the expected schema. Log pass/fail per user per agent per run.

---

## Part 3 — Eval Infrastructure

### Folder Structure

```
eval/
├── cost_tracker.py          # Token logging decorator + SQLite writer
├── data/
│   └── token_costs.db       # SQLite database — gitignored
├── datasets/
│   ├── planner_golden.json
│   ├── routing_golden.json
│   ├── tone_golden.json
│   └── checkin_golden.json
├── evaluators/
│   ├── plan_quality.py
│   ├── tone_check.py
│   ├── citation_check.py
│   ├── routing_accuracy.py
│   └── background_output.py
└── runners/
    ├── cost_report.py       # Print cost breakdown — run manually
    ├── run_evals.py         # Run all quality evals — run before deploy
    └── daily_summary.py     # Print overnight background agent results
```

---

### When to Run What

| Script | When to run | What it checks |
|---|---|---|
| `cost_report.py` | Weekly, before every deploy | Token costs by agent, projections |
| `run_evals.py` | Before every deploy, after every prompt change | All 4 quality dimensions |
| `daily_summary.py` | Every morning | Background agent success/failure overnight |
| `routing_accuracy.py` | After any Orchestrator prompt change | Routing correctness |
| `background_output.py` | After every background worker run | Structured output validity |

---

### LangSmith — What to Use It For

LangSmith is still useful but only for specific things. Do not use it for everything.

**Use LangSmith for:**
- Debugging a specific agent failure — the trace view is invaluable
- Comparing two prompt versions side by side
- Sharing traces with another engineer

**Do not use LangSmith for:**
- Routine cost tracking — your SQLite report is cheaper and faster
- Golden dataset evals — your local evaluators are sufficient
- Production monitoring — Railway logs + daily_summary.py is enough for MVP

This keeps LangSmith on the free developer tier indefinitely.

---

## Part 4 — Cost Optimization Triggers

These are the signals that should trigger a cost optimization investigation:

- Any agent consistently over its token budget
- Monthly projection exceeds your revenue per user
- One agent accounts for more than 30% of total cost
- Cache hit rate below 20% for cacheable agents
- Background agent latency exceeding time budget
- MockPrep cost spiking — this agent can get expensive fast

When a trigger fires, run `cost_report.py`, identify the agent, inspect its prompt for unnecessary context, consider model tiering down, and consider caching.

---

*Last updated: April 2026*
*Tooling: SQLite · Python · Claude Haiku (judge) · LangSmith (debugging only)*

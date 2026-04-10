from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crisiscoach.config import CORS_ORIGINS
from crisiscoach.api.routes import chat, checkin, plan, auth, profile, goal_plan, daily_log

app = FastAPI(title="CrisisCoach AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(checkin.router, prefix="/api", tags=["checkin"])
app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(goal_plan.router, prefix="/api", tags=["goal-plan"])
app.include_router(daily_log.router, prefix="/api", tags=["daily-log"])


@app.get("/health")
def health():
    return {"status": "ok"}

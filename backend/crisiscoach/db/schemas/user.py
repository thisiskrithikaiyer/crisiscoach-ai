from pydantic import BaseModel, EmailStr
from typing import Any


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    layoff_date: str | None = None
    visa_type: str | None = None
    visa_deadline: str | None = None
    monthly_expenses: float | None = None
    monthly_savings: float | None = None


class UserOut(BaseModel):
    id: str
    email: str
    layoff_date: str | None
    visa_type: str | None
    visa_deadline: str | None
    runway_weeks: int | None
    burnout_flag: bool
    talent_map: dict[str, Any] | None
    active: bool

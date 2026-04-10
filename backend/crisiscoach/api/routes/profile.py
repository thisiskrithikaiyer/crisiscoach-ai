from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from crisiscoach.api.routes.auth import get_current_user

router = APIRouter()


class ResumeUpload(BaseModel):
    text: str


class LinkedInUpload(BaseModel):
    text: str


@router.post("/resume")
async def upload_resume(body: ResumeUpload, user: dict = Depends(get_current_user)):
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        from crisiscoach.db.supabase import get_client
        sb = get_client()
        sb.table("users").update({"resume_text": body.text}).eq("id", user_id).execute()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/linkedin")
async def upload_linkedin(body: LinkedInUpload, user: dict = Depends(get_current_user)):
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        from crisiscoach.db.supabase import get_client
        sb = get_client()
        sb.table("users").update({"linkedin_text": body.text}).eq("id", user_id).execute()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

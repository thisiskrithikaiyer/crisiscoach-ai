from functools import lru_cache
from supabase import create_client, Client
from crisiscoach.config import SUPABASE_URL, SUPABASE_SERVICE_KEY


@lru_cache(maxsize=1)
def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

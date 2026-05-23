import os
import logging
from fastapi import FastAPI, HTTPException, Header
from metabase import fetch_leads
from logic import init_seen, run_checks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MetaBase Lead Alert Service")

RUN_SECRET = os.environ.get("RUN_SECRET", "")


def _check_secret(x_run_secret: str | None) -> None:
    if RUN_SECRET and x_run_secret != RUN_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.on_event("startup")
async def startup():
    """Pre-load today's entries so restarts don't send duplicate notifications."""
    try:
        df = fetch_leads()
        init_seen(df)
        logger.info(f"Startup: silently loaded {len(df)} existing entries")
    except Exception as e:
        logger.error(f"Startup preload failed: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run(x_run_secret: str | None = Header(default=None)):
    _check_secret(x_run_secret)
    df = fetch_leads()
    result = run_checks(df)
    logger.info(f"Run complete: {result}")
    return {"status": "done", **result}

# orchestrator/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import json
import os
from datetime import datetime

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(REDIS_URL)

app = FastAPI(title="MeetBot Orchestrator")

class ScheduleJob(BaseModel):
    user_id: str
    meet_link: str
    start_time: datetime
    end_time: datetime
    auth_cookie: str = None
    profile_storage_state: str = None

@app.post("/schedule")
async def schedule_job(job: ScheduleJob):
    if job.end_time <= job.start_time:
        raise HTTPException(400, "end_time must be after start_time")

    job_id = f"job:{int(datetime.utcnow().timestamp())}:{job.user_id}"

    payload = {
        "job_id": job_id,
        "user_id": job.user_id,
        "meet_link": job.meet_link,
        "start_time": job.start_time.isoformat(),
        "end_time": job.end_time.isoformat(),
        "auth_cookie": job.auth_cookie,
        "profile_storage_state": job.profile_storage_state
    }

    try:
        r.rpush("meet_jobs", json.dumps(payload))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to push job to Redis: {e}")

    return {"status": "scheduled", "job_id": job_id}

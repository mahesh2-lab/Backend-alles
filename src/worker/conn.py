from celery import Celery

from ..services.token_service import create_token
from ..utils.email_utils import send_email
import os
from dotenv import load_dotenv
import asyncio
import threading

load_dotenv()

# REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# celery_app = Celery(
#     "email_worker",
#     broker=REDIS_URL,
#     backend=REDIS_URL
    
# )

# celery_app.conf.worker_pool = "solo"


# @celery_app.task(bind=True, max_retries=5)
# def send_email_task(self, to_email: str, candidate_name: str, position: str, is_eligible: bool, candidate_id: str, evaluation_id: str, requisition_id: str):
#     """Celery background task with retry handling."""
    
    
#     user = {
#         "candidate_name": candidate_name,
#         "candidate_id": candidate_id,
#         "evaluation_id": evaluation_id,
#         "requisition_id": requisition_id
#     }
    
#     print(f"🚀 Task started: Sending email to {to_email} for position {position}, eligible: {is_eligible}, {candidate_name}")
#     try:
#         result = asyncio.run(create_token(user))
#         send_email(to_email, candidate_name, position, is_eligible, result["id"], result["password"])
#     except Exception as exc:
#         print(f"❌ Failed attempt: {exc}")
#         # raise self.retry(exc=exc, countdown=2 ** self.request.retries)  # exponential retry delay

def _run_coro_sync(coro):
    """Run a coroutine in a new thread to avoid calling asyncio.run in an already running loop."""
    result = {}
    exc = {}

    def _runner():
        try:
            result["value"] = asyncio.run(coro)
        except Exception as e:
            exc["e"] = e

    t = threading.Thread(target=_runner)
    t.start()
    t.join()

    if "e" in exc:
        raise exc["e"]
    return result.get("value")


def send_email_task( to_email: str, candidate_name: str, position: str, is_eligible: bool, candidate_id: str, evaluation_id: str, requisition_id: str):
    """Celery background task with retry handling."""


    user = {
        "candidate_name": candidate_name,
        "candidate_id": candidate_id,
        "evaluation_id": evaluation_id,
        "requisition_id": requisition_id
    }
    
    print(f"🚀 Task started: Sending email to {to_email} for position {position}, eligible: {is_eligible}, {candidate_name}")
    try:
        result = _run_coro_sync(create_token(user))
        send_email(to_email, candidate_name, position, is_eligible, result["id"], result["password"]) # type: ignore
    except Exception as exc:
        print(f"❌ Failed attempt: {exc}")
        # raise self.retry(exc=exc, countdown=2 ** self.request.retries)  # exponential retry delay
        # raise self.retry(exc=exc, countdown=2 ** self.request.retries)  # exponential retry delay

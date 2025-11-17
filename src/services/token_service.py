from livekit import api
import os
import uuid
from ..db.init_db import get_db
from fastapi import Body, HTTPException
from ..models.interview import Interview


def get_room_name() -> str:
    return uuid.uuid4().hex[:6]


async def create_token(user):

    db = next(get_db())

    if not os.getenv('LIVEKIT_API_KEY') or not os.getenv('LIVEKIT_API_SECRET'):
        raise HTTPException(
            status_code=500, detail="LiveKit API key and secret are not set in environment variables.")

    livekit_api_key = os.getenv('LIVEKIT_API_KEY')
    livekit_api_secret = os.getenv('LIVEKIT_API_SECRET')
    room = get_room_name()

    token = api.AccessToken(
        livekit_api_key,
        livekit_api_secret
    ).with_identity(user.get("candidate_name") or "interviewer").with_name(user.get("candidate_name") or "interviewer").with_grants(api.VideoGrants(
        room_join=True,
        room=room
    ))

    interview = Interview(
        room_name=room,
        token=token.to_jwt(),
        password=uuid.uuid4().hex[:5],
        candidate_profile_id=user.get("candidate_id"),
        requisition_id=user.get("requisition_id"),
        evaluation_id=user.get("evaluation_id")
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    return {
        "token": token.to_jwt(),
        "room": room,
        "id": interview.id,
        "password": interview.password
    }

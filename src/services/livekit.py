import os
from typing import Any, Dict
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from dotenv import load_dotenv

load_dotenv()


def verify_livekit_token(token: str) -> Dict[str, Any]:
    if not token:
        return {"valid": False, "error": "Token or secret missing"}

    secret = os.getenv("LIVEKIT_API_SECRET")
    if not secret:
        return {"valid": False, "error": "Token or secret missing"}

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return {"valid": True, "payload": payload}
    except ExpiredSignatureError:
        return {"valid": False, "error": "Token expired"}
    except InvalidTokenError as err:
        return {"valid": False, "error": str(err)}
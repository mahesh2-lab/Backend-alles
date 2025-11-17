from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.core.security import decode_token
from src.db.init_db import SessionLocal
from src.models.user import User

# Public endpoints that do NOT require authentication
PUBLIC_PATHS = {
    "/",
    "/health",
    "/api/docs",
    "/api/redoc",
    "/api/openapi.json",
    "/api/auth/register",
    "/api/auth/login",
    "/api/interview/analyze",
    "/api/interview/ws",
    "/api/interview/get-context",
    "/api/interview/get-data",
    "/api/interview/check-password",
}

# Public path prefixes
PUBLIC_PATH_PREFIXES = {
    "/api/interview/get-context/",
    "/api/interview/get-data/",
    "/api/interview/ws",
    "/api/interview/check-password",
}


class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Allow WebSocket traffic completely here
        if scope["type"] == "websocket":
            return await self.app(scope, receive, send)

        request = Request(scope, receive=receive)
        path = request.url.path

        # Skip auth if the route is public
        if path in PUBLIC_PATHS or any(path.startswith(prefix) for prefix in PUBLIC_PATH_PREFIXES):
            return await self.app(scope, receive, send)

        # Extract Bearer token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return await self._send_error(
                scope,
                receive,
                send,
                "auth_required",
                "Authentication required",
                {"WWW-Authenticate": "Bearer"}
            )

        token = auth_header.split("Bearer ")[1]

        # Decode JWT
        try:
            payload = decode_token(token)
        except Exception:
            return await self._send_error(
                scope,
                receive,
                send,
                "invalid_token",
                "Invalid or expired token",
                {"WWW-Authenticate": "Bearer"}
            )

        # Check payload validity & type
        if not isinstance(payload, dict) or payload.get("type") != "access":
            return await self._send_error(scope, receive, send, "invalid_token_type", "Invalid token type")

        # Validate user exists in DB
        db = SessionLocal()
        try:
            email = payload.get("sub")
            if not email:
                return await self._send_error(scope, receive, send, "invalid_token_payload", "Invalid token payload")

            user = db.query(User).filter(User.email == email).first()
            if not user:
                return await self._send_error(scope, receive, send, "user_not_found", "User not found")

            # Attach user to request.state
            scope.setdefault("state", {})
            scope["state"]["user"] = user

        finally:
            db.close()

        return await self.app(scope, receive, send)

    async def _send_error(self, scope, receive, send, code: str, message: str, headers: dict | None = None):
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "error": {"code": code, "message": message}},
            headers=headers or {},
        )
        await response(scope, receive, send)

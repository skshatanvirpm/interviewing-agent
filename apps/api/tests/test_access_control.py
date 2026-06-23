from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from interviewing_agent.config import Settings
from interviewing_agent.routes.dependencies import require_api_access
from interviewing_agent.services.access_control import (
    SlidingWindowRateLimiter,
    generate_session_access_token,
    hash_session_access_token,
    verify_session_access_token,
)


def make_app(*, token: str | None, limit: int = 0) -> FastAPI:
    app = FastAPI()
    app.state.settings = Settings(
        api_access_token=token,
        api_rate_limit_per_minute=limit,
        _env_file=None,
    )
    app.state.api_rate_limiter = SlidingWindowRateLimiter(limit)

    @app.get("/protected", dependencies=[Depends(require_api_access)])
    def protected_route() -> dict[str, bool]:
        return {"ok": True}

    return app


def test_access_control_is_optional_for_local_development() -> None:
    with TestClient(make_app(token=None)) as client:
        response = client.get("/protected")

    assert response.status_code == 200


def test_access_control_requires_matching_bearer_token() -> None:
    with TestClient(make_app(token="deployment-secret")) as client:
        missing = client.get("/protected")
        invalid = client.get(
            "/protected",
            headers={"Authorization": "Bearer incorrect"},
        )
        accepted = client.get(
            "/protected",
            headers={"Authorization": "Bearer deployment-secret"},
        )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert accepted.status_code == 200


def test_access_control_enforces_per_client_request_limit() -> None:
    with TestClient(make_app(token=None, limit=1)) as client:
        accepted = client.get("/protected")
        limited = client.get("/protected")

    assert accepted.status_code == 200
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"


def test_rate_limiter_tracks_each_client_key_independently() -> None:
    limiter = SlidingWindowRateLimiter(limit=1)

    assert limiter.allow("client-a") is True
    assert limiter.allow("client-a") is False
    assert limiter.allow("client-b") is True


def test_session_access_tokens_are_verified_by_hash() -> None:
    token = generate_session_access_token()
    token_hash = hash_session_access_token(token)

    assert token not in token_hash
    assert verify_session_access_token(token, token_hash) is True
    assert verify_session_access_token("wrong-token", token_hash) is False
    assert verify_session_access_token(token, None) is False

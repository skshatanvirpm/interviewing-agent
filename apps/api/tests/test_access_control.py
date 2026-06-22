from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from interviewing_agent.config import Settings
from interviewing_agent.routes.dependencies import require_api_access
from interviewing_agent.services.access_control import SlidingWindowRateLimiter


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


def test_access_control_enforces_global_request_limit() -> None:
    with TestClient(make_app(token=None, limit=1)) as client:
        accepted = client.get("/protected")
        limited = client.get("/protected")

    assert accepted.status_code == 200
    assert limited.status_code == 429
    assert limited.headers["retry-after"] == "60"

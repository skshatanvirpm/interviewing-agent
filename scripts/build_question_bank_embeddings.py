from __future__ import annotations

import sys
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
API_SRC = WORKSPACE_ROOT / "apps" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from interviewing_agent.config import Settings  # noqa: E402
from interviewing_agent.services.question_bank import QuestionBankService  # noqa: E402


def main() -> None:
    settings = Settings(_env_file=None)
    service = QuestionBankService(settings)
    output_path = service.write_jsonl()
    print(f"Wrote embedded question bank to {output_path}")


if __name__ == "__main__":
    main()

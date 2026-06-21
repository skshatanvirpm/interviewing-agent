from __future__ import annotations

from pathlib import Path


SOURCE_PATH = (
    Path(__file__).resolve().parents[1] / "docs" / "examples" / "question-bank-source.md"
)
OUTPUT_PATH = (
    Path(__file__).resolve().parents[1] / "apps" / "api" / "data" / "ml_questions.md"
)


def main() -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(source, encoding="utf-8")

    print(f"Wrote project-authored question bank to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

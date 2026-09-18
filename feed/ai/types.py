from dataclasses import dataclass


@dataclass
class AISummaryResult:
    summary: str
    tags: list[str]

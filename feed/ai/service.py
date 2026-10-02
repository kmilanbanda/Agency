import json

from .exceptions import AIResponseError
from .prompts import build_summary_prompt
from .providers import MockProvider
from .types import AISummaryResult


class AIService:
    def __init__(self, provider):
        self.provider = provider or MockProvider()

    def summarize_article(self, article):
        prompt = build_summary_prompt(article.content)

        # send prompt to provider
        response = self.provider.generate(prompt)

        # unload JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise AIResponseError("Provider returned invalid JSON") from exc

        if "summary" not in data:
            raise AIResponseError("Summary not included in agent's response")
        elif not isinstance(data["summary"], str):
            raise AIResponseError("Summary is not a string")
        summary = data["summary"]

        if "tags" not in data:
            raise AIResponseError("Tags not included in agent's response")

        tags = data["tags"]
        if not isinstance(data["tags"], list):
            raise AIResponseError("Tags is not a list")
        if not all(isinstance(tag, str) for tag in tags):
            raise AIResponseError("All tags must be strings")
        elif len(tags) < 3 or len(tags) > 7:
            raise AIResponseError(
                f"The number of tags should be between 3 and 7. (was {len(tags)})"
            )
        elif len(set(tags)) != len(tags):
            raise AIResponseError("There are duplicate tags")

        result = AISummaryResult(summary=summary, tags=tags)

        return result

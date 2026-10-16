import json

from django.conf import settings
from openai import OpenAI


class LLMProvider:
    def generate(self, prompt):
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate(self, prompt):
        response = self.client.responses.create(
            model=settings.OPENAI_MODEL,
            input=prompt,
            text={
                "format": {
                    "type": "json_object",
                }
            },
        )

        return response.output_text


class MockProvider(LLMProvider):
    def __init__(
        self,
        response=None,
        summary="[Mock] This is a great summary!",
        tags=None,
        exception=None,
    ):
        self.response = response
        self.summary = summary
        self.tags = tags or ["Mock", "AI", "Tags"]
        self.exception = exception

    def generate(self, _):
        if self.exception is not None:
            raise self.exception
        if self.response is not None:
            return self.response

        return json.dumps({"summary": self.summary, "tags": self.tags})

import json


class LLMProvider:
    def generate(self, prompt):
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    def generate(self, prompt):
        raise NotImplementedError


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

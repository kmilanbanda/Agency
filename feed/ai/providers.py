import json


class LLMProvider:
    def generate(self, prompt):
        raise NotImplementedError


class OpenAIProvider(LLMProvider):
    def generate(self, prompt):
        raise NotImplementedError


class MockProvider(LLMProvider):
    def generate(self, _):
        summary = "[Mock] This is a very good article!"
        tags = ["Mock", "Good", "Mock AI"]
        return json.dumps({"summary": summary, "tags": tags})

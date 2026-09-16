class LLMProvider:
    def generate(self, prompt):
        raise NotImplementedError


class MockProvider(LLMProvider):
    def generate(self, _):
        return "[Mock] This is a very good article!"

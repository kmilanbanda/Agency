from .prompt import SUMMARY_PROMPT
from .providers import OpenAIProvider


class AIService:
    def __init__(self, provider):
        self.provider = provider or OpenAIProvider()

    def summarize_article(self, article):
        prompt = SUMMARY_PROMPT.format(content=article.content)

        return self.provider.generate(prompt)

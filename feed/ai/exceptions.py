class AIError(Exception):
    pass


class AIProviderError(AIError):
    pass


class AIRateLimitError(AIProviderError):
    pass


class AIResponseError(AIError):
    pass

class AIError(Exception):
    pass


class AIProviderError(AIError):
    pass


class AIRateLimitError(AIError):
    pass


class AIResponseError(AIError):
    pass

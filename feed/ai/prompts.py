MAX_ARTICLE_CHARS = 2000

SUMMARY_PROMPT = """
Return only valid JSON.

Do not include markdown.

Do not include explanations.

Use this schema:

{
    "summary": "string",
    "tags": ["string", "..."]
}

If the article does not contain enough meaningful content,
return:

{
    "summary": "",
    "tags": []
}

Rules for summary:
 - Be concise
 - Avoid opinions
 - Preserve important details
 - Ignore advertisements, navigation text, cookie notices, and unrelated boilerplate
 - Only use information contained in the article
 - Do not infer or invent facts

Rules for tags:
 - Include between 3 to 7
 - No duplicates

Article:

{content}
"""


def build_summary_prompt(content):
    return SUMMARY_PROMPT.format(
        content=content[:MAX_ARTICLE_CHARS]
    )  # in a future update, limit by tokens, not chars

import json
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


def judge_review_comment(
    generated_comment: str, expected_issues: list[str], diff: str
) -> dict:
    """Score a generated comment from 1-5 for correctness using an LLM judge."""
    llm = ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
        temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"],
        max_tokens=512,
    )

    prompt = f"""You are evaluating an AI code reviewer's output.

EXPECTED ISSUES TO FIND:
{json.dumps(expected_issues)}

DIFF REVIEWED:
{diff[:1000]}

GENERATED REVIEW:
{generated_comment[:1500]}

Score the review on correctness from 1-5:
5 = found all expected issues with correct explanations
4 = found main issue, minor gaps
3 = partially correct
2 = found wrong issues or missed main one
1 = completely wrong or empty

Respond ONLY with JSON: {{"score": <1-5>, "reason": "<one sentence>"}}"""

    response = llm.invoke(prompt)
    try:
        return json.loads(response.content)
    except Exception:
        return {"score": 1, "reason": "parse error"}

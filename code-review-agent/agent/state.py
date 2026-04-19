from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    repo_name: str
    pr_number: int
    analysis: dict
    messages: Annotated[list, add_messages]
    current_issue: str
    current_patch: str
    execution_result: dict
    iteration: int
    max_iterations: int
    approved: bool
    escalate: bool
    review_issues: list[dict]
    final_comment: str

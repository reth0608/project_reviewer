from langgraph.graph import END, StateGraph

from agent.nodes.evaluate import evaluate_node
from agent.nodes.execute import execute_node
from agent.nodes.generate import generate_node
from agent.nodes.plan import plan_node
from agent.state import AgentState


def _route_after_evaluate(state: AgentState) -> str:
    if state.get("approved") or state.get("escalate"):
        return "done"
    return "retry"


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("plan", plan_node)
    builder.add_node("generate", generate_node)
    builder.add_node("execute", execute_node)
    builder.add_node("evaluate", evaluate_node)

    builder.set_entry_point("plan")
    builder.add_edge("plan", "generate")
    builder.add_edge("generate", "execute")
    builder.add_edge("execute", "evaluate")
    builder.add_conditional_edges(
        "evaluate",
        _route_after_evaluate,
        {"retry": "plan", "done": END},
    )
    return builder.compile()


_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph

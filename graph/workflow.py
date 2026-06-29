import logging
from langgraph.graph import StateGraph, END
from state.research_state import ResearchState

# Placeholder imports for agent nodes (to be implemented in Phase 2)
from agents.planner import planner_node
from agents.researcher import researcher_node
from agents.analyst import analyst_node
from agents.fact_checker import fact_checker_node
from agents.writer import writer_node

logger = logging.getLogger(__name__)

async def human_approval_node(state: ResearchState) -> ResearchState:
    """
    Interrupt node for human validation. 
    In a FastAPI context, this state is saved and paused.
    """
    logger.info(f"Awaiting human approval for topic: {state.get('topic')}")
    # Defaulting to pending to trigger the interrupt
    return {"approval_status": "pending"}

def approval_router(state: ResearchState) -> str:
    """
    Conditional edge router based on human approval status.
    """
    status = state.get("approval_status")
    if status == "approved":
        return "writer"
    elif status == "rejected":
        # Route back to planner to regenerate the scope
        return "planner"
    else:
        # If still pending, loop back to approval (LangGraph will pause execution here)
        return "human_approval"

def create_research_graph() -> StateGraph:
    """
    Compiles the LangGraph workflow for the multi-agent system.
    """
    workflow = StateGraph(ResearchState)

    # 1. Add Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("fact_checker", fact_checker_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("writer", writer_node)

    # 2. Define standard edges
    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "analyst")
    workflow.add_edge("analyst", "fact_checker")
    workflow.add_edge("fact_checker", "human_approval")
    
    # 3. Define conditional edges (The Gate)
    workflow.add_conditional_edges(
        "human_approval",
        approval_router,
        {
            "writer": "writer",
            "planner": "planner",
            "human_approval": "human_approval"
        }
    )

    # 4. End edge
    workflow.add_edge("writer", END)
    
    return workflow
import os
import uuid
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from langgraph.checkpoint.memory import MemorySaver

from graph.workflow import create_research_graph
from state.research_state import ResearchState

# Configure Production Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Agent Research API",
    description="Production-grade autonomous research and report generation system.",
    version="1.0.0"
)

# Initialize in-memory checkpointer for human-in-the-loop state persistence
memory = MemorySaver()

# Compile the graph with the checkpointer
# Note: We override the compile from Phase 1 to inject memory here
workflow = create_research_graph()
app_graph = workflow.compile(checkpointer=memory, interrupt_before=["human_approval"])


class ResearchRequest(BaseModel):
    topic: str

class ApprovalRequest(BaseModel):
    action: str # "approve", "reject", or "regenerate"

class ResearchResponse(BaseModel):
    thread_id: str
    status: str
    message: str


@app.post("/research", response_model=ResearchResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Initializes a new research workflow and returns a thread ID.
    The workflow will pause automatically at the human approval node.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = ResearchState(
        topic=request.topic,
        research_plan=[],
        urls=[],
        raw_documents=[],
        extracted_facts=[],
        verified_facts=[],
        citations=[],
        report_markdown="",
        report_pdf_path="",
        approval_status="pending"
    )

    # We run the graph invocation in the background so the API returns immediately
    async def run_graph():
        try:
            logger.info(f"Starting graph execution for thread {thread_id}")
            async for event in app_graph.astream(initial_state, config):
                for key, value in event.items():
                    logger.info(f"Node '{key}' completed.")
        except Exception as e:
            logger.error(f"Graph execution failed: {str(e)}")

    background_tasks.add_task(run_graph)

    return ResearchResponse(
        thread_id=thread_id,
        status="running",
        message="Research started. Poll /research/{thread_id}/status to check for human approval."
    )


@app.get("/research/{thread_id}/status")
async def get_status(thread_id: str):
    """
    Retrieves the current state of the research graph.
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = app_graph.get_state(config)
    
    if not state_snapshot or not state_snapshot.values:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    current_state = state_snapshot.values
    next_nodes = state_snapshot.next
    
    status = "running"
    if not next_nodes:
        status = "completed"
    elif "human_approval" in next_nodes:
        status = "awaiting_approval"
        
    return {
        "thread_id": thread_id,
        "status": status,
        "topic": current_state.get("topic"),
        "research_plan": current_state.get("research_plan", []),
        "verified_facts_count": len(current_state.get("verified_facts", [])),
        "report_pdf": current_state.get("report_pdf_path")
    }


@app.post("/research/{thread_id}/approve")
async def approve_research(thread_id: str, request: ApprovalRequest, background_tasks: BackgroundTasks):
    """
    Resumes a paused graph based on human input (approve/reject).
    """
    config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = app_graph.get_state(config)
    
    if not state_snapshot or "human_approval" not in state_snapshot.next:
        raise HTTPException(status_code=400, detail="Workflow is not awaiting approval.")
        
    if request.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'.")

    # Update the state with the human's decision
    app_graph.update_state(config, {"approval_status": f"{request.action}d"})

    # Resume graph execution in the background
    async def resume_graph():
        logger.info(f"Resuming graph execution for thread {thread_id} with action: {request.action}")
        async for event in app_graph.astream(None, config):
            for key, value in event.items():
                logger.info(f"Node '{key}' completed.")

    background_tasks.add_task(resume_graph)
    
    return {"status": "resumed", "action_taken": request.action}
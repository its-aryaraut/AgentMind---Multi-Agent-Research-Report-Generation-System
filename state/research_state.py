import operator
from typing import TypedDict, List, Dict, Any, Annotated
from pydantic import BaseModel, Field

class VerifiedFact(BaseModel):
    claim: str
    confidence: float
    sources: List[str]

class ResearchState(TypedDict):
    """
    Core state object passed between all LangGraph agents.
    Annotated[List, operator.add] ensures lists are appended to rather than overwritten,
    which is critical for parallel node execution.
    """
    topic: str
    research_plan: List[str]
    urls: Annotated[List[str], operator.add]
    raw_documents: Annotated[List[Dict[str, Any]], operator.add]
    extracted_facts: Annotated[List[Dict[str, Any]], operator.add]
    verified_facts: Annotated[List[VerifiedFact], operator.add]
    citations: Annotated[List[str], operator.add]
    report_markdown: str
    report_pdf_path: str
    approval_status: str # "pending", "approved", "rejected"
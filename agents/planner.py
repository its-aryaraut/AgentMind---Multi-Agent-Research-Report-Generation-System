import json
import logging
from typing import Dict, Any
from state.research_state import ResearchState
from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

async def planner_node(state: ResearchState) -> Dict[str, Any]:
    """
    Analyzes the user's topic and generates a structured research plan.
    """
    topic = state.get("topic")
    logger.info(f"Planner Agent initialized for topic: {topic}")

    llm_service = OllamaService(temperature=0.2)
    
    system_prompt = """
    You are a Senior Research Architect. Your job is to break down a given research topic 
    into 5-6 highly specific, non-overlapping subtopics that ensure comprehensive coverage.
    You must return a valid JSON object with a single key "subtopics" containing a list of strings.
    Example: {"subtopics": ["History", "Current State", "Technical Challenges"]}
    """
    
    user_prompt = f"Create a research plan for the topic: {topic}"

    try:
        response_text = await llm_service.generate_json(system_prompt, user_prompt)
        
        # Clean the response in case the model wraps it in markdown code blocks
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        parsed_plan = json.loads(clean_json)
        
        subtopics = parsed_plan.get("subtopics", [])
        if not subtopics:
            raise ValueError("LLM returned empty subtopics list.")
            
        logger.info(f"Research plan generated: {subtopics}")
        
        # We return only the keys in ResearchState that we want to update
        return {"research_plan": subtopics}
        
    except Exception as e:
        logger.error(f"Planner node failed: {str(e)}")
        # Fallback plan in case of failure to keep the graph moving
        fallback_plan = [
            f"{topic} Overview", 
            f"{topic} Key Concepts", 
            f"{topic} Industry Impact"
        ]
        return {"research_plan": fallback_plan}
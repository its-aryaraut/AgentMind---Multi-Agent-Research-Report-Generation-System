import json
import logging
import asyncio
from typing import Dict, Any, List
from state.research_state import ResearchState
from services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

async def _analyze_document(doc: Dict[str, Any], llm: OllamaService) -> List[Dict[str, Any]]:
    """
    Extracts structured facts from a single document.
    """
    content = doc.get("content", "")
    # Truncate content to avoid blowing up the context window (Qwen3:8B handles 8k well, but play it safe)
    if len(content) > 15000:
        content = content[:15000]
        
    system_prompt = """
    You are an Expert Data Analyst. Extract strictly factual key findings, statistics, 
    and trends from the provided text. Ignore fluff and marketing speak.
    Return a valid JSON object with a single key "facts" containing a list of objects.
    Each object must have:
    - "claim": The specific fact or statistic.
    - "context": Brief context around the fact.
    Example: {"facts": [{"claim": "AI market to reach $500B by 2027", "context": "Global revenue projection"}]}
    """
    
    user_prompt = f"Source Title: {doc.get('title')}\n\nContent:\n{content}"
    
    try:
        response_text = await llm.generate_json(system_prompt, user_prompt)
        clean_json = response_text.replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(clean_json)
        
        facts = parsed_data.get("facts", [])
        # Attach the source URL to each fact for traceability
        for fact in facts:
            fact["source_url"] = doc.get("url")
            
        return facts
    except Exception as e:
        logger.error(f"Failed to analyze document {doc.get('url')}: {str(e)}")
        return []

async def analyst_node(state: ResearchState) -> Dict[str, Any]:
    """
    Processes raw documents to extract key facts and statistics.
    """
    raw_documents = state.get("raw_documents", [])
    logger.info(f"Analyst Agent processing {len(raw_documents)} documents.")
    
    llm_service = OllamaService(temperature=0.1) # Low temperature for analytical precision
    
    # Process all documents concurrently
    tasks = [_analyze_document(doc, llm_service) for doc in raw_documents]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    extracted_facts = []
    for res in results:
        if not isinstance(res, Exception):
            extracted_facts.extend(res)
            
    logger.info(f"Analyst Agent extracted {len(extracted_facts)} raw facts.")
    
    return {"extracted_facts": extracted_facts}
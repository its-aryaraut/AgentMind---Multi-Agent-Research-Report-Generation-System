import logging
from typing import Dict, Any, List
from state.research_state import ResearchState, VerifiedFact

logger = logging.getLogger(__name__)

async def fact_checker_node(state: ResearchState) -> Dict[str, Any]:
    """
    Validates extracted facts, assigns confidence scores, and deduplicates claims.
    In a full implementation, this might use an LLM to cross-reference claims against
    the source text again, but here we implement a fast programmatic filter based on 
    the metadata gathered by the Analyst.
    """
    extracted_facts = state.get("extracted_facts", [])
    logger.info(f"Fact Checker Agent validating {len(extracted_facts)} claims.")
    
    verified_facts: List[VerifiedFact] = []
    citations_set = set()
    
    # Group similar claims to build confidence and multiple sources
    claim_map = {}
    for fact in extracted_facts:
        claim_text = fact.get("claim", "")
        source_url = fact.get("source_url")
        
        if not claim_text or not source_url:
            continue
            
        # Simplistic grouping (in production, use embedding similarity here)
        claim_key = claim_text.lower()
        if claim_key not in claim_map:
            claim_map[claim_key] = {
                "original_claim": claim_text,
                "sources": set()
            }
        
        claim_map[claim_key]["sources"].add(source_url)
        citations_set.add(source_url)

    # Assign confidence scores based on source corroboration
    for data in claim_map.values():
        source_count = len(data["sources"])
        # Base confidence 0.7 for a single source, +0.1 for each additional source (max 0.99)
        confidence = min(0.99, 0.70 + (0.10 * (source_count - 1)))
        
        verified_facts.append(VerifiedFact(
            claim=data["original_claim"],
            confidence=round(confidence, 2),
            sources=list(data["sources"])
        ))

    # Sort by highest confidence first
    verified_facts.sort(key=lambda x: x.confidence, reverse=True)
    
    # Keep only facts with a confidence >= 0.7
    highly_verified = [f for f in verified_facts if f.confidence >= 0.7]

    logger.info(f"Fact Checker approved {len(highly_verified)} facts. Generating citations.")
    
    return {
        "verified_facts": highly_verified,
        "citations": list(citations_set),
        # Route to approval gate next (handled by graph logic)
        "approval_status": "pending" 
    }
import logging
import asyncio
from typing import Dict, Any, List
from state.research_state import ResearchState
from services.tavily_service import TavilySearchService
from services.firecrawl_service import FirecrawlService

logger = logging.getLogger(__name__)

async def _research_subtopic(subtopic: str, tavily: TavilySearchService, firecrawl: FirecrawlService) -> Dict[str, Any]:
    """
    Helper function to search and scrape a single subtopic.
    """
    logger.info(f"Researching subtopic: {subtopic}")
    
    # 1. Search for sources
    search_results = await tavily.execute_search(query=subtopic, max_results=3)
    
    urls_found = []
    documents_scraped = []
    
    # 2. Scrape the content of each found URL
    for result in search_results:
        url = result.get("url")
        if not url:
            continue
            
        urls_found.append(url)
        content = await firecrawl.scrape_url(url)
        
        if content:
            documents_scraped.append({
                "subtopic": subtopic,
                "title": result.get("title"),
                "url": url,
                "content": content,
                "source": "firecrawl"
            })
            
    return {
        "urls": urls_found,
        "documents": documents_scraped
    }

async def researcher_node(state: ResearchState) -> Dict[str, Any]:
    """
    Executes parallel research tasks based on the generated plan.
    """
    research_plan = state.get("research_plan", [])
    logger.info(f"Researcher Agent starting execution for {len(research_plan)} subtopics.")

    tavily_service = TavilySearchService()
    firecrawl_service = FirecrawlService()

    # Create concurrent tasks for all subtopics
    tasks = [
        _research_subtopic(subtopic, tavily_service, firecrawl_service) 
        for subtopic in research_plan
    ]
    
    # Execute all searches and scrapes in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_urls = []
    all_documents = []

    # Aggregate the results
    for res in results:
        if isinstance(res, Exception):
            logger.error(f"A subtopic research task failed: {str(res)}")
            continue
            
        all_urls.extend(res.get("urls", []))
        all_documents.extend(res.get("documents", []))

    logger.info(f"Research complete. Found {len(all_urls)} URLs and scraped {len(all_documents)} documents.")

    # Return state updates. Because these are Annotated with operator.add in the state schema,
    # LangGraph will automatically append these to the existing lists rather than overwriting them.
    return {
        "urls": all_urls,
        "raw_documents": all_documents
    }
import os
import logging
import asyncio
from typing import List, Dict, Any
from tavily import AsyncTavilyClient

logger = logging.getLogger(__name__)

class TavilySearchService:
    def __init__(self):
        # Replace this string with your actual key
        api_key = "Your_Tavily_API_Key_Here"  # Replace with your actual Tavily API key
        
        if not api_key:
            raise ValueError("TAVILY_API_KEY environment variable is missing.")
        self.client = AsyncTavilyClient(api_key=api_key)

    async def execute_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Executes an asynchronous search to gather sources for a specific subtopic.
        """
        try:
            logger.info(f"Executing Tavily search for query: {query}")
            response = await self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_images=False
            )
            
            # Standardize output for the Research State
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "score": item.get("score", 0.0)
                })
            return results
        except Exception as e:
            logger.error(f"Tavily search failed for query '{query}': {str(e)}")
            return []
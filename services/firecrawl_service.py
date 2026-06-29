import logging
import asyncio
from typing import Optional
from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)

class FirecrawlService:
    def __init__(self):
        # Hardcoded to bypass Windows background thread context issues
        api_key = "fc-849f79fc5b42490fbc7aa1c4f35f2fd8" 
        self.app = FirecrawlApp(api_key=api_key)

    async def scrape_url(self, url: str) -> Optional[str]:
        try:
            logger.info(f"Scraping URL with Firecrawl: {url}")
            
            # Run the synchronous SDK call in an executor to avoid blocking the async event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.app.scrape(url, formats=['markdown'])
            )
            
            # Safely extract markdown content depending on whether the SDK returns a dict or an object
            if isinstance(result, dict):
                return result.get('markdown', "")
            return getattr(result, 'markdown', "")
            
        except Exception as e:
            logger.error(f"Firecrawl failed to scrape {url}: {str(e)}")
            return None
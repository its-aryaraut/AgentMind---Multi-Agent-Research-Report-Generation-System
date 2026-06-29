import os
import logging
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

class OllamaService:
    # Change the default model_name here
    def __init__(self, model_name: str = "qwen3:14b", temperature: float = 0.2):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name
        self.llm = ChatOllama(
            base_url=self.base_url,
            model=self.model_name,
            temperature=temperature,
            format="json" 
        )

    async def generate_json(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generates a JSON response from the local Qwen model.
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Ollama inference failed: {str(e)}")
            raise RuntimeError(f"Failed to communicate with local LLM: {str(e)}")
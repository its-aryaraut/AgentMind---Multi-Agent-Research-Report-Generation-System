import os
import logging
from typing import Dict, Any
from state.research_state import ResearchState
from services.ollama_service import OllamaService
from services.pdf_generator import PDFGeneratorService

logger = logging.getLogger(__name__)

async def writer_node(state: ResearchState) -> Dict[str, Any]:
    """
    Synthesizes the verified facts into a comprehensive, professional Markdown report 
    and generates the final PDF.
    """
    topic = state.get("topic")
    verified_facts = state.get("verified_facts", [])
    citations = state.get("citations", [])
    
    logger.info(f"Writer Agent compiling report for: {topic}")
    
    llm_service = OllamaService(temperature=0.4) # Slightly higher temp for writing flow
    pdf_service = PDFGeneratorService()
    
    # Prepare data payload for the LLM
    facts_payload = "\n".join([f"- {f.claim} (Confidence: {f.confidence})" for f in verified_facts])
    
    system_prompt = """
    You are a Principal Industry Analyst. Your objective is to write a comprehensive, 
    evidence-based research report (2000-3000 words).
    
    MANDATORY STRUCTURE:
    # Executive Summary
    # Introduction
    # Research Findings
    # Industry Analysis
    # Challenges
    # Future Outlook
    # Conclusion
    
    RULES:
    - Write in a professional, consulting style (like McKinsey or Gartner).
    - Rely EXCLUSIVELY on the provided facts. Do not hallucinate external data.
    - Ensure logical transitions between sections.
    - Output ONLY pure Markdown. Do not wrap in JSON or backticks.
    """
    
    user_prompt = f"Topic: {topic}\n\nVerified Facts:\n{facts_payload}"
    
    try:
        # Note: For OllamaService here, we bypass generate_json and use standard generation
        # Assuming you add a standard `generate_text` method to OllamaService
        # For simplicity in this script, we'll invoke the LLM directly
        messages = [
            ("system", system_prompt),
            ("human", user_prompt)
        ]
        
        # Disable JSON format enforcement for the writing stage
        llm_service.llm.format = "" 
        response = await llm_service.llm.ainvoke(messages)
        report_markdown = response.content.strip()
        
        # Append Citations manually to ensure they are captured accurately
        report_markdown += "\n\n# References\n"
        for i, url in enumerate(citations, 1):
            report_markdown += f"{i}. {url}\n"
            
        # Save Markdown to disk
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        
        safe_topic_name = topic.replace(" ", "_").lower()
        md_path = f"{reports_dir}/{safe_topic_name}_report.md"
        pdf_path = f"{reports_dir}/{safe_topic_name}_report.pdf"
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_markdown)
            
        # Generate PDF
        pdf_success = await pdf_service.generate_pdf(report_markdown, pdf_path)
        if not pdf_success:
            logger.warning("PDF generation failed, falling back to Markdown only.")
            pdf_path = md_path
            
        logger.info(f"Report generation complete: {pdf_path}")
        
        return {
            "report_markdown": report_markdown,
            "report_pdf_path": pdf_path,
            "approval_status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Writer node failed: {str(e)}")
        return {"approval_status": "failed"}
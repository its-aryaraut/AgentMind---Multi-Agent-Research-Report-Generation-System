import os
import logging
import markdown
import pdfkit
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class PDFGeneratorService:
    def __init__(self):
        # Basic CSS to ensure the PDF looks like a professional consulting report
        self.css_style = """
        <style>
            body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; margin: 40px; }
            h1 { color: #2C3E50; border-bottom: 2px solid #34495E; padding-bottom: 10px; }
            h2 { color: #2980B9; margin-top: 30px; }
            h3 { color: #7F8C8D; }
            p { text-align: justify; }
            blockquote { border-left: 4px solid #BDC3C7; padding-left: 15px; color: #7F8C8D; font-style: italic; }
            ul, ol { margin-bottom: 20px; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #BDC3C7; padding: 8px; text-align: left; }
            th { background-color: #ECF0F1; }
        </style>
        """

    async def generate_pdf(self, markdown_content: str, output_path: str) -> bool:
        """
        Converts Markdown text to a formatted PDF.
        """
        try:
            logger.info(f"Generating PDF report at {output_path}")
            
            # Convert Markdown to HTML with extension support for tables and code blocks
            html_content = markdown.markdown(
                markdown_content, 
                extensions=['extra', 'tables', 'fenced_code']
            )
            
            # Inject CSS
            full_html = f"<!DOCTYPE html><html><head>{self.css_style}</head><body>{html_content}</body></html>"
            
            # Configure pdfkit options (adjust path if wkhtmltopdf is installed elsewhere)
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'custom-header': [
                    ('Accept-Encoding', 'gzip')
                ],
                'no-outline': None
            }

            # Run synchronous PDF generation in a threadpool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: pdfkit.from_string(full_html, output_path, options=options)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            return False
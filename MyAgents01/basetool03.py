import logging
import subprocess
import os
import re
from typing import Dict, List, Optional
from jinja2 import Template
import requests  # For LLM API calls

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

class BaseTool:
    def __init__(self, llm_api_key: Optional[str] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm_api_key = llm_api_key  # For LLM API calls (e.g., Claude 3.7, Devstrai)
    
    def _log(self, message: str, level: str = "info"):
        if level == "info":
            self.logger.info(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
    
    def _call_llm(self, prompt: str) -> str:
        """Call an external LLM API (e.g., Claude 3.7, Devstrai)"""
        if not self.llm_api_key:
            self._log("LLM API key not provided. Skipping AI suggestions.", "warning")
            return ""
        
        try:
            # Example: Claude 3.7 API call (replace with actual endpoint)
            headers = {"Authorization": f"Bearer {self.llm_api_key}"}
            response = requests.post(
                "https://api.anthropic.com/v1/messages",   # Claude API
                headers=headers,
                json={"prompt": prompt, "model": "claude-3-opus-20240229", "max_tokens": 1000}
            )
            return response.json().get("content", "")
        except Exception as e:
            self._log(f"LLM API call failed: {str(e)}", "error")
            return ""
    
    def _ask_human_feedback(self, question: str) -> str:
        """Prompt user for input (GitHub Copilot-style interaction)"""
        self._log(f"[Human Feedback Required] {question}", "warning")
        response = input(f"🤖 {question} (Type 'skip' to bypass): ")
        return response.strip()
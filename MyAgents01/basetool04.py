class BaseTool:
    def __init__(self, tool_name: str, llm_api_key: Optional[str] = None):
        self.logger = logging.getLogger(tool_name)
        self.llm_api_key = llm_api_key
    
    def _ask_human_feedback(self, question: str) -> str:
        """Interactive GitHub Copilot-style feedback"""
        print(f"🤖 {question}")
        return input("Your response: ").strip()
    
    def _call_llm(self, prompt: str) -> str:
        """Mock LLM API call (replace with real service like Claude 3.7)"""
        if not self.llm_api_key:
            return "[LLM] API key missing - cannot generate suggestions"
        return f"[LLM] Suggested fix for '{prompt[:50]}...'"
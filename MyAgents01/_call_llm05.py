    def _call_llm(self, prompt: str) -> str:
        """Mock LLM API call (replace with real service like Claude 3.7 [[4]])."""
        if not self.llm_api_key:
            return "[LLM] API key missing - cannot generate suggestions"
        return f"[LLM Suggestion] Fix: {prompt.split(':')[0]}"
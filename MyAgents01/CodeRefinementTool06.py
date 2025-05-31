class CodeRefinementTool:
    # ... (previous code)

    @log_activity
    @handle_errors
    def refine_code(self, code: str, task: str) -> str:
        """Refine code using LLM suggestions and human feedback."""
        prompt = f"Refine this code for {task}: {code}"
        refined_code = self._call_llm(prompt)
        
        # Interactive validation
        print(f"🔍 Proposed refinement:\n{refined_code}")
        feedback = self._ask_human_feedback("Accept changes? (y/n)")
        
        if feedback.lower() == "y":
            return refined_code
        else:
            manual_edit = input("Enter manual edits: ")
            return manual_edit or code  # Fallback to original if empty
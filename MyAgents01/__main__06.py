if __name__ == "__main__":
    tool = CodeRefinementTool("PythonCodeRefiner", llm_api_key="mock-key")
    
    # Sample code to refine
    code = """
    def add(a, b):
        return a + b
    """
    
    refined = tool.refine_code(code, "type hints and docstring")
    print("Final Code:\n", refined)
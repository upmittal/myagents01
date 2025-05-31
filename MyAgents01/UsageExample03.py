# Initialize tools with LLM API key
llm_key = "your_claude_api_key_here"
code_retriever = TfsCodeRetrieverTool(llm_key)
vb_converter = VBNetConverterTool(llm_key)

# Run tasks
result = code_retriever.run(tfs_repo_url="http://tfs.example.com/project", local_path="./legacy_code")
if result["status"] == "success":
    vb_converter.run(vb_project_path="./legacy_code/MyApp.vbproj")
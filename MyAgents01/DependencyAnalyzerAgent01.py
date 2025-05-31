dependency_analyzer = Agent(
    role="Dependency Analyzer",
    goal="Analyze namespaces, NuGet packages, and common libraries; flag unsupported elements like ITASCA",
    tools=[CodeExecutionTool(), GitTool()],
    verbose=True,
    backstory="Identifies outdated dependencies and legacy namespaces requiring human intervention."
)
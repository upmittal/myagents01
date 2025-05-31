report_generator = Agent(
    role="Report Generator",
    goal="Compile upgrade reports, including errors, fixes, and options for non-upgradable projects",
    tools=[CodeExecutionTool()],
    verbose=True,
    backstory="Documents the entire upgrade process and provides actionable recommendations."
)
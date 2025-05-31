deployment_agent = Agent(
    role="Deployment Engineer",
    goal="Deploy upgraded applications to IIS on a VM and validate basic functionality",
    tools=[CodeExecutionTool(), GitTool()],
    verbose=True,
    backstory="Automates deployment to IIS and ensures compatibility with the new framework."
)
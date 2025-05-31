upgrade_coordinator = Agent(
    role="Upgrade Coordinator",
    goal="Upgrade .csproj files to target framework, resolve build errors, and commit changes",
    tools=[CodeExecutionTool(), GitTool()],
    verbose=True,
    backstory="Manages framework upgrades and ensures build stability post-changes."
)
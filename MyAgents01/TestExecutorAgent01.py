test_executor = Agent(
    role="Test Automation Engineer",
    goal="Trigger NeoLoad validation tests (1-user) and report results",
    tools=[CodeExecutionTool()],
    verbose=True,
    backstory="Validates performance and stability post-upgrade using automated testing tools."
)
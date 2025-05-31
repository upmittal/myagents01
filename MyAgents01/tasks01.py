# Task 1: Retrieve code from TFS
task1 = Task(
    description="Fetch code from TFS and initialize Git repository",
    agent=code_retriever,
    expected_output="Git repository initialized with TFS code."
)

# Task 2: Convert VB.NET to C#
task2 = Task(
    description="Convert VB.NET projects to C#, create a new branch, and validate builds",
    agent=vb_converter,
    expected_output="C#-converted code with successful builds."
)

# Task 3: Analyze dependencies
task3 = Task(
    description="Scan for ITASCA namespaces, outdated NuGet packages, and legacy libraries",
    agent=dependency_analyzer,
    expected_output="List of unsupported dependencies and flagged namespaces."
)

# Task 4: Upgrade framework
task4 = Task(
    description="Update .csproj files to target .NET 8, resolve errors, and commit changes",
    agent=upgrade_coordinator,
    expected_output="Upgraded projects with successful builds."
)

# Task 5: Deploy to IIS
task5 = Task(
    description="Deploy application to IIS on a VM and verify basic functionality",
    agent=deployment_agent,
    expected_output="Application deployed to IIS with no critical errors."
)

# Task 6: Run NeoLoad tests
task6 = Task(
    description="Execute NeoLoad tests with 1 user and validate performance metrics",
    agent=test_executor,
    expected_output="Test results confirming stability."
)

# Task 7: Generate report
task7 = Task(
    description="Compile final report with upgrade details, errors, and options for unresolved issues",
    agent=report_generator,
    expected_output="Comprehensive PDF/HTML report."
)

# Assemble the crew
crew = Crew(
    agents=[
        code_retriever, 
        vb_converter, 
        dependency_analyzer, 
        upgrade_coordinator, 
        deployment_agent, 
        test_executor, 
        report_generator
    ],
    tasks=[task1, task2, task3, task4, task5, task6, task7],
    verbose=2
)

# Kick off the process
result = crew.kickoff()
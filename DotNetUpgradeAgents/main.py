import os
from crewai import Crew, Process
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff
from .agents import DotNetUpgradeAgents  # Commented out for script-first approach
from .tasks import DotNetUpgradeTasks   # Commented out for script-first approach
from .core_components import logger, HumanFeedback # Commented out for script-first approach

# agents: List[Agent]
# tasks: List[Task]
# This allows the script to be run from the root directory of the project or from within DotNetUpgradeAgents
if __package__ is None or __package__ == '':
    # When run as a script, adjust path to import from sibling directories
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from agents import DotNetUpgradeAgents
    from tasks import DotNetUpgradeTasks
    from core_components import logger, HumanFeedback
else:
    # When imported as a module
    from .agents import DotNetUpgradeAgents
    from .tasks import DotNetUpgradeTasks
    from .core_components import logger, HumanFeedback


def main():
    logger.info("Starting the .NET Upgrade Crew orchestration script.")

    # --- Configuration ---
    # These would typically come from a config file, environment variables, or user input.
    # For this example, we'll use placeholders. User might be prompted for some.

    # Use HumanFeedback to get critical paths
    print("\n--- .NET Upgrade Agent System Configuration ---")
    tfs_repo_url = HumanFeedback.get_feedback(
        "Enter the TFS repository URL (e.g., tfs://server/collection/project):",
        options=["tfs://server/collection/project", "https://dev.azure.com/your_org/your_project/_git/your_repo"]
    )

    # Suggest a default local path based on the current working directory
    default_checkout_base = os.path.join(os.getcwd(), "temp_upgrade_work")
    local_checkout_base_path = HumanFeedback.get_feedback(
        f"Enter the base local path for code checkout and operations (default: {default_checkout_base}):",
        options=[default_checkout_base]
    )
    if not local_checkout_base_path:
        local_checkout_base_path = default_checkout_base

    # Ensure the base path exists
    os.makedirs(local_checkout_base_path, exist_ok=True)
    logger.info(f"Using base path for operations: {local_checkout_base_path}")

    # Define specific subdirectories for clarity
    code_checkout_dir = os.path.join(local_checkout_base_path, "source_code")
    # Path to a specific VB project/file within the checkout (example)
    vb_project_to_convert = os.path.join(code_checkout_dir, "MyLegacyVBApp", "MyLegacyVBApp.vbproj")
    # Path to a specific C# project/solution to analyze and upgrade (example)
    csharp_project_to_upgrade = os.path.join(code_checkout_dir, "MyMainCSharpApp", "MyMainCSharpApp.csproj")
    upgraded_app_build_output_dir = os.path.join(csharp_project_to_upgrade, "bin", "Release", "net6.0") # Example

    target_framework = HumanFeedback.get_feedback("Enter the target .NET framework (e.g., net6.0, net7.0, net48):", ["net6.0", "net7.0", "net8.0", "net48"])

    # Git branch names
    vb_conversion_branch = f"feature/vb_to_csharp_{target_framework.replace('.', '')}"
    framework_upgrade_branch = f"feature/upgrade_to_{target_framework.replace('.', '')}"

    iis_site_to_deploy = "UpgradedDotNetWebApp"
    neoload_project_file = "PerformanceTests/UpgradeValidation.nlp" # Example path

    # --- Instantiate Agent and Task Factories ---
    agent_factory = DotNetUpgradeAgents()
    task_factory = DotNetUpgradeTasks()

    # --- Define Tasks with specific inputs ---
    # Task 1: Retrieve Code
    task_retrieve_code = task_factory.retrieve_code_task(
        tfs_repo_url=tfs_repo_url,
        local_checkout_path=code_checkout_dir
    )

    # Task 2: Convert VB.NET to C# (conditional, or targets a specific known VB project)
    # In a real scenario, you might have logic to detect VB projects first.
    # For this example, we assume 'vb_project_to_convert' is a known VB project.
    task_convert_vb = task_factory.convert_vb_to_csharp_task(
        vb_project_path_or_file=vb_project_to_convert, # This path needs to exist after checkout
        git_branch_name=vb_conversion_branch
    )
    # This task should only run if vb_project_to_convert exists.
    # CrewAI doesn't have conditional task execution out-of-the-box in simple linear flows.
    # This would typically be handled by agent logic or a more complex workflow manager.
    # For now, we include it and rely on tool/agent to handle non-existent paths gracefully.

    # Task 3: Analyze Dependencies (targets a specific C# project post-checkout/conversion)
    task_analyze_deps = task_factory.analyze_dependencies_task(
        project_or_solution_file=csharp_project_to_upgrade # This path needs to exist
    )
    task_analyze_deps.context = [task_retrieve_code] # Depends on code being checked out

    # Task 4: Upgrade Project Framework
    task_upgrade_framework = task_factory.upgrade_project_framework_task(
        csproj_file_path=csharp_project_to_upgrade,
        target_framework=target_framework,
        git_branch_name=framework_upgrade_branch
    )
    # Depends on dependency analysis potentially, and code checkout
    task_upgrade_framework.context = [task_analyze_deps, task_retrieve_code]
    # If VB conversion happened and this project was the result, add task_convert_vb to context.

    # Task 5: Deploy Application
    task_deploy_app = task_factory.deploy_application_task(
        application_build_path=upgraded_app_build_output_dir, # Path to BUILT application
        iis_site_name=iis_site_to_deploy
    )
    task_deploy_app.context = [task_upgrade_framework] # Depends on successful upgrade and build

    # Task 6: Run Performance Tests
    task_run_tests = task_factory.run_performance_tests_task(
        neoload_project=neoload_project_file,
        users=5 # Example user count
    )
    task_run_tests.context = [task_deploy_app] # Depends on deployment

    # Task 7: Generate Final Report
    # This task will implicitly use the outputs of all previous tasks.
    # CrewAI handles context passing. The input `collected_upgrade_data` for the task
    # will be the string representation of the combined outputs of its context tasks.
    # The ReportTool's _run method needs to be robust enough to handle this string input,
    # or the task description should guide the LLM (if agent uses LLM for this) to parse it.
    # For our direct ReportTool, it expects a dictionary.
    # This means the reporting agent or a prior task needs to aggregate results into a dict.
    # For now, we'll pass a placeholder or the agent needs to be smart.

    # Let's assume the reporting agent's tool is smart enough or the agent itself will gather context.
    # The task description already mentions "The input 'collected_upgrade_data' dictionary contains all this information."
    # This implies the reporting agent needs to be able to access this context.
    # The final task in a crew gets the output of all previous tasks as its context.
    task_generate_report = task_factory.generate_final_report_task(
        collected_upgrade_data={} # Placeholder; actual data comes from context
    )
    task_generate_report.context = [
        task_retrieve_code,
        task_convert_vb, # Even if it only creates a message about not finding VB files
        task_analyze_deps,
        task_upgrade_framework,
        task_deploy_app,
        task_run_tests
    ]


    # --- Assemble the Crew ---
    # Instantiate agents using the agent_factory
    code_retrieval_agent = agent_factory.code_retrieval_agent()
    code_conversion_agent = agent_factory.code_conversion_agent()
    dependency_analyzer_agent = agent_factory.dependency_analyzer_agent()
    upgrade_coordinator_agent = agent_factory.upgrade_coordinator_agent()
    deployment_agent = agent_factory.deployment_agent()
    testing_agent = agent_factory.testing_agent()
    reporting_agent = agent_factory.reporting_agent()

    # We need to list the unique agents involved.
    agents_list = [
        code_retrieval_agent,
        code_conversion_agent,
        dependency_analyzer_agent,
        upgrade_coordinator_agent,
        deployment_agent,
        testing_agent,
        reporting_agent
    ]

    tasks_list = [
        task_retrieve_code,
        # task_convert_vb, # We might make this conditional based on user input or initial scan
        task_analyze_deps,
        task_upgrade_framework,
        task_deploy_app,
        task_run_tests,
        task_generate_report
    ]

    # Add VB conversion task if user indicates there's VB code
    has_vb_code = HumanFeedback.get_feedback("Does the project contain VB.NET code that needs conversion?", ["Yes", "No"])
    if has_vb_code == "Yes":
        tasks_list.insert(1, task_convert_vb) # Insert after code retrieval
        # Ensure subsequent tasks that might depend on conversion are aware
        if task_analyze_deps in tasks_list: # if csharp_project_to_upgrade could be a result of conversion
            task_analyze_deps.context.append(task_convert_vb)
        if task_upgrade_framework in tasks_list: # if csharp_project_to_upgrade could be a result of conversion
             task_upgrade_framework.context.append(task_convert_vb)


    logger.info("Assembling the .NET Upgrade Crew...")
    crew = Crew(
        agents=[code_retrieval_agent,code_conversion_agent,dependency_analyzer_agent,upgrade_coordinator_agent,deployment_agent,testing_agent, reporting_agent],  # Convert agents to dicts
        tasks=tasks_list,
        process=Process.sequential,  # Tasks will run one after another
        verbose= True # 0 for no logs, 1 for agent logs, 2 for detailed logs
        # memory=True # Optional: enable memory for the crew
    )

    # --- Kick off the Crew ---
    logger.info("Starting .NET Upgrade Crew execution...")
    print("\n================================================================================")
    print("🚀 Kicking off the .NET Upgrade Crew! Monitor the console for progress and prompts.")
    print("================================================================================\n")

    try:
        # Inputs for the first task can be passed here if not embedded in task description
        # or if the task needs dynamic data not available at definition time.
        # For 'task_retrieve_code', inputs are already in its description via f-string.
        result = crew.kickoff()

        print("\n================================================================================")
        print("🎉 .NET Upgrade Crew execution finished!")
        print("Crew Result:")
        print(result) # The result of the last task (report generation)
        print("================================================================================\n")
        logger.info(f".NET Upgrade Crew execution completed. Final Result: {result}")

    except Exception as e:
        logger.error(f"An error occurred during Crew execution: {e}", exc_info=True)
        print(f"An error occurred during Crew execution: {e}")

if __name__ == "__main__":
    main()

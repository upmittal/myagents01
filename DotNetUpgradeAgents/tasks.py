from crewai import Task
from .agents import DotNetUpgradeAgents # Assuming agents are defined here
from .core_components import logger

# Instantiate the agent factory
agent_factory = DotNetUpgradeAgents()

# It's good practice to define dynamic inputs for tasks if they are known only at runtime.
# For now, we'll use placeholders in descriptions or assume they'll be passed via context/inputs to crew.kickoff().
# Example: tfs_repo_url, project_path, target_framework etc. will be part of the 'inputs' to the crew.

class DotNetUpgradeTasks:

    def retrieve_code_task(self, tfs_repo_url: str, local_checkout_path: str) -> Task:
        logger.info(f"Defining task: Retrieve Code from {tfs_repo_url} to {local_checkout_path}")
        return Task(
            description=f"Retrieve the latest source code from TFS repository '{tfs_repo_url}' and place it into the local directory '{local_checkout_path}'. Then, initialize a Git repository in '{local_checkout_path}', add all files, and create an initial commit.",
            expected_output=f"Source code successfully retrieved from TFS to '{local_checkout_path}', a Git repository initialized in '{local_checkout_path}' with an initial commit containing all files. A confirmation message of success or detailed error message if failed.",
            agent=agent_factory.code_retrieval_agent(),
            # inputs will be dynamically filled by crew.kickoff if this task is the first one
            # or from the context of a previous task.
            # For clarity, we are showing explicit inputs here.
            # inputs={'tfs_repo_url': tfs_repo_url, 'destination_path': local_checkout_path} # This is how you might structure inputs if task took them directly
        )

    def convert_vb_to_csharp_task(self, vb_project_path_or_file: str, git_branch_name: str) -> Task:
        logger.info(f"Defining task: Convert VB.NET in {vb_project_path_or_file} on branch {git_branch_name}")
        return Task(
            description=f"Identify all VB.NET files within the specified path '{vb_project_path_or_file}'. For each VB.NET file, convert it to C#. After conversion, create a new Git branch named '{git_branch_name}', attempt to build the converted project. If build is successful, commit changes to this branch. If build fails, report errors.",
            expected_output=f"All VB.NET files in '{vb_project_path_or_file}' converted to C#. A new Git branch '{git_branch_name}' created with the C# code. Build status (success or failure with errors) reported. Confirmation message of successful conversion and commit, or detailed error messages.",
            agent=agent_factory.code_conversion_agent(),
            context=[] # This task might depend on the output of retrieve_code_task
        )

    def analyze_dependencies_task(self, project_or_solution_file: str) -> Task:
        logger.info(f"Defining task: Analyze Dependencies for {project_or_solution_file}")
        return Task(
            description=f"Analyze the .NET project or solution file at '{project_or_solution_file}' to identify all NuGet packages, custom library references (project references), and check for the usage of the 'ITASCA' namespace. If 'ITASCA' is found, human feedback must be solicited regarding how to proceed.",
            expected_output=f"A dictionary or structured report detailing: list of NuGet packages, list of custom libraries, a boolean indicating if 'ITASCA' namespace was found, and the human feedback received if it was. Path to the analyzed file: '{project_or_solution_file}'.",
            agent=agent_factory.dependency_analyzer_agent(),
            context=[]
        )

    def upgrade_project_framework_task(self, csproj_file_path: str, target_framework: str, git_branch_name: str) -> Task:
        logger.info(f"Defining task: Upgrade Framework for {csproj_file_path} to {target_framework} on branch {git_branch_name}")
        return Task(
            description=f"For the .csproj file at '{csproj_file_path}', upgrade its target framework to '{target_framework}'. This involves modifying the .csproj file content. Before modification, create a new Git branch named '{git_branch_name}'. After attempting the upgrade, build the project. If build is successful, commit changes. If build fails, report errors.",
            expected_output=f"The .csproj file '{csproj_file_path}' modified to target '{target_framework}'. A new Git branch '{git_branch_name}' created. Build status (success or failure with errors) after upgrade reported. Confirmation of successful upgrade and commit, or detailed error messages.",
            agent=agent_factory.upgrade_coordinator_agent(),
            context=[]
        )

    def deploy_application_task(self, application_build_path: str, iis_site_name: str) -> Task:
        logger.info(f"Defining task: Deploy Application from {application_build_path} to IIS site {iis_site_name}")
        return Task(
            description=f"Deploy the application from the build output directory '{application_build_path}' to the IIS website named '{iis_site_name}'. This involves configuring IIS (simulated) to point to the new application bits.",
            expected_output=f"Application from '{application_build_path}' successfully deployed to IIS site '{iis_site_name}' (simulated). Confirmation message of success or detailed error message.",
            agent=agent_factory.deployment_agent(),
            context=[]
        )

    def run_performance_tests_task(self, neoload_project: str, users: int) -> Task:
        logger.info(f"Defining task: Run NeoLoad Test for {neoload_project} with {users} users")
        return Task(
            description=f"Execute a NeoLoad performance test for the project/scenario '{neoload_project}' with {users} virtual users against the deployed application.",
            expected_output=f"NeoLoad test for '{neoload_project}' with {users} users completed (simulated). A summary of test results (e.g., status, average response time, error rate).",
            agent=agent_factory.testing_agent(),
            context=[]
        )

    def generate_final_report_task(self, collected_upgrade_data: dict) -> Task:
        # 'collected_upgrade_data' would be dynamically assembled from the outputs of previous tasks.
        logger.info(f"Defining task: Generate Final Report")
        return Task(
            description=f"Compile all information gathered during the upgrade process into a comprehensive report. This includes details from code retrieval, conversion, dependency analysis, framework upgrade, build results, deployment status, and test results. The input 'collected_upgrade_data' dictionary contains all this information.",
            expected_output="Path to the generated final report file (e.g., 'upgrade_report_YYYYMMDD_HHMMSS.json' or '.txt'). The report should contain a structured summary of the entire upgrade process.",
            agent=agent_factory.reporting_agent(),
            context=[] # This task would typically have context from all previous tasks
        )

if __name__ == '__main__':
    logger.info("Testing task definitions...")

    tasks_collection = DotNetUpgradeTasks()

    # Example: Define some placeholder inputs for task creation
    tfs_url_sample = "tfs://your_server/your_project_collection/your_project"
    checkout_path_sample = "/mnt/d/temp/upgrade_checkout"
    vb_project_sample = f"{checkout_path_sample}/vb_app/vb_app.vbproj"
    git_conversion_branch_sample = "feature/vb_to_csharp_conversion"
    csproj_sample = f"{checkout_path_sample}/csharp_app/csharp_app.csproj"
    target_fw_sample = "net6.0"
    git_upgrade_branch_sample = "feature/framework_upgrade_net6"
    app_build_path_sample = f"{checkout_path_sample}/csharp_app/bin/Release/net6.0"
    iis_site_sample = "UpgradedDotNetApp"
    neoload_project_sample = "MyApplicationTests.nlp"

    task1 = tasks_collection.retrieve_code_task(tfs_repo_url=tfs_url_sample, local_checkout_path=checkout_path_sample)
    agent_role1 = getattr(task1.agent, "role", "Unknown") if task1.agent is not None else "None"
    print(f"Created Task: {task1.description[:50]}... for agent: {agent_role1}")

    task2 = tasks_collection.convert_vb_to_csharp_task(vb_project_path_or_file=vb_project_sample, git_branch_name=git_conversion_branch_sample)
    agent_role2 = getattr(task2.agent, "role", "Unknown") if task2.agent is not None else "None"
    print(f"Created Task: {task2.description[:50]}... for agent: {agent_role2}")

    task3 = tasks_collection.analyze_dependencies_task(project_or_solution_file=csproj_sample)
    agent_role3 = getattr(task3.agent, "role", "Unknown") if task3.agent is not None else "None"
    print(f"Created Task: {task3.description[:50]}... for agent: {agent_role3}")

    task4 = tasks_collection.upgrade_project_framework_task(csproj_file_path=csproj_sample, target_framework=target_fw_sample, git_branch_name=git_upgrade_branch_sample)
    agent_role4 = getattr(task4.agent, "role", "Unknown") if task4.agent is not None else "None"
    print(f"Created Task: {task4.description[:50]}... for agent: {agent_role4}")

    task5 = tasks_collection.deploy_application_task(application_build_path=app_build_path_sample, iis_site_name=iis_site_sample)
    agent_role5 = getattr(task5.agent, "role", "Unknown") if task5.agent is not None else "None"
    print(f"Created Task: {task5.description[:50]}... for agent: {agent_role5}")

    task6 = tasks_collection.run_performance_tests_task(neoload_project=neoload_project_sample, users=10)
    agent_role6 = getattr(task6.agent, "role", "Unknown") if task6.agent is not None else "None"
    print(f"Created Task: {task6.description[:50]}... for agent: {agent_role6}")

    # For the report task, collected_data would come from the crew's execution context
    sample_report_data = {"step1_result": "Success", "step2_result": "Partial Success with warnings"}
    task7 = tasks_collection.generate_final_report_task(collected_upgrade_data=sample_report_data)
    agent_role7 = getattr(task7.agent, "role", "Unknown") if task7.agent is not None else "None"
    print(f"Created Task: {task7.description[:50]}... for agent: {agent_role7}")

    logger.info("Task definition tests complete. All task creation methods tested.")

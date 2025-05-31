from crewai import Agent
from .tools import (
    TFSTool,
    GitInitTool,
    VBToCSTool,
    DependencyAnalyzerTool,
    ProjectUpgradeTool,
    BuildTool,
    IISTool,
    NeoLoadTool,
    ReportTool
)
from .core_components import LLMApiClient, logger

# Optional: Initialize a shared LLM client instance if you want all agents/tools to use the same one.
# llm_client = LLMApiClient(api_key="YOUR_ACTUAL_API_KEY", endpoint="YOUR_ACTUAL_ENDPOINT")
# If not, tools will instantiate their own default LLMApiClient.

# Initialize tools once here if they need specific setup or shared resources,
# or let agents initialize them if they are stateless.
# For tools that use LLM, they can either be passed an llm_client or create their own.
# We'll let the tools create their own LLM clients for simplicity,
# or they can be instantiated with a shared client if needed.

tfs_tool = TFSTool()
git_tool = GitInitTool()
vb_to_cs_tool = VBToCSTool() # Can take llm_client=llm_client
dep_analyzer_tool = DependencyAnalyzerTool()
project_upgrade_tool = ProjectUpgradeTool() # Can take llm_client=llm_client
build_tool = BuildTool() # Can take llm_client=llm_client
iis_tool = IISTool()
neoload_tool = NeoLoadTool()
report_tool = ReportTool()

class DotNetUpgradeAgents:
    @staticmethod
    def code_retrieval_agent() -> Agent:
        logger.info("Initializing Code Retrieval Agent")
        return Agent(
            role="Code Retrieval Specialist",
            goal="Fetch the latest application code from Team Foundation Server (TFS) and initialize a Git repository on a designated server/path.",
            backstory="An expert in version control systems, specializing in migrating code from TFS to Git and setting up clean, workable repositories.",
            tools=[tfs_tool, git_tool],
            verbose=True,
            allow_delegation=False # This agent's tasks are fairly atomic
        )

    @staticmethod
    def code_conversion_agent() -> Agent:
        logger.info("Initializing Code Conversion Agent")
        return Agent(
            role="VB.NET to C# Conversion Engineer",
            goal="Convert any VB.NET applications or libraries to C#, ensure the converted code builds successfully, and commit the changes to a new Git branch.",
            backstory="A seasoned software engineer with deep expertise in .NET languages, specializing in automated code conversion and ensuring functional equivalence post-conversion.",
            tools=[vb_to_cs_tool, build_tool, git_tool], # Git tool for branching/committing
            verbose=True,
            allow_delegation=True # Might delegate build checking or specific conversion issues
        )

    @staticmethod
    def dependency_analyzer_agent() -> Agent:
        logger.info("Initializing Dependency Analyzer Agent")
        return Agent(
            role="Dependency Analysis Expert",
            goal="Analyze the entire application/solution to map all project dependencies, identify custom libraries, and flag usage of specific namespaces like 'ITASCA', prompting for human feedback when necessary.",
            backstory="A meticulous analyst with a knack for untangling complex dependency webs in large .NET solutions. Ensures all components are accounted for before an upgrade.",
            tools=[dep_analyzer_tool],
            verbose=True,
            allow_delegation=False
        )

    @staticmethod
    def upgrade_coordinator_agent() -> Agent:
        logger.info("Initializing Upgrade Coordinator Agent")
        return Agent(
            role=".NET Upgrade Coordinator",
            goal="Upgrade .csproj files to the target .NET version, manage Git branches for upgrades, and coordinate with the Build Agent to resolve build errors and warnings until successful.",
            backstory="An experienced .NET developer who has led multiple large-scale framework upgrade projects. Proficient in MSBuild, .csproj intricacies, and automated build resolution.",
            tools=[project_upgrade_tool, build_tool, git_tool], # Git tool for branching/committing
            verbose=True,
            allow_delegation=True # Can delegate build fixing
        )

    @staticmethod
    def deployment_agent() -> Agent:
        logger.info("Initializing Deployment Agent")
        return Agent(
            role="IIS Deployment Specialist",
            goal="Deploy the upgraded and successfully built .NET application to a specified IIS server on a virtual machine.",
            backstory="A DevOps engineer with extensive experience in deploying .NET applications to IIS environments, ensuring correct configuration and smooth rollouts.",
            tools=[iis_tool],
            verbose=True,
            allow_delegation=False
        )

    @staticmethod
    def testing_agent() -> Agent:
        logger.info("Initializing Testing Agent")
        return Agent(
            role="NeoLoad Test Executor",
            goal="Trigger NeoLoad validation tests against the deployed application to ensure basic functionality and performance post-upgrade.",
            backstory="A QA engineer skilled in performance testing tools, particularly NeoLoad. Ensures applications meet performance benchmarks after significant changes.",
            tools=[neoload_tool],
            verbose=True,
            allow_delegation=False
        )

    @staticmethod
    def reporting_agent() -> Agent:
        logger.info("Initializing Reporting Agent")
        return Agent(
            role="Upgrade Process Reporter",
            goal="Generate a comprehensive report detailing the entire upgrade process, including steps taken, issues encountered, resolutions, and the status of non-upgradable projects.",
            backstory="A technical writer with an eye for detail, responsible for documenting complex technical processes clearly and concisely.",
            tools=[report_tool],
            verbose=True,
            allow_delegation=False
        )

if __name__ == '__main__':
    logger.info("Testing agent definitions...")

    agents_collection = DotNetUpgradeAgents()

    code_retriever = agents_collection.code_retrieval_agent()
    print(f"Created Agent: {code_retriever.role}")

    code_converter = agents_collection.code_conversion_agent()
    print(f"Created Agent: {code_converter.role}")

    dep_analyzer = agents_collection.dependency_analyzer_agent()
    print(f"Created Agent: {dep_analyzer.role}")

    upgrader = agents_collection.upgrade_coordinator_agent()
    print(f"Created Agent: {upgrader.role}")

    deployer = agents_collection.deployment_agent()
    print(f"Created Agent: {deployer.role}")

    tester = agents_collection.testing_agent()
    print(f"Created Agent: {tester.role}")

    reporter = agents_collection.reporting_agent()
    print(f"Created Agent: {reporter.role}")

    logger.info("Agent definition tests complete. All agents initialized.")

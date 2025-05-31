import os
import subprocess
import logging
import json
from datetime import datetime
from crewai import Agent, Task, Crew
from crewai_tools import BaseTool
from functools import wraps
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("DotNetUpgrade")

# Compact decorator for logging and error handling
def log_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Run {func.__name__}")
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}")
            raise
    return wrapper

# Simulated LLM API client
class LLMApiClient:
    def __init__(self, api_key="YOUR_API_KEY", endpoint="YOUR_LLM_ENDPOINT"):
        self.api_key, self.endpoint = api_key, endpoint

    @log_error
    def generate_code(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.endpoint, headers={"Authorization": f"Bearer {self.api_key}"},
                json={"prompt": prompt, "max_tokens": 1000}
            )
            response.raise_for_status()
            return response.json().get("generated_code", "# Simulated C# code")
        except requests.RequestException:
            return "# LLM failed, manual input needed"

# Human feedback interface
class HumanFeedback:
    @staticmethod
    @log_error
    def get_feedback(prompt: str, options: list = None) -> str:
        print(f"\n=== Feedback Needed ===\n{prompt}")
        if options:
            print("Options:", *[f"{i}. {opt}" for i, opt in enumerate(options, 1)], sep="\n")
        response = input("Decision: ")
        logger.info(f"Feedback: {response}")
        return response

# Tools
class TFSTool(BaseTool):
    name, description = "TFSTool", "Retrieve TFS code"

    @log_error
    def _run(self, repo_url: str, dest: str) -> str:
        os.makedirs(dest, exist_ok=True)
        try:
            subprocess.run(["tf", "get", repo_url, dest], check=True, capture_output=True)
            return f"Code at {dest}"
        except subprocess.SubprocessError as e:
            return HumanFeedback.get_feedback(f"TFS failed: {e}. Retry?", ["Retry", "Skip"])

class GitInitTool(BaseTool):
    name, description = "GitInitTool", "Initialize Git repo"

    @log_error
    def _run(self, path: str) -> str:
        subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Init"], cwd=path, check=True, capture_output=True)
        return f"Git repo at {path}"

class VBToCSTool(BaseTool):
    name, description = "VBToCSTool", "Convert VB.NET to C#"
    def __init__(self): super().__init__(); self.llm = LLMApiClient()

    @log_error
    def _run(self, vb_path: str) -> str:
        with open(vb_path, 'r') as f:
            vb_code = f.read()
        cs_code = self.llm.generate_code(f"Convert VB.NET to C#:\n{vb_code}")
        cs_path = vb_path.replace(".vb", ".cs")
        with open(cs_path, 'w') as f:
            f.write(cs_code)
        return f"Converted to {cs_path}"

class DependencyAnalyzerTool(BaseTool):
    name, description = "DependencyAnalyzerTool", "Analyze .NET dependencies"

    @log_error
    def _run(self, path: str) -> dict:
        deps = {"nuget": [], "custom_libs": [], "itasca": False}
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".csproj"):
                    with open(os.path.join(root, file), 'r') as f:
                        if "ITASCA" in f.read():
                            deps["itasca"] = True
                            deps["itasca_action"] = HumanFeedback.get_feedback(
                                "ITASCA detected. Proceed?", ["Replace", "Keep", "Custom"]
                            )
                    deps["nuget"].append("SamplePackage")
        return deps

class ProjectUpgradeTool(BaseTool):
    name, description = "ProjectUpgradeTool", "Upgrade .csproj to latest .NET"
    def __init__(self): super().__init__(); self.llm = LLMApiClient()

    @log_error
    def _run(self, csproj_path: str, target: str) -> str:
        with open(csproj_path, 'r') as f:
            content = f.read()
        upgraded = self.llm.generate_code(f"Upgrade .csproj to {target}:\n{content}")
        with open(csproj_path, 'w') as f:
            f.write(upgraded)
        return f"Upgraded {csproj_path} to {target}"

class BuildTool(BaseTool):
    name, description = "BuildTool", "Build .NET project"
    def __init__(self): super().__init__(); self.llm = LLMApiClient()

    @log_error
    def _run(self, path: str) -> str:
        try:
            result = subprocess.run(["dotnet", "build", path], check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.SubprocessError as e:
            fix = self.llm.generate_code(f"Fix build errors:\n{e.stderr}")
            choice = HumanFeedback.get_feedback(f"Build failed. Apply fix?\n{fix}", ["Apply", "Custom", "Skip"])
            return choice if choice != "Apply" else "Fix applied"

class IISTool(BaseTool):
    name, description = "IISTool", "Deploy to IIS"

    @log_error
    def _run(self, path: str, site: str) -> str:
        try:
            subprocess.run(["deploy_to_iis", path, site], check=True, capture_output=True)
            return f"Deployed to {site}"
        except subprocess.SubprocessError as e:
            return HumanFeedback.get_feedback(f"IIS failed: {e}. Retry?", ["Retry", "Skip"])

class NeoLoadTool(BaseTool):
    name, description = "NeoLoadTool", "Run NeoLoad test"

    @log_error
    def _run(self, path: str) -> str:
        try:
            subprocess.run(["neoload", "run", "--users", "1", path], check=True, capture_output=True)
            return "NeoLoad test done"
        except subprocess.SubprocessError as e:
            return HumanFeedback.get_feedback(f"NeoLoad failed: {e}. Retry?", ["Retry", "Skip"])

class ReportTool(BaseTool):
    name, description = "ReportTool", "Generate upgrade report"

    @log_error
    def _run(self, details: dict) -> str:
        report = {"timestamp": datetime.now().isoformat(), "details": details, "status": "Completed" if details.get("success") else "Failed"}
        path = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(path, 'w') as f:
            json.dump(report, f, indent=2)
        return f"Report at {path}"

# Agents
agents = [
    Agent(role="Code Retrieval", goal="Fetch TFS code, init Git", backstory="Source control expert", tools=[TFSTool(), GitInitTool()], verbose=True),
    Agent(role="Code Conversion", goal="Convert VB.NET to C#", backstory=".NET conversion specialist", tools=[VBToCSTool(), BuildTool()], verbose=True),
    Agent(role="Dependency Analyzer", goal="Analyze dependencies, handle ITASCA", backstory="Dependency expert", tools=[DependencyAnalyzerTool()], verbose=True),
    Agent(role="Upgrade Agent", goal="Upgrade .NET projects", backstory="Upgrade specialist", tools=[ProjectUpgradeTool(), BuildTool()], verbose=True),
    Agent(role="Deployment", goal="Deploy to IIS", backstory="IIS deployment expert", tools=[IISTool()], verbose=True),
    Agent(role="Testing", goal="Run NeoLoad tests", backstory="Testing expert", tools=[NeoLoadTool()], verbose=True),
    Agent(role="Reporting", goal="Generate upgrade report", backstory="Reporting expert", tools=[ReportTool()], verbose=True)
]

# Tasks
tasks = [
    Task(description="Fetch TFS code, init Git", expected_output="Code retrieved, Git initialized", agent=agents[0]),
    Task(description="Convert VB.NET to C#, validate build", expected_output="Code converted, build OK", agent=agents[1]),
    Task(description="Analyze dependencies, handle ITASCA", expected_output="Dependency report", agent=agents[2]),
    Task(description="Upgrade .csproj, fix build errors", expected_output="Projects upgraded", agent=agents[3]),
    Task(description="Deploy to IIS", expected_output="Deployed to IIS", agent=agents[4]),
    Task(description="Run NeoLoad test", expected_output="Test completed", agent=agents[5]),
    Task(description="Generate report", expected_output="Report path", agent=agents[6])
]

# Run Crew
if __name__ == "__main__":
    logger.info("Starting upgrade")
    crew = Crew(agents=agents, tasks=tasks, verbose=True)
    result = crew.kickoff()
    logger.info(f"Upgrade done: {result}")
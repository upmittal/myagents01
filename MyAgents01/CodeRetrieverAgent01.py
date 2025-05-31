from crewai import Agent, Task, Crew
from crewai_tools import GitTool, CodeExecutionTool

code_retriever = Agent(
    role="Code Retriever",
    goal="Fetch the latest code from TFS and initialize a Git repository on a virtual server",
    tools=[GitTool(), CodeExecutionTool()],
    verbose=True,
    backstory="Responsible for retrieving legacy code and preparing it for upgrades."
)
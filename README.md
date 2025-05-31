# .NET Upgrade Multi-Agent System

This project implements a multi-agent system using CrewAI to automate and assist in the process of upgrading older .NET applications. The system uses a series of specialized agents that collaborate to perform tasks such as code retrieval, VB.NET to C# conversion, dependency analysis, framework upgrades, deployment, testing, and reporting.

## Project Structure

-   `DotNetUpgradeAgents/`: Contains the core Python code for the agent system.
    -   `__init__.py`: Marks the directory as a Python package.
    -   `main.py`: The main orchestration script to run the agent crew.
    -   `core_components.py`: Defines shared components like logging, LLM API client simulation, and human feedback mechanisms.
    -   `tools.py`: Implements the various tools used by the agents (e.g., TFSTool, GitInitTool, BuildTool).
    -   `agents.py`: Defines the specialized CrewAI agents (e.g., CodeRetrievalAgent, UpgradeCoordinatorAgent).
    -   `tasks.py`: Defines the tasks that the agents will perform.
-   `MyAgents01/`: Contains older, LLM-generated files that served as initial input and reference. Not directly used by the `DotNetUpgradeAgents` system but kept for historical context.
-   `tests/`: Contains unit tests for the agent system components.
    -   `__init__.py`: Marks the directory as a Python package.
    -   `test_tools.py`: Unit tests for some of the tools defined in `DotNetUpgradeAgents/tools.py`.
-   `README.md`: This file.

## Features

-   **Modular Agent Design**: Specialized agents for distinct parts of the upgrade process.
-   **Tool-Based Functionality**: Agents use a collection of tools to interact with filesystems, version control, build processes (simulated), and LLMs (simulated).
-   **Interactive Human Feedback**: The system can prompt the user for decisions at critical points (e.g., handling specific namespaces, resolving ambiguous errors).
-   **Simulated External Systems**: Interactions with TFS, IIS, NeoLoad, and LLM APIs are currently simulated, allowing for end-to-end testing of the agent logic without requiring live external systems.
-   **Sequential Task Execution**: The upgrade process is managed as a sequence of tasks performed by the appropriate agents.
-   **Reporting**: Generates a final report summarizing the upgrade activities.

## Prerequisites

-   Python 3.8+
-   CrewAI and CrewAI Tools:
    ```bash
    pip install crewai crewai-tools
    ```
-   Requests (for LLMApiClient, even if simulated):
    ```bash
    pip install requests
    ```
-   (Optional, for BuildTool simulation) .NET SDK installed and accessible in the PATH if you want to test `dotnet build` commands against real or dummy projects.
-   (Optional, for TFSTool/GitInitTool simulation) Git command-line tools installed and accessible in the PATH.

## Setup and Configuration

1.  **Clone the repository.**
2.  **Install dependencies**: `pip install crewai crewai-tools requests`
3.  **LLM API Configuration (Simulated by default)**:
    -   The `LLMApiClient` in `DotNetUpgradeAgents/core_components.py` is currently configured to simulate LLM responses.
    -   To use a real LLM, you would need to update the `LLMApiClient` class:
        -   Modify the `__init__` method to accept your API key and endpoint.
        -   Update the `generate_code` method to make actual HTTP requests to your chosen LLM API.
        -   Pass your API key and endpoint when `LLMApiClient` is instantiated, or set them as environment variables that the client reads.
    -   The `main.py` script and tools currently rely on the default simulated client.

4.  **External Tool Paths (Simulated by default)**:
    -   Tools like `TFSTool`, `IISTool`, `NeoLoadTool` simulate their operations.
    -   To interact with real systems:
        -   **TFSTool**: Would require Team Foundation Server Command Line (tf.exe) or TFS APIs. The tool would need to be modified to call `tf.exe`.
        -   **IISTool**: Would require PowerShell cmdlets for IIS, MSDeploy, or IIS Administration APIs. The tool would need modification to execute these.
        -   **NeoLoadTool**: Would require NeoLoad Command Line Interface or APIs. The tool would need modification.

## Running the System

The main entry point for the agent system is `DotNetUpgradeAgents/main.py`.

1.  Navigate to the root directory of the project.
2.  Run the main script:
    ```bash
    python -m DotNetUpgradeAgents.main
    ```
    Or, if you are inside the `DotNetUpgradeAgents` directory:
    ```bash
    python main.py
    ```

3.  The script will prompt you for necessary inputs:
    -   TFS repository URL.
    -   Base local path for code checkout.
    -   Target .NET framework.
    -   Whether the project contains VB.NET code.

4.  Monitor the console for progress logs from the agents and any prompts requiring human feedback.

## Running Tests

Unit tests are located in the `tests/` directory.

1.  Navigate to the root directory of the project.
2.  Run the tests using Python's `unittest` module:
    ```bash
    python -m unittest discover -s tests
    ```
    Or, to run a specific test file:
    ```bash
    python -m unittest tests.test_tools
    ```

## How it Works

The `main.py` script orchestrates the upgrade process:
1.  It gathers initial configuration from the user.
2.  It defines a series of tasks based on the .NET upgrade workflow (code retrieval, conversion, analysis, upgrade, deployment, testing, reporting).
3.  Each task is assigned to a specialized agent (e.g., `CodeRetrievalAgent`, `UpgradeCoordinatorAgent`).
4.  Agents use tools (e.g., `TFSTool`, `BuildTool`) to perform their tasks. These tools encapsulate specific actions, including simulated interactions with external systems or LLMs.
5.  The CrewAI framework manages the sequential execution of these tasks, passing context and results between them.
6.  Human intervention is requested via `HumanFeedback` tool when agents face ambiguity or critical decision points.
7.  A final report summarizes the entire operation.

## Customization and Extension

-   **Real LLM/External Tools**: Modify the respective tool implementations in `DotNetUpgradeAgents/tools.py` and `DotNetUpgradeAgents/core_components.py` to connect to your actual LLM provider, TFS server, IIS environments, or NeoLoad instance.
-   **New Agents/Tools/Tasks**:
    -   Define new tool classes in `tools.py`.
    -   Define new agent roles and capabilities in `agents.py`.
    -   Define new task structures in `tasks.py`.
    -   Integrate them into the workflow in `main.py`.
-   **Workflow Logic**: The `main.py` script can be modified to change the sequence of tasks, add conditional logic, or implement more complex orchestration patterns if needed.
-   **Error Handling**: Enhance error handling within tools and agent logic for more robust recovery or alternative paths.

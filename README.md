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
3.  **LLM API Configuration (Real or Simulated)**:

    The system can interact with a real Large Language Model (LLM) API for tasks like code conversion and error suggestion. It supports both generic cloud-based LLM APIs and local LLMs via Ollama.

    **Common Setup:**
    - The `LLMApiClient` in `DotNetUpgradeAgents/core_components.py` handles LLM interactions.
    - **LLM Interaction Logging**: All prompts sent to the LLM and the full raw responses (or errors) are logged to a dedicated file named `llm_interactions.log`, located in the `DotNetUpgradeAgents` directory. This is useful for debugging and reviewing LLM performance.

    **A. Using Ollama (for Local LLMs):**
    -   Ensure Ollama is installed and running with your desired models pulled (e.g., `ollama pull mistral`).
    -   Set the following environment variables:
        -   `LLM_API_ENDPOINT`: Your local Ollama API endpoint.
            -   For generation tasks (like code conversion, project upgrades): `http://localhost:11434/api/generate`
            -   For chat-style interactions (if tools are adapted for it): `http://localhost:11434/api/chat`
            *(The client currently defaults to using `/api/generate` if the endpoint doesn't specify `/api/chat` or `/api/generate` but looks like Ollama. It can also distinguish if `/api/chat` is in the endpoint string)*
        -   `OLLAMA_MODEL`: The name of the Ollama model you want to use (e.g., `mistral`, `codellama:13b`, `llama2`). If not set, the system defaults to `mistral`.
        -   `LLM_API_KEY`: This is typically **not required** for local Ollama instances. If set, it will be ignored when an Ollama endpoint is detected.

    **B. Using Generic Cloud-Based LLM APIs (e.g., OpenAI, Anthropic, Azure OpenAI):**
    -   Set the following environment variables:
        -   `LLM_API_ENDPOINT`: The full HTTP(S) endpoint URL for your cloud provider's API.
            -   *Example for an OpenAI-compatible API*: `https://api.openai.com/v1/chat/completions`
            -   *Example for Azure OpenAI*: `https://<your-resource-name>.openai.azure.com/openai/deployments/<your-deployment-name>/chat/completions?api-version=<api-version>`
        -   `LLM_API_KEY`: Your API key for the chosen LLM provider. This is **required** for most cloud APIs.
        -   `OLLAMA_MODEL`: This variable is ignored if the endpoint is not detected as an Ollama endpoint.

    **Important Notes on LLM Client Behavior:**
    -   The `LLMApiClient` attempts to auto-detect if the `LLM_API_ENDPOINT` is for Ollama (by checking for "ollama" or "localhost:11434" in the URL).
    -   **Payload Structure**: The JSON payload sent to the LLM (within `LLMApiClient.generate_code`) is structured based on whether an Ollama endpoint is detected or not. You may still need to adjust the payload details (e.g., specific parameters for temperature, top_p, or model-specific fields) within the `LLMApiClient.generate_code` method to optimally match your chosen LLM provider or model's requirements.
    -   **Response Parsing**: The client attempts to parse various common response structures from both Ollama and generic APIs. If your specific LLM provider has a unique response format for the generated text, you might need to update the parsing logic in `LLMApiClient.generate_code`.
    -   **API Costs**: Be aware that making calls to commercial LLM APIs will likely incur costs. Using local LLMs via Ollama avoids direct API costs but utilizes your local hardware resources.
    -   If the necessary endpoint (and API key for cloud LLMs) is not configured, the `LLMApiClient` will not be able to make calls, and tools relying on it will indicate a configuration error or prompt for alternative actions.

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

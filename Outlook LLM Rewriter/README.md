# Outlook LLM Rewriter Add-in

## Description

An Outlook add-in that uses a locally running Ollama instance to rewrite selected text within an email. This helps improve clarity, conciseness, or tone of your email content directly within Outlook.

## Features

-   Integrates with the Outlook ribbon to open a task pane.
-   Opens a task pane for interaction, model selection, and triggering rewrites.
-   Dynamically loads available LLM models from your Ollama instance into a dropdown selector in the task pane.
-   Allows selection of the desired Ollama model for rewriting.
-   Connects to a local Ollama service to perform the text generation using the chosen model.
-   Replaces the selected text in the email with the rewritten version.
-   Provides status updates and error messages within the task pane.

## Getting Started

### Prerequisites

-   [Node.js](https://nodejs.org/) (version 18 or later recommended) and npm.
-   A running instance of [Ollama](https://ollama.com/) with the desired model(s) downloaded (e.g., `mistral`).
-   Microsoft Office connected to a Microsoft 365 subscription that supports Outlook Add-ins.

### Installation and Setup

1.  **Clone the repository (or ensure you are in the project directory):**
    ```bash
    # If you had cloned a repo, you'd cd into it. For this environment, files are already present.
    cd OutlookLlmRewriter
    ```

2.  **Install dependencies:**
    This command installs all the necessary dependencies defined in `package.json`.
    ```bash
    npm install
    ```

3.  **Build the add-in:**
    This command compiles the TypeScript code and bundles assets.
    ```bash
    npm run build
    ```

4.  **Start the development server:**
    This command starts a local web server (usually on `https://localhost:3000`) to serve your add-in's static files (HTML, JS, CSS). The manifest file (`manifest.xml`) points to this server.
    ```bash
    npm start
    # or sometimes: npm run dev-server
    ```
    Keep this server running while you are testing the add-in.

5.  **Sideload the add-in in Outlook:**
    *   Open Outlook (on the web, or desktop client).
    *   Go to "Get Add-ins" > "My add-ins".
    *   Under "Custom Addins", choose "Add a custom add-in" > "Add from file...".
    *   Upload the `manifest.xml` file located in the project's root directory (`OutlookLlmRewriter/manifest.xml`).
    *   Follow the prompts to install. The "Rewrite Selected Text" button should appear under an "LLM Tools" group in the Outlook ribbon.

## Ollama Configuration

This add-in requires a running instance of Ollama to function.

-   **API Endpoint**: The add-in is configured to connect to Ollama at `http://localhost:11434/api/generate`. If your Ollama instance is running on a different URL or port, you will need to modify the `OLLAMA_API_URL` constant in the `src/utils/ollamaApi.ts` file and rebuild the add-in (`npm run build`).
-   **Model**: By default, the add-in uses the `"mistral"` model for rewriting if available. This is specified as a default in the `rewriteTextWithOllama` function in `src/utils/ollamaApi.ts` and the task pane attempts to select it if present. You can change the selected model in the task pane, or modify the code for a different hardcoded default if desired.
-   **Model Discovery**: The add-in fetches the list of available models by querying the `/api/tags` endpoint of your Ollama instance (e.g., `http://localhost:11434/api/tags`). Ensure this endpoint is accessible if you want the model dropdown to populate correctly.
-   **Ensure Ollama is Running**: Before using the add-in, make sure your Ollama application is running and the desired model (e.g., `mistral`) is downloaded and available. You can typically pull a model using `ollama pull mistral` in your terminal.

## Usage

1.  Once the add-in is sideloaded and Ollama is running with your desired models:
2.  Open an email in Outlook (or compose a new one).
3.  Click the "Rewrite with LLM" button in the Outlook ribbon (usually on the Home tab or Message tab, under "LLM Tools").
4.  The add-in's task pane will open on the side.
5.  The task pane will attempt to load the list of available models from your Ollama instance into the "Choose LLM Model" dropdown.
    - If successful, select your desired model. "mistral" (if available and contains "mistral" in its name) will be selected by default.
    - If there's an error (e.g., Ollama not reachable), a message will be displayed in the status area of the task pane.
6.  Select the text you want to rewrite in the email body.
7.  Click the "Rewrite Selected Text" button in the task pane.
8.  The add-in will send the selected text and chosen model to Ollama.
9.  Status messages (e.g., "Rewriting...", "Text successfully rewritten!", or errors) will appear in the task pane.
10. If successful, the selected text in your email will be replaced with the rewritten version.

## Important Note on Testing Limitations

This add-in code was primarily developed and verified through static analysis and simulated testing due to limitations in the automated development environment that prevented a full `npm install` and `npm run build`. While the core logic is believed to be correct, it is crucial to **thoroughly test the add-in after sideloading it into your Outlook environment**. Please report any issues encountered.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License. See the `LICENSE` file (if one exists in the project - typically generated by `yo office`) for details.
---

*This README was generated and enhanced as part of an automated development process.*

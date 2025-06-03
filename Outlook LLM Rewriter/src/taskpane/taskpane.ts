/*
 * Copyright (c) Microsoft Corporation. All rights reserved. Licensed under the MIT license.
 * See LICENSE in the project root for license information.
 */

// Import the Ollama API utility functions
// getOllamaModels will be created in a subsequent step, but we assume its signature here.
import { rewriteTextWithOllama, getOllamaModels } from "../utils/ollamaApi";

/* global document, Office */

Office.onReady(info => {
  if (info.host === Office.HostType.Outlook) {
    document.addEventListener("DOMContentLoaded", run);
  }
});

async function run() {
  const modelSelector = document.getElementById("model-selector") as HTMLSelectElement;
  const rewriteButton = document.getElementById("rewrite-button") as HTMLButtonElement;
  const statusArea = document.getElementById("status-area") as HTMLDivElement;

  // Function to update status messages in the task pane
  function updateStatus(message: string, isError: boolean = false) {
    statusArea.innerHTML = ""; // Clear previous messages
    const messageDiv = document.createElement("div");
    messageDiv.innerText = message;
    messageDiv.className = isError ? "ms-MessageBar ms-MessageBar--error" : "ms-MessageBar ms-MessageBar--success"; // Basic styling

    // For a more authentic Fabric UI notification, you might need more complex HTML structure.
    // This is a simplified version.
    const icon = document.createElement("i");
    icon.className = isError ? "ms-Icon ms-Icon--Error" : "ms-Icon ms-Icon--Completed"; // Example icons
    messageDiv.prepend(icon, " ");

    statusArea.appendChild(messageDiv);
  }

  function clearStatus() {
      statusArea.innerHTML = "";
  }

  // Populate model list
  async function populateModels() {
    try {
      updateStatus("Loading LLM models...", false);
      modelSelector.disabled = true;
      const models = await getOllamaModels(); // This function will be added to ollamaApi.ts

      modelSelector.innerHTML = ""; // Clear "Loading models..." or previous options

      if (models.length === 0) {
        updateStatus("No models found in Ollama. Please ensure Ollama is running and models are downloaded.", true);
        return;
      }

      let mistralExists = false;
      models.forEach(modelName => {
        const option = document.createElement("option");
        option.value = modelName;
        option.textContent = modelName;
        modelSelector.appendChild(option);
        if (modelName.toLowerCase().includes("mistral")) { // Simple check for mistral
            mistralExists = true;
        }
      });

      if (mistralExists) {
        modelSelector.value = models.find(m => m.toLowerCase().includes("mistral")) || models[0];
      } else if (models.length > 0) {
        modelSelector.value = models[0]; // Default to the first model if mistral is not found
      }

      modelSelector.disabled = false;
      clearStatus(); // Clear "Loading models..."
    } catch (error) {
      console.error("Failed to populate models:", error);
      updateStatus(`Error loading models: ${error.message || error}. Please ensure Ollama is running at http://localhost:11434.`, true);
      modelSelector.innerHTML = '<option value="" disabled selected>Error loading models</option>';
    }
  }

  // Attach event listener to the rewrite button
  rewriteButton.addEventListener("click", async () => {
    const selectedModel = modelSelector.value;
    if (!selectedModel) {
      updateStatus("Please select a model first.", true);
      return;
    }

    try {
      Office.context.mailbox.item.getSelectedDataAsync(Office.CoercionType.Text, async (asyncResult: Office.AsyncResult<string>) => {
        if (asyncResult.status === Office.AsyncResultStatus.Failed || !asyncResult.value || asyncResult.value.trim() === "") {
          updateStatus("No text selected in the email, or failed to get selected text. Please select some text to rewrite.", true);
          console.error("Error getting selected data or no text selected:", asyncResult.error?.message);
          return;
        }

        const selectedText = asyncResult.value;
        updateStatus(`Rewriting with ${selectedModel}...`, false);
        rewriteButton.disabled = true;

        try {
          const rewrittenText = await rewriteTextWithOllama(selectedText, selectedModel);

          Office.context.mailbox.item.setSelectedDataAsync(rewrittenText, { coercionType: Office.CoercionType.Text }, setResult => {
            if (setResult.status === Office.AsyncResultStatus.Failed) {
              updateStatus(`Error updating email content: ${setResult.error.message}`, true);
              console.error("Failed to set selected data:", setResult.error.message);
            } else {
              updateStatus("Text successfully rewritten!", false);
            }
            rewriteButton.disabled = false;
          });

        } catch (apiError) {
          updateStatus(`Error from LLM API: ${apiError.message || apiError}`, true);
          console.error("LLM API Error:", apiError);
          rewriteButton.disabled = false;
        }
      });
    } catch (error) {
      updateStatus(`An unexpected error occurred: ${error.message || error}`, true);
      console.error("Unexpected error:", error);
      rewriteButton.disabled = false;
    }
  });

  // Initial population of models
  populateModels();
}

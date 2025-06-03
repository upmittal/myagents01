/*
 * Copyright (c) Microsoft Corporation. All rights reserved. Licensed under the MIT license.
 * See LICENSE in the project root for license information.
 */

/* global Office */

Office.onReady(() => {
  // If needed, Office.js is ready to be called.
});

/**
 * Shows a notification when the add-in command is executed.
 * @param event {Office.AddinCommands.Event}
 */
function action(event) {
  const message = {
    type: Office.MailboxEnums.ItemNotificationMessageType.InformationalMessage,
    message: "Performed action.",
    icon: "Icon.80x80",
    persistent: true,
  };

  // Show a notification message.
  Office.context.mailbox.item.notificationMessages.replaceAsync(
    "ActionPerformanceNotification",
    message
  );

  // Be sure to indicate when the add-in command function is complete.
  event.completed();
}

async function callOllamaApi(textToRewrite) {
  const OLLAMA_API_ENDPOINT = "http://localhost:11434/api/generate";
  const requestBody = {
    model: "mistral", // Using mistral model
    prompt: "Please rewrite the following text: \n" + textToRewrite,
    stream: false, // Expect a single response object
  };

  try {
    const response = await fetch(OLLAMA_API_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorBody = await response.text(); // Get error details if possible
      console.error("Ollama API request failed:", response.status, response.statusText, errorBody);
      throw new Error(`Ollama API request failed: ${response.status} ${response.statusText}`);
    }

    const jsonResponse = await response.json();
    if (jsonResponse && jsonResponse.response) {
      return jsonResponse.response; // The rewritten text
    } else {
      console.error("Ollama API response did not contain expected 'response' field:", jsonResponse);
      throw new Error("Invalid response structure from Ollama API");
    }
  } catch (error) {
    console.error("Error calling Ollama API:", error);
    // Depending on how you want to handle errors upstream, you might re-throw or return null
    // For now, re-throwing to let the caller (rewriteSelectedText) know.
    throw error; 
  }
}

async function rewriteSelectedText(event) {
  Office.context.mailbox.item.getSelectedDataAsync(Office.CoercionType.Text, async function (asyncResult) {
    try {
      if (asyncResult.status === Office.AsyncResultStatus.Succeeded) {
        const selectedText = asyncResult.value.data;
        console.log("Selected text:", selectedText);

        if (selectedText && selectedText.trim().length > 0) {
          console.log("Calling Ollama API to rewrite text...");
          const rewrittenText = await callOllamaApi(selectedText);
          console.log("Rewritten text from Ollama:", rewrittenText);

          if (rewrittenText && rewrittenText.trim() !== "") {
            try {
              await new Promise((resolve, reject) => {
                Office.context.mailbox.item.setSelectedDataAsync(
                  rewrittenText,
                  { coercionType: Office.CoercionType.Text },
                  (asyncResultReplace) => {
                    if (asyncResultReplace.status === Office.AsyncResultStatus.Succeeded) {
                      console.log("Text replacement successful.");
                      resolve();
                    } else {
                      console.error("Error replacing text: ", asyncResultReplace.error.message);
                      reject(new Error(asyncResultReplace.error.message)); // Reject the promise on error
                    }
                  }
                );
              });
            } catch (error) {
              // This catch is for errors from the Promise (e.g., if reject was called)
              console.error("Failed to set selected data:", error.message); 
              // No need to re-throw here as we want event.completed() to be called in finally.
            }
          } else {
            console.log("No rewritten text to insert or rewritten text is empty.");
          }
        } else {
          console.log("No text selected or selected text is empty.");
        }
      } else {
        console.error("Error getting selected text:", asyncResult.error.message);
        // Optionally, notify the user here if appropriate
      }
    } catch (error) {
      // This catch block handles errors from callOllamaApi or other errors within the try block
      console.error("An error occurred during text rewriting:", error);
      // Optionally, notify the user of the failure
    } finally {
      // Always call event.completed(), regardless of success or failure of the operations above.
      event.completed();
    }
  });
}

// Register the function with Office.
Office.actions.associate("action", action);
Office.actions.associate("rewriteSelectedText", rewriteSelectedText);

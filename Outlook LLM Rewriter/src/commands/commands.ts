/*
 * Copyright (c) Microsoft Corporation. All rights reserved. Licensed under the MIT license.
 * See LICENSE in the project root for license information.
 */

// images references in the manifest
import "../../assets/icon-16.png";
import "../../assets/icon-32.png";
import "../../assets/icon-80.png";
import { rewriteTextWithOllama } from "../utils/ollamaApi";

/* global global, Office, self, window */

/**
 * Handles the "rewriteSelectedText" command defined in the manifest.
 * This function is triggered when the user clicks the "Rewrite Selected Text" button in the Outlook ribbon.
 * It retrieves the selected text from the current email, sends it to the Ollama API for rewriting,
 * and then replaces the selected text with the rewritten version.
 * It also provides user notifications for various states (in progress, success, error).
 * @param {Office.AddinCommands.Event} event The Office.AddinCommands.Event object provided by the Office runtime.
 */
Office.actions.associate("rewriteSelectedText", async (event: Office.AddinCommands.Event) => {
  try {
    // Get a reference to the current Outlook item (email or appointment).
    const item = Office.context.mailbox.item;

    // Get the selected data from the email. This is an asynchronous operation.
    item.getSelectedDataAsync(Office.CoercionType.Text, (asyncResult: Office.AsyncResult<string>) => {
      if (asyncResult.status === Office.AsyncResultStatus.Failed) {
        console.error(`Failed to get selected data: ${asyncResult.error.message}`);
        Office.context.mailbox.item.notificationMessages.replaceAsync("getSelectedDataError", {
          type: Office.MailboxEnums.ItemNotificationMessageType.ErrorMessage,
          message: `Error getting selected text: ${asyncResult.error.message}`,
          persistent: false,
        });
        event.completed(); // Must call completed even on error for getSelectedDataAsync
        return;
      }

      const selectedText = asyncResult.value;
      console.log("Selected text:", selectedText);

      // Check if any text was actually selected
      if (!selectedText || selectedText.trim() === "") {
        Office.context.mailbox.item.notificationMessages.replaceAsync("noSelection", {
          type: Office.MailboxEnums.ItemNotificationMessageType.InformationalMessage,
          message: "No text selected. Please select text in the email body to rewrite.",
          persistent: false,
        });
        event.completed(); // Complete here if no text is selected
      } else {
        // Notify the user that rewriting is in progress
        Office.context.mailbox.item.notificationMessages.replaceAsync("rewritingInProgress", {
          type: Office.MailboxEnums.ItemNotificationMessageType.InformationalMessage,
          message: "Rewriting text with LLM...",
          persistent: false,
        });

        // Call the Ollama API utility function
        rewriteTextWithOllama(selectedText)
          .then(rewrittenText => {
            console.log("Rewritten text:", rewrittenText);

            // Replace the selected text in the email with the rewritten text. This is an asynchronous operation.
            Office.context.mailbox.item.setSelectedDataAsync(
              rewrittenText,
              { coercionType: Office.CoercionType.Text },
              (setAsyncResult: Office.AsyncResult<void>) => {
                if (asyncResult.status === Office.AsyncResultStatus.Failed) {
                  console.error(`Failed to set selected data: ${asyncResult.error.message}`);
                  Office.context.mailbox.item.notificationMessages.replaceAsync("setSelectedDataError", {
                    type: Office.MailboxEnums.ItemNotificationMessageType.ErrorMessage,
                    message: `Error updating selected text: ${setAsyncResult.error.message}`, // Clarified error message
                    persistent: false,
                  });
                } else {
                  console.log("Successfully replaced selected text with rewritten content.");
                  Office.context.mailbox.item.notificationMessages.replaceAsync("rewriteSuccessNotification", {
                    type: Office.MailboxEnums.ItemNotificationMessageType.InformationalMessage,
                    message: "Text successfully rewritten and updated!", // Clarified success message
                    persistent: false, 
                  });
                }
                // Crucially, event.completed() must be called after setSelectedDataAsync finishes.
                event.completed();
              }
            );
          })
          .catch(error => {
            // This catch block handles errors from rewriteTextWithOllama or any preceding .then() blocks
            console.error("Failed to rewrite text due to API error or other issue:", error);
            Office.context.mailbox.item.notificationMessages.replaceAsync("rewriteApiError", { // Changed notification ID for clarity
              type: Office.MailboxEnums.ItemNotificationMessageType.ErrorMessage,
              message: `Error during text rewriting process: ${error.message}`, // Centralized error message
              persistent: false,
            });
            event.completed(); // Ensure completion even if the API call or processing fails
          });
      }
      // Note: event.completed() is handled within each specific asynchronous path's final callback (getSelectedDataAsync, setSelectedDataAsync, or catch blocks).
    });
  } catch (error) {
    // This catch block handles synchronous errors in the main try block or errors from Office.context.mailbox.item if it's invalid.
    console.error("General error in rewriteSelectedText command:", error);
    // Attempt to notify the user if possible, though Office.context.mailbox.item might be null if that's the source of error
    if (Office.context.mailbox && Office.context.mailbox.item && Office.context.mailbox.item.notificationMessages) {
      Office.context.mailbox.item.notificationMessages.replaceAsync("commandGeneralError", {
        type: Office.MailboxEnums.ItemNotificationMessageType.ErrorMessage,
        message: `An unexpected error occurred while trying to rewrite text: ${error.message || error}`,
        persistent: false,
      });
    }
    event.completed(); // Ensure completion for general errors.
  }
});

// src/utils/ollamaApi.ts

/**
 * Interface for the expected JSON response structure from the Ollama API's /api/generate endpoint
 * when `stream: false` is used.
 */
export interface OllamaResponse {
  /** The model name that generated the response. */
  model: string;
  /** Timestamp of when the response was created. */
  created_at: string;
  /** The generated text response. This is the primary content of interest. */
  response: string;
  /** Indicates if the generation is complete. Should be true when stream is false. */
  done: boolean;
  /** An encoding of the conversation context, if returned. */
  context?: number[];
  /** Total duration for generating the response. */
  total_duration?: number;
  /** Time spent loading the model. */
  load_duration?: number;
  /** Number of tokens in the prompt. */
  prompt_eval_count?: number;
  /** Time spent evaluating the prompt. */
  prompt_eval_duration?: number;
  /** Number of tokens in the response. */
  eval_count?: number;
  /** Time spent generating the response. */
  eval_duration?: number;
}

/**
 * Calls the Ollama API to rewrite the provided text using a specified model.
 * @param {string} textToRewrite The text string to be rewritten.
 * @param {string} [model="mistral"] The Ollama model to use for rewriting (e.g., "mistral", "llama2").
 *              IMPORTANT: This model must be available in your running Ollama instance.
 *              You may need to configure this if you use a different default model.
 * @returns {Promise<string>} A Promise that resolves to the rewritten text string.
 * @throws {Error} An error if the API call fails, the response is not ok, or the response format is unexpected.
 */
export async function rewriteTextWithOllama(textToRewrite: string, model: string = "mistral"): Promise<string> {
  // IMPORTANT: User Configuration Point
  // Ensure this URL matches your running Ollama instance (e.g., if it's on a different port or host).
  const OLLAMA_API_URL = "http://localhost:11434/api/generate";

  // Construct a more specific prompt for rewriting. This could be further enhanced for better results.
  const prompt = `Rewrite the following text to improve its clarity and conciseness. Original text: "${textToRewrite}"`;

  try {
    const response = await fetch(OLLAMA_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        // IMPORTANT: User Configuration Point
        // The 'model' parameter determines which Ollama model is used.
        // Ensure this model (e.g., "mistral") is available in your Ollama instance.
        // You can pull models using 'ollama pull <modelname>' in your terminal.
        model: model,
        prompt: prompt,
        stream: false, // We want the full response, not a stream
      }),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error("Ollama API Error:", response.status, errorBody);
      throw new Error(`Ollama API request failed with status ${response.status}: ${errorBody}`);
    }

    const data = (await response.json()) as OllamaResponse;
    
    // Check if the response field exists and is a string
    if (data && typeof data.response === 'string') {
      return data.response.trim();
    } else {
      console.error("Ollama API Error: Unexpected response format or missing 'response' field.", data);
      throw new Error("Ollama API Error: Unexpected response format. 'response' field missing or not a string.");
    }

  } catch (error) {
    console.error("Error calling Ollama API:", error);
    // Re-throw the error so the caller can handle it, or customize the error message
    if (error instanceof Error) {
        throw new Error(`Failed to rewrite text via Ollama: ${error.message}`);
    }
    throw new Error("An unknown error occurred while contacting the Ollama API.");
  }
}

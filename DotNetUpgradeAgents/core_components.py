import logging
import requests
from functools import wraps
from datetime import datetime
import os
import json

# Existing logger for general application logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DotNetUpgradeSystem") # General application logger

# --- Dedicated LLM Interaction Logger ---
llm_interaction_logger = logging.getLogger("LLMInteractions")
llm_interaction_logger.setLevel(logging.DEBUG)
llm_interaction_logger.propagate = False

try:
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_interactions.log")
    llm_fh = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
    logger.info(f"LLM interaction log will be saved to: {log_file_path}")
except Exception as e:
    # Fallback if the above path is not writable for some reason
    fallback_log_path = "llm_interactions.log"
    llm_fh = logging.FileHandler(fallback_log_path, mode='a', encoding='utf-8')
    logger.warning(f"Could not create LLM log at preferred location {log_file_path} due to {e}. Using fallback: {fallback_log_path}")

llm_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
llm_fh.setFormatter(llm_formatter)
llm_interaction_logger.addHandler(llm_fh)
# --- End of New Logger Setup ---

def log_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        class_name = ""
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__

        logger.info(f"Running {class_name}.{func.__name__} with args: {args[1:]} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{class_name}.{func.__name__} completed successfully with result: {str(result)[:200]}...") # Log snippet of result
            return result
        except Exception as e:
            logger.error(f"{class_name}.{func.__name__} failed with error: {e}", exc_info=True)
            raise
    return wrapper

class LLMApiClient:
    def __init__(self, api_key: str = None, endpoint: str = None, ollama_model_name: str = None):
        env_api_key = os.getenv("LLM_API_KEY")
        env_endpoint = os.getenv("LLM_API_ENDPOINT")
        env_ollama_model = os.getenv("OLLAMA_MODEL")

        self.api_key = api_key if api_key is not None else env_api_key
        self.endpoint = endpoint if endpoint is not None else env_endpoint
        self.ollama_model = ollama_model_name if ollama_model_name is not None else env_ollama_model

        self.is_ollama_like_endpoint = self.endpoint and \
                                       ("ollama" in self.endpoint.lower() or "localhost:11434" in self.endpoint)

        if not self.endpoint:
            logger.error("LLMApiClient: API Endpoint is not configured. LLM calls will fail.")
            self.endpoint = "MISSING_ENDPOINT" # Mark as missing
        elif self.is_ollama_like_endpoint and not self.ollama_model:
            logger.warning(f"LLMApiClient: Endpoint '{self.endpoint}' appears to be Ollama, but OLLAMA_MODEL environment variable is not set. Will default to 'mistral' if Ollama path is taken in generate_code.")

        if not self.is_ollama_like_endpoint:
            if not self.api_key: # API Key is crucial if not Ollama
                logger.warning("LLMApiClient: API Key for non-Ollama endpoint is not configured. LLM calls might fail or be restricted.")
                self.api_key = "MISSING_API_KEY" # Mark as missing for clarity in generate_code
            else:
                logger.info("LLMApiClient: Configured for a generic/cloud LLM endpoint.")
        elif self.is_ollama_like_endpoint:
            logger.info(f"LLMApiClient: Configured for Ollama-like endpoint: {self.endpoint}. Model: {self.ollama_model or '(will use default)'}.")
            if self.api_key and self.api_key != "MISSING_API_KEY": # API key is set but looks like Ollama
                logger.info("LLMApiClient: API key is set but will be ignored for Ollama calls, as Ollama typically doesn't use Bearer token auth.")

    @log_error
    def generate_code(self, prompt: str, max_tokens: int = 2048) -> str: # Increased default max_tokens
        if not self.endpoint or self.endpoint == "MISSING_ENDPOINT":
            error_msg = "LLMApiClient: Cannot make LLM call. API endpoint is not configured."
            logger.error(error_msg)
            llm_interaction_logger.error(error_msg)
            return f"# ERROR: LLM_CLIENT_NOT_CONFIGURED. {error_msg}"

        headers = {}
        payload = {}
        actual_endpoint = self.endpoint

        llm_interaction_logger.info(f"LLM Request - Endpoint: {actual_endpoint}")
        llm_interaction_logger.debug(f"LLM Request - Prompt (first 300 chars): {prompt[:300]}")

        if self.is_ollama_like_endpoint:
            logger.info("LLMApiClient: Using Ollama-specific request structure.")
            llm_interaction_logger.info("LLM Request Type: Ollama")

            headers = {"Content-Type": "application/json"}

            current_ollama_model = self.ollama_model
            if not current_ollama_model:
                current_ollama_model = "mistral"
                logger.warning(f"LLMApiClient: OLLAMA_MODEL not set, defaulting to '{current_ollama_model}' for Ollama request.")
                llm_interaction_logger.warning(f"Ollama model not specified, defaulting to '{current_ollama_model}'.")

            # Determine if using /api/generate or /api/chat based on common Ollama practice or endpoint structure
            if actual_endpoint.endswith("/api/chat"):
                payload = {
                    "model": current_ollama_model,
                    "messages": [{"role": "user", "content": prompt}], # Chat completions format
                    "stream": False
                }
                # Ollama's /api/chat doesn't use num_predict directly in options for max_tokens.
                # It's more about the model's context window or specific chat parameters.
                # We'll omit explicit max_tokens for /api/chat for now.
            else: # Assuming /api/generate or similar
                actual_endpoint = actual_endpoint if actual_endpoint.endswith("/api/generate") else actual_endpoint.strip('/') + "/api/generate"
                payload = {
                    "model": current_ollama_model,
                    "prompt": prompt,
                    "stream": False
                }
                if max_tokens > 0: # Ollama uses num_predict in options for max output tokens for /generate
                    payload.setdefault("options", {})["num_predict"] = max_tokens

        else: # Generic/Cloud LLM path
            logger.info("LLMApiClient: Using generic LLM request structure.")
            llm_interaction_logger.info("LLM Request Type: Generic/Cloud")
            if not self.api_key or self.api_key == "MISSING_API_KEY":
                error_msg = "LLMApiClient: Cannot make generic LLM call. API key is not configured for this non-Ollama endpoint."
                logger.error(error_msg)
                llm_interaction_logger.error(error_msg)
                return f"# ERROR: LLM_CLIENT_NOT_CONFIGURED. {error_msg}"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            # Generic payload, might need adjustment for specific cloud providers
            payload = {
                "prompt": prompt,
                "max_tokens": max_tokens
                # Some APIs might require a "model" field here too, e.g. OpenAI
                # "model": "gpt-3.5-turbo-instruct" # Example for OpenAI completions
            }

        try:
            payload_str = json.dumps(payload)
            llm_interaction_logger.debug(f"LLM Request - Payload: {payload_str}")
        except Exception as e:
            llm_interaction_logger.error(f"LLM Request - Failed to serialize payload for logging: {e}")
        llm_interaction_logger.debug(f"LLM Request - Headers: {headers}")

        try:
            response = requests.post(
                actual_endpoint, # Use actual_endpoint which might be adjusted for /api/generate
                headers=headers,
                json=payload,
                timeout=180  # Increased timeout further for local LLMs
            )
            response.raise_for_status()
            response_json = response.json()

            llm_interaction_logger.info(f"LLM Response - Success (Status: {response.status_code})")
            try:
                response_json_str = json.dumps(response_json)
                llm_interaction_logger.debug(f"LLM Response - Full JSON: {response_json_str}")
            except Exception as e:
                llm_interaction_logger.error(f"LLM Response - Failed to serialize successful JSON response for logging: {e}")
                llm_interaction_logger.debug(f"LLM Response - Raw Text (if serialization failed): {response.text}")

            generated_text = None
            if self.is_ollama_like_endpoint:
                if actual_endpoint.endswith("/api/chat"): # Ollama chat response
                    if "message" in response_json and "content" in response_json["message"]:
                        generated_text = response_json["message"]["content"]
                elif "response" in response_json: # Ollama generate response
                    generated_text = response_json["response"]

                if generated_text is None: # Common fallback if specific fields not found for Ollama
                    logger.error(f"LLMApiClient: Could not find expected 'response' or 'message.content' field in Ollama JSON. Keys: {response_json.keys()}")
                    llm_interaction_logger.error(f"LLM Response (Ollama) - Text extraction failed. Keys: {response_json.keys()}. Full JSON logged at DEBUG.")
            else: # Generic/Cloud LLM parsing
                if "text" in response_json:
                    generated_text = response_json["text"]
                elif "generated_text" in response_json:
                    generated_text = response_json["generated_text"]
                elif "choices" in response_json and isinstance(response_json["choices"], list) and len(response_json["choices"]) > 0:
                    choice = response_json["choices"][0]
                    if "text" in choice:
                        generated_text = choice["text"]
                    elif "message" in choice and "content" in choice["message"]:
                        generated_text = choice["message"]["content"]
                elif "results" in response_json and isinstance(response_json["results"], list) and len(response_json["results"]) > 0 and "outputText" in response_json["results"][0]:
                     generated_text = response_json["results"][0]["outputText"]

            if generated_text is None:
                log_msg_detail = "Ollama path failed." if self.is_ollama_like_endpoint else "Generic path failed."
                logger.error(f"LLMApiClient: Could not extract text from LLM response. {log_msg_detail} Response keys: {response_json.keys()}")
                llm_interaction_logger.error(f"LLM Response - Text extraction failed. {log_msg_detail} Keys: {response_json.keys()}. Full JSON logged at DEBUG.")
                return f"# ERROR: LLM_RESPONSE_PARSE_FAILED. Unknown response structure. JSON: {str(response_json)[:200]}"

            logger.info(f"LLMApiClient: Successfully received and parsed response. Output (first 100 chars): {str(generated_text)[:100]}") # Ensure generated_text is str
            llm_interaction_logger.debug(f"LLM Response - Extracted text (first 100 chars): {str(generated_text)[:100]}")
            return str(generated_text) # Ensure it's a string

        except requests.exceptions.Timeout as e:
            error_message = f"Timeout: {e}"
            logger.error(f"LLMApiClient: API request timed out: {error_message}")
            llm_interaction_logger.error(f"LLM Error - {error_message}")
            return f"# ERROR: LLM_API_CALL_FAILED. {error_message}"
        except requests.exceptions.RequestException as e:
            response_text = e.response.text if e.response else "No response body"
            error_message = f"RequestException: {e}"
            logger.error(f"LLMApiClient: API request failed: {error_message}. Response body: {response_text}")
            llm_interaction_logger.error(f"LLM Error - {error_message}. Response: {response_text}")
            return f"# ERROR: LLM_API_CALL_FAILED. {error_message}. Check logs for response body."
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e: # Added json.JSONDecodeError to this line
            response_text_for_parse_error = response.text if 'response' in locals() and hasattr(response, 'text') else 'Response object or text not available'
            error_message = f"Failed to parse LLM response JSON or access expected keys: {e}"
            logger.error(f"LLMApiClient: {error_message}. Response was: {response_text_for_parse_error}")
            llm_interaction_logger.error(f"LLM Error - {error_message}. Response text: {response_text_for_parse_error}")
            return f"# ERROR: LLM_RESPONSE_PARSE_FAILED. Error: {e}. Check logs for response body."
        except Exception as e:
            error_message = f"Unexpected error: {e}"
            logger.error(f"LLMApiClient: {error_message}", exc_info=True)
            llm_interaction_logger.error(f"LLM Error - {error_message}", exc_info=True)
            return f"# ERROR: LLM_UNEXPECTED_ERROR. {error_message}"

class HumanFeedback:
    @staticmethod
    @log_error
    def get_feedback(prompt: str, options: list = None) -> str:
        print(f"\n=== Human Feedback Required ===\n{prompt}")
        if options:
            print("Options:")
            for i, opt in enumerate(options, 1):
                print(f"{i}. {opt}")

        while True:
            try:
                response = input("Your decision: ").strip()
            except EOFError: # Handle environments where input might be piped and EOF is sent
                logger.warning("HumanFeedback: EOFError received, no input can be obtained. Defaulting to empty response or first option if available.")
                if options:
                    return options[0] # Default to first option
                return "" # Default to empty for free-form

            if not options:
                if response:
                    logger.info(f"HumanFeedback: Received input: {response}")
                    return response
                else:
                    print("Input cannot be empty. Please provide your decision.")
            elif response.isdigit() and 1 <= int(response) <= len(options):
                decision = options[int(response) - 1]
                logger.info(f"HumanFeedback: Received option: {response} ('{decision}')")
                return decision
            else:
                print(f"Invalid input. Please enter a number between 1 and {len(options)}.")


if __name__ == '__main__':
    logger.info("Testing core components...")
    # TestClass for log_error (can be uncommented for specific decorator testing)
    # class TestClass:
    #     @log_error
    #     def test_method(self, x, y): return x + y
    #     @log_error
    #     def test_method_error(self, x): raise ValueError("Test error")
    # tc = TestClass(); tc.test_method(5, 3)
    # try: tc.test_method_error(1)
    # except ValueError: logger.info("Successfully caught test error from test_method_error.")

    print("\n--- Testing LLMApiClient ---")
    print("Note: For LLMApiClient to make REAL calls, ensure relevant environment variables are set:")
    print("  - LLM_API_ENDPOINT (e.g., http://localhost:11434/api/generate for Ollama, or your cloud endpoint)")
    print("  - OLLAMA_MODEL (e.g., mistral, llama2) if using Ollama")
    print("  - LLM_API_KEY if using a cloud endpoint that requires it")
    print("Output will be logged to console and 'llm_interactions.log'.")

    llm_client_env = LLMApiClient()
    print(f"LLM Client (from env): Endpoint: {llm_client_env.endpoint}, Key set: {bool(llm_client_env.api_key and llm_client_env.api_key != 'MISSING_API_KEY')}, Ollama Model: {llm_client_env.ollama_model}")

    # Example test prompt
    test_prompt = "Explain Python decorators in simple terms."
    if llm_client_env.is_ollama_like_endpoint and not llm_client_env.ollama_model:
        print(f"WARNING: Testing with Ollama endpoint but OLLAMA_MODEL is not set. It will default to 'mistral'. Please set OLLAMA_MODEL for specific model testing.")

    env_output = llm_client_env.generate_code(test_prompt, max_tokens=50) # Short max_tokens for testing
    print(f"LLM Output (env client for '{test_prompt[:30]}...'):\n{env_output}")

    # Test HumanFeedback (will require manual input)
    # print("\n--- Testing HumanFeedback (requires manual input) ---")
    # hf_options = ["Option A", "Option B", "Option C"]
    # hf_decision = HumanFeedback.get_feedback("Please choose an option for testing HumanFeedback:", hf_options)
    # print(f"HumanFeedback Decision: {hf_decision}")
    # hf_freeform = HumanFeedback.get_feedback("Please enter some freeform text:")
    # print(f"HumanFeedback Freeform: {hf_freeform}")

    logger.info("Core components test completed. Check 'llm_interactions.log' for detailed LLM logs.")

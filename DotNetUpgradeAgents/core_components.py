import logging
import requests
from functools import wraps
from datetime import datetime
import os # <-- Add this import

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DotNetUpgradeSystem")

# Compact decorator for logging and error handling
def log_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        class_name = ""
        if args and hasattr(args[0], '__class__'):
            class_name = args[0].__class__.__name__

        logger.info(f"Running {class_name}.{func.__name__} with args: {args[1:]} and kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{class_name}.{func.__name__} completed successfully with result: {result}")
            return result
        except Exception as e:
            logger.error(f"{class_name}.{func.__name__} failed with error: {e}", exc_info=True)
            # Depending on the desired behavior, you might want to re-raise the exception
            # or handle it and return a specific value (e.g., None or an error message)
            # For now, let's re-raise to make sure issues are visible
            raise
    return wrapper

# Simulated LLM API client -> Will become Real LLM API client
class LLMApiClient:
    def __init__(self, api_key: str = None, endpoint: str = None):
        # Load from environment variables first
        env_api_key = os.getenv("LLM_API_KEY")
        env_endpoint = os.getenv("LLM_API_ENDPOINT")

        # Use provided args if they exist, otherwise use env vars
        self.api_key = api_key if api_key is not None else env_api_key
        self.endpoint = endpoint if endpoint is not None else env_endpoint

        if not self.api_key:
            logger.warning("LLMApiClient: API key not found. Please set LLM_API_KEY environment variable or pass as argument.")
        if not self.endpoint:
            logger.warning("LLMApiClient: API endpoint not found. Please set LLM_API_ENDPOINT environment variable or pass as argument.")

        if not self.api_key or not self.endpoint:
            logger.error("LLMApiClient: Crucial configuration (API Key or Endpoint) is missing. Real LLM calls will fail.")
            # Retain placeholder values if essential config is missing, so generate_code can check them.
            self.api_key = self.api_key or "MISSING_API_KEY"
            self.endpoint = self.endpoint or "MISSING_ENDPOINT"


    @log_error
    def generate_code(self, prompt: str, max_tokens: int = 1500) -> str: # Added max_tokens
        if not self.api_key or self.api_key == "MISSING_API_KEY" or            not self.endpoint or self.endpoint == "MISSING_ENDPOINT":
            error_msg = "LLMApiClient: Cannot make LLM call. API key or endpoint is not configured."
            logger.error(error_msg)
            return f"# ERROR: LLM_CLIENT_NOT_CONFIGURED. {error_msg}"

        logger.info(f"LLMApiClient: Sending prompt to {self.endpoint} (first 100 chars): {prompt[:100]}...")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # The structure of this payload is HIGHLY DEPENDENT on the specific LLM API provider.
        # Users will need to adjust this. Common examples:
        # OpenAI-like: {"model": "model-name", "prompt": prompt, "max_tokens": max_tokens}
        # Anthropic-like: {"prompt": f"\n\nHuman: {prompt}\n\nAssistant:", "model": "claude-2", "max_completion_tokens": max_tokens}
        # Simple generic: {"prompt": prompt, "max_tokens": max_tokens}
        # We'll use a simple generic one here.
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens
        }
        # Add a log for the payload being sent (omitting sensitive parts if necessary, though API key is in header)
        logger.debug(f"LLMApiClient: Sending payload: {payload}")


        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=60  # seconds
            )
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)

            response_json = response.json()
            logger.debug(f"LLMApiClient: Received JSON response: {response_json}") # Log the whole JSON for debugging

            # Extracting generated text - THIS IS HIGHLY PROVIDER-SPECIFIC.
            # Common patterns:
            # 1. response_json.get("text")
            # 2. response_json.get("generated_text")
            # 3. response_json.get("choices")[0].get("text")
            # 4. response_json.get("completions")[0].get("data").get("text")
            # 5. response_json.get("results")[0].get("outputText")
            # For this generic client, we'll try a few common ones.
            generated_text = None
            if "text" in response_json:
                generated_text = response_json["text"]
            elif "generated_text" in response_json:
                generated_text = response_json["generated_text"]
            elif "choices" in response_json and isinstance(response_json["choices"], list) and len(response_json["choices"]) > 0:
                if "text" in response_json["choices"][0]:
                    generated_text = response_json["choices"][0]["text"]
                elif "message" in response_json["choices"][0] and "content" in response_json["choices"][0]["message"]: # OpenAI chat format
                    generated_text = response_json["choices"][0]["message"]["content"]
            elif "results" in response_json and isinstance(response_json["results"], list) and len(response_json["results"]) > 0 and "outputText" in response_json["results"][0]: # AI21 Studio
                 generated_text = response_json["results"][0]["outputText"]

            if generated_text is None:
                logger.error(f"LLMApiClient: Could not find known text field in LLM response. Response keys: {response_json.keys()}")
                return f"# ERROR: LLM_RESPONSE_PARSE_FAILED. Unknown response structure. JSON: {str(response_json)[:200]}"

            logger.info(f"LLMApiClient: Successfully received and parsed response. Output (first 100 chars): {generated_text[:100]}")
            return generated_text

        except requests.exceptions.Timeout as e:
            logger.error(f"LLMApiClient: API request timed out: {e}")
            return f"# ERROR: LLM_API_CALL_FAILED. Timeout: {e}"
        except requests.exceptions.RequestException as e:
            logger.error(f"LLMApiClient: API request failed: {e}. Response body: {e.response.text if e.response else 'No response body'}")
            return f"# ERROR: LLM_API_CALL_FAILED. RequestException: {e}. Check logs for response body."
        except (KeyError, IndexError, TypeError, requests.exceptions.JSONDecodeError) as e: # Added TypeError for safety & requests.exceptions.JSONDecodeError
            logger.error(f"LLMApiClient: Failed to parse LLM response JSON or access expected keys: {e}. Response was: {response.text if 'response' in locals() else 'Response object not available'}")
            return f"# ERROR: LLM_RESPONSE_PARSE_FAILED. Error: {e}. Check logs for response body."
        except Exception as e:
            logger.error(f"LLMApiClient: An unexpected error occurred: {e}", exc_info=True)
            return f"# ERROR: LLM_UNEXPECTED_ERROR. {e}"


# Human feedback interface
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
            response = input("Your decision: ").strip()
            if not options: # Free-form input
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
                print(f"Invalid input. Please enter a number between 1 and {len(options)} or type out your choice if free-form.")

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    logger.info("Testing core components...")

    # Test log_error decorator
    # class TestClass:
    #     @log_error
    #     def test_method(self, x, y):
    #         return x + y

    #     @log_error
    #     def test_method_error(self, x):
    #         raise ValueError("Test error")

    # tc = TestClass()
    # tc.test_method(5, 3)
    # try:
    #     tc.test_method_error(1)
    # except ValueError:
    #     logger.info("Successfully caught test error from test_method_error.")

    # Test LLMApiClient
    print("\n--- Testing LLMApiClient ---")
    print("Note: For LLMApiClient to make REAL calls in later steps, ensure LLM_API_KEY and LLM_API_ENDPOINT environment variables are set.")
    print("Currently, it will indicate missing configuration or that real calls are not yet implemented.")

    # Instantiate to pick up from environment variables (or be None)
    llm_client_env = LLMApiClient()
    print(f"LLM Client (from env): Key set: {bool(llm_client_env.api_key and llm_client_env.api_key != 'MISSING_API_KEY')}, Endpoint set: {bool(llm_client_env.endpoint and llm_client_env.endpoint != 'MISSING_ENDPOINT')}")
    env_output = llm_client_env.generate_code("Test prompt for env-configured client")
    print(f"LLM Output (env client): {env_output}")

    # Instantiate with direct parameters (for testing override or specific cases)
    # llm_client_direct = LLMApiClient(api_key="test_key", endpoint="http://localhost:1234/api")
    # print(f"LLM Client (direct params): Key set: {bool(llm_client_direct.api_key)}, Endpoint set: {bool(llm_client_direct.endpoint)}")
    # direct_output = llm_client_direct.generate_code("Test prompt for direct-configured client")
    # print(f"LLM Output (direct client): {direct_output}")

    # Test HumanFeedback
    # Note: input() will require manual interaction if you run this directly.
    # feedback_decision = HumanFeedback.get_feedback("ITASCA namespace detected. How should we proceed?", ["Replace with alternative", "Keep as is", "Custom action"])
    # print(f"Human Feedback Decision: {feedback_decision}")

    # feedback_freeform = HumanFeedback.get_feedback("Please provide the path to the NeoLoad executable:")
    # print(f"Human Feedback Freeform: {feedback_freeform}")
    logger.info("Core components test completed.")

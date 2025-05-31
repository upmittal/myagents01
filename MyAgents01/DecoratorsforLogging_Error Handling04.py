import logging
import functools
from typing import Any, Callable, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def log_activity(func: Callable) -> Callable:
    """Log function entry/exit with arguments/results"""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)
        logger.info(f"→ Entering {func.__name__} with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"← Exiting {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Error in {func.__name__}: {str(e)}", exc_info=True)
            raise
    return wrapper

def handle_errors(llm_api_key: Optional[str] = None) -> Callable:
    """Handle errors with LLM suggestions and human feedback"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"{func.__name__} failed: {str(e)}"
                
                # LLM suggestion (mocked here; replace with real API)
                suggestion = f"[LLM Suggestion] Consider checking {error_msg.split(':')[0]}"
                
                # Interactive feedback loop
                print(f"🤖 ERROR: {error_msg}")
                print(f"💡 Suggestion: {suggestion}")
                choice = input("Options: [r]etry, [s]kip, [f]ix with AI, [q]uit: ").lower()
                
                if choice == "r":
                    return wrapper(*args, **kwargs)  # Retry
                elif choice == "s":
                    return None  # Skip
                elif choice == "f":
                    print(f"🔧 Applying AI fix: {suggestion}")
                    # Simulate AI-assisted repair
                    return func(*args, **kwargs)  # Retry after fix
                else:
                    raise SystemExit("Operation cancelled by user")
        return wrapper
    return decorator
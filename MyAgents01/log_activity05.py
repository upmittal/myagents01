def log_activity(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"→ Entering {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"← Exiting {func.__name__} with result: {result}")
            return result
        except Exception as e:
            logging.error(f"❌ Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"{func.__name__} failed: {str(e)}"
            print(f"🚨 ERROR: {error_msg}")
            suggestion = args[0]._call_llm(error_msg)  # args[0] is the class instance
            print(f"💡 Suggestion: {suggestion}")
            choice = input("Options: [r]etry, [s]kip, [f]ix with AI: ").lower()
            if choice == "r":
                return wrapper(*args, **kwargs)
            elif choice == "f":
                print(f"🔧 Applying AI fix: {suggestion}")
                return func(*args, **kwargs)  # Retry after fix
            else:
                return None
    return wrapper
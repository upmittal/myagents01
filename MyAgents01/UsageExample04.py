if __name__ == "__main__":
    converter = VBConverterTool(llm_api_key="your-llm-key")
    
    # Test with valid code
    valid_code = "VB Function Example"
    output = converter.interactive_conversion(valid_code)
    print("Output:", output)
    
    # Test with invalid code
    invalid_code = "BadVBCode Invalid Syntax"
    output = converter.interactive_conversion(invalid_code)
    print("Output after feedback:", output)
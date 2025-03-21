from langchain_ollama import OllamaLLM

def get_llama_response(user_input: str, model_name: str = "llama3.3:70b") -> str:
    """
    Get a response from the llama3.3 model using OllamaLLM.
    
    Args:
        user_input: The user's query
        model_name: Name of the Ollama model to use
        
    Returns:
        String response from the model
    """
    # Initialize OllamaLLM with the specified model
    ollama_llm = OllamaLLM(model=model_name, request_timeout=420)
    
    try:
        # Invoke the model with the user input
        response = ollama_llm.invoke(user_input)
        return response
    except Exception as e:
        print(f"Model invocation failed: {e}")
        return "Error: LLM timed out or encountered an issue."

# Example usage:
response = get_llama_response("What are the common findings in PSMA PET scans?")
print(response)
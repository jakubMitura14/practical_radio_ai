# **************************************************************************
# * Import
# **************************************************************************
import os
import json
import requests
import time
from pathlib import Path
import streamlit as st
import uuid  # Add import for UUID generation

# **************************************************************************
# * Init
# **************************************************************************
# Hardcoded values
API_BASE = "https://ki-plattform.diz-ag.med.ovgu.de/api/"
MODEL = "llama3.2-vision:90b"
PROVIDER = "DeepSeek"
API_KEY_FILE = "api_key.txt"  # File to store the API key

# **************************************************************************
# * Function
# **************************************************************************
def request_DIZ_deepseek(prompt: str, api_key: str, system_msg: str = "") -> str:
    r"""
    Send a prompt to DIZ API (DeepSeek) and return the response.

    Args:
        - prompt: The prompt to send to the API.
        - api_key: API key provided by the user
        - system_msg: Optional system message

    Returns:
        The response from the API or error message.
    """
    # Define the endpoint for completions
    url = f"{API_BASE}chat/completions"
    
    # Define headers with the user-provided API key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Define the JSON data to be sent in the POST request
    data = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_msg
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    max_retries = 8
    retry_count = 0
    wait_time = 1  # Start with 1 second

    while retry_count <= max_retries:
        try:
            # Make the POST request using the requests library
            # Add a space at the end of the user prompt
            data["messages"][1]["content"] += " "

            response = requests.post(url, headers=headers, json=data, timeout=30)


            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Parse the response
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "No response content")
        
        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count > max_retries:
                return f"Error connecting to the API after {max_retries} retries: {str(e)}"
            
            print(f"API request failed (attempt {retry_count}/{max_retries}). Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            wait_time *= 2  # Exponential backoff

def save_api_key(api_key: str):
    """Save the API key to a local file."""
    try:
        with open(API_KEY_FILE, "w") as f:
            f.write(api_key)
        return True
    except Exception as e:
        print(f"Error saving API key: {str(e)}")
        return False

def load_api_key():
    """Load the API key from a local file if it exists."""
    try:
        if os.path.exists(API_KEY_FILE):
            with open(API_KEY_FILE, "r") as f:
                return f.read().strip()
    except Exception as e:
        print(f"Error loading API key: {str(e)}")
    return ""

# **************************************************************************
# * Main
# **************************************************************************
if __name__ == '__main__':
    # Streamlit app
    st.set_page_config(layout="wide")
    st.title("DIZ DeepSeek Chatbot")

    # Create layout with columns
    col1_top, col2_top = st.columns([1, 3])
    col1_bottom, col2_bottom = st.columns(2)
    
    # Initialize session state for storing responses
    if "grammar_response" not in st.session_state:
        st.session_state.grammar_response = ""
    if "summary_response" not in st.session_state:
        st.session_state.summary_response = ""
    if "last_input" not in st.session_state:
        st.session_state.last_input = ""
    if "initial_grammar_correction" not in st.session_state:
        st.session_state.initial_grammar_correction = ""
    
    # Small window top left for API key
    with col1_top:
        # Load API key from file if it exists
        default_api_key = load_api_key()
        api_key = st.text_input("API Key", value=default_api_key, key="api_key", type="password")
        
        # Save API key if it changes
        if api_key != default_api_key and api_key:
            if save_api_key(api_key):
                st.success("API key saved successfully!")
    
    # Big window top right for input text
    with col2_top:
        user_input = st.text_area(
            "Original Text (Press Process button to analyze)",
            "",
            key="user_input",
            height=200
        )
        
        # Add a process button
        if st.button("Process Text"):
            if api_key and user_input:
                grammar_response = request_DIZ_deepseek("hello", api_key, " ")

                with st.spinner("Processing grammar correction..."):
                    # First get and display grammar correction
                    grammar_system = "Sie sind Experte für deutsche Grammatik. Ihre Aufgabe besteht darin, Grammatikfehler im Text zu korrigieren, ohne die Bedeutung zu verändern. Entfernen Sie keine Informationen. Behalten Sie alles Unwichtige bei, egal ob Sie es für wichtig halten oder nicht."
                    grammar_response = request_DIZ_deepseek(user_input, api_key, grammar_system)
                    st.session_state.grammar_response = grammar_response
                    # Store the initial grammar correction before user edits
                    st.session_state.initial_grammar_correction = grammar_response
                    st.session_state.last_input = user_input
                
                with st.spinner("Processing inconsistencies analysis..."):
                    # Then get and display inconsistencies
                    summary_system = "Sie sind Experte für Nuklearmedizin und Radiologie. Sollten Sie in sich widersprüchliche oder irrelevante Informationen finden, beschreiben Sie diese bitte."
                    st.session_state.summary_response = request_DIZ_deepseek(user_input, api_key, summary_system)
                
                st.success("Processing complete!")
            else:
                st.error("Please provide both API Key and Original Text.")
    
    # Big window bottom left for grammar correction
    with col1_bottom:
        st.subheader("Corrected Grammar")
        
        grammar_text = st.text_area(
            "Grammar corrected text (editable)",
            value=st.session_state.grammar_response,
            key="grammar_text_area",
            height=300
        )
        
        # Save button for grammar correction
        if st.button("Save Corrected Text"):
            if grammar_text:
                try:
                    # Generate a UUID4 for the filename
                    filename = f"{uuid.uuid4()}.json"
                    
                    # Create a dictionary with all required fields
                    data = {
                        "input_text": st.session_state.last_input,
                        "initial_grammar_correction": st.session_state.initial_grammar_correction,
                        "user_corrected_text": grammar_text,
                        "inconsistencies": st.session_state.summary_response
                    }
                    
                    # Save as JSON file
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    st.success(f"Text saved to {filename}")
                except Exception as e:
                    st.error(f"Error saving file: {str(e)}")
            else:
                st.warning("No text to save.")
    
    # Window bottom right for summary
    with col2_bottom:
        st.subheader("Inconsistencies")
        
        st.text_area(
            "Inconsistencies in text",
            value=st.session_state.summary_response,
            key="summary_text_area",
            height=300
        )
    
    # Add instructions at the bottom
    st.markdown("---")
    st.markdown("**Instructions:** Enter your API key, paste your text in the input field, "
                "then click 'Process Text'. You can edit the corrected text before saving it.")
    

#python3 -m streamlit run /workspaces/practical_radio_ai/DIZ_deepseek_api.py
import os
import torch
import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
from prompts import build_prompts

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_huggingface_model(model_name: str, device: str = "cuda" if torch.cuda.is_available() else "cpu") -> Tuple[Any, Any]:
    """Load model and tokenizer without event loop dependencies"""
    logger.info(f"Loading model {model_name} on {device}")
    
    try:
        # Load HuggingFace token for gated models
        token_path = "/workspaces/practical_radio_ai/hugging_face_key.txt"
        if os.path.exists(token_path):
            with open(token_path, "r") as file:
                token = file.read().strip()
                login(token=token)
                logger.info("Successfully logged in with HuggingFace token")
        
        # Load tokenizer with padding on left side
        tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side="left")
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model with appropriate configuration
        model = AutoModelForCausalLM.from_pretrained(
            model_name, 
            device_map=device,
            torch_dtype=torch.float16
        )
        
        return model, tokenizer
        
    except Exception as e:
        error_message = f"Error loading model {model_name}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_message)
        raise RuntimeError(error_message)

def process_prompts_in_batches(
    user_input: str,
    prompt_keys: List[str],
    prompts_dict: Dict[str, Dict[str, Any]],
    model_name: str,
    batch_size: int = 4
) -> Dict[str, str]:
    """Process prompts in batches with fixed token length handling"""
    logger.info(f"Processing {len(prompt_keys)} prompts in batches of {batch_size}")
    
    # Filter valid prompts
    valid_prompt_keys = [key for key in prompt_keys if key in prompts_dict]
    if not valid_prompt_keys:
        logger.error(f"No valid prompts found in keys: {prompt_keys}")
        return {}
    
    try:
        model, tokenizer = load_huggingface_model(model_name)
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return {key: f"ERROR: Model loading failed: {str(e)}" for key in valid_prompt_keys}
    
    results = {}
    max_input_length = 1024  # Reduce input length to avoid token overflow
    
    for i in range(0, len(valid_prompt_keys), batch_size):
        batch_keys = valid_prompt_keys[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(valid_prompt_keys) + batch_size - 1)//batch_size}: {batch_keys}")
        
        batch_prompts = []
        for key in batch_keys:
            prompt_data = prompts_dict[key]
            system_prompt = prompt_data.get("prompt", f"Analyze the following text for {key}.")
            
            # Format prompt and truncate input if needed
            if len(user_input) > max_input_length:
                truncated_input = user_input[:max_input_length] + "..."
            else:
                truncated_input = user_input
                
            formatted_prompt = f"<prompt>{system_prompt}</prompt>\n\n{truncated_input}"
            batch_prompts.append(formatted_prompt)
        
        try:
            inputs = tokenizer(batch_prompts, return_tensors="pt", padding=True, truncation=True, max_length=max_input_length)
            inputs = {k: v.to(model.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.1,
                    num_return_sequences=1,
                    pad_token_id=tokenizer.pad_token_id
                )
            
            batch_responses = tokenizer.batch_decode(output_ids, skip_special_tokens=True)
            
            for j, key in enumerate(batch_keys):
                response = batch_responses[j]
                if truncated_input in response:
                    response = response.split(truncated_input)[-1].strip()
                results[key] = response
                logger.info(f"Processed {key}: Response length {len(response)}  response {response}")
                
        except Exception as e:
            error_message = f"Error processing batch: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            for key in batch_keys:
                results[key] = f"ERROR: {str(e)}"
    
    return results

def apply_field_dependencies(form_values: Dict[str, Any], form_fields: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Apply dependencies between fields based on current values."""
    updated_fields = {}
    for field_key, field_info in form_fields.items():
        if isinstance(field_info, dict):
            updated_fields[field_key] = field_info.copy()
        else:
            updated_fields[field_key] = field_info
            
    # Handle field dependencies
    for field_key, field_info in updated_fields.items():
        # Skip non-dict fields
        if not isinstance(field_info, dict):
            continue
            
        # Check for dependency
        if "dependency" in field_info:
            dep = field_info["dependency"]
            dep_field = dep.get("field")
            dep_value = dep.get("value")
            
            # Get the current value of the dependent field
            current_value = form_values.get(dep_field)
            
            # Check if dependency is met
            is_dependent = False
            if current_value is not None:
                if isinstance(dep_value, list):
                    is_dependent = current_value not in dep_value
                else:
                    is_dependent = current_value != dep_value
                    
            # Update disabled state
            if is_dependent:
                field_info["disabled"] = True
    
    return updated_fields

def process_text_input(
    user_input: str,
    field_info_dict: Dict[str, Dict[str, Any]],
    model_name: str,
    batch_size: int = 4
) -> Dict[str, Dict[str, Any]]:
    """Main function to process text input and update observables"""
    from prompts import build_prompts
    
    logger.info(f"Processing text input with model {model_name}, batch size {batch_size}")
    
    # Group fields by prompt_key
    prompt_groups = {}
    for field_key, field_info in field_info_dict.items():
        prompt_key = field_info.get('prompt_key')
        if prompt_key:
            if prompt_key not in prompt_groups:
                prompt_groups[prompt_key] = []
            prompt_groups[prompt_key].append((field_key, field_info))
    
    unique_prompt_keys = list(prompt_groups.keys())
    
    # Process prompts
    prompt_responses = process_prompts_in_batches(
        user_input,
        unique_prompt_keys,
        build_prompts(),
        model_name,
        batch_size
    )
    
    # Map responses to fields
    field_results = {}
    for prompt_key, response in prompt_responses.items():
        fields = prompt_groups.get(prompt_key, [])
        for field_key, field_info in fields:
            field_results[field_key] = {
                'field_key': field_key,
                'prompt_key': prompt_key,
                'response': response,
                'success': not response.startswith("ERROR:"),
                'error': response if response.startswith("ERROR:") else None,
                'field_type': field_info.get('type', 'text'),
                'value': postprocess_response(response, field_info)
            }
    
    return field_results

def postprocess_response(response: str, field_info: Dict[str, Any]) -> Any:
    """Process response based on field type"""
    field_type = field_info.get('type', 'text')
    
    if field_type == 'radio':
        return parse_yes_no(response) or "Unknown"
    elif field_type == 'multiselect':
        options = field_info.get('options', [])
        return parse_list_values(response, options)
    elif field_type == 'number':
        return parse_number(response) or 0.0
    elif field_type == 'date':
        return parse_date(response)
    
    return response.strip() if response else ""

def parse_yes_no(response: str) -> Optional[str]:
    """Parse Yes/No response"""
    response_lower = response.lower()
    yes_patterns = ['yes', 'positive', 'present', 'confirmed', 'true']
    no_patterns = ['no', 'negative', 'absent', 'not present', 'false']
    
    if any(p in response_lower for p in yes_patterns):
        return 'Yes'
    if any(p in response_lower for p in no_patterns):
        return 'No'
    return None

def parse_list_values(response: str, valid_options: List[str]) -> List[str]:
    """Parse list values from response"""
    response_lower = response.lower()
    return [opt for opt in valid_options if opt.lower() in response_lower]

def parse_number(response: str) -> Optional[float]:
    """Parse number from response"""
    import re
    match = re.search(r'[-+]?\d*\.?\d+', response)
    try:
        return float(match.group(0)) if match else None
    except (ValueError, AttributeError):
        return None

def parse_date(response: str) -> Optional[str]:
    """Parse date from response"""
    import re
    date_patterns = [
        r'(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})',
        r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, response)
        if match:
            return match.group(0)
    return None
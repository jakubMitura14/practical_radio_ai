import streamlit as st
import datetime
import json
import re
import time
import traceback
import os
from typing import Dict, Any, List
import logging
from create_summary import generate_summary
# Import from local modules
from prompts import build_prompts
from main_text_input_process import process_text_input

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize observable state
if 'form_state' not in st.session_state:
    st.session_state.form_state = {}

# Load language from config
config = {"language": "en"}
with open("/workspaces/practical_radio_ai/psma_GUI_model/config.json", "r") as f:
    config.update(json.load(f))

# Load prompts based on configured language
language = config.get("language", "en")
prompt_dict = build_prompts(language)

def update_field_value(field_key: str, value: Any):
    """Update a field value in the form state"""
    st.session_state.form_state[field_key] = value
    # Update summary whenever a field changes
    st.session_state.form_state["summary"] = generate_summary(st.session_state.form_state)

def update_summary():
    """Update the summary based on current form state"""
    summary_lines = []
    form_fields = initialize_form_fields()
    
    # Process each section in order
    sections = sorted(set(field["section"] for field in form_fields.values()))
    
    for section in sections:
        section_fields = {k: v for k, v in form_fields.items() if v["section"] == section}
        
        for field_key, field_info in section_fields.items():
            value = get_field_value(field_key)
            if value:
                if isinstance(value, list):
                    value_str = ", ".join(map(str, value))
                elif isinstance(value, datetime.date):
                    value_str = value.strftime("%Y-%m-%d")
                else:
                    value_str = str(value)
                    
                if value_str.strip() and value_str.lower() not in ["no", "unknown", "0"]:
                    summary_lines.append(f"{field_info['label']}: {value_str}")
    
    # Update summary field
    summary = "\n".join(summary_lines)
    st.session_state.form_state["summary"] = summary

def get_field_value(field_key: str, default: Any = None) -> Any:
    """Get a field value from the form state"""
    return st.session_state.form_state.get(field_key, default)

def on_field_change(field_key: str):
    """Callback for field value changes"""
    def callback():
        widget_key = f"widget_{field_key}"
        if widget_key in st.session_state:
            value = st.session_state[widget_key]
            update_field_value(field_key, value)
    return callback

def render_field(field_key: str, field_info: Dict[str, Any], enabled: bool = True):
    """Render a form field using the observable pattern"""
    if not enabled:
        return
    
    current_value = get_field_value(field_key, field_info.get("default"))
    widget_key = f"widget_{field_key}"
    
    if field_info["type"] == "text":
        st.text_input(
            field_info["label"],
            value=current_value,
            key=widget_key,
            on_change=on_field_change(field_key),
            disabled=not enabled
        )
        
    elif field_info["type"] == "text_area":
        st.text_area(
            field_info["label"],
            value=current_value,
            key=widget_key,
            height=150,
            on_change=on_field_change(field_key),
            disabled=not enabled
        )
        
    elif field_info["type"] == "number":
        try:
            value = float(current_value) if current_value is not None else 0.0
        except (ValueError, TypeError):
            value = 0.0
            
        st.number_input(
            field_info["label"],
            value=value,
            key=widget_key,
            on_change=on_field_change(field_key),
            disabled=not enabled
        )
        
    elif field_info["type"] == "date":
        if isinstance(current_value, str) and current_value:
            try:
                value = datetime.datetime.strptime(current_value, "%Y-%m-%d").date()
            except:
                value = None
        else:
            value = current_value if current_value else None
            
        st.date_input(
            field_info["label"],
            value=value,
            key=widget_key,
            on_change=on_field_change(field_key),
            disabled=not enabled
        )
        
    elif field_info["type"] == "radio":
        options = field_info["options"]
        if current_value in options:
            index = options.index(current_value)
        else:
            index = options.index(field_info["default"]) if current_value is None else 0
            
        st.radio(
            field_info["label"],
            options=options,
            index=index,
            key=widget_key,
            horizontal=True,
            on_change=on_field_change(field_key),
            disabled=not enabled
        )
        
    elif field_info["type"] == "multiselect":
        if current_value is None:
            default = field_info["default"]
        elif not isinstance(current_value, list):
            default = [current_value] if current_value else []
        else:
            default = current_value
            
        # Ensure all values are in options
        default = [v for v in default if v in field_info["options"]]
        
        st.multiselect(
            label=field_info["label"],
            options=field_info["options"],
            default=default,
            key=widget_key,
            on_change=on_field_change(field_key),
            disabled=not enabled
        )

def check_field_dependencies(field_info: Dict[str, Any]) -> bool:
    """Check if a field's dependencies are satisfied"""
    if "dependency" not in field_info:
        return True
        
    dep = field_info["dependency"]
    dep_field = dep.get("field")
    dep_value = dep.get("value")
    
    current_value = get_field_value(dep_field)
    
    if current_value is None:
        return False
        
    if isinstance(dep_value, list):
        return current_value in dep_value
    
    return current_value == dep_value

def display_form(form_fields: Dict[str, Dict[str, Any]]):
    """Display the form using observable pattern"""
    # Get all sections in the form fields
    sections = sorted(set(field["section"] for field in form_fields.values()))
    
    for section in sections:
        st.subheader(section)
        with st.expander(f"Expand {section}", expanded=(section == "Clinical History & Procedure")):
            section_fields = {k: v for k, v in form_fields.items() if v["section"] == section}
            
            for field_key, field_info in section_fields.items():
                enabled = check_field_dependencies(field_info)
                render_field(field_key, field_info, enabled)
                
            st.markdown("---")

def process_text():
    """Process text input and update form state"""
    # Get raw text
    raw_text = st.session_state.raw_text
    if not raw_text.strip():
        st.error("Please enter text to process.")
        return
    
    # Initialize progress tracking
    progress_bar = st.session_state.get("progress_bar")
    progress_text = st.session_state.get("progress_text")
    
    try:
        # Process text
        form_fields = initialize_form_fields()
        results, execution_time = process_text_input(
            raw_text,
            form_fields,
        )
        
        # Update form state with results
        if results:
            total = len(results)
            for i, (field_key, result) in enumerate(results.items()):
                if progress_bar:
                    progress_bar.progress((i + 1) / total)
                if progress_text:
                    progress_text.text(f"Processing field {i+1}/{total}: {field_key}")
                
                if result["success"]:
                    update_field_value(field_key, result["value"])
                
                time.sleep(0.05)  # Small delay for UI updates
        
        # Update progress
        if progress_bar:
            progress_bar.progress(1.0)
        if progress_text:
            progress_text.text("Processing complete!")
            
        st.success(f"Text processing completed successfully! Time taken: {execution_time}")
        st.session_state.processing_complete = True
        
    except Exception as e:
        st.error(f"Error processing text: {str(e)}")
        logger.error(f"Error in process_text: {str(e)}\n{traceback.format_exc()}")

def initialize_form_fields() -> Dict[str, Dict[str, Any]]:
    """Initialize form fields with their metadata based on prompt dictionary"""
    # Generate dynamic form fields based on the prompt dictionary
    dynamic_fields = {}
    
    for prompt_key, prompt_data in prompt_dict.items():
        field_info = {}
        field_info["label"] = prompt_key
        field_info["prompt_key"] = prompt_key
        field_info["field_key"] = prompt_data.get("field_key", prompt_key.lower().replace(" ", "_"))
        field_info["section"] = prompt_data.get("section", "Other")
        field_info["type"] = prompt_data.get("type", "text")
        
        # Set default values based on field type
        if field_info["type"] == "text" or field_info["type"] == "text_area":
            field_info["default"] = ""
        elif field_info["type"] == "number":
            field_info["default"] = 0.0
        elif field_info["type"] == "date":
            field_info["default"] = None
        elif field_info["type"] == "radio":
            if "allowed_answers" in prompt_data:
                field_info["options"] = prompt_data["allowed_answers"] + ["Unknown"]
            else:
                field_info["options"] = ["Yes", "No", "Unknown"]
            field_info["default"] = "Unknown"
        elif field_info["type"] == "multiselect":
            if "options" in prompt_data:
                field_info["options"] = prompt_data["options"]
            field_info["default"] = []
        
        # Add dependency if it exists
        if "dependency" in prompt_data:
            field_info["dependency"] = prompt_data["dependency"]
        
        # Add field to dynamic fields dictionary
        dynamic_fields[field_info["field_key"]] = field_info
    
    # Add special fields
    if "summary" not in dynamic_fields:
        dynamic_fields["summary"] = {
            "label": "Summary",
            "prompt_key": "Summary",
            "field_key": "summary",
            "section": "Summary",
            "type": "text_area",
            "default": ""
        }
    
    if "raw_text" not in dynamic_fields:
        dynamic_fields["raw_text"] = {
            "label": "Raw Text Input",
            "prompt_key": "Raw Text Input",
            "field_key": "raw_text",
            "section": "Input",
            "type": "text_area",
            "default": ""
        }
    
    return dynamic_fields

def main():
    st.set_page_config(page_title="PSMA PET/CT Report", layout="wide")
    st.title("PSMA PET/CT Structured Report Generator")
    
    # Initialize state and summary
    if 'raw_text' not in st.session_state:
        st.session_state.raw_text = ""
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'form_state' not in st.session_state:
        st.session_state.form_state = {}
        st.session_state.form_state["summary"] = ""
    
    # Add this before display_form to ensure summary is initialized
    if "summary" not in st.session_state.form_state:
        st.session_state.form_state["summary"] = ""
    
    # Sidebar
    st.sidebar.title("Input Options")
    st.sidebar.markdown("### Enter raw text to process")
    st.sidebar.text_area("Raw Text Input", key="raw_text", height=300)
    
    if st.sidebar.button("Process Text"):
        st.session_state.progress_bar = st.sidebar.progress(0)
        st.session_state.progress_text = st.sidebar.empty()
        process_text()
    
    # User guide
    with st.sidebar.expander("User Guide"):
        st.markdown("""
        ### How to use this tool:
        1. Enter the raw text in the sidebar
        2. Click "Process Text" to analyze
        3. Review and edit the form fields
        4. Export results when done
        """)
    
    # Main form
    form_fields = initialize_form_fields()
    display_form(form_fields)
    
    # Summary section
    st.header("Summary")
    summary = get_field_value("summary", "")
    st.text_area("Summary", value=summary, height=300, key="summary_display", disabled=True)
    
    # Export options
    st.header("Export Options")
    col1, col2 = st.columns(2)
    
    if col1.button("Export as JSON"):
        data = {k: get_field_value(k) for k in form_fields.keys()}
        st.download_button(
            "Download JSON",
            data=json.dumps(data, indent=2, default=str),
            file_name=f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    if col2.button("Export as Text"):
        text = generate_text_report(form_fields)
        st.download_button(
            "Download Text",
            data=text,
            file_name=f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

def generate_text_report(form_fields: Dict[str, Dict[str, Any]]) -> str:
    """Generate text report from form state"""
    lines = [
        "PSMA PET/CT STRUCTURED REPORT",
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 50,
        ""
    ]
    
    sections = sorted(set(field["section"] for field in form_fields.values() if field["section"] != "Input"))
    for section in sections:
        lines.extend([f"\n{section.upper()}", "-" * len(section)])
        
        section_fields = {k: v for k, v in form_fields.items() if v["section"] == section}
        for field_key, field_info in section_fields.items():
            value = get_field_value(field_key)
            if value:
                if isinstance(value, list):
                    value_str = ", ".join(map(str, value))
                elif isinstance(value, datetime.date):
                    value_str = value.strftime("%Y-%m-%d")
                else:
                    value_str = str(value)
                    
                if value_str.strip():
                    lines.append(f"{field_info['label']}: {value_str}")
    
    return "\n".join(lines)

if __name__ == "__main__":
    main()
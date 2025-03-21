import streamlit as st
import datetime
import json
import re
import time
import traceback
import os
from typing import Dict, Any, List
import logging
# Import from local modules
from prompts import build_prompts
from main_text_input_process import process_text_input

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize observable state
if 'form_state' not in st.session_state:
    st.session_state.form_state = {}

def update_field_value(field_key: str, value: Any):
    """Update a field value in the form state"""
    st.session_state.form_state[field_key] = value

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
            index = options.index(field_info["default"])
            
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
    sections = set(field["section"] for field in form_fields.values())
    
    for section in sorted(sections):
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
    
    # Load config
    config = {"model_name": "ibm-granite/granite-3.2-8b-instruct-preview", "batch_size": 1}
    try:
        with open("/workspaces/practical_radio_ai/psma_GUI_model/config.json", "r") as f:
            config.update(json.load(f))
    except Exception as e:
        logger.warning(f"Using default config: {str(e)}")
    
    # Initialize progress tracking
    progress_bar = st.session_state.get("progress_bar")
    progress_text = st.session_state.get("progress_text")
    
    try:
        # Process text
        form_fields = initialize_form_fields()
        results = process_text_input(
            raw_text,
            form_fields,
            config["model_name"],
            config["batch_size"]
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
            
        st.success("Text processing completed successfully!")
        st.session_state.processing_complete = True
        
    except Exception as e:
        st.error(f"Error processing text: {str(e)}")
        logger.error(f"Error in process_text: {str(e)}\n{traceback.format_exc()}")

def initialize_form_fields() -> Dict[str, Dict[str, Any]]:
    """Initialize form fields with their metadata"""
    return {
        # Clinical History & Procedure
        "indication_for_scan": {
            "type": "multiselect",
            "label": "Indication for the scan",
            "options": ["Primary staging", "CRPC/Recurrent restaging", "PSMA expression assessment for PSMA targeted therapy"],
            "default": [],
            "section": "Clinical History & Procedure",
            "prompt_key": "Indication for the scan"
        },
        "therapy_date": {
            "type": "date",
            "label": "Date of initiation of last/recurrent therapy",
            "default": None,
            "section": "Clinical History & Procedure",
            "prompt_key": "Date of initiation of last/recurrent therapy"
        },
        "radical_prostatectomy": {
            "type": "radio",
            "label": "Radical prostatectomy?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Clinical History & Procedure",
            "prompt_key": "Radical prostatectomy"
        },
        "external_beam_radiation": {
            "type": "radio",
            "label": "External beam radiation to prostate?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Clinical History & Procedure",
            "prompt_key": "External beam radiation to prostate"
        },
        "post_prostatectomy_radiation": {
            "type": "radio",
            "label": "Post-prostatectomy external beam radiation?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Clinical History & Procedure",
            "prompt_key": "Post-prostatectomy external beam radiation"
        },
        "brachytherapy": {
            "type": "radio",
            "label": "Brachytherapy to prostate?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Clinical History & Procedure",
            "prompt_key": "Brachytherapy to prostate"
        },
        "androgen_deprivation": {
            "type": "radio",
            "label": "Androgen deprivation therapy?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Clinical History & Procedure",
            "prompt_key": "Androgen deprivation therapy"
        },
        "arpi": {
            "type": "radio",
            "label": "ARPI (i.e., abiraterone)?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Clinical History & Procedure",
            "prompt_key": "ARPI (i.e., abiraterone)"
        },
        "chemotherapy": {
            "type": "radio",
            "label": "Chemotherapy?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Clinical History & Procedure",
            "prompt_key": "Chemotherapy"
        },
        "other_therapies": {
            "type": "text",
            "label": "Other (therapies, etc.)",
            "default": "",
            "section": "Clinical History & Procedure",
            "prompt_key": "Other therapies"
        },
        "psa_level": {
            "type": "text",
            "label": "Most recent PSA levels (ng/mL)",
            "default": "",
            "section": "Clinical History & Procedure",
            "prompt_key": "Most recent PSA levels (ng/mL)"
        },
        "psa_date": {
            "type": "date",
            "label": "Date of measurement (dd/mm/yyyy)",
            "default": None,
            "section": "Clinical History & Procedure",
            "prompt_key": "Date of PSA measurement"
        },
        
        # Comparison or Prior Imaging
        "radiopharmaceutical": {
            "type": "text",
            "label": "Radiopharmaceutical used",
            "default": "",
            "section": "Comparison or Prior Imaging",
            "prompt_key": "Radiopharmaceutical used"
        },
        "dosage_injection_time": {
            "type": "text",
            "label": "Dosage and Injection Time",
            "default": "",
            "section": "Comparison or Prior Imaging",
            "prompt_key": "Dosage and Injection Time"
        },
        
        # Accompanying CT
        "ct_type": {
            "type": "radio",
            "label": "Accompanying CT",
            "options": ["Attenuation Correction Only", "Diagnostic with contrast", "Diagnostic without contrast"],
            "default": "Attenuation Correction Only",
            "section": "Accompanying CT",
            "prompt_key": "Accompanying CT"
        },
        
        # Background Reference Uptake
        "liver_suv_mean": {
            "type": "number",
            "label": "Liver SUV mean",
            "default": 0.0,
            "section": "Background Reference Uptake",
            "prompt_key": "Liver SUV mean"
        },
        "liver_lesion": {
            "type": "radio",
            "label": "Liver lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Background Reference Uptake",
            "prompt_key": "Liver lesion present"
        },
        "blood_pool_suv_mean": {
            "type": "number",
            "label": "Blood pool SUV mean",
            "default": 0.0,
            "section": "Background Reference Uptake",
            "prompt_key": "Blood pool SUV mean"
        },
        "blood_pool_lesion": {
            "type": "radio",
            "label": "Blood pool lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Background Reference Uptake",
            "prompt_key": "Blood pool lesion present"
        },
        "other_suv_mean": {
            "type": "number",
            "label": "Other SUV mean",
            "default": 0.0,
            "section": "Background Reference Uptake",
            "prompt_key": "Other SUV mean"
        },
        "other_lesion": {
            "type": "radio",
            "label": "Other lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Background Reference Uptake",
            "prompt_key": "Other lesion present"
        },
        
        # Prostate Gland
        "prostate_lesions": {
            "type": "radio",
            "label": "Prostate Gland: Lesion(s) present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Prostate Gland",
            "prompt_key": "Prostate Gland lesions"
        },
        "prostate_lesion_count": {
            "type": "text",
            "label": "Number of lesions",
            "default": "",
            "section": "Prostate Gland",
            "prompt_key": "Prostate Gland number of lesions",
            "dependency": {"field": "prostate_lesions", "value": "Yes"}
        },
        "prostate_suv_max": {
            "type": "text",
            "label": "SUVmax",
            "default": "",
            "section": "Prostate Gland",
            "prompt_key": "Prostate Gland SUVmax",
            "dependency": {"field": "prostate_lesions", "value": "Yes"}
        },
        "prostate_localization": {
            "type": "multiselect",
            "label": "Localization",
            "options": ["Left", "Right", "Base", "Mid", "Apical", "Anterior", "Posterior"],
            "default": [],
            "section": "Prostate Gland",
            "prompt_key": "Prostate Gland localization",
            "dependency": {"field": "prostate_lesions", "value": "Yes"}
        },
        
        # Prostate Bed (Post-Prostatectomy)
        "prostate_bed_lesions": {
            "type": "radio",
            "label": "Prostate Bed: Lesion(s) present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Prostate Bed (Post-Prostatectomy)",
            "prompt_key": "Prostate Bed lesions"
        },
        "prostate_bed_lesion_count": {
            "type": "text",
            "label": "Number of lesions",
            "default": "",
            "section": "Prostate Bed (Post-Prostatectomy)",
            "prompt_key": "Prostate Bed number of lesions",
            "dependency": {"field": "prostate_bed_lesions", "value": "Yes"}
        },
        "prostate_bed_suv_max": {
            "type": "text",
            "label": "SUVmax",
            "default": "",
            "section": "Prostate Bed (Post-Prostatectomy)",
            "prompt_key": "Prostate Bed SUVmax",
            "dependency": {"field": "prostate_bed_lesions", "value": "Yes"}
        },
        "prostate_bed_localization": {
            "type": "multiselect",
            "label": "Localization",
            "options": ["Left", "Right", "Base", "Mid", "Apical", "Anterior", "Posterior"],
            "default": [],
            "section": "Prostate Bed (Post-Prostatectomy)",
            "prompt_key": "Prostate Bed localization",
            "dependency": {"field": "prostate_bed_lesions", "value": "Yes"}
        },
        
        # Seminal Vesicles
        "seminal_vesicles_lesions": {
            "type": "radio",
            "label": "Seminal Vesicles: Lesion(s) present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Seminal Vesicles",
            "prompt_key": "Seminal Vesicles lesions"
        },
        "seminal_vesicles_lesion_count": {
            "type": "text",
            "label": "Number of lesions",
            "default": "",
            "section": "Seminal Vesicles",
            "prompt_key": "Seminal Vesicles number of lesions",
            "dependency": {"field": "seminal_vesicles_lesions", "value": "Yes"}
        },
        "seminal_vesicles_suv_max": {
            "type": "text",
            "label": "SUVmax",
            "default": "",
            "section": "Seminal Vesicles",
            "prompt_key": "Seminal Vesicles SUVmax",
            "dependency": {"field": "seminal_vesicles_lesions", "value": "Yes"}
        },
        "seminal_vesicles_localization": {
            "type": "multiselect",
            "label": "Localization",
            "options": ["Left", "Right"],
            "default": [],
            "section": "Seminal Vesicles",
            "prompt_key": "Seminal Vesicles localization",
            "dependency": {"field": "seminal_vesicles_lesions", "value": "Yes"}
        },
        
        # Pelvic LN(s)
        "pelvic_ln_lesions": {
            "type": "radio",
            "label": "Pelvic LN(s): Lesion(s) present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Pelvic LN(s)",
            "prompt_key": "Pelvic LN lesions"
        },
        
        # External Iliac
        "external_iliac_lesion": {
            "type": "radio",
            "label": "External Iliac: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Pelvic LN(s)",
            "prompt_key": "External Iliac lesion",
            "dependency": {"field": "pelvic_ln_lesions", "value": "Yes"}
        },
        "external_iliac_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "External Iliac size and SUVmax",
            "dependency": {"field": "external_iliac_lesion", "value": "Yes"}
        },
        "external_iliac_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "External Iliac notes",
            "dependency": {"field": "external_iliac_lesion", "value": "Yes"}
        },
        
        # Internal Iliac
        "internal_iliac_lesion": {
            "type": "radio",
            "label": "Internal Iliac: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Pelvic LN(s)",
            "prompt_key": "Internal Iliac lesion",
            "dependency": {"field": "pelvic_ln_lesions", "value": "Yes"}
        },
        "internal_iliac_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Internal Iliac size and SUVmax",
            "dependency": {"field": "internal_iliac_lesion", "value": "Yes"}
        },
        "internal_iliac_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Internal Iliac notes",
            "dependency": {"field": "internal_iliac_lesion", "value": "Yes"}
        },
        
        # Obturator
        "obturator_lesion": {
            "type": "radio",
            "label": "Obturator: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Pelvic LN(s)",
            "prompt_key": "Obturator lesion",
            "dependency": {"field": "pelvic_ln_lesions", "value": "Yes"}
        },
        "obturator_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Obturator size and SUVmax",
            "dependency": {"field": "obturator_lesion", "value": "Yes"}
        },
        "obturator_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Obturator notes",
            "dependency": {"field": "obturator_lesion", "value": "Yes"}
        },
        
        # Common iliac
        "common_iliac_lesion": {
            "type": "radio",
            "label": "Common iliac: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Pelvic LN(s)",
            "prompt_key": "Common iliac lesion",
            "dependency": {"field": "pelvic_ln_lesions", "value": "Yes"}
        },
        "common_iliac_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Common iliac size and SUVmax",
            "dependency": {"field": "common_iliac_lesion", "value": "Yes"}
        },
        "common_iliac_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Common iliac notes",
            "dependency": {"field": "common_iliac_lesion", "value": "Yes"}
        },
        
        # Perirectal
        "perirectal_lesion": {
            "type": "radio",
            "label": "Perirectal: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Pelvic LN(s)",
            "prompt_key": "Perirectal lesion",
            "dependency": {"field": "pelvic_ln_lesions", "value": "Yes"}
        },
        "perirectal_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Perirectal size and SUVmax",
            "dependency": {"field": "perirectal_lesion", "value": "Yes"}
        },
        "perirectal_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Perirectal notes",
            "dependency": {"field": "perirectal_lesion", "value": "Yes"}
        },
        
        # Presacral
        "presacral_lesion": {
            "type": "radio",
            "label": "Presacral: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Pelvic LN(s)",
            "prompt_key": "Presacral lesion",
            "dependency": {"field": "pelvic_ln_lesions", "value": "Yes"}
        },
        "presacral_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Presacral size and SUVmax",
            "dependency": {"field": "presacral_lesion", "value": "Yes"}
        },
        "presacral_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Presacral notes",
            "dependency": {"field": "presacral_lesion", "value": "Yes"}
        },
        
        # Other Pelvic LN
        "other_pelvic_ln_lesion": {
            "type": "radio",
            "label": "Other Pelvic LN: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Pelvic LN(s)",
            "prompt_key": "Other Pelvic LN lesion",
            "dependency": {"field": "pelvic_ln_lesions", "value": "Yes"}
        },
        "other_pelvic_ln_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Other Pelvic LN size and SUVmax",
            "dependency": {"field": "other_pelvic_ln_lesion", "value": "Yes"}
        },
        "other_pelvic_ln_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Pelvic LN(s)",
            "prompt_key": "Other Pelvic LN notes",
            "dependency": {"field": "other_pelvic_ln_lesion", "value": "Yes"}
        },
        
        # Extra-pelvic LN(s)
        "extra_pelvic_ln_lesions": {
            "type": "radio",
            "label": "Extra-pelvic LN(s): Lesion(s) present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Extra-pelvic LN lesions"
        },
        
        # Abdominal
        "abdominal_lesion": {
            "type": "radio",
            "label": "Abdominal: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Abdominal lesion",
            "dependency": {"field": "extra_pelvic_ln_lesions", "value": "Yes"}
        },
        "abdominal_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Abdominal size and SUVmax",
            "dependency": {"field": "abdominal_lesion", "value": "Yes"}
        },
        "abdominal_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Abdominal notes",
            "dependency": {"field": "abdominal_lesion", "value": "Yes"}
        },
        
        # Thoracic
        "thoracic_lesion": {
            "type": "radio",
            "label": "Thoracic: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Thoracic lesion",
            "dependency": {"field": "extra_pelvic_ln_lesions", "value": "Yes"}
        },
        "thoracic_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Thoracic size and SUVmax",
            "dependency": {"field": "thoracic_lesion", "value": "Yes"}
        },
        "thoracic_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Thoracic notes",
            "dependency": {"field": "thoracic_lesion", "value": "Yes"}
        },
        
        # Supraclavicular
        "supraclavicular_lesion": {
            "type": "radio",
            "label": "Supraclavicular: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Supraclavicular lesion",
            "dependency": {"field": "extra_pelvic_ln_lesions", "value": "Yes"}
        },
        "supraclavicular_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Supraclavicular size and SUVmax",
            "dependency": {"field": "supraclavicular_lesion", "value": "Yes"}
        },
        "supraclavicular_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Supraclavicular notes",
            "dependency": {"field": "supraclavicular_lesion", "value": "Yes"}
        },
        
        # Other Extra-pelvic LN
        "other_extra_pelvic_ln_lesion": {
            "type": "radio",
            "label": "Other Extra-pelvic LN: Lesion present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Other Extra-pelvic LN lesion",
            "dependency": {"field": "extra_pelvic_ln_lesions", "value": "Yes"}
        },
        "other_extra_pelvic_ln_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Other Extra-pelvic LN size and SUVmax",
            "dependency": {"field": "other_extra_pelvic_ln_lesion", "value": "Yes"}
        },
        "other_extra_pelvic_ln_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Extra-pelvic LN(s)",
            "prompt_key": "Other Extra-pelvic LN notes",
            "dependency": {"field": "other_extra_pelvic_ln_lesion", "value": "Yes"}
        },
        
        # Skeletal/Bone Metastases
        "skeletal_lesions": {
            "type": "radio",
            "label": "Skeletal/Bone Metastases: Lesion(s) present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Skeletal/Bone Metastases",
            "prompt_key": "Skeletal lesions"
        },
        "skeletal_lesion_count": {
            "type": "radio",
            "label": "Number of lesions",
            "options": ["0", "1", "2-4", "5+"],
            "default": "0",
            "section": "Skeletal/Bone Metastases",
            "prompt_key": "Skeletal number of lesions",
            "dependency": {"field": "skeletal_lesions", "value": "Yes"}
        },
        "bone_marrow_involvement": {
            "type": "radio",
            "label": "Bone marrow involvement",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Skeletal/Bone Metastases",
            "prompt_key": "Bone marrow involvement",
            "dependency": {"field": "skeletal_lesions", "value": "Yes"}
        },
        "skeletal_localization_notes": {
            "type": "text",
            "label": "Localization Notes",
            "default": "",
            "section": "Skeletal/Bone Metastases",
            "prompt_key": "Skeletal localization notes",
            "dependency": {"field": "skeletal_lesions", "value": "Yes"}
        },
        
        # Visceral Metastases
        "visceral_lesions": {
            "type": "radio",
            "label": "Visceral Metastases: Lesion(s) present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "Visceral Metastases",
            "prompt_key": "Visceral lesions"
        },
        "visceral_localization": {
            "type": "multiselect",
            "label": "Localization",
            "options": ["Lung", "Liver", "Brain", "Other"],
            "default": [],
            "section": "Visceral Metastases",
            "prompt_key": "Visceral localization",
            "dependency": {"field": "visceral_lesions", "value": "Yes"}
        },
        "visceral_size_suv": {
            "type": "text",
            "label": "Size & SUVmax",
            "default": "",
            "section": "Visceral Metastases",
            "prompt_key": "Visceral size and SUVmax",
            "dependency": {"field": "visceral_lesions", "value": "Yes"}
        },
        "visceral_notes": {
            "type": "text",
            "label": "Notes",
            "default": "",
            "section": "Visceral Metastases",
            "prompt_key": "Visceral notes",
            "dependency": {"field": "visceral_lesions", "value": "Yes"}
        },
        
        # PSMA-negative lesions
        "psma_negative_lesions": {
            "type": "radio",
            "label": "PSMA-negative lesions noted on CT: Lesion(s) present?",
            "options": ["Yes", "No", "Unknown"],
            "default": "Unknown",
            "section": "PSMA-negative lesions",
            "prompt_key": "PSMA-negative lesions"
        },
        "psma_negative_lesion_count": {
            "type": "text",
            "label": "Number of lesions",
            "default": "",
            "section": "PSMA-negative lesions",
            "prompt_key": "PSMA-negative number of lesions",
            "dependency": {"field": "psma_negative_lesions", "value": "Yes"}
        },
        "psma_negative_localization_notes": {
            "type": "text",
            "label": "Localization Notes",
            "default": "",
            "section": "PSMA-negative lesions",
            "prompt_key": "PSMA-negative localization notes",
            "dependency": {"field": "psma_negative_lesions", "value": "Yes"}
        },
        
        # Indeterminate findings
        "indeterminate_findings": {
            "type": "text_area",
            "label": "Indeterminate findings/ additional notes",
            "default": "",
            "section": "Indeterminate findings",
            "prompt_key": "Indeterminate findings"
        },
        
        # Impression
        "mitnm": {
            "type": "text",
            "label": "miTNM",
            "default": "",
            "section": "Impression",
            "prompt_key": "miTNM classification"
        },
        "promise": {
            "type": "text",
            "label": "PROMISE",
            "default": "",
            "section": "Impression",
            "prompt_key": "PROMISE score"
        },
        "primary": {
            "type": "text",
            "label": "PRIMARY",
            "default": "",
            "section": "Impression",
            "prompt_key": "PRIMARY score"
        },
        "recip": {
            "type": "text",
            "label": "RECIP",
            "default": "",
            "section": "Impression",
            "prompt_key": "RECIP score"
        },
        
        # Other scoring systems
        "other_scoring_systems": {
            "type": "text_area",
            "label": "Other scoring systems notes",
            "default": "",
            "section": "Other scoring systems",
            "prompt_key": "Other scoring systems notes"
        },
        
        # Summary
        "summary": {
            "type": "text_area",
            "label": "Summary",
            "default": "",
            "section": "Summary",
            "prompt_key": "Summary"
        }
    }

def main():
    st.set_page_config(page_title="PSMA PET/CT Report", layout="wide")
    st.title("PSMA PET/CT Structured Report Generator")
    
    # Initialize state
    if 'raw_text' not in st.session_state:
        st.session_state.raw_text = ""
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
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
    
    sections = set(field["section"] for field in form_fields.values())
    for section in sorted(sections):
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
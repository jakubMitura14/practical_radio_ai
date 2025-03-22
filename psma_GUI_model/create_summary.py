from typing import Dict, Any
import datetime

def generate_summary(form_state: Dict[str, Any]) -> str:
    """
    Generate a summary from the form state in a format where each observation
    starts with the question/category followed by the finding.
    """
    summary_lines = []

    def add_field(label: str, value: Any):
        if value and str(value).strip() and str(value).lower() not in ["no", "unknown", "0"]:
            if isinstance(value, list):
                value_str = ", ".join(map(str, value))
            elif isinstance(value, datetime.date):
                value_str = value.strftime("%Y-%m-%d")
            else:
                value_str = str(value)
            summary_lines.append(f"{label}: {value_str}")

    # Clinical History & Procedure
    if form_state.get("indication_for_scan"):
        add_field("Indication for scan", form_state["indication_for_scan"])
    
    if form_state.get("therapy_date"):
        add_field("Last therapy date", form_state["therapy_date"])

    treatment_fields = [
        ("radical_prostatectomy", "Radical prostatectomy"),
        ("external_beam_radiation", "External beam radiation"),
        ("post_prostatectomy_radiation", "Post-prostatectomy radiation"),
        ("brachytherapy", "Brachytherapy"),
        ("androgen_deprivation", "Androgen deprivation therapy"),
        ("arpi", "ARPI"),
        ("chemotherapy", "Chemotherapy")
    ]
    
    for field, label in treatment_fields:
        if form_state.get(field) == "Yes":
            add_field("Previous treatment", label)

    if form_state.get("other_therapies"):
        add_field("Other therapies", form_state["other_therapies"])

    if form_state.get("psa_level"):
        add_field("PSA level", f"{form_state['psa_level']} ng/mL")
        if form_state.get("psa_date"):
            add_field("PSA measurement date", form_state["psa_date"])

    # Imaging Details
    if form_state.get("radiopharmaceutical"):
        add_field("Radiopharmaceutical", form_state["radiopharmaceutical"])
    
    if form_state.get("dosage_injection_time"):
        add_field("Dosage and injection", form_state["dosage_injection_time"])
    
    if form_state.get("ct_type"):
        add_field("CT type", form_state["ct_type"])

    # Background Reference
    background_fields = [
        ("liver", "Liver"),
        ("blood_pool", "Blood pool"),
        ("other", "Other")
    ]
    
    for prefix, label in background_fields:
        suv = form_state.get(f"{prefix}_suv_mean")
        if suv and float(suv) > 0:
            add_field(f"{label} SUV mean", suv)
        if form_state.get(f"{prefix}_lesion") == "Yes":
            add_field(f"{label} status", "Lesion present")

    # Disease Sites
    sites = [
        ("prostate", "Prostate Gland"),
        ("prostate_bed", "Prostate Bed"),
        ("seminal_vesicles", "Seminal Vesicles")
    ]
    
    for prefix, label in sites:
        if form_state.get(f"{prefix}_lesions") == "Yes":
            findings = []
            if form_state.get(f"{prefix}_lesion_count"):
                findings.append(f"Number of lesions: {form_state[f'{prefix}_lesion_count']}")
            if form_state.get(f"{prefix}_suv_max"):
                findings.append(f"SUVmax: {form_state[f'{prefix}_suv_max']}")
            if form_state.get(f"{prefix}_localization"):
                findings.append(f"Location: {', '.join(form_state[f'{prefix}_localization'])}")
            if findings:
                add_field(label, "; ".join(findings))

    # Lymph Nodes
    if form_state.get("pelvic_ln_lesions") == "Yes":
        pelvic_nodes = [
            "external_iliac",
            "internal_iliac",
            "obturator",
            "common_iliac",
            "perirectal",
            "presacral",
            "other_pelvic_ln"
        ]
        
        for node in pelvic_nodes:
            if form_state.get(f"{node}_lesion") == "Yes":
                details = []
                if form_state.get(f"{node}_size_suv"):
                    details.append(form_state[f"{node}_size_suv"])
                if form_state.get(f"{node}_notes"):
                    details.append(form_state[f"{node}_notes"])
                if details:
                    node_label = node.replace("_", " ").title()
                    add_field(f"Pelvic LN - {node_label}", "; ".join(details))

    # Extra-pelvic Nodes
    if form_state.get("extra_pelvic_ln_lesions") == "Yes":
        extra_pelvic_nodes = [
            "abdominal",
            "thoracic",
            "supraclavicular",
            "other_extra_pelvic_ln"
        ]
        
        for node in extra_pelvic_nodes:
            if form_state.get(f"{node}_lesion") == "Yes":
                details = []
                if form_state.get(f"{node}_size_suv"):
                    details.append(form_state[f"{node}_size_suv"])
                if form_state.get(f"{node}_notes"):
                    details.append(form_state[f"{node}_notes"])
                if details:
                    node_label = node.replace("_", " ").title()
                    add_field(f"Extra-pelvic LN - {node_label}", "; ".join(details))

    # Metastases
    if form_state.get("skeletal_lesions") == "Yes":
        details = []
        if form_state.get("skeletal_lesion_count"):
            details.append(f"Number of lesions: {form_state['skeletal_lesion_count']}")
        if form_state.get("bone_marrow_involvement") == "Yes":
            details.append("Bone marrow involvement present")
        if form_state.get("skeletal_localization_notes"):
            details.append(form_state["skeletal_localization_notes"])
        if details:
            add_field("Skeletal/Bone Metastases", "; ".join(map(str, details)))

    if form_state.get("visceral_lesions") == "Yes":
        details = []
        if form_state.get("visceral_localization"):
            details.append(f"Sites: {', '.join(map(str, form_state['visceral_localization']))}")
        if form_state.get("visceral_size_suv"):
            details.append(str(form_state["visceral_size_suv"]))
        if form_state.get("visceral_notes"):
            details.append(str(form_state["visceral_notes"]))
        if details:
            add_field("Visceral Metastases", "; ".join(map(str, details)))

    # PSMA-negative lesions
    if form_state.get("psma_negative_lesions") == "Yes":
        details = []
        if form_state.get("psma_negative_lesion_count"):
            details.append(f"Number of lesions: {form_state['psma_negative_lesion_count']}")
        if form_state.get("psma_negative_localization_notes"):
            details.append(str(form_state["psma_negative_localization_notes"]))
        if details:
            add_field("PSMA-negative lesions", "; ".join(map(str, details)))

    # Impression
    impression_fields = [
        ("mitnm", "miTNM"),
        ("promise", "PROMISE"),
        ("primary", "PRIMARY"),
        ("recip", "RECIP")
    ]
    
    for field, label in impression_fields:
        if form_state.get(field):
            add_field(label, form_state[field])

    # Additional Notes
    if form_state.get("indeterminate_findings"):
        add_field("Additional Notes", form_state["indeterminate_findings"])
    
    if form_state.get("other_scoring_systems"):
        add_field("Other Scoring Systems", form_state["other_scoring_systems"])

    return "\n".join(summary_lines)
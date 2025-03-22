# You can place this script in a file, for example: survey_prompts.py
# The script generates a dictionary of prompts for each question,
# starting with the system prompt "You are nuclear medicine expert".
# It uses Pydantic to ensure basic structure validity.
from pydantic import BaseModel, Field, conlist, ValidationError
from typing import List, Optional, Dict, Union, Any

# General prompts for English and German
general_prompt_en = "You are nuclear medicine expert. Based on the provided clinical information, provide a brief and precise answer"
general_prompt_de = "Sie sind Nuklearmedizinexperte. Basierend auf den bereitgestellten klinischen Informationen, geben Sie eine kurze und präzise Antwort"

class ClosedQuestion(BaseModel):
    question: str
    allowed_answers: List[str]

class OpenQuestion(BaseModel):
    question: str

class CheckboxQuestion(BaseModel):
    question: str
    options: List[str]

class SurveySchema(BaseModel):
    # Each key in 'questions' maps to either a closed question, open question, or checkbox question
    questions: Dict[str, Union[ClosedQuestion, OpenQuestion, CheckboxQuestion]]

def determine_field_type(prompt_data: Dict[str, Any], key: str = "") -> str:
    """Determine the appropriate field type based on prompt data"""
    if "options" in prompt_data:
        return "multiselect"
    elif "allowed_answers" in prompt_data:
        return "radio"
    elif prompt_data["question"].lower().find("date") >= 0:
        return "date"
    elif prompt_data["question"].lower().find("suv") >= 0 or prompt_data["question"].lower().find("psa") >= 0:
        return "number"
    elif prompt_data["question"].lower().find("notes") >= 0 or key == "Summary" or key == "Indeterminate findings":
        return "text_area"
    else:
        return "text"

def build_prompts(language: str = "en") -> Dict[str, Union[Dict, str]]:
    """
    Returns a dictionary of prompts for each question, prefixed by the system prompt.
    In case of checkbox or closed questions, only the given set of answers are allowed.
    
    Args:
        language (str): Language code - "en" for English or "de" for German
    """
    # Define sections and their order
    sections = {
        "Clinical History & Procedure": 1,
        "Comparison or Prior Imaging": 2,
        "Accompanying CT": 3,
        "Background Reference Uptake": 4,
        "Prostate Gland": 5,
        "Prostate Bed (Post-Prostatectomy)": 6,
        "Seminal Vesicles": 7,
        "Pelvic LN(s)": 8,
        "Extra-pelvic LN(s)": 9,
        "Skeletal/Bone Metastases": 10,
        "Visceral Metastases": 11,
        "PSMA-negative lesions": 12,
        "Indeterminate findings": 13,
        "Impression": 14,
        "Summary": 15
    }
    
    survey_dict = {
        # Clinical History & Procedure
        "Indication for the scan": {
            "question": f"{general_prompt_en}, what is the indication for the PSMA PET/CT scan?",
            "question_de": f"{general_prompt_de}, was ist die Indikation für den PSMA-PET/CT-Scan?",
            "options": [
                "Primary staging",
                "CRPC/Recurrent restaging",
                "PSMA expression assessment for PSMA targeted therapy"
            ],
            "section": "Clinical History & Procedure",
            "field_key": "indication"
        },
        "Date of initiation of last/recurrent therapy": {
            "question": f"{general_prompt_en}, what is the date of initiation of last/recurrent therapy (dd/mm/yyyy)?",
            "question_de": f"{general_prompt_de}, wann wurde die letzte/wiederkehrende Therapie begonnen (TT/MM/JJJJ)?",
            "section": "Clinical History & Procedure",
            "field_key": "therapy_date"
        },
        "Radical prostatectomy": {
            "question": f"{general_prompt_en}, has the patient undergone radical prostatectomy?",
            "question_de": f"{general_prompt_de}, wurde bei dem Patienten eine radikale Prostatektomie durchgeführt?",
            "allowed_answers": ["Yes", "No"],
            "section": "Clinical History & Procedure",
            "field_key": "radical_prostatectomy"
        },
        "External beam radiation to prostate": {
            "question": f"{general_prompt_en}, has the patient received external beam radiation to prostate?",
            "question_de": f"{general_prompt_de}, hat der Patient eine externe Strahlentherapie der Prostata erhalten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Clinical History & Procedure",
            "field_key": "external_beam_radiation"
        },
        "Post-prostatectomy external beam radiation": {
            "question": f"{general_prompt_en}, has the patient received post-prostatectomy external beam radiation?",
            "question_de": f"{general_prompt_de}, hat der Patient nach der Prostatektomie eine externe Strahlentherapie erhalten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Clinical History & Procedure",
            "field_key": "post_prostatectomy_radiation"
        },
        "Brachytherapy to prostate": {
            "question": f"{general_prompt_en}, has the patient undergone brachytherapy to prostate?",
            "question_de": f"{general_prompt_de}, wurde bei dem Patienten eine Brachytherapie der Prostata durchgeführt?",
            "allowed_answers": ["Yes", "No"],
            "section": "Clinical History & Procedure",
            "field_key": "brachytherapy"
        },
        "Androgen deprivation therapy": {
            "question": f"{general_prompt_en}, has the patient received androgen deprivation therapy?",
            "question_de": f"{general_prompt_de}, hat der Patient eine Androgendeprivationstherapie erhalten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Clinical History & Procedure",
            "field_key": "androgen_deprivation"
        },
        "ARPI (i.e., abiraterone)": {
            "question": f"{general_prompt_en}, has the patient received ARPI (i.e., abiraterone)?",
            "question_de": f"{general_prompt_de}, hat der Patient ARPI (z.B. Abirateron) erhalten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Clinical History & Procedure",
            "field_key": "arpi"
        },
        "Chemotherapy": {
            "question": f"{general_prompt_en}, has the patient undergone chemotherapy?",
            "question_de": f"{general_prompt_de}, wurde bei dem Patienten eine Chemotherapie durchgeführt?",
            "allowed_answers": ["Yes", "No"],
            "section": "Clinical History & Procedure",
            "field_key": "chemotherapy"
        },
        "Other therapies": {
            "question": f"{general_prompt_en}, what other therapies has the patient received?",
            "question_de": f"{general_prompt_de}, welche anderen Therapien hat der Patient erhalten?",
            "section": "Clinical History & Procedure",
            "field_key": "other_therapies"
        },
        "Most recent PSA levels (ng/mL)": {
            "question": f"{general_prompt_en}, what is the most recent PSA level (ng/mL)?",
            "question_de": f"{general_prompt_de}, wie hoch ist der aktuellste PSA-Wert (ng/mL)?",
            "section": "Clinical History & Procedure",
            "field_key": "psa_level"
        },
        "Date of PSA measurement": {
            "question": f"{general_prompt_en}, what is the date of the most recent PSA measurement (dd/mm/yyyy)?",
            "question_de": f"{general_prompt_de}, wann wurde der aktuellste PSA-Wert gemessen (TT/MM/JJJJ)?",
            "section": "Clinical History & Procedure",
            "field_key": "psa_date"
        },
        # Comparison or Prior Imaging
        "Radiopharmaceutical used": {
            "question": f"{general_prompt_en}, what radiopharmaceutical was used for the PSMA PET/CT scan?",
            "question_de": f"{general_prompt_de}, welches Radiopharmazeutikum wurde für den PSMA-PET/CT-Scan verwendet?",
            "section": "Comparison or Prior Imaging",
            "field_key": "radiopharmaceutical"
        },
        "Dosage and Injection Time": {
            "question": f"{general_prompt_en}, what was the dosage and injection time for the PSMA PET/CT scan?",
            "question_de": f"{general_prompt_de}, welche Dosierung und Injektionszeit wurde für den PSMA-PET/CT-Scan verwendet?",
            "section": "Comparison or Prior Imaging",
            "field_key": "dosage_injection_time"
        },
        # Accompanying CT
        "Accompanying CT": {
            "question": f"{general_prompt_en}, what type of CT scan accompanied the PSMA PET scan?",
            "question_de": f"{general_prompt_de}, welche Art von CT-Scan begleitete den PSMA-PET-Scan?",
            "options": ["Attenuation Correction Only", "Diagnostic with contrast", "Diagnostic without contrast"],
            "section": "Accompanying CT",
            "field_key": "accompanying_ct"
        },
        # Background Reference Uptake
        "Liver SUV mean": {
            "question": f"{general_prompt_en}, what is the liver SUV mean?",
            "question_de": f"{general_prompt_de}, wie hoch ist der mittlere SUV-Wert der Leber?",
            "section": "Background Reference Uptake",
            "field_key": "liver_suv_mean"
        },
        "Liver lesion present": {
            "question": f"{general_prompt_en}, is there a liver lesion present?",
            "question_de": f"{general_prompt_de}, ist eine Leberläsion vorhanden?",
            "allowed_answers": ["Yes", "No"],
            "section": "Background Reference Uptake",
            "field_key": "liver_lesion"
        },
        "Blood pool SUV mean": {
            "question": f"{general_prompt_en}, what is the blood pool SUV mean?",
            "question_de": f"{general_prompt_de}, wie hoch ist der mittlere SUV-Wert des Blutpools?",
            "section": "Background Reference Uptake",
            "field_key": "blood_pool_suv_mean"
        },
        "Blood pool lesion present": {
            "question": f"{general_prompt_en}, is there a blood pool lesion present?",
            "question_de": f"{general_prompt_de}, ist eine Blutpool-Läsion vorhanden?",
            "allowed_answers": ["Yes", "No"],
            "section": "Background Reference Uptake",
            "field_key": "blood_pool_lesion"
        },
        "Other SUV mean": {
            "question": f"{general_prompt_en}, what is the other SUV mean (if available)?",
            "question_de": f"{general_prompt_de}, wie hoch ist der andere mittlere SUV-Wert (falls verfügbar)?",
            "section": "Background Reference Uptake",
            "field_key": "other_suv_mean"
        },
        "Other lesion present": {
            "question": f"{general_prompt_en}, are there any other lesions present?",
            "question_de": f"{general_prompt_de}, sind andere Läsionen vorhanden?",
            "allowed_answers": ["Yes", "No"],
            "section": "Background Reference Uptake",
            "field_key": "other_lesion"
        },
        # Prostate Gland
        "Prostate Gland lesions": {
            "question": f"{general_prompt_en}, are there lesions in the prostate gland?",
            "question_de": f"{general_prompt_de}, gibt es Läsionen in der Prostatadrüse?",
            "allowed_answers": ["Yes", "No"],
            "section": "Prostate Gland",
            "field_key": "prostate_lesions"
        },
        "Prostate Gland number of lesions": {
            "question": f"{general_prompt_en}, how many lesions are present in the prostate gland?",
            "question_de": f"{general_prompt_de}, wie viele Läsionen sind in der Prostatadrüse vorhanden?",
            "section": "Prostate Gland",
            "field_key": "prostate_lesion_count"
        },
        "Prostate Gland SUVmax": {
            "question": f"{general_prompt_en}, what is the SUVmax of the prostate gland lesion(s)?",
            "question_de": f"{general_prompt_de}, wie hoch ist der SUVmax-Wert der Läsion(en) in der Prostatadrüse?",
            "section": "Prostate Gland",
            "field_key": "prostate_suvmax"
        },
        "Prostate Gland localization": {
            "question": f"{general_prompt_en}, what is the localization of the prostate gland lesion(s)?",
            "question_de": f"{general_prompt_de}, wo sind die Läsion(en) in der Prostatadrüse lokalisiert?",
            "options": ["Left", "Right", "Base", "Mid", "Apical", "Anterior", "Posterior"],
            "section": "Prostate Gland",
            "field_key": "prostate_localization"
        },
        
        # Prostate Bed (Post-Prostatectomy)
        "Prostate Bed lesions": {
            "question": f"{general_prompt_en}, are there lesions in the prostate bed (post-prostatectomy)?",
            "question_de": f"{general_prompt_de}, gibt es Läsionen im Prostatabett (nach Prostatektomie)?",
            "allowed_answers": ["Yes", "No"],
            "section": "Prostate Bed (Post-Prostatectomy)",
            "field_key": "prostate_bed_lesions"
        },
        "Prostate Bed number of lesions": {
            "question": f"{general_prompt_en}, how many lesions are present in the prostate bed?",
            "question_de": f"{general_prompt_de}, wie viele Läsionen sind im Prostatabett vorhanden?",
            "section": "Prostate Bed (Post-Prostatectomy)",
            "field_key": "prostate_bed_lesion_count"
        },
        "Prostate Bed SUVmax": {
            "question": f"{general_prompt_en}, what is the SUVmax of the prostate bed lesion(s)?",
            "question_de": f"{general_prompt_de}, wie hoch ist der SUVmax-Wert der Läsion(en) im Prostatabett?",
            "section": "Prostate Bed (Post-Prostatectomy)",
            "field_key": "prostate_bed_suvmax"
        },
        "Prostate Bed localization": {
            "question": f"{general_prompt_en}, what is the localization of the prostate bed lesion(s)?",
            "question_de": f"{general_prompt_de}, wo sind die Läsion(en) im Prostatabett lokalisiert?",
            "options": ["Left", "Right", "Base", "Mid", "Apical", "Anterior", "Posterior"],
            "section": "Prostate Bed (Post-Prostatectomy)",
            "field_key": "prostate_bed_localization"
        },
        
        # Seminal Vesicles
        "Seminal Vesicles lesions": {
            "question": f"{general_prompt_en}, are there lesions in the seminal vesicles?",
            "question_de": f"{general_prompt_de}, gibt es Läsionen in den Samenblasen?",
            "allowed_answers": ["Yes", "No"],
            "section": "Seminal Vesicles",
            "field_key": "seminal_vesicles_lesions"
        },
        "Seminal Vesicles number of lesions": {
            "question": f"{general_prompt_en}, how many lesions are present in the seminal vesicles?",
            "question_de": f"{general_prompt_de}, wie viele Läsionen sind in den Samenblasen vorhanden?",
            "section": "Seminal Vesicles",
            "field_key": "seminal_vesicles_lesion_count"
        },
        "Seminal Vesicles SUVmax": {
            "question": f"{general_prompt_en}, what is the SUVmax of the seminal vesicles lesion(s)?",
            "question_de": f"{general_prompt_de}, wie hoch ist der SUVmax-Wert der Läsion(en) in den Samenblasen?",
            "section": "Seminal Vesicles",
            "field_key": "seminal_vesicles_suvmax"
        },
        "Seminal Vesicles localization": {
            "question": f"{general_prompt_en}, what is the localization of the seminal vesicles lesion(s)?",
            "question_de": f"{general_prompt_de}, wo sind die Läsion(en) in den Samenblasen lokalisiert?",
            "options": ["Left", "Right"],
            "section": "Seminal Vesicles",
            "field_key": "seminal_vesicles_localization"
        },
        
        # Pelvic LN(s)
        "Pelvic LN lesions": {
            "question": f"{general_prompt_en}, are there pelvic lymph node lesions?",
            "question_de": f"{general_prompt_de}, gibt es Läsionen in den Beckenlymphknoten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Pelvic LN(s)",
            "field_key": "pelvic_ln_lesions"
        },
        "External Iliac lesion": {
            "question": f"{general_prompt_en}, are there external iliac lesions?",
            "question_de": f"{general_prompt_de}, gibt es Läsionen in den externen Iliakal-Lymphknoten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Pelvic LN(s)",
            "field_key": "external_iliac_lesion"
        },
        "External Iliac size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the external iliac lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die externe(n) Iliakal-Läsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Pelvic LN(s)",
            "field_key": "external_iliac_size_suv"
        },
        "External Iliac notes": {
            "question": f"{general_prompt_en}, what are the notes for the external iliac lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den externen Iliakal-Läsion(en)?",
            "section": "Pelvic LN(s)",
            "field_key": "external_iliac_notes"
        },
        "Internal Iliac lesion": {
            "question": f"{general_prompt_en}, are there internal iliac lesions?",
            "question_de": f"{general_prompt_de}, gibt es Läsionen in den internen Iliakal-Lymphknoten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Pelvic LN(s)",
            "field_key": "internal_iliac_lesion"
        },
        "Internal Iliac size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the internal iliac lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die interne(n) Iliakal-Läsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Pelvic LN(s)",
            "field_key": "internal_iliac_size_suv"
        },
        "Internal Iliac notes": {
            "question": f"{general_prompt_en}, what are the notes for the internal iliac lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den internen Iliakal-Läsion(en)?",
            "section": "Pelvic LN(s)",
            "field_key": "internal_iliac_notes"
        },
        "Obturator lesion": {
            "question": f"{general_prompt_en}, are there obturator lesions?",
            "question_de": f"{general_prompt_de}, gibt es Läsionen in den Obturator-Lymphknoten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Pelvic LN(s)",
            "field_key": "obturator_lesion"
        },
        "Obturator size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the obturator lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die Obturator-Läsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Pelvic LN(s)",
            "field_key": "obturator_size_suv"
        },
        "Obturator notes": {
            "question": f"{general_prompt_en}, what are the notes for the obturator lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den Obturator-Läsion(en)?",
            "section": "Pelvic LN(s)",
            "field_key": "obturator_notes"
        },
        "Common iliac lesion": {
            "question": f"{general_prompt_en}, are there common iliac lesions?",
            "question_de": f"{general_prompt_de}, gibt es Läsionen in den gemeinsamen Iliakal-Lymphknoten?",
            "allowed_answers": ["Yes", "No"],
            "section": "Pelvic LN(s)",
            "field_key": "common_iliac_lesion"
        },
        "Common iliac size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the common iliac lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die gemeinsame(n) Iliakal-Läsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Pelvic LN(s)",
            "field_key": "common_iliac_size_suv"
        },
        "Common iliac notes": {
            "question": f"{general_prompt_en}, what are the notes for the common iliac lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den gemeinsamen Iliakal-Läsion(en)?",
            "section": "Pelvic LN(s)",
            "field_key": "common_iliac_notes"
        },
        "Perirectal lesion": {
            "question": f"{general_prompt_en}, are there perirectal lesions?",
            "question_de": f"{general_prompt_de}, gibt es perirektale Läsionen?",
            "allowed_answers": ["Yes", "No"],
            "section": "Pelvic LN(s)",
            "field_key": "perirectal_lesion"
        },
        "Perirectal size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the perirectal lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die perirektale(n) Läsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Pelvic LN(s)",
            "field_key": "perirectal_size_suv"
        },
        "Perirectal notes": {
            "question": f"{general_prompt_en}, what are the notes for the perirectal lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den perirektalen Läsion(en)?",
            "section": "Pelvic LN(s)",
            "field_key": "perirectal_notes"
        },
        "Presacral lesion": {
            "question": f"{general_prompt_en}, are there presacral lesions?",
            "question_de": f"{general_prompt_de}, gibt es präsakrale Läsionen?",
            "allowed_answers": ["Yes", "No"],
            "section": "Pelvic LN(s)",
            "field_key": "presacral_lesion"
        },
        "Presacral size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the presacral lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die präsakrale(n) Läsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Pelvic LN(s)",
            "field_key": "presacral_size_suv"
        },
        "Presacral notes": {
            "question": f"{general_prompt_en}, what are the notes for the presacral lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den präsakralen Läsion(en)?",
            "section": "Pelvic LN(s)",
            "field_key": "presacral_notes"
        },
        "Other Pelvic LN lesion": {
            "question": f"{general_prompt_en}, are there other pelvic lymph node lesions?",
            "question_de": f"{general_prompt_de}, gibt es andere Lymphknotenläsionen im Beckenbereich?",
            "allowed_answers": ["Yes", "No"],
            "section": "Pelvic LN(s)",
            "field_key": "other_pelvic_ln_lesion"
        },
        "Other Pelvic LN size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the other pelvic lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die andere(n) Lymphknotenläsion(en) im Beckenbereich und wie hoch ist der SUVmax-Wert?",
            "section": "Pelvic LN(s)",
            "field_key": "other_pelvic_ln_size_suv"
        },
        "Other Pelvic LN notes": {
            "question": f"{general_prompt_en}, what are the notes for the other pelvic lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den anderen Lymphknotenläsionen im Beckenbereich?",
            "section": "Pelvic LN(s)",
            "field_key": "other_pelvic_ln_notes"
        },
        
        # Extra-pelvic LN(s)
        "Extra-pelvic LN lesions": {
            "question": f"{general_prompt_en}, are there extra-pelvic lymph node lesions?",
            "question_de": f"{general_prompt_de}, gibt es Lymphknotenläsionen außerhalb des Beckenbereichs?",
            "allowed_answers": ["Yes", "No"],
            "section": "Extra-pelvic LN(s)",
            "field_key": "extrapelvic_ln_lesions"
        },
        "Abdominal lesion": {
            "question": f"{general_prompt_en}, are there abdominal lymph node lesions?",
            "question_de": f"{general_prompt_de}, gibt es abdominale Lymphknotenläsionen?",
            "allowed_answers": ["Yes", "No"],
            "section": "Extra-pelvic LN(s)",
            "field_key": "abdominal_lesion"
        },
        "Abdominal size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the abdominal lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die abdominale(n) Lymphknotenläsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Extra-pelvic LN(s)",
            "field_key": "abdominal_size_suv"
        },
        "Abdominal notes": {
            "question": f"{general_prompt_en}, what are the notes for the abdominal lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den abdominalen Lymphknotenläsionen?",
            "section": "Extra-pelvic LN(s)",
            "field_key": "abdominal_notes"
        },
        "Thoracic lesion": {
            "question": f"{general_prompt_en}, are there thoracic lymph node lesions?",
            "question_de": f"{general_prompt_de}, gibt es thorakale Lymphknotenläsionen?",
            "allowed_answers": ["Yes", "No"],
            "section": "Extra-pelvic LN(s)",
            "field_key": "thoracic_lesion"
        },
        "Thoracic size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the thoracic lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die thorakale(n) Lymphknotenläsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Extra-pelvic LN(s)",
            "field_key": "thoracic_size_suv"
        },
        "Thoracic notes": {
            "question": f"{general_prompt_en}, what are the notes for the thoracic lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den thorakalen Lymphknotenläsionen?",
            "section": "Extra-pelvic LN(s)",
            "field_key": "thoracic_notes"
        },
        "Supraclavicular lesion": {
            "question": f"{general_prompt_en}, are there supraclavicular lymph node lesions?",
            "question_de": f"{general_prompt_de}, gibt es supraklavikuläre Lymphknotenläsionen?",
            "allowed_answers": ["Yes", "No"],
            "section": "Extra-pelvic LN(s)",
            "field_key": "supraclavicular_lesion"
        },
        "Supraclavicular size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the supraclavicular lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die supraklavikuläre(n) Lymphknotenläsion(en) und wie hoch ist der SUVmax-Wert?",
            "section": "Extra-pelvic LN(s)",
            "field_key": "supraclavicular_size_suv"
        },
        "Supraclavicular notes": {
            "question": f"{general_prompt_en}, what are the notes for the supraclavicular lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den supraklavikulären Lymphknotenläsionen?",
            "section": "Extra-pelvic LN(s)",
            "field_key": "supraclavicular_notes"
        },
        "Other Extra-pelvic LN lesion": {
            "question": f"{general_prompt_en}, are there other extra-pelvic lymph node lesions?",
            "question_de": f"{general_prompt_de}, gibt es andere Lymphknotenläsionen außerhalb des Beckenbereichs?",
            "allowed_answers": ["Yes", "No"],
            "section": "Extra-pelvic LN(s)",
            "field_key": "other_extrapelvic_ln_lesion"
        },
        "Other Extra-pelvic LN size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the other extra-pelvic lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, wie groß ist/sind die andere(n) Lymphknotenläsion(en) außerhalb des Beckenbereichs und wie hoch ist der SUVmax-Wert?",
            "section": "Extra-pelvic LN(s)",
            "field_key": "other_extrapelvic_ln_size_suv"
        },
        "Other Extra-pelvic LN notes": {
            "question": f"{general_prompt_en}, what are the notes for the other extra-pelvic lymph node lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den anderen Lymphknotenläsionen außerhalb des Beckenbereichs?",
            "section": "Extra-pelvic LN(s)",
            "field_key": "other_extrapelvic_ln_notes"
        },
        
        # Skeletal/Bone Metastases
        "Skeletal lesions": {
            "question": f"{general_prompt_en}, are there skeletal lesions?",
            "question_de": f"{general_prompt_de}, gibt es Skelettläsionen?",
            "allowed_answers": ["Yes", "No"],
            "section": "Skeletal/Bone Metastases",
            "field_key": "skeletal_lesions"
        },
        "Skeletal number of lesions": {
            "question": f"{general_prompt_en}, how many skeletal lesions are present?",
            "question_de": f"{general_prompt_de}, wie viele Skelettläsionen sind vorhanden?",
            "allowed_answers": ["0", "1", "2-4", "5+"],
            "section": "Skeletal/Bone Metastases",
            "field_key": "skeletal_lesion_count"
        },
        "Bone marrow involvement": {
            "question": f"{general_prompt_en}, is there bone marrow involvement?",
            "question_de": f"{general_prompt_de}, ist das Knochenmark beteiligt?",
            "allowed_answers": ["Yes", "No"],
            "section": "Skeletal/Bone Metastases",
            "field_key": "bone_marrow_involvement"
        },
        "Skeletal localization notes": {
            "question": f"{general_prompt_en}, what are the localization notes for the skeletal lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Lokalisierungshinweise gibt es für die Skelettläsion(en)?",
            "section": "Skeletal/Bone Metastases",
            "field_key": "skeletal_localization_notes"
        },
        
        # Visceral Metastases
        "Visceral lesions": {
            "question": f"{general_prompt_en}, are there visceral metastases?",
            "question_de": f"{general_prompt_de}, gibt es viszerale Metastasen?",
            "allowed_answers": ["Yes", "No"],
            "section": "Visceral Metastases",
            "field_key": "visceral_lesions"
        },
        "Visceral localization": {
            "question": f"{general_prompt_en}, what is the localization of the visceral metastases?",
            "question_de": f"{general_prompt_de}, wo sind die viszeralen Metastasen lokalisiert?",
            "options": ["Lung", "Liver", "Brain", "Other"],
            "section": "Visceral Metastases",
            "field_key": "visceral_localization"
        },
        "Visceral size and SUVmax": {
            "question": f"{general_prompt_en}, what is the size and SUVmax of the visceral metastases?",
            "question_de": f"{general_prompt_de}, wie groß sind die viszeralen Metastasen und wie hoch ist der SUVmax-Wert?",
            "section": "Visceral Metastases",
            "field_key": "visceral_size_suv"
        },
        "Visceral notes": {
            "question": f"{general_prompt_en}, what are the notes for the visceral metastases?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu den viszeralen Metastasen?",
            "section": "Visceral Metastases",
            "field_key": "visceral_notes"
        },
        
        # PSMA-negative lesions
        "PSMA-negative lesions": {
            "question": f"{general_prompt_en}, are there PSMA-negative lesions noted on CT?",
            "question_de": f"{general_prompt_de}, gibt es PSMA-negative Läsionen, die im CT festgestellt wurden?",
            "allowed_answers": ["Yes", "No"],
            "section": "PSMA-negative lesions",
            "field_key": "psma_negative_lesions"
        },
        "PSMA-negative number of lesions": {
            "question": f"{general_prompt_en}, how many PSMA-negative lesions are present?",
            "question_de": f"{general_prompt_de}, wie viele PSMA-negative Läsionen sind vorhanden?",
            "section": "PSMA-negative lesions",
            "field_key": "psma_negative_lesion_count"
        },
        "PSMA-negative localization notes": {
            "question": f"{general_prompt_en}, what are the localization notes for the PSMA-negative lesion(s)?",
            "question_de": f"{general_prompt_de}, welche Lokalisierungshinweise gibt es für die PSMA-negativen Läsion(en)?",
            "section": "PSMA-negative lesions",
            "field_key": "psma_negative_localization_notes"
        },
        
        # Indeterminate findings
        "Indeterminate findings": {
            "question": f"{general_prompt_en}, what are the indeterminate findings or additional notes?",
            "question_de": f"{general_prompt_de}, welche unbestimmten Befunde oder zusätzlichen Anmerkungen gibt es?",
            "section": "Indeterminate findings",
            "field_key": "indeterminate_findings"
        },
        
        # Impression section
        "miTNM classification": {
            "question": f"{general_prompt_en}, what is the miTNM classification?",
            "question_de": f"{general_prompt_de}, wie lautet die miTNM-Klassifikation?",
            "section": "Impression",
            "field_key": "mitnm_classification"
        },
        "PROMISE score": {
            "question": f"{general_prompt_en}, what is the PROMISE score?",
            "question_de": f"{general_prompt_de}, wie hoch ist der PROMISE-Score?",
            "section": "Impression",
            "field_key": "promise_score"
        },
        "PRIMARY score": {
            "question": f"{general_prompt_en}, what is the PRIMARY score?",
            "question_de": f"{general_prompt_de}, wie hoch ist der PRIMARY-Score?",
            "section": "Impression",
            "field_key": "primary_score"
        },
        "RECIP score": {
            "question": f"{general_prompt_en}, what is the RECIP score?",
            "question_de": f"{general_prompt_de}, wie hoch ist der RECIP-Score?",
            "section": "Impression",
            "field_key": "recip_score"
        },
        
        # Other scoring systems
        "Other scoring systems notes": {
            "question": f"{general_prompt_en}, what are the notes for other scoring systems?",
            "question_de": f"{general_prompt_de}, welche Anmerkungen gibt es zu anderen Scoring-Systemen?",
            "section": "Impression",
            "field_key": "other_scoring_notes"
        },
        
        # Summary 
        "Summary": {
            "question": f"{general_prompt_en}. Based on the provided clinical information and all previous findings, provide a comprehensive summary of the PSMA PET/CT scan findings, including key observations, significant lesions, and overall impression.",
            "question_de": f"{general_prompt_de}. Basierend auf den bereitgestellten klinischen Informationen und allen vorherigen Befunden, geben Sie eine umfassende Zusammenfassung der PSMA-PET/CT-Scan-Befunde, einschließlich der wichtigsten Beobachtungen, signifikanten Läsionen und des Gesamteindrucks.",
            "section": "Summary",
            "field_key": "summary"
        }
    }

    processed_dict = {}
    for key, value in survey_dict.items():
        question_info = {}
        
        # Select the appropriate question based on language
        if language == "de" and "question_de" in value:
            question_info['question'] = value['question_de']
        else:
            question_info['question'] = value['question']
        
        # For closed questions, add the allowed answers
        if 'allowed_answers' in value:
            question_info['allowed_answers'] = value['allowed_answers']
        
        # For checkbox questions, add the options
        if 'options' in value:
            question_info['options'] = value['options']
        
        # Add section information
        question_info['section'] = value['section']
        question_info['field_key'] = value['field_key']
        
        # Determine field type
        question_info['type'] = determine_field_type(value, key)
        
        # Add dependencies if they exist
        if 'dependency' in value:
            question_info['dependency'] = value['dependency']
        
        # Store the processed question
        processed_dict[key] = question_info
        
    return processed_dict


if __name__ == "__main__":
    prompts = build_prompts()
    for question_key, prompt_data in prompts.items():
        print(f"{question_key} => {prompt_data}")
# You can place this script in a file, for example: survey_prompts.py
# The script generates a dictionary of prompts for each question,
# starting with the system prompt "You are nuclear medicine expert".
# It uses Pydantic to ensure basic structure validity.
from pydantic import BaseModel, Field, conlist, ValidationError
from typing import List, Optional, Dict, Union

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

def build_prompts() -> Dict[str, Union[Dict, str]]:
    """
    Returns a dictionary of prompts for each question, prefixed by the system prompt.
    In case of checkbox or closed questions, only the given set of answers are allowed.
    """
    survey_dict = {
        # Clinical History & Procedure
        "Indication for the scan": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the indication for the PSMA PET/CT scan?",
            "options": [
                "Primary staging",
                "CRPC/Recurrent restaging",
                "PSMA expression assessment for PSMA targeted therapy"
            ]
        },
        "Date of initiation of last/recurrent therapy": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the date of initiation of last/recurrent therapy (dd/mm/yyyy)?"
        },
        "Radical prostatectomy": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, has the patient undergone radical prostatectomy?",
            "allowed_answers": ["Yes", "No"]
        },
        "External beam radiation to prostate": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, has the patient received external beam radiation to prostate?",
            "allowed_answers": ["Yes", "No"]
        },
        "Post-prostatectomy external beam radiation": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, has the patient received post-prostatectomy external beam radiation?",
            "allowed_answers": ["Yes", "No"]
        },
        "Brachytherapy to prostate": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, has the patient undergone brachytherapy to prostate?",
            "allowed_answers": ["Yes", "No"]
        },
        "Androgen deprivation therapy": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, has the patient received androgen deprivation therapy?",
            "allowed_answers": ["Yes", "No"]
        },
        "ARPI (i.e., abiraterone)": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, has the patient received ARPI (i.e., abiraterone)?",
            "allowed_answers": ["Yes", "No"]
        },
        "Chemotherapy": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, has the patient undergone chemotherapy?",
            "allowed_answers": ["Yes", "No"]
        },
        "Other therapies": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what other therapies has the patient received?"
        },
        "Most recent PSA levels (ng/mL)": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the most recent PSA level (ng/mL)?"
        },
        "Date of PSA measurement": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the date of the most recent PSA measurement (dd/mm/yyyy)?"
        },
        # Comparison or Prior Imaging
        "Radiopharmaceutical used": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what radiopharmaceutical was used for the PSMA PET/CT scan?"
        },
        "Dosage and Injection Time": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what was the dosage and injection time for the PSMA PET/CT scan?"
        },
        # Accompanying CT
        "Accompanying CT": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what type of CT scan accompanied the PSMA PET scan?",
            "options": ["Attenuation Correction Only", "Diagnostic with contrast", "Diagnostic without contrast"]
        },
        # Background Reference Uptake
        "Liver SUV mean": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the liver SUV mean?"
        },
        "Liver lesion present": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, is there a liver lesion present?",
            "allowed_answers": ["Yes", "No"]
        },
        "Blood pool SUV mean": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the blood pool SUV mean?"
        },
        "Blood pool lesion present": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, is there a blood pool lesion present?",
            "allowed_answers": ["Yes", "No"]
        },
        "Other SUV mean": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the other SUV mean (if available)?"
        },
        "Other lesion present": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there any other lesions present?",
            "allowed_answers": ["Yes", "No"]
        },
        # Prostate Gland
        "Prostate Gland lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there lesions in the prostate gland?",
            "allowed_answers": ["Yes", "No"]
        },
        "Prostate Gland number of lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, how many lesions are present in the prostate gland?"
        },
        "Prostate Gland SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the SUVmax of the prostate gland lesion(s)?"
        },
        "Prostate Gland localization": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the localization of the prostate gland lesion(s)?",
            "options": ["Left", "Right", "Base", "Mid", "Apical", "Anterior", "Posterior"]
        },
        
        # Prostate Bed (Post-Prostatectomy)
        "Prostate Bed lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there lesions in the prostate bed (post-prostatectomy)?",
            "allowed_answers": ["Yes", "No"]
        },
        "Prostate Bed number of lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, how many lesions are present in the prostate bed?"
        },
        "Prostate Bed SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the SUVmax of the prostate bed lesion(s)?"
        },
        "Prostate Bed localization": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the localization of the prostate bed lesion(s)?",
            "options": ["Left", "Right", "Base", "Mid", "Apical", "Anterior", "Posterior"]
        },
        
        # Seminal Vesicles
        "Seminal Vesicles lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there lesions in the seminal vesicles?",
            "allowed_answers": ["Yes", "No"]
        },
        "Seminal Vesicles number of lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, how many lesions are present in the seminal vesicles?"
        },
        "Seminal Vesicles SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the SUVmax of the seminal vesicles lesion(s)?"
        },
        "Seminal Vesicles localization": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the localization of the seminal vesicles lesion(s)?",
            "options": ["Left", "Right"]
        },
        
        # Pelvic LN(s)
        "Pelvic LN lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there pelvic lymph node lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "External Iliac lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there external iliac lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "External Iliac size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the external iliac lesion(s)?"
        },
        "External Iliac notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the external iliac lesion(s)?"
        },
        "Internal Iliac lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there internal iliac lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Internal Iliac size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the internal iliac lesion(s)?"
        },
        "Internal Iliac notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the internal iliac lesion(s)?"
        },
        "Obturator lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there obturator lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Obturator size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the obturator lesion(s)?"
        },
        "Obturator notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the obturator lesion(s)?"
        },
        "Common iliac lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there common iliac lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Common iliac size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the common iliac lesion(s)?"
        },
        "Common iliac notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the common iliac lesion(s)?"
        },
        "Perirectal lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there perirectal lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Perirectal size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the perirectal lesion(s)?"
        },
        "Perirectal notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the perirectal lesion(s)?"
        },
        "Presacral lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there presacral lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Presacral size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the presacral lesion(s)?"
        },
        "Presacral notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the presacral lesion(s)?"
        },
        "Other Pelvic LN lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there other pelvic lymph node lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Other Pelvic LN size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the other pelvic lymph node lesion(s)?"
        },
        "Other Pelvic LN notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the other pelvic lymph node lesion(s)?"
        },
        
        # Extra-pelvic LN(s)
        "Extra-pelvic LN lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there extra-pelvic lymph node lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Abdominal lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there abdominal lymph node lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Abdominal size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the abdominal lymph node lesion(s)?"
        },
        "Abdominal notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the abdominal lymph node lesion(s)?"
        },
        "Thoracic lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there thoracic lymph node lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Thoracic size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the thoracic lymph node lesion(s)?"
        },
        "Thoracic notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the thoracic lymph node lesion(s)?"
        },
        "Supraclavicular lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there supraclavicular lymph node lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Supraclavicular size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the supraclavicular lymph node lesion(s)?"
        },
        "Supraclavicular notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the supraclavicular lymph node lesion(s)?"
        },
        "Other Extra-pelvic LN lesion": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there other extra-pelvic lymph node lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Other Extra-pelvic LN size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the other extra-pelvic lymph node lesion(s)?"
        },
        "Other Extra-pelvic LN notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the other extra-pelvic lymph node lesion(s)?"
        },
        
        # Skeletal/Bone Metastases
        "Skeletal lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there skeletal lesions?",
            "allowed_answers": ["Yes", "No"]
        },
        "Skeletal number of lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, how many skeletal lesions are present?",
            "allowed_answers": ["0", "1", "2-4", "5+"]
        },
        "Bone marrow involvement": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, is there bone marrow involvement?",
            "allowed_answers": ["Yes", "No"]
        },
        "Skeletal localization notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the localization notes for the skeletal lesion(s)?"
        },
        
        # Visceral Metastases
        "Visceral lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there visceral metastases?",
            "allowed_answers": ["Yes", "No"]
        },
        "Visceral localization": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the localization of the visceral metastases?",
            "options": ["Lung", "Liver", "Brain", "Other"]
        },
        "Visceral size and SUVmax": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the size and SUVmax of the visceral metastases?"
        },
        "Visceral notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for the visceral metastases?"
        },
        
        # PSMA-negative lesions
        "PSMA-negative lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, are there PSMA-negative lesions noted on CT?",
            "allowed_answers": ["Yes", "No"]
        },
        "PSMA-negative number of lesions": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, how many PSMA-negative lesions are present?"
        },
        "PSMA-negative localization notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the localization notes for the PSMA-negative lesion(s)?"
        },
        
        # Indeterminate findings
        "Indeterminate findings": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the indeterminate findings or additional notes?"
        },
        
        # Impression section
        "miTNM classification": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the miTNM classification?"
        },
        "PROMISE score": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the PROMISE score?"
        },
        "PRIMARY score": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the PRIMARY score?"
        },
        "RECIP score": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what is the RECIP score?"
        },
        
        # Other scoring systems
        "Other scoring systems notes": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information, what are the notes for other scoring systems?"
        },
        
        # Summary 
        "Summary": {
            "question": "You are nuclear medicine expert. Based on the provided clinical information and all previous findings, provide a comprehensive summary of the PSMA PET/CT scan findings, including key observations, significant lesions, and overall impression."
        }
    }

    processed_dict = {}
    for key, value in survey_dict.items():
        question_info = {}
        
        # Each question becomes a dictionary with at least the 'question' key
        question_info['question'] = value['question']
        
        # For closed questions, add the allowed answers
        if 'allowed_answers' in value:
            question_info['allowed_answers'] = value['allowed_answers']
        
        # For checkbox questions, add the options
        if 'options' in value:
            question_info['options'] = value['options']
        
        # Store the processed question
        processed_dict[key] = question_info
        
    return processed_dict


if __name__ == "__main__":
    prompts = build_prompts()
    for question_key, prompt_data in prompts.items():
        print(f"{question_key} => {prompt_data}")
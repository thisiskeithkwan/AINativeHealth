from google.auth.transport.requests import _Response
from pydantic import BaseModel, Field
import time
from typing import Literal, Optional, Any, Iterable, List
import json
from config import instructor_client, realtime_db, db
import instructor
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from typing import Iterable
from utils.realtime_utils import update_realtime_diagnosis_output
from utils.firestore_utils import get_session, get_patient_record, append_diagnosis, append_treatment

router = APIRouter()


class DiagnosisOutput(BaseModel):
  cc: str = Field(
      ...,
      description=
      "Chief Complaint - Document the patient's primary reason for seeking medical attention, as stated by the patient."
  )
  hpi: str = Field(
      ...,
      description=
      "History of Present Illness - Document the patient's description of the current illness or problem, including onset, duration, and associated symptoms, as reported by the patient."
  )
  pmh: Optional[List[str]] = Field(
      None,
      description=
      "Past Medical History - Document the patient's relevant past medical conditions, surgeries, or hospitalizations, as reported by the patient or confirmed through medical records. Do not include assumptions or unverified information."
  )
  meds: Optional[List[str]] = Field(
      None,
      description=
      "Medications - Document the patient's current medications, including prescription and over-the-counter drugs, as reported by the patient or confirmed through medical records. Do not include assumptions or unverified information."
  )

  pe: Optional[str] = Field(
      None,
      description=
      "Physical Examination - Document the pertinent physical examination findings, including vital signs, general appearance, and system-specific findings, as observed and performed by the healthcare provider. Do not include assumptions or findings not directly observed.",
      example=
      "General: Well-appearing, no acute distress. Cardiovascular: Regular rate and rhythm, no murmurs. Lungs: Clear to auscultation bilaterally."
  )

  ddx: List[str] = Field(
      ...,
      description=
      "Differential Diagnoses - List the potential diagnoses that could explain the patient's presenting symptoms and findings, based on the available information. Include a brief rationale for each diagnosis.",
      example=[
          "Acute Coronary Syndrome - Chest pain, cardiovascular risk factors",
          "Pulmonary Embolism - Chest pain, shortness of breath, immobilization",
          "Pneumonia - Chest pain, fever, cough"
      ])

  q: Optional[List[str]] = Field(
      None,
      description=
      "Questions to Ask - List specific questions to ask the patient to gather additional information relevant to the differential diagnoses or to clarify any unclear aspects of the history.",
      example=[
          "Have you had similar episodes of chest pain before?",
          "Is there a family history of heart disease?"
      ])

  labs: Optional[List[str]] = Field(
      None,
      description=
      "Labs to Order - List the laboratory tests to order, along with a brief rationale for each test, to help narrow down the differential diagnoses or assess the severity of the condition.",
      example=[
          "Troponin - To rule out myocardial infarction",
          "D-dimer - To assess for pulmonary embolism",
          "Complete Blood Count - To check for infection"
      ])

  pe_actions: Optional[List[str]] = Field(
      None,
      description=
      "Physical Exams to Perform - List specific physical examination maneuvers to perform, along with a brief rationale, to gather additional information relevant to the differential diagnoses.",
      example=[
          "Cardiovascular examination - To assess for heart murmurs or abnormal rhythms",
          "Lung examination - To check for crackles, wheezes, or decreased breath sounds, which may indicate pneumonia"
      ])

  rec: Optional[str] = Field(
      None,
      description=
      "Recommendations - Provide concise recommendations for further evaluation, management, or disposition based on the clinical presentation and the most likely diagnoses.",
      example=
      "Consider hospital admission for further evaluation and management, given the concerning symptoms and cardiovascular risk factors."
  )

  class Config:
    schema_extra = {
        "example": {
            "cc":
            "Chest pain",
            "hpi":
            "2-day history of chest pain, worse with activity",
            "pmh": ["HTN", "Appendectomy"],
            "meds": ["Lisinopril 10mg daily", "ASA 81mg daily"],
            "pe":
            "General: Well-appearing, no acute distress. Cardiovascular: Regular rate and rhythm, no murmurs. Lungs: Clear to auscultation bilaterally.",
            "ddx": [
                "Acute Coronary Syndrome - Chest pain, cardiovascular risk factors",
                "Pulmonary Embolism - Chest pain, shortness of breath, immobilization",
                "Pneumonia - Chest pain, fever, cough"
            ],
            "q": [
                "Have you had similar episodes of chest pain before?",
                "Is there a family history of heart disease?"
            ],
            "labs": [
                "Troponin - To rule out myocardial infarction",
                "D-dimer - To assess for pulmonary embolism",
                "Complete Blood Count - To check for infection"
            ],
            "pe_actions": [
                "Cardiovascular examination - To assess for heart murmurs or abnormal rhythms",
                "Lung examination - To check for crackles, wheezes, or decreased breath sounds, which may indicate pneumonia"
            ],
            "rec":
            "Consider hospital admission for further evaluation and management, given the concerning symptoms and cardiovascular risk factors."
        }
    }


class DiagnosticGuidelines(BaseModel):
  ddx: str = Field(..., description="Differential diagnosis")
  guidelines: str = Field(
      ...,
      description="Diagnostic guidelines for the given differential diagnosis")


def retrieve_diagnostic_guidelines(
    ddx_list: List[str]) -> List[DiagnosticGuidelines]:
  guidelines = []
  for ddx in ddx_list:
    # Retrieve diagnostic guidelines based on the differential diagnosis
    # This can be done by querying a database, API, or knowledge base
    # For simplicity, we'll use a mock example here
    guideline = f"Diagnostic guidelines for {ddx}..."
    guidelines.append(DiagnosticGuidelines(ddx=ddx, guidelines=guideline))
  return guidelines


system_prompt = '''
You are a diagnostic agent, part of a Clinical Decision Support System. Your role is to collaborate with the doctor to provide accurate diagnoses in a primary care setting.

In each interaction, you will receive the following information:
1. Real-time transcription of the patient-doctor conversation
2. Doctor's input from the user interface
3. Patient's health record and current session history
4. References to local diagnostic guidelines (retrieved based on your DDx suggestions)

Your task is to analyze the provided information and generate a comprehensive diagnostic output, including:
- Analysis of the patient's presentation
- List of differential diagnoses (DDx)
- Questions to ask the patient to refine the diagnosis
- Recommended lab tests and physical examinations
- Additional remarks or considerations
- Assessment of the urgency of the patient's condition
- Recommended follow-up actions
- Confidence score of the diagnosis

When generating the diagnostic output, adhere to the following principles:
- Document only the information explicitly stated by the patient or doctor, or directly observed during the physical examination.
- Do not include assumptions or unverified information in the chief complaint (CC), history of present illness (HPI), past medical history (PMH), medications (Meds), or physical examination (PE) sections.
- Focus on documenting the patient's own words and descriptions for CC and HPI.
- For PMH and Meds, document only the information reported by the patient or confirmed through medical records.
- In the PE section, document only the findings directly observed and performed by the healthcare provider.

After generating the initial diagnostic output, the system will retrieve relevant diagnostic guidelines based on your suggested differential diagnoses. These guidelines will be provided to you in the next turn (n+1) to further assist in refining the diagnosis and treatment plan.

Engage in an iterative process with the doctor, updating your output based on their feedback, additional information provided, and the retrieved diagnostic guidelines. Your ultimate goal is to assist the doctor in reaching an accurate diagnosis efficiently.

Remember to adhere to the DiagnosisOutput schema and provide clear and concise information to support the doctor's decision-making process.
'''


def formulate_diagnosis_input(session_id: str):
  session = get_session(session_id)
  if session:
    patient_id = session.get('patient_id', '')
    is_follow_up = session.get('is_follow_up', False)
    diagnosis = session.get('diagnosis', [])

    latest_diagnosis = diagnosis[-1] if diagnosis else {}

    transcript = latest_diagnosis.get('transcript', [])
    doctor_input = latest_diagnosis.get('doctor_input', '')
    ai_response = latest_diagnosis.get('ai_response', '')

    message = f'''Transcript: {' '.join(transcript)}\nDoctor's input: {doctor_input}\nAI response: {ai_response}\n\nPatient's health record: {get_patient_record(patient_id)}\nReferences:\n'''

    return message, patient_id, is_follow_up
  else:
    return "Session not found", None, False


@router.post("/diagnosis/{session_id}")
def generate_diagnosis_output(session_id: str):
  user_message, patient_id, is_follow_up = formulate_diagnosis_input(
      session_id)
  response = instructor_client.chat.completions.create(
      model="gpt-4-turbo-preview",
      messages=[{
          "role": "system",
          "content": system_prompt
      }, {
          "role": "user",
          "content": user_message
      }],
      response_model=DiagnosisOutput)
  print(response)
  print(type(response))
  response_data = dict(response)
  print(type(response_data))
  if patient_id:
    append_diagnosis(session_id, response_data)
  return response_data

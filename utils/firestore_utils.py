from google.cloud import firestore
from datetime import datetime
from config import db


def get_session(session_id: str):
  session_ref = db.collection('sessions').document(session_id)
  session_doc = session_ref.get()
  if session_doc.exists:
    return session_doc.to_dict()
  else:
    return None


def get_patient_record(patient_id: str):
  patient_ref = db.collection('patients').document(patient_id)
  patient_doc = patient_ref.get()
  if patient_doc.exists:
    return patient_doc.to_dict()
  else:
    return None


def append_diagnosis(session_id: str, diagnosis_data: dict):
  session_ref = db.collection('sessions').document(session_id)
  session_ref.update({
      'diagnosis':
      firestore.ArrayUnion([{
          'ai_response': diagnosis_data,
      }]),
      'updated_at':
      firestore.SERVER_TIMESTAMP,
  })


def append_treatment(session_id: str, ai_response: str):
  session_ref = db.collection('sessions').document(session_id)
  session_doc = session_ref.get()
  if session_doc.exists:
    treatment = session_doc.get('treatment', [])
    treatment.append({
        'timestamp': datetime.now().isoformat(),
        'ai_response': ai_response
    })
    session_ref.update({'treatment': treatment})
  else:
    print(f"Session {session_id} not found.")

from config import realtime_db


def update_realtime_diagnosis_output(session_id: str, diagnosis_output: str):
  session_ref = realtime_db.reference(f'sessions/{session_id}')
  session_ref.update({'latest_diagnosis_output': diagnosis_output})


def get_realtime_diagnosis_output(session_id: str):
  session_ref = realtime_db.reference(f'sessions/{session_id}')
  session_data = session_ref.get()
  if session_data:
    return session_data.get('latest_diagnosis_output')
  else:
    return None


def delete_realtime_session(session_id: str):
  session_ref = realtime_db.reference(f'sessions/{session_id}')
  session_ref.delete()

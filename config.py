from instructor import function_calls
import instructor
from instructor.patch import retry_sync
from openai import OpenAI, AsyncOpenAI
import os
import json
import firebase_admin
from firebase_admin import credentials, db, firestore

cred = credentials.Certificate(
    'ainativehealth-firebase-adminsdk-9m59t-baf8f8e63a.json')
firebase_admin.initialize_app(
    cred, {
        'databaseURL':
        'https://ainativehealth-default-rtdb.asia-southeast1.firebasedatabase.app/',
        'projectId': 'ainativehealth'
    })

realtime_db = db.reference()
db = firestore.client()

instructor_client = instructor.patch(
    OpenAI(api_key=os.environ["OPENAI_API_KEY"]))

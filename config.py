from instructor import function_calls
import instructor
from instructor.patch import retry_sync
from openai import OpenAI, AsyncOpenAI
import os
import json
import firebase_admin
from firebase_admin import credentials, db, firestore
from ragatouille import RAGPretrainedModel
from dotenv import load_dotenv

RAG = RAGPretrainedModel.from_pretrained("colbert-ir/colbertv2.0")

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

load_dotenv()

instructor_client = instructor.patch(
    OpenAI(api_key=os.getenv("OPENAI_API_KEY")))


path_to_index = ".ragatouille/colbert/indexes/KenyaIndex"
RAG = RAGPretrainedModel.from_index(path_to_index)
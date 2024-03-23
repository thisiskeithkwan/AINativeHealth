from fastapi import FastAPI
from routers.diagnosis import router as diagnosis_router
#cors
from fastapi.middleware.cors import CORSMiddleware
from config import instructor_client
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Iterator, Iterable
import instructor

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diagnosis_router, prefix="/diagnosis", tags=["Diagnosis"])


@app.get("/")
async def root():
  return {"message": "Welcome to the Clinical Decision Support System"}

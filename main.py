import asyncio
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import FastAPI, Header, Request, HTTPException, Query
import httpx
import os
from googleapiclient.discovery import build
import re
import time
import logging
from fastapi.responses import JSONResponse, Response
from supabase import create_client, Client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
from models import *

# from dotenv import load_dotenv
# load_dotenv()

app = FastAPI()

# ++++++++++++++++++++++++++++++
# ++++++++++ SUPABASE ++++++++++
# ++++++++++++++++++++++++++++++

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/db/table_info")
def table_info_endpoint(db: Session = Depends(get_db)):
    table_info = get_table_info(db)
    return {"status": "success", "data": table_info}

@app.post("/db/new_team")
def create_new_team(team: TeamCreateRequest, db: Session = Depends(get_db)):
    new_team = Team(
        name=team.name,
        whatsapp_number=team.whatsapp_number,
        whatsapp_number_id=team.whatsapp_number_id,
        created_at=datetime.now(timezone.utc)
    )
    try:
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
        return {"status": "success", "data": new_team}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint to create a new patient
@app.post("/db/new_patient")
def create_new_patient(patient: PatientCreateRequest,  db: Session = Depends(get_db)):
    new_patient = Patient(
        first_name=patient.first_name,
        last_name=patient.last_name,
        assigned_to=patient.assigned_to,
        phone_number=patient.phone_number,
        email=patient.email,
        created_at=datetime.now(timezone.utc)
    )
    
    # Add the new patient to the session and commit
    try:
        db.add(new_patient)
        db.commit()
        db.refresh(new_patient)  # Refresh to get the updated instance (with ID, etc.)
        return {"status": "success", "data": new_patient}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    


# Endpoint to create a new user
@app.post("/db/new_user")
def create_new_user(user: UserCreateRequest, db: Session = Depends(get_db)):
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        title=user.title,
        email=user.email,
        team_id=user.team_id,
        created_at= datetime.now(timezone.utc)
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"status": "success", "data": new_user}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/db/new_template/")
def create_new_template(template: TemplateCreateRequest, db: Session = Depends(get_db)):
    new_template = Template(
        owner=template.owner,
        duration=template.duration,
        questions=template.questions,
        title=template.title,
        created_at=datetime.now(timezone.utc)
    )
    
    try:
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        return {"status": "success", "data": new_template}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def create_new_questionnaire(patient_id, template_id, user_id, current_status, db: Session = Depends(get_db)):
    try:
        # Fetch the template from the database
        template_instance = db.query(Template).filter(Template.id == template_id).first()
        if not template_instance:
            print("ERROR: Template not found")
            raise HTTPException(status_code=404, detail="Template not found")

        # Process questions
        questions = template_instance.questions

        new_questionnaire = Questionnaire(
            patient_id=patient_id,
            template_id=template_id,
            user_id=user_id,
            questions=questions,
            current_status=current_status,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(new_questionnaire)
        db.commit()
        db.refresh(new_questionnaire)
        return {"status": "success", "data": new_questionnaire}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



def create_new_conversation(patient_id: int, user_id: int, status: str, questionnaire_id: int | None, db: Session = Depends(get_db)):
    new_conversation = Conversation(
        patient_id=patient_id,
        user_id=user_id,
        created_at=datetime.now(timezone.utc),
        ended_at=None,
        status=status,
        questionnaire_id=questionnaire_id
    )
    
    try:
        db.add(new_conversation)
        db.commit()
        db.refresh(new_conversation)
        return {"status": "success", "data": new_conversation}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def log_chat_message(conversation_id: int, patient_id: int, message: str, role: str, db: Session = Depends(get_db)):
    new_message = ChatLogMessage(
        message_text=message,
        patient_id=patient_id,
        conversation_id=conversation_id,
        created_at=datetime.now(timezone.utc),
        role=role
    )
    
    try:
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        return {"status": "success", "data": new_message}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



# +++++++++++++++++++++++++++++++
# ++++++++++ WHATSAPP +++++++++++
# +++++++++++++++++++++++++++++++

from openai import OpenAI
from pydub import AudioSegment
from io import BytesIO
import io
import tempfile
import json


WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
WHATSAPP_GRAPH_API_TOKEN = os.getenv("WHATSAPP_GRAPH_API_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

def init_openai():
    return OpenAI(api_key=os.getenv("OPENAI_KEY"))



@app.post("/whatsapp/webhook")
async def webhook(body: WhatsAppWebhookBody):
    print('webhook post')
    # Attempt to read the Request
    print(body)
    try:
        message = body.entry[0].changes[0].value.messages[0]
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid message structure")

    business_phone_number_id = body.entry[0].changes[0].value.metadata.phone_number_id

    if message.type == "text":
        print('Text message')
        message_text = message.text.body
    elif message.type == "audio":
        print('Audio message')
        message_text = await process_audio_message(message)
    else:
        print('Message type:', message.type)
    
    await mark_message_as_read(business_phone_number_id, message.id)
    await send_whatsapp_message(business_phone_number_id, message.from_, message_text, message.id)
    return {"status": "success"}


@app.get("/whatsapp/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        print("Webhook verified successfully!")
        res = Response(content=challenge, media_type="text/plain")
        return res
    else:
        raise HTTPException(status_code=403, detail="Forbidden")


async def send_whatsapp_message(business_phone_number_id: str, recipient_number, message_text, context_message_id = None):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": recipient_number,
                    "text": {"body": message_text},
                    **({"context": {"message_id": context_message_id}} if context_message_id else {})
                    }
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"Error sending WhatsApp message: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        print(f"An error occurred while sending the WhatsApp message: {str(e)}")
        raise

async def mark_message_as_read(business_phone_number_id: str, message_id):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "status": "read",
                    "message_id": message_id,
                }
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"Error marking message as read: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        print(f"An error occurred while marking the message as read: {str(e)}")
        raise


async def process_audio_message(message: Message):
    print(f"Received audio message: {message.audio.id}")
    try:

        async with httpx.AsyncClient() as client:
            # Get the audio file
            response = await client.get(
                f"https://graph.facebook.com/v20.0/{message.audio.id}/",
                headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
            )
            audio_data = response.json()
            audio_binary_data = await client.get(
                audio_data['url'],
                headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},)
            text = await transcribe_audio(audio_binary_data.content)

            return text            

    except Exception as e:
        print("Error querying the API:", str(e))
        return None

# Helper function to parse numeric responses
def parse_numeric_response(response: str) -> int:
    try:
        # Try converting directly if response is a digit
        if response.isdigit():
            return int(response)
        
        # Handle written numbers (e.g., "two", "three")
        text_to_num = {
            "zero": 0, "one": 1, "two": 2, "three": 3,
            "four": 4, "five": 5, "six": 6, "seven": 7,
            "eight": 8, "nine": 9, "ten": 10
        }
        response = response.lower().strip()
        return text_to_num.get(response, -1)
    except ValueError:
        return -1

@app.get("/")
async def root():
    return {"message": "Nothing to see here. Checkout README.md to start."}


@app.post("/init_questionnaire")
def init_questionnaire(request: InitQuestionnaireRequest, db: Session = Depends(get_db)):
    return  start_questionnaire(request.patient_id, request.user_id, request.template_id, db)
    return {"status": "success"}


def start_questionnaire(patient_id: int, user_id: int, template_id: int, db: Session):

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}

        team = db.query(Team).filter(Team.id == user.team_id).first()
        if not team:
            return {"status": "error", "message": "Team not found"}

        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return {"status": "error", "message": "Patient not found"}


        return {"status": "success", "user": user, "team": team, "patient": patient}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
    # Create a new questionnaire
    questionnaire = create_new_questionnaire(patient_id, template_id, user_id, current_status)
    
    # Create a new conversation
    conversation = create_new_conversation(patient_id, user_id, "active", questionnaire.get("data").get("id"))

    patient_phone_number = patient.get('data').get('phone_number')

    send_whatsapp_message()

    return {"status": "success", "data": conversation}



# +++++++++++++++++++++++++++++++
# ++++++++++ OPENAI +++++++++++++
# +++++++++++++++++++++++++++++++



async def flowise_chatGPT(prompt: str) -> dict:
    prompt = {"question": prompt}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://whatsappai-f2f3.onrender.com/api/v1/prediction/17bbeae4-f50b-43ca-8eb0-2aeea69d5359",
                json=prompt,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Prediction service returned an error: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        print(f"An error occurred while requesting the prediction service: {str(e)}")
        raise


# Send to OpenAI's API
async def transcribe_audio(ogg_bytes: bytes) -> str:
    print('Transcribing audio')

    try:
        url = "https://api.openai.com/v1/audio/transcriptions"

        # Create a BytesIO object from the binary data
        ogg_file = io.BytesIO(ogg_bytes)

        # Construct the multipart/form-data payload
        files = {
            'file': ('audio.ogg', ogg_file, 'audio/ogg')
        }
        data = {
            'model': 'whisper-1'
        }
        headers = {
            'Authorization': f'Bearer {OPENAI_KEY}'
        }

        # Make the request using httpx.AsyncClient
        async with httpx.AsyncClient() as client:
            response = await client.post(url, files=files, data=data, headers=headers)

        # Check for a successful response
        response.raise_for_status()

        transcription_result = response.json()
        return transcription_result.get('text')

    except httpx.RequestError as e:
        print(f"An error occurred while requesting {e.request.url!r}: {str(e)}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"Error response {e.response.status_code} while requesting {e.request.url!r}: {str(e)}")
        return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None
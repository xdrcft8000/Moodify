import asyncio
from fastapi import FastAPI, Header, Request, HTTPException, Query
import httpx
import os
from googleapiclient.discovery import build
import re
import time
import logging
from fastapi.responses import JSONResponse, Response
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, RootModel
from supabase import create_client, Client

class Text(BaseModel):
    body: str

class Audio(BaseModel):
    id: str
    mime_type: str

class Message(BaseModel):
    from_: Optional[str] = Field(None, alias='from')
    id: Optional[str] = None
    timestamp: Optional[str] = None
    text: Optional[Text] = None
    type: Optional[str] = None
    audio: Optional[Audio] = None


class Profile(BaseModel):
    name: str

class Contact(BaseModel):
    profile: Profile
    wa_id: str

class Metadata(BaseModel):
    display_phone_number: str
    phone_number_id: str

class Value(BaseModel):
    messaging_product: str
    metadata: Metadata
    contacts: List[Contact]
    messages: List[Message]

class Change(BaseModel):
    value: Value
    field: str

class Entry(BaseModel):
    id: str
    changes: List[Change]

class WhatsAppWebhookBody(BaseModel):
    object: str
    entry: List[Entry]


class AnyRequestModel(RootModel[Dict[str, Any]]):
    pass
    
# from dotenv import load_dotenv
# load_dotenv()

app = FastAPI()

# ++++++++++++++++++++++++++++++
# ++++++++++ SUPABASE ++++++++++
# ++++++++++++++++++++++++++++++

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


@app.post('/db/insert')
async def insert_data(request: Request):
    print('Inserting data')
    logging.info('Inserting data')
    try:
        request = await request.json()
        print(request)
        table = request['table']
        data = request['data']
        print('Table:', table)
        print('title:', data)
    except Exception as e:
        print('Error:', str(e))
        return JSONResponse(content={"status": "error"}, status_code=500)
    if not table or not data:
        return JSONResponse(content={"status": "error"}, status_code=400)
    try:
        response = supabase.table(table).insert(data).execute()
        print('Response:', response)
        return JSONResponse(content={"status": "success", "data": response.data}, status_code=200)
    except Exception as e:
        print('Error:', str(e))
        return JSONResponse(content={"status": "error"}, status_code=500)





# ++++++++++++++++++++++++++++++
# ++++++++++ MOODIFY ++++++++++
# ++++++++++++++++++++++++++++++

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


async def process_text_message(message: Message, business_phone_number_id: str):
    print(f"Received message: {message.text.body}")
    prompt = message.text.body

    default_message_template = "*Wagwaan family* 🤙🏾. Dr Singh wants 2 kno a bit about ur day and dat 😊 \n send a vn tho, i aint on dat reading ting 2daii. \n _+ dont make it longer than 2 mins tho man aint tryna hear a podcast._ \n I'm on dat polygot ting so any language is calm. \n \n bless up urself gstar \n -1- \n \n (powered by Moodify(?) n dat u know wat it is cmon.)"

    try:
        # flowise_response = await flowise_chatGPT(prompt)

        # Prepare the message text to be sent as a reply
        # message_text = f"Here's a joke about '{message.text.body}': {flowise_response['text']}"

        # Send a reply to the user
        await send_whatsapp_message(
            business_phone_number_id=business_phone_number_id,
            recipient_number=message.from_,
            message_text=default_message_template,
            context_message_id=message.id
        )

        # Mark the incoming message as read
        await mark_message_as_read(
            business_phone_number_id=business_phone_number_id,
            message_id=message.id
        )

        return {"status": "success"}

    except Exception as e:
        print("Error processing the message:", str(e))
        raise HTTPException(status_code=500, detail="Error processing the message")
    

async def process_audio_message(message: Message, business_phone_number_id: str):
    print(f"Received audio message: {message.audio.id}")
    try:
        # Use an async client to make HTTP requests
        async with httpx.AsyncClient() as client:
            # Call to external service
            response = await client.get(
                f"https://graph.facebook.com/v20.0/{message.audio.id}/",
                headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
            )
            audio_data = response.json()
            audio_binary_data = await client.get(
                audio_data['url'],
                headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},)
            text = await transcribe_audio(audio_binary_data.content)

            await send_whatsapp_message(
                business_phone_number_id=business_phone_number_id, 
                recipient_number=message.from_,
                message_text=f"I heard: \n{text}", 
                context_message_id=message.id)
            
            await mark_message_as_read(
                business_phone_number_id=business_phone_number_id,
                message_id=message.id
            )

            return {"status": "success"}
    except Exception as e:
        print("Error querying the API:", str(e))
        raise HTTPException(status_code=500, detail="Error getting media location")
    

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
        return await process_text_message(message, business_phone_number_id)
    elif message.type == "audio":
        print('Audio message')
        return await process_audio_message(message, business_phone_number_id)

    else:
        print('Message type:', message.type)
        return {"status": "success"}


@app.get("/")
async def root():
    return {"message": "Nothing to see here. Checkout README.md to start."}

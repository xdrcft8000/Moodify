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


WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
WHATSAPP_GRAPH_API_TOKEN = os.getenv("WHATSAPP_GRAPH_API_TOKEN")


def init_openai():
    return OpenAI(api_key=os.getenv("OPENAI_KEY"))


#  SPEECH TO TEXT:
# The best way to do this is to use a service that supports OGG
# Current implementation is quicker but not the best way to do it

def convert_ogg_to_wav(ogg_data: bytes) -> BytesIO:
    print('Converting OGG to WAV')
    try:
        audio = AudioSegment.from_file(BytesIO(ogg_data), format="ogg")
        wav_data = BytesIO()
        audio.export(wav_data, format="wav")
        wav_bytes = wav_data.getvalue()
        print('WAV bytes:', wav_bytes)
        return wav_bytes
    except Exception as e:
        print("Error converting OGG to WAV:", str(e))
        return None

# def check_ogg_file(ogg_data: bytes):
#     print('Checking OGG file')
#     try:
#         # Load the OGG file into a bytes stream
#         ogg_stream = io.BytesIO(ogg_data)

#         # Probe the file to get metadata
#         probe = ffmpeg.probe(ogg_stream)
        
#         print("File format:", probe.get('format', {}).get('format_name'))
#         print("Duration:", probe.get('format', {}).get('duration'))
#         print("Bitrate:", probe.get('format', {}).get('bit_rate'))

#         return probe.get('format', {}).get('format_name') == 'ogg'
#     except ffmpeg.Error as e:
#         print("Error checking OGG file:", e)
#         return False


# Send to OpenAI's API
async def transcribe_audio(ogg_file: bytes):
    print('Transcribing audio')
    print('OGG file:', ogg_file)
    try:
        openai = init_openai()
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=ogg_file,
            response_format="text"
        )
        print('transcription:', response.text)
        return response.text
    except Exception as e:
        print("Error transcribing audio:", str(e))
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


@app.post("/whatsapp/webhook")
async def webhook(body: WhatsAppWebhookBody):
    print('webhook post')
    # Attempt to read the Request
    print(body)
    try:
        message = body.entry[0].changes[0].value.messages[0]
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid message structure")

    if message.type == "text":
        business_phone_number_id = body.entry[0].changes[0].value.metadata.phone_number_id
        prompt = {"question": message.text.body}
        print(f"Received message: {message.text.body}")
        try:
            # Use an async client to make HTTP requests
            async with httpx.AsyncClient() as client:
                # Call to external service
                response = await client.post(
                    "https://whatsappai-f2f3.onrender.com/api/v1/prediction/17bbeae4-f50b-43ca-8eb0-2aeea69d5359",
                    json=prompt,
                    headers={"Content-Type": "application/json"},
                )
                flowise_data = response.json()
                # Send a reply to the user
                await client.post(
                    f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
                    headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
                    json={
                        "messaging_product": "whatsapp",
                        "to": message.from_,
                        "text": {"body": f"Here's a joke about '{message.text.body}': {flowise_data['text']}"},
                        "context": {"message_id": message.id},
                    }
                )

                # Mark the incoming message as read
                await client.post(
                    f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
                    headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
                    json={
                        "messaging_product": "whatsapp",
                        "status": "read",
                        "message_id": message.id,
                    }
                )
                return {"status": "success"}

        except Exception as e:
            print("Error querying the API:", str(e))
            raise HTTPException(status_code=500, detail="Error querying the API")
    elif message.type == "audio":
        print('Audio message')
        print(message.audio.id)
        print(message.audio.mime_type)
        try:
            # Use an async client to make HTTP requests
            async with httpx.AsyncClient() as client:
                # Call to external service
                response = await client.get(
                    f"https://graph.facebook.com/v20.0/{message.audio.id}/",
                    headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
                )
                audio_data = response.json()
                print(audio_data)
                print(audio_data['url'])

                audio_binary_data = await client.get(
                    audio_data['url'],
                    headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},)
                print('audio_binary_data:', audio_binary_data.headers)
                print('audio_binary_data:', audio_binary_data)
                text = await transcribe_audio(audio_binary_data.content)
                print(text)
                return {"status": "success"}
        except Exception as e:
            print("Error querying the API:", str(e))
            raise HTTPException(status_code=500, detail="Error getting media location")


    else:
        print('Message type:', message.type)
        return {"status": "success"}


@app.get("/")
async def root():
    return {"message": "Nothing to see here. Checkout README.md to start."}

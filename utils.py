import httpx
import os
import re
import time
import logging
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAI
from pydub import AudioSegment
from io import BytesIO
import io
import tempfile
import json



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
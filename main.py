import traceback
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Header, Request, HTTPException, Query
import httpx
import os
from googleapiclient.discovery import build
from fastapi.responses import JSONResponse, Response
from supabase import create_client, Client
from sqlalchemy.exc import SQLAlchemyError
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)
from db import *
from models import *
from utils import *
from core import *
# from dotenv import load_dotenv
# load_dotenv()



# +++++++++++++++++++++++++++++++
# ++++++++++ WHATSAPP +++++++++++
# +++++++++++++++++++++++++++++++


WHATSAPP_WEBHOOK_VERIFY_TOKEN = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
WHATSAPP_GRAPH_API_TOKEN = os.getenv("WHATSAPP_GRAPH_API_TOKEN")

#Inital route that verifies the webhook
@app.get("/whatsapp/webhook")
async def whatsapp_verify_webhook(request: Request):
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
async def whatsapp_notify_webhook(request: WebhookRequest, db: Session = Depends(get_db)):
    try:
        for entry in request.entry:
            for change in entry.changes:
                value = change.value
                if value.messages:
                    message = value.messages[0]
                    print(f"message from: {message.from_}")
                    patient = get_patient_from_phone_number(message.from_, db)
                    if not patient:
                        print("ERROR: Recieved message from unknown patient")
                        return {"status": "success"}
                    print(f"Patient: {patient}")
                    if message.type == 'text':
                        print(f"Text message: {message.text['body']}")
                        message_text = message.text['body']
                        await handle_incoming_message(patient.id, message_text, message.id, db)

                    elif message.type == 'audio':
                        print(f"Audio message: {message.audio}")
                        message_text = await process_audio_message(message)
                        await handle_incoming_message(patient.id, message_text, message.id, db)

                    elif message.type == 'button':
                        print(f"Button pressed: {message.button['payload']}")
                        message_text = "Thank you for pressing a button"
                        if message.button['payload'] == 'Begin':
                            message_text = "Let's start the questionnaire"
                            await handle_begin_button(patient.id, db)

                    business_phone_number_id = value.metadata.phone_number_id
                    message_id = message.id
                    message_from = message.from_

                    await mark_message_as_read(business_phone_number_id, message_id)

                elif value.statuses:
                    status = value.statuses[0]
                    print(f"Status update: {status.status} for message {status.id}")

        return {"status": "success"}
    except Exception as e:
        print(f"Error processing WhatsApp webhook: {str(e)}")
        print(f"Full error details: {traceback.format_exc()}")
        return {"status": "success"}

def get_patient_from_phone_number(phone_number: str, db: Session):
    return db.query(Patient).filter(Patient.phone_number == phone_number).first()

async def handle_incoming_message(patient_id: int, message_text: str, message_id: str, db: Session):
    
    conversation = db.query(Conversation).filter(
        Conversation.patient_id == patient_id,
        Conversation.status == "QuestionnaireInProgress",
        Conversation.ended_at > datetime.now(timezone.utc)
    ).order_by(Conversation.created_at.desc()).first()


    twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
    conversation_awaiting_feedback = db.query(Conversation).filter(
        Conversation.patient_id == patient_id,
        Conversation.status == "ReadyToComplete",
        Conversation.questionnaire_id.isnot(None),
        Conversation.ended_at > twenty_four_hours_ago,
    ).order_by(Conversation.created_at.desc()).first()

    most_recent_conversation = db.query(Conversation).filter(
        Conversation.patient_id == patient_id
    ).order_by(Conversation.created_at.desc()).first()


    if conversation:
        log_chat_message(conversation.id, patient_id, message_text, "user", db)
        questionnaire = db.query(Questionnaire).filter(Questionnaire.patient_id == patient_id).order_by(Questionnaire.created_at.desc()).first()
        parsed_response = await parse_message_text(message_text)
        if not parsed_response:
            await ask_for_clarication(patient_id, conversation.id, db, questionnaire)
            return
        validation_response = await range_check_response(parsed_response, questionnaire)
        if validation_response != "Valid":
            await send_whatsapp_message(patient_id, conversation.id, validation_response, db)
            return
        skipped = parsed_response == "skip"
        if parsed_response == "end":
            cancel_questionnaire(conversation, questionnaire, message_id, db)
        else:
            await answer_question(parsed_response, conversation, questionnaire, message_id, db, skipped)

    elif conversation_awaiting_feedback:
        # Save the message as a comment
        log_chat_message(conversation_awaiting_feedback.id, patient_id, message_text, "user", db)
        questionnaire = db.query(Questionnaire).filter(Questionnaire.id == conversation_awaiting_feedback.questionnaire_id).first()
        if "comments" not in questionnaire.questions:
            questionnaire.questions["comments"] = []
        questionnaire.questions["comments"].append(message_text)
        send_whatsapp_message(patient_id, conversation_awaiting_feedback.id, "Thank you for sharing, your message has been saved for your clinician to review.", db)
        db.commit()


    elif most_recent_conversation:
        log_chat_message(most_recent_conversation.id, patient_id, message_text, "user", db)
        send_whatsapp_message(patient_id, most_recent_conversation.id, "Thank you for sharing! We currently don't process any messages unless they're part of a questionnaire. \n\n Hang tight, your clinician will send another one soon.", db)
        db.commit()

    else:
    #LATER NEED TO HANDLE THE CASE WHERE THERE IS NO IN PROGRESS QUESTIONNAIRE
        print("No conversation found")
        send_whatsapp_message(patient_id, "We have no record of you as a patient. Please contact your mental health care provider to get started.", db)


async def handle_begin_button(patient_id: int, db: Session):

    # Get the most recent conversation with status "Initiated"
    conversation = db.query(Conversation).filter(
        Conversation.patient_id == patient_id,
        Conversation.status == "Initiated"
    ).order_by(Conversation.created_at.desc()).first()

    log_chat_message(conversation.id, patient_id, "Begin", "user", db)

    questionnaire = db.query(Questionnaire).filter(Questionnaire.id == conversation.questionnaire_id).first()


    if questionnaire:
        # Update the conversation status to "QuestionnaireInProgress"
        conversation.status = "QuestionnaireInProgress"
        await ask_question(questionnaire, conversation.id, patient_id, db)
        db.commit()
        print("Questionnaire inprogress")
    else:
        print("No initiated conversation found for 'Begin' button")


async def ask_for_clarication(patient_id: int, conversation_id: int, db: Session, questionnaire: Questionnaire):
    help_text = questionnaire.questions["answer_schemes"][questionnaire.current_status]["explanation"]
    help_text = f"I didn't understand that. {help_text} \n\n You can respond with 'skip' to skip the question or 'end' if you'd like to end the questionnaire early."
    await send_whatsapp_message(patient_id, conversation_id, help_text, db)

async def range_check_response(answer: str, questionnaire: Questionnaire):
    current_index = int(questionnaire.current_status)
    questions = questionnaire.questions["questions_list"]
    answer = int(answer)
    for question in questions:
        if question["index"] == current_index:
            response_format = question["response_format"]
            break
    answer_scheme = questionnaire.questions["answer_schemes"][response_format]
    if range in answer_scheme:
        start = answer_scheme["range"]["start"]
        end = answer_scheme["range"]["end"]
        if start <= answer <= end:
            return "Valid"
        else:
            return f"{answer_scheme['explanation']}. \n\n You can respond with 'skip' to skip the question or 'end' if you'd like to end the questionnaire early."
    return "Valid"

async def ask_question(questionnaire: Questionnaire, conversation_id: int, patient_id: int, db: Session):
    current_question_index = int(questionnaire.current_status)
    print(f"Asking question: {current_question_index}")
    questions = questionnaire.questions["questions_list"]
    question_text = ""
    for question in questions:
        print(f"Question: {question}")
        index = question["index"]
        if index == current_question_index:
            question_text = question["text"]
            answer_scheme = question["response_format"]
            print(f"Answer scheme: {answer_scheme}")
            break
    explanation = questionnaire.questions["answer_schemes"][answer_scheme]["explanation"]
    print(f"Explanation: {explanation}")
    question_text = f"Question {current_question_index + 1}: {question_text}\n\n{explanation}"
    print(f"Question text: {question_text}")
    await send_whatsapp_message(patient_id, conversation_id, question_text, db)



async def answer_question(answer: str, conversation: Conversation, questionnaire: Questionnaire, message_id: str, db: Session, skipped = False):
    emoji = "⏭️" if skipped else "👍"
    react_to_message(questionnaire.patient_id, message_id, emoji, db)
    current_index = int(questionnaire.current_status)
    for question in questionnaire.questions["questions_list"]:
        if question["index"] == current_index:
            question["answer"] = answer
            break
    db.commit()
    if current_index == len(questionnaire.questions["questions_list"]) - 1:
        finish_questionnaire(conversation, questionnaire, message_id, db)
    else:
        questionnaire.current_status = str(current_index + 1)
        db.commit()
        await ask_question(questionnaire, conversation.id, questionnaire.patient_id, db)


def finish_questionnaire(conversation: Conversation, questionnaire: Questionnaire, message_id: str, db: Session):
    conversation.status = "ReadyToComplete"
    conversation.ended_at = datetime.now(timezone.utc)
    questionnaire.current_status = "Completed"
    db.commit()
    send_whatsapp_message(questionnaire.patient_id,
                           conversation.id,
                           "Thank you for completing the questionnaire. We'll send your clinician a summary of your responses. If you have anything else you want to say about how you're in the meantime, you can respond here. \n\n Take care!",
                           db,
                           message_id)

def cancel_questionnaire(conversation: Conversation, questionnaire: Questionnaire, message_id: str, db: Session):
    conversation.status = "ReadyToComplete"
    conversation.ended_at = datetime.now(timezone.utc)
    questionnaire.current_status = "Cancelled"
    db.commit()
    send_whatsapp_message(questionnaire.patient_id,
                           conversation.id,
                           "Got you, we'll stop here. \n\n We'll send your clinician a summary of your responses so far. If you have any feedback in the meantime, you can send a message or a voice note here. \n\n Take care!",
                           db,
                           message_id)

def get_patient_relations(patient_id:int, db: Session):
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            print("Error in get_patient_relations: Patient not found")
            raise Exception("Error in get_patient_relations: Patient not found")
        print('found patient')
        if patient.assigned_to is None:
            print("Error in get_patient_relations: Patient not assigned to any user")
            raise Exception("Error in get_patient_relations: Patient not assigned to any user")
        user = db.query(User).filter(User.id == patient.assigned_to).first()
        if not user:
            print("Error in get_patient_relations: User not found")
            raise Exception("Error in get_patient_relations: User not found")
        print('found user')
        team = db.query(Team).filter(Team.id == user.team_id).first()
        if not team:
            print("Error in get_patient_relations: Team not found")
            raise Exception("Error in get_patient_relations: Team not found")
        print('found team')
        return patient, user, team
    except Exception as e:
        print(f"Error in get_patient_relations: {str(e)}")
        raise

async def send_whatsapp_message(patient_id: int, conversation_id: int, message_text: str, db: Session, context_message_id = None, logging = True):
    try:
        print(f"Sending message: {message_text}")
        patient, user, team = get_patient_relations(patient_id, db)
        recipient_number = patient.phone_number
        business_phone_number_id = team.whatsapp_number_id

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
            if logging:
                log_chat_message(conversation_id, patient_id, message_text, "system", db)
    except httpx.HTTPStatusError as e:
        print(f"Error sending WhatsApp message: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        print(f"An error occurred while sending the WhatsApp message: {str(e)}")
        raise



async def send_whatsapp_begin_questionnaire_template(patient_id, conversation_id, duration,db: Session):
    patient, user, team = get_patient_relations(patient_id, db)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{team.whatsapp_number_id}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": patient.phone_number,
                    "type": "template",
                    "template": {
                        "name": "begin_questionnaire",
                        "language": {
                            "code": "en"
                        },
                        "components": [
                            {
                                "type": "body",
                                "parameters": [
                                    {
                                        "type": "text",
                                        "text": duration
                                    }
                                ]
                            },
                            {
                                 "type": "BUTTON",
                                 "sub_type": "QUICK_REPLY",
                                 "index": "0",
                                 "parameters": [
                                     {
                                         "type": "text",
                                         "text": "Begin",
                                         "payload": "Begin"
                                     }
                                 ]
                             }
                        ]
                    }
                }
            )
            response.raise_for_status()
            log_chat_message(conversation_id, patient_id, "Template: begin_questionnaire", "system", db)
    except httpx.HTTPStatusError as e:
        print(f"Error sending WhatsApp template message: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        print(f"An error occurred while sending the WhatsApp template message: {str(e)}")
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


async def react_to_message(patient_id: int, message_id: str, emoji: str, db: Session):
    patient, user, team = get_patient_relations(patient_id, db)
    business_phone_number_id = team.whatsapp_number_id

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://graph.facebook.com/v18.0/{business_phone_number_id}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_GRAPH_API_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "type": "reaction",
                    "reaction": {
                        "message_id": message_id,
                        "emoji": emoji
                    }
                }
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Error reacting to message: {e.response.status_code}")
        raise
    except httpx.RequestError as e:
        print(f"An error occurred while reacting to the message: {str(e)}")
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
    

async def parse_message_text(message_text: str) -> str | None:
    message_text = message_text.lower().strip()
    
    if message_text in ["end", "skip"]:
        return message_text

    try:
        if message_text == "0":
            return "0"

        if message_text.isdigit():
            return int(message_text)
        
        text_to_num = {
            "zero": 0, "one": 1, "two": 2, "three": 3,
            "four": 4, "five": 5, "six": 6, "seven": 7,
            "eight": 8, "nine": 9, "ten": 10
        }
        result = text_to_num.get(message_text)
        if result is not None:
            return result
        
        # If we reach here, use OpenAI to interpret the message
        chat_gpt = init_openai()
        response = chat_gpt.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that interprets user messages. If the user intends to say a number (0-10), 'skip', or 'end', respond with just that word or number. For typos or wordy messages, interpret the likely intent. If the user doesn't intend any of these, respond with 'None'. Examples: 'I want to stop' -> end, 'Let's move on' -> skip, 'I feel about a seven today' -> 7, 'I had toast for breakfast' -> None. Response with only the desired string without any other text or any quotation marks."},
                {"role": "user", "content": message_text}
            ]
        )
        interpreted_text = response.choices[0].message.content.strip().lower()
        print(interpreted_text)
        if interpreted_text.isdigit():
            return int(interpreted_text)
        elif interpreted_text in ["skip", "end"]:
            return interpreted_text
        else:
            return None
    except ValueError:
        return None
    

# +++++++++++++++++++++++++++++++
# ++++++++++ MOODULATE ++++++++++
# +++++++++++++++++++++++++++++++


@app.get("/")
async def root():
    return {"message": "Nothing to see here. Checkout README.md to start."}


@app.post("/init_questionnaire")
async def init_questionnaire(request: InitQuestionnaireRequest, db: Session = Depends(get_db)):

    try:
        # Make sure that there isn't already an inprogress conversation for this patient
        conversation = db.query(Conversation).filter(
            Conversation.patient_id == request.patient_id,
            Conversation.status == "QuestionnaireInProgress",
            Conversation.ended_at > datetime.now(timezone.utc)
        ).first()

        if conversation:
            return {"status": "error", "message": "There is already an inprogress conversation for this patient"}


        template = db.query(Template).filter(Template.id == request.template_id).first()

        # Check if a questionnaire with the same patient, template, and status (0) already exists
        questionnaire = db.query(Questionnaire).filter(
            Questionnaire.patient_id == request.patient_id,
            Questionnaire.template_id == request.template_id,
            Questionnaire.current_status == "0"
        ).first()

        # Check if a conversation with the same patient and status ("Initiated") already exists
        conversation = db.query(Conversation).filter(
            Conversation.patient_id == request.patient_id,
            Conversation.status == "Initiated"
        ).first()

        already_initiated = conversation and questionnaire
        if not already_initiated:

            questionnaire = create_new_questionnaire(request.patient_id, request.template_id, request.user_id, "0", db)

            conversation = create_new_conversation(request.patient_id, "Initiated", questionnaire.id, db)

        await send_whatsapp_begin_questionnaire_template(request.patient_id, conversation.id, template.duration, db)

        return {"status": "success", "data":"conversation and questionnaire created"}
    except Exception as e:
        return {"status": "error", "message": str(e)}




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
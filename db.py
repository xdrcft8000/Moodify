from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import os
from googleapiclient.discovery import build
from fastapi.responses import JSONResponse, Response
from supabase import create_client, Client
from sqlalchemy.exc import SQLAlchemyError
from models import *
from main import app


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


def create_item_in_db(db: Session, item):
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"status": "success", "data": item}
    except SQLAlchemyError as e:
        print('Error:', str(e), 'Rolling back')
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

def create_item_in_db_internal(db: Session, item):
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
        return item
    except Exception as e:
        print('Error:', str(e), 'Rolling back')
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create item: {str(e)}")


@app.get("/db/table_info")
def table_info_endpoint(db: Session = Depends(get_db)):
    table_info = get_table_info(db)
    return {"status": "success", "data": table_info}

# Helper function to create new objects
@app.post("/db/new_team")
def create_new_team(team: TeamCreateRequest, db: Session = Depends(get_db)):
    new_team = Team(
        name=team.name,
        whatsapp_number=team.whatsapp_number,
        whatsapp_number_id=team.whatsapp_number_id,
        created_at=datetime.now(timezone.utc)
    )
    return create_item_in_db(db, new_team)

@app.post("/db/new_patient")
def create_new_patient(patient: PatientCreateRequest, db: Session = Depends(get_db)):
    new_patient = Patient(
        first_name=patient.first_name,
        last_name=patient.last_name,
        assigned_to=patient.assigned_to,
        phone_number=patient.phone_number,
        email=patient.email,
        created_at=datetime.now(timezone.utc)
    )
    return create_item_in_db(db, new_patient)


@app.post("/db/new_user")
def create_new_user(user: UserCreateRequest, db: Session = Depends(get_db)):
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        title=user.title,
        email=user.email,
        team_id=user.team_id,
        created_at=datetime.now(timezone.utc)
    )
    return create_item_in_db(db, new_user)


@app.post("/db/new_template")
def create_new_template(template: TemplateCreateRequest, db: Session = Depends(get_db)):
    new_template = Template(
        owner=template.owner,
        duration=template.duration,
        questions=template.questions,
        title=template.title,
        created_at=datetime.now(timezone.utc)
    )
    return create_item_in_db(db, new_template)


def create_new_questionnaire(patient_id, template_id, user_id, current_status, db: Session):
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
        return create_item_in_db_internal(db, new_questionnaire)
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))



def create_new_conversation(patient_id: int, status: str, questionnaire_id: int | None, db: Session):
    new_conversation = Conversation(
        patient_id=patient_id,
        created_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc) + timedelta(days=3),
        status=status,
        questionnaire_id=questionnaire_id
    )
    return create_item_in_db_internal(db, new_conversation)


def log_chat_message(conversation_id: int, patient_id: int, message: str, role: str, db: Session):
    new_message = ChatLogMessage(
        message_text=message,
        patient_id=patient_id,
        conversation_id=conversation_id,
        created_at=datetime.now(timezone.utc),
        role=role
    )

    return create_item_in_db_internal(db, new_message)

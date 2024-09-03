import os
from pydantic import BaseModel, Field, RootModel, EmailStr
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import declarative_base, sessionmaker, Session


#PYDANTIC MODELS

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



class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    assigned_to: Optional[int] = None
    phone_number: str
    email: EmailStr

class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    title: Optional[str] = None
    email: EmailStr

class TemplateCreateRequest(BaseModel):
    owner: int
    duration: str
    title: str
    questions: Dict[str, Any]  

class QuestionnaireCreateRequest(BaseModel):
    patient_id: int
    template_id: int
    user_id: int
    questions: Dict[str, Any]
    current_status: str

class AnyRequestModel(RootModel[Dict[str, Any]]):
    pass



#POSTGRES MODELS

from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import declarative_base
# from dotenv import load_dotenv
# load_dotenv()


# Connect to your PostgreSQL database
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL, echo=True)

# Reflect the tables
metadata = MetaData()
metadata.reflect(bind=engine)

# Create a base class for declarative models
Base = declarative_base(metadata=metadata)

# Example of accessing a table
class User(Base):
    __table__ = metadata.tables['Users'] 

class Patient(Base):
    __table__ = metadata.tables['Patients'] 

class Template(Base):
    __table__ = metadata.tables['Templates'] 

class Questionnaire(Base):
    __table__ = metadata.tables['Questionnaires']  

class ChatLogMessage(Base):
    __table__ = metadata.tables['Chat_logs'] 

class Conversation(Base):
    __table__ = metadata.tables['Conversations']  


SessionLocal = sessionmaker(bind=engine)

def get_table_info(db: Session) -> List[Dict[str, Any]]:
    table_info = []
    models = [User, Patient, Template, Questionnaire, ChatLogMessage, Conversation]

    for model in models:
        table_details = {
            "table_name": model.__table__.name,
            "columns": []
        }

        table = model.__table__
        for column in table.columns:
            column_info = {
                "name": column.name,
                "type": str(column.type),
                "primary_key": column.primary_key
            }
            table_details["columns"].append(column_info)

        table_info.append(table_details)

    return table_info

# Call the function to print the table information

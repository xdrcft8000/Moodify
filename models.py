import os
from pydantic import BaseModel, Field, RootModel, EmailStr
from typing import List, Optional, Dict, Any
# from dotenv import load_dotenv
# load_dotenv()


#PYDANTIC REQUEST MODELS

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

class TeamCreateRequest(BaseModel):
    name: str
    whatsapp_number: str
    whatsapp_number_id: str

class PatientCreateRequest(BaseModel):
    first_name: str
    last_name: str
    assigned_to: Optional[int] = None
    phone_number: str
    email: EmailStr

class UserCreateRequest(BaseModel):
    first_name: str
    last_name: str
    team_id: int
    title: Optional[str] = None
    email: EmailStr

class TemplateCreateRequest(BaseModel):
    owner: int
    duration: str
    title: str
    team_id: Optional[int] = None
    questions: Dict[str, Any]  

class QuestionnaireCreateRequest(BaseModel):
    patient_id: int
    template_id: int
    user_id: int
    questions: Dict[str, Any]
    current_status: str

class AnyRequestModel(RootModel[Dict[str, Any]]):
    pass

class InitQuestionnaireRequest(BaseModel):
    patient_id: int
    template_id: int
    user_id: int

#POSTGRES DB MODELS

from sqlalchemy import create_engine, MetaData, Table, inspect
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func


DATABASE_URL = os.environ.get('DATABASE_URL')  # Ensure this environment variable is correctly set
engine = create_engine(DATABASE_URL, echo=True)

# Create a base class for declarative models
Base = declarative_base()

# Set up a session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Team model
class Team(Base):
    __tablename__ = 'Teams'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    name = Column(Text, nullable=False)
    whatsapp_number = Column(String(255), nullable=False)
    whatsapp_number_id = Column(BigInteger, nullable=False)
    users = relationship("User", back_populates="team")
    templates = relationship("Template", back_populates="team")

# User model
class User(Base):
    __tablename__ = 'Users'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    title = Column(String(255), nullable=True)
    email = Column(String(255), nullable=False)
    team_id = Column(BigInteger, ForeignKey('Teams.id'), nullable=False)

    team = relationship("Team", back_populates="users")
    patients = relationship("Patient", back_populates="assigned_to_user")
    templates = relationship("Template", back_populates="owner_user")
    questionnaires = relationship("Questionnaire", back_populates="user")

# Patient model
class Patient(Base):
    __tablename__ = 'Patients'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    assigned_to = Column(BigInteger, ForeignKey('Users.id'), nullable=True)
    phone_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    assigned_to_user = relationship("User", back_populates="patients")
    questionnaires = relationship("Questionnaire", back_populates="patient")
    chat_logs = relationship("ChatLogMessage", back_populates="patient")
    conversations = relationship("Conversation", back_populates="patient")

# Template model
class Template(Base):
    __tablename__ = 'Templates'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    owner = Column(BigInteger, ForeignKey('Users.id'))
    duration = Column(Text)
    questions = Column(JSONB)
    title = Column(Text)
    team_id = Column(BigInteger, ForeignKey('Teams.id'))

    owner_user = relationship("User", back_populates="templates")
    team = relationship("Team", back_populates="templates")
    questionnaires = relationship("Questionnaire", back_populates="template")

# Questionnaire model
class Questionnaire(Base):
    __tablename__ = 'Questionnaires'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    patient_id = Column(BigInteger, ForeignKey('Patients.id'))
    template_id = Column(BigInteger, ForeignKey('Templates.id'))
    user_id = Column(BigInteger, ForeignKey('Users.id'))
    questions = Column(JSONB)
    current_status = Column(String)

    patient = relationship("Patient", back_populates="questionnaires")
    template = relationship("Template", back_populates="questionnaires")
    user = relationship("User", back_populates="questionnaires")
    conversations = relationship("Conversation", back_populates="questionnaire")

# ChatLogMessage model
class ChatLogMessage(Base):
    __tablename__ = 'Chat_logs'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    role = Column(Text)
    patient_id = Column(BigInteger, ForeignKey('Patients.id'))
    message_text = Column(Text)
    conversation_id = Column(BigInteger, ForeignKey('Conversations.id'))

    patient = relationship("Patient", back_populates="chat_logs")
    conversation = relationship("Conversation", back_populates="chat_logs")

# Conversation model
class Conversation(Base):
    __tablename__ = 'Conversations'
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    ended_at = Column(TIMESTAMP, server_default=None)
    questionnaire_id = Column(BigInteger, ForeignKey('Questionnaires.id'))
    status = Column(Text)
    patient_id = Column(BigInteger, ForeignKey('Patients.id'))

    questionnaire = relationship("Questionnaire", back_populates="conversations")
    chat_logs = relationship("ChatLogMessage", back_populates="conversation")
    patient = relationship("Patient", back_populates="conversations")

SessionLocal = sessionmaker(bind=engine)

def get_table_info(db: Session) -> List[Dict[str, Any]]:
    # Use SQLAlchemy's Inspector to fetch information directly from the database
    inspector = inspect(db.bind)
    
    # Get a list of all table names in the database
    table_names = inspector.get_table_names()
    
    table_info = []

    # Loop through each table in the database
    for table_name in table_names:
        table_details = {
            "table_name": table_name,
            "columns": []
        }
        
        # Get column information for each table
        columns = inspector.get_columns(table_name)
        for column in columns:
            column_info = {
                "name": column['name'],
                "type": str(column['type']),
                "nullable": column['nullable'],  # Whether the column can contain NULL values
                "default": column.get('default'),  # The default value (if any)
                "autoincrement": column.get('autoincrement', False),  # Auto-increment
                "primary_key": column.get('primary_key', False),  # Primary key
            }
            
            # Check for foreign key relationships
            foreign_keys = inspector.get_foreign_keys(table_name)
            column_info["foreign_key"] = None
            for fk in foreign_keys:
                for fk_column in fk['constrained_columns']:
                    if fk_column == column['name']:
                        column_info["foreign_key"] = {
                            "referred_table": fk['referred_table'],
                            "referred_column": fk['referred_columns'][0]
                        }

            table_details["columns"].append(column_info)
        
        table_info.append(table_details)
    
    return table_info